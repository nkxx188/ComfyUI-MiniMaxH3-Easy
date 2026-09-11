"""Optional sampling strategies shared by MiniMax H3 Easy workflows.

The strategy objects in this module are lightweight execution plans.  Nodes
may carry one through a workflow without modifying the MODEL, conditioning, or
latent objects.  The first strategy is a progressive-resolution SelfLift-style
H3 sampler: early Euler evaluations run on a smaller spatial grid, the clean
prediction is lifted to the requested grid, and the remaining evaluations run
at the final resolution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import torch
import torch.nn.functional as F

import comfy.k_diffusion.sampling
import comfy.model_management
import comfy.model_sampling
import comfy.nested_tensor
import comfy.sample
import comfy.samplers

from .h3_latent_upscaler import MiniMaxH3EasyLatentUpscaler3D


LOGGER = logging.getLogger("MiniMaxH3Easy.sampling")
SAMPLING_PLAN_TYPE = "MINIMAX_H3_SAMPLING_PLAN"
SELFLIFT_KIND = "selflift"


@dataclass(frozen=True)
class MiniMaxH3SamplingPlan:
    """A reusable, immutable sampling strategy selected by a workflow node."""

    kind: str
    cfg: float = 1.0
    transition_step: int = 5
    lowres_scale: float = 0.8
    correction_ratio: float = 0.0
    correction_min: float = 0.5
    correction_max: float = 1.0
    upscaler_model: str = "none"
    upscaler_device: str = "cuda"
    upscaler_precision: str = "fp16"
    upscaler_chunking: bool = True


def _streams(value: Any) -> tuple[list[torch.Tensor], bool]:
    if isinstance(value, (tuple, list)):
        return list(value), True
    nested = bool(getattr(value, "is_nested", False))
    return (list(value.unbind()), True) if nested else ([value], False)


def _pack(streams: list[torch.Tensor], nested: bool) -> Any:
    if nested:
        return comfy.nested_tensor.NestedTensor(streams)
    return streams[0]


def _zero_conditioning(conditioning: Any) -> list[list[Any]]:
    result: list[list[Any]] = []
    for tensor, metadata in conditioning:
        copied = dict(metadata)
        for key in ("pooled_output", "conditioning_lyrics", "conditioning_scale"):
            value = copied.get(key)
            if isinstance(value, torch.Tensor):
                copied[key] = torch.zeros_like(value)
        result.append([torch.zeros_like(tensor), copied])
    return result


def _resize_keyframe_conditioning(conditioning: Any, height: int, width: int) -> list[list[Any]]:
    """Resize only grid-bound H3 guide latents for the low-resolution stage."""
    result: list[list[Any]] = []
    for tensor, metadata in conditioning:
        keyframes = metadata.get("minimax_keyframes")
        if not isinstance(keyframes, (list, tuple)):
            result.append([tensor, metadata])
            continue
        copied = dict(metadata)
        resized: list[dict[str, Any]] = []
        for source in keyframes:
            keyframe = dict(source)
            latent = keyframe.get("latent")
            if isinstance(latent, torch.Tensor) and latent.ndim == 5 and latent.shape[-2:] != (height, width):
                keyframe["latent"] = F.interpolate(
                    latent.float(),
                    size=(int(latent.shape[2]), int(height), int(width)),
                    mode="trilinear",
                    align_corners=False,
                ).to(device=latent.device, dtype=latent.dtype)
            resized.append(keyframe)
        copied["minimax_keyframes"] = resized
        result.append([tensor, copied])
    return result


def _validate_plan(plan: MiniMaxH3SamplingPlan, model: Any, sampler: Any, sigmas: torch.Tensor) -> None:
    if plan.kind != SELFLIFT_KIND:
        raise ValueError(f"Unsupported MiniMax H3 sampling strategy: {plan.kind}")
    model_sampling = model.get_model_object("model_sampling")
    if not isinstance(model_sampling, comfy.model_sampling.CONST):
        raise ValueError("SelfLift sampling requires a rectified-flow/CONST model")
    if not isinstance(sampler, comfy.samplers.KSAMPLER):
        raise ValueError("SelfLift sampling requires the standard Euler sampler")
    if sampler.sampler_function is not comfy.k_diffusion.sampling.sample_euler:
        raise ValueError("SelfLift sampling currently supports Euler only")
    if float(sampler.extra_options.get("s_churn", 0.0)) != 0.0:
        raise ValueError("SelfLift sampling requires Euler with s_churn set to 0")
    if not isinstance(sigmas, torch.Tensor) or sigmas.ndim != 1 or not sigmas.is_floating_point():
        raise ValueError("SelfLift sigmas must be a one-dimensional floating-point tensor")
    if sigmas.numel() < 3:
        raise ValueError("SelfLift sampling needs at least two denoising steps")
    if not bool(torch.isfinite(sigmas).all()) or bool((sigmas < 0).any()):
        raise ValueError("SelfLift sigmas must be finite and non-negative")
    if bool((sigmas[1:] > sigmas[:-1]).any()):
        raise ValueError("SelfLift sigmas must be non-increasing")
    if bool((sigmas[:-1] <= 0).any()):
        raise ValueError("SelfLift requires every sigma except the final value to be greater than zero")
    step_count = int(sigmas.numel()) - 1
    if not 1 <= int(plan.transition_step) < step_count:
        raise ValueError(
            f"SelfLift transition step must be between 1 and {step_count - 1} for this {step_count}-step schedule"
        )
    if float(sigmas[int(plan.transition_step)]) >= 1.0:
        raise ValueError("SelfLift needs the first full-resolution sigma to be below 1")
    if not 0.25 <= float(plan.lowres_scale) <= 1.0:
        raise ValueError("SelfLift low-resolution scale must be between 0.25 and 1.0")
    if not 0.0 <= float(plan.correction_ratio) <= 1.0:
        raise ValueError("SelfLift correction ratio must be between 0 and 1")
    if not 0.0 <= float(plan.correction_min) <= float(plan.correction_max) <= 1.0:
        raise ValueError("SelfLift correction weights must satisfy 0 <= minimum <= maximum <= 1")


def _validate_target(
    latent: Mapping[str, Any],
) -> tuple[list[torch.Tensor], bool, bool, list[torch.Tensor] | None]:
    """Validate the narrow target contract supported by SelfLift.

    Normal generation still requires an all-zero H3 AV target.  The one
    supported exception is Digital Human: its video stream is empty while
    the audio stream contains an externally encoded track and is paired with
    an all-one video mask / all-zero audio mask.  This is deliberately more
    restrictive than generic noise-mask support so Soft/Hard AV and arbitrary
    video-to-video latents continue to fail loudly.
    """
    if not isinstance(latent, Mapping) or not isinstance(latent.get("samples"), torch.Tensor):
        # NestedTensor is Tensor-like but some builds do not satisfy the exact
        # isinstance check. Fall through when the object exposes unbind/is_nested.
        samples = latent.get("samples") if isinstance(latent, Mapping) else None
        if samples is None or not (hasattr(samples, "unbind") or isinstance(samples, (tuple, list))):
            raise ValueError("SelfLift sampling requires an H3 LATENT size template")
    streams, nested = _streams(latent["samples"])
    if not streams or streams[0].ndim != 5:
        raise ValueError("SelfLift H3 sampling requires a five-dimensional video latent stream")
    batch = int(streams[0].shape[0])
    for stream in streams:
        if stream.ndim < 1 or int(stream.shape[0]) != batch or any(int(size) <= 0 for size in stream.shape):
            raise ValueError("SelfLift received an invalid H3 AV latent layout")
    if bool(torch.count_nonzero(streams[0]).item()):
        raise ValueError("SelfLift requires an empty video latent; selected-video and encoded-video refinement are not supported")

    mask_streams = None
    locked_audio = False
    mask = latent.get("noise_mask")
    if mask is not None:
        mask_streams, mask_nested = _streams(mask)
        if not mask_nested or len(mask_streams) != len(streams) or len(streams) != 2:
            raise ValueError(
                "SelfLift only supports the Digital Human locked-audio mask; arbitrary AV noise masks are not supported"
            )
        video_mask, audio_mask = mask_streams
        video, audio = streams
        if video_mask.ndim != video.ndim or audio_mask.ndim != audio.ndim:
            raise ValueError("SelfLift Digital Human audio mask has an incompatible AV layout")
        if tuple(video_mask.shape) != tuple((video.shape[0], 1, *video.shape[2:])):
            raise ValueError("SelfLift Digital Human video mask has an incompatible shape")
        if tuple(audio_mask.shape) != tuple((audio.shape[0], 1, *audio.shape[2:])):
            raise ValueError("SelfLift Digital Human audio mask has an incompatible shape")
        if not bool(torch.all(video_mask == 1).item()) or not bool(torch.all(audio_mask == 0).item()):
            raise ValueError(
                "SelfLift only supports Digital Human locked audio (video mask=1, audio mask=0); "
                "Soft/Hard AV and arbitrary noise masks are not supported"
            )
        locked_audio = True
    else:
        for stream in streams[1:]:
            if bool(torch.count_nonzero(stream).item()):
                raise ValueError(
                    "SelfLift requires an all-zero AV target, except for Digital Human locked audio"
                )
    return streams, nested, locked_audio, mask_streams


def _euler_update(state: torch.Tensor, clean: torch.Tensor, sigma: torch.Tensor, sigma_next: torch.Tensor) -> torch.Tensor:
    delta = ((sigma_next - sigma) / sigma).to(device=state.device, dtype=state.dtype)
    return state + (state - clean.to(device=state.device, dtype=state.dtype)) * delta


def _fit_video_latent(value: torch.Tensor, temporal: int, height: int, width: int) -> torch.Tensor:
    if value.ndim != 5:
        raise ValueError("SelfLift resolution transition produced an invalid H3 video latent")
    if value.shape[2:] != (temporal, height, width):
        value = F.interpolate(
            value.float(),
            size=(temporal, height, width),
            mode="trilinear",
            align_corners=False,
        ).to(dtype=value.dtype)
    return value


def _learned_lift(
    clean: torch.Tensor,
    target_height: int,
    target_width: int,
    plan: MiniMaxH3SamplingPlan,
) -> torch.Tensor:
    model_name = str(plan.upscaler_model or "none")
    if model_name.lower() == "none":
        return F.interpolate(
            clean.float(),
            size=(int(clean.shape[2]), int(target_height), int(target_width)),
            mode="nearest",
        )
    if model_name.startswith("("):
        raise ValueError("Select an H3 latent upscaler checkpoint for the SelfLift sampling strategy")
    output = MiniMaxH3EasyLatentUpscaler3D.execute(
        {"samples": clean},
        model_name,
        {
            "mode": "target dimensions",
            "width": int(target_width) * 16,
            "height": int(target_height) * 16,
        },
        32,
        bool(plan.upscaler_chunking),
        str(plan.upscaler_device),
        str(plan.upscaler_precision),
    )[0]
    lifted = output.get("samples") if isinstance(output, Mapping) else None
    if not isinstance(lifted, torch.Tensor):
        raise RuntimeError("The H3 latent upscaler did not return a tensor during SelfLift sampling")
    return _fit_video_latent(lifted, int(clean.shape[2]), target_height, target_width)


def _pixel_lift(
    clean: torch.Tensor,
    video_vae: Any,
    target_height: int,
    target_width: int,
) -> torch.Tensor:
    """Construct a VAE round-trip anchor without retaining two full RGB copies."""
    if int(clean.shape[0]) > 1:
        return torch.cat([
            _pixel_lift(sample, video_vae, target_height, target_width)
            for sample in clean.split(1)
        ], dim=0)
    frames = video_vae.decode(clean)
    if frames.ndim == 5:
        frames = frames.reshape(-1, frames.shape[-3], frames.shape[-2], frames.shape[-1])
    if frames.ndim != 4 or frames.shape[-1] < 3:
        raise RuntimeError("SelfLift could not decode its low-resolution transition latent")
    pixel_height = int(target_height) * 16
    pixel_width = int(target_width) * 16
    resized_chunks: list[torch.Tensor] = []
    for start in range(0, int(frames.shape[0]), 16):
        chunk = frames[start:start + 16, ..., :3].movedim(-1, 1).float()
        chunk = F.interpolate(
            chunk,
            size=(pixel_height, pixel_width),
            mode="bicubic",
            align_corners=False,
            antialias=True,
        )
        resized_chunks.append(chunk.movedim(1, -1).to(device="cpu"))
    del frames
    resized = torch.cat(resized_chunks, dim=0)
    encoded = video_vae.encode(resized).float()
    del resized, resized_chunks
    return _fit_video_latent(encoded, int(clean.shape[2]), target_height, target_width)


def _combine_lifts(
    direct: torch.Tensor | None,
    anchor: torch.Tensor | None,
    ratio: float,
    minimum: float,
    maximum: float,
) -> torch.Tensor:
    if ratio <= 0.0 or maximum <= 0.0:
        if direct is None:
            raise RuntimeError("SelfLift direct transition latent is unavailable")
        return direct
    if direct is None:
        if anchor is None:
            raise RuntimeError("SelfLift transition anchor is unavailable")
        return anchor
    if anchor is None:
        return direct
    anchor = anchor.to(device=direct.device, dtype=direct.dtype)
    if ratio >= 1.0 and minimum >= 1.0 and maximum >= 1.0:
        return anchor
    residual = anchor - direct
    risk = residual.abs().mean(dim=1)
    flat = risk.flatten(1)
    threshold = torch.quantile(flat, 1.0 - float(ratio), dim=1)
    threshold = threshold.view((-1,) + (1,) * (risk.ndim - 1))
    selected = risk >= threshold
    selected_min = risk.masked_fill(~selected, float("inf")).flatten(1).amin(dim=1)
    selected_max = risk.masked_fill(~selected, float("-inf")).flatten(1).amax(dim=1)
    shape = (-1,) + (1,) * (risk.ndim - 1)
    selected_min = selected_min.view(shape)
    selected_max = selected_max.view(shape)
    weight = float(minimum) + (float(maximum) - float(minimum)) * (
        (risk - selected_min) / (selected_max - selected_min + 1e-8)
    )
    weight = torch.where(selected, weight, torch.zeros_like(weight)).unsqueeze(1)
    return direct + weight * residual


def sample_with_plan(
    plan: MiniMaxH3SamplingPlan,
    *,
    model: Any,
    positive: Any,
    latent: Mapping[str, Any],
    sampler: Any,
    sigmas: torch.Tensor,
    seed: int,
    video_vae: Any,
    callback: Callable[[int, Any, Any, int], Any] | None = None,
    disable_pbar: bool = True,
) -> dict[str, Any]:
    """Execute an H3 strategy and return a standard ComfyUI LATENT mapping."""
    if not isinstance(plan, MiniMaxH3SamplingPlan):
        raise ValueError("Connect a MiniMax H3 Easy sampling strategy")
    _validate_plan(plan, model, sampler, sigmas)
    normalized_latent = dict(latent)
    normalized_latent["samples"] = comfy.sample.fix_empty_latent_channels(
        model,
        latent["samples"],
        latent.get("downscale_ratio_spacial"),
        latent.get("downscale_ratio_temporal"),
    )
    target_streams, nested, locked_audio, mask_streams = _validate_target(normalized_latent)
    target_video = target_streams[0]
    batch, channels, temporal, target_height, target_width = map(int, target_video.shape)
    low_height = max(2, round(target_height * float(plan.lowres_scale) / 2) * 2)
    low_width = max(2, round(target_width * float(plan.lowres_scale) / 2) * 2)
    low_video = torch.zeros(
        (batch, channels, temporal, low_height, low_width),
        device=comfy.model_management.intermediate_device(),
        dtype=target_video.dtype,
    )
    # Digital Human carries a real encoded audio stream.  Keep that stream in
    # the low-resolution pass and lock it with a zero audio mask; only video
    # participates in the progressive spatial transition.
    low_auxiliary = [
        target_streams[index].to(device=comfy.model_management.intermediate_device())
        if locked_audio and index == 1 else torch.zeros_like(stream)
        for index, stream in enumerate(target_streams[1:], start=1)
    ]
    low_samples = _pack([low_video, *low_auxiliary], nested)
    low_noise = comfy.sample.prepare_noise(low_samples, int(seed), normalized_latent.get("batch_index"))
    low_mask = None
    high_mask_streams = None
    if locked_audio:
        audio_mask = mask_streams[1].to(device=low_video.device)
        low_mask = _pack([
            torch.ones(
                (batch, 1, temporal, low_height, low_width),
                device=low_video.device,
                dtype=target_video.dtype,
            ),
            audio_mask,
        ], nested)
        high_mask_streams = mask_streams
    positive_low = _resize_keyframe_conditioning(positive, low_height, low_width)
    negative = _zero_conditioning(positive)
    negative_low = _resize_keyframe_conditioning(negative, low_height, low_width)
    transition_step = int(plan.transition_step)
    total_steps = int(sigmas.numel()) - 1
    captured: dict[str, Any] = {}
    low_calls = 0

    def low_callback(_step, clean, state, _total):
        nonlocal low_calls
        current = low_calls
        low_calls += 1
        if current == transition_step - 1:
            captured["state"] = state
            captured["clean"] = clean
        if callback is not None:
            callback(current, clean, state, total_steps)

    LOGGER.info(
        "SelfLift H3: %d low-resolution and %d full-resolution evaluations; latent %dx%d -> %dx%d",
        transition_step,
        total_steps - transition_step,
        low_width,
        low_height,
        target_width,
        target_height,
    )
    comfy.samplers.sample(
        model,
        low_noise,
        positive_low,
        negative_low,
        float(plan.cfg),
        model.load_device,
        sampler,
        sigmas[:transition_step + 1],
        model.model_options,
        latent_image=low_samples,
        denoise_mask=low_mask,
        callback=low_callback,
        disable_pbar=disable_pbar,
        seed=int(seed),
    )
    if low_calls != transition_step or "state" not in captured or "clean" not in captured:
        raise RuntimeError("SelfLift could not capture the low-resolution transition prediction")

    low_state_streams, nested = _streams(captured.pop("state"))
    low_clean_streams, _ = _streams(captured.pop("clean"))
    sigma_current = sigmas[transition_step - 1]
    sigma_resume = sigmas[transition_step]
    auxiliary_resume = [
        torch.zeros_like(state)
        if locked_audio and index == 1
        else _euler_update(state, clean, sigma_current, sigma_resume)
        for index, (state, clean) in enumerate(zip(low_state_streams[1:], low_clean_streams[1:]), start=1)
    ]
    latent_format = model.get_model_object("latent_format")
    clean_native = latent_format.process_out(low_clean_streams[0].float()).to(
        comfy.model_management.intermediate_device()
    )
    ratio = float(plan.correction_ratio)
    need_anchor = ratio > 0.0 and float(plan.correction_max) > 0.0
    need_direct = not (
        ratio >= 1.0
        and float(plan.correction_min) >= 1.0
        and float(plan.correction_max) >= 1.0
    )
    learned_upscaler = need_direct and str(plan.upscaler_model or "none").lower() != "none"
    if learned_upscaler and str(plan.upscaler_device).lower() in {"cuda", "rocm"}:
        # The manually loaded 3D upscaler is not a Comfy MODEL input. Release
        # the H3 denoiser before loading it so both large weight sets are not
        # resident together; the high-resolution sampler reloads H3 normally.
        try:
            comfy.model_management.unload_model_and_clones(
                model,
                unload_additional_models=False,
            )
            comfy.model_management.soft_empty_cache()
        except Exception:
            LOGGER.debug("Could not pre-unload the H3 model before SelfLift upscaling", exc_info=True)
    if learned_upscaler and need_anchor:
        LOGGER.warning(
            "SelfLift H3 is combining a learned latent upscaler with pixel-anchor correction; "
            "this is an experimental hybrid configuration"
        )
    direct_native = _learned_lift(clean_native, target_height, target_width, plan) if need_direct else None
    anchor_native = _pixel_lift(clean_native, video_vae, target_height, target_width) if need_anchor else None
    direct_model = latent_format.process_in(direct_native) if direct_native is not None else None
    anchor_model = latent_format.process_in(anchor_native) if anchor_native is not None else None
    lifted_model = _combine_lifts(
        direct_model,
        anchor_model,
        ratio,
        float(plan.correction_min),
        float(plan.correction_max),
    ).to(model.load_device)
    del clean_native, direct_native, anchor_native, direct_model, anchor_model, low_state_streams, low_clean_streams

    high_noise = comfy.sample.prepare_noise(
        lifted_model,
        (int(seed) + 1) % (1 << 64),
        normalized_latent.get("batch_index"),
    ).to(lifted_model)
    noisy = model.get_model_object("model_sampling").noise_scaling(
        sigma_current,
        high_noise,
        lifted_model,
    )
    video_resume = _euler_update(noisy, lifted_model, sigma_current, sigma_resume)
    resumed_streams = [video_resume, *auxiliary_resume]
    model_sampling = model.get_model_object("model_sampling")
    resumed_streams = [model_sampling.inverse_noise_scaling(sigma_resume, stream) for stream in resumed_streams]
    packed_resume = _pack(resumed_streams, nested)
    if locked_audio:
        high_mask = _pack([
            high_mask_streams[index].to(device=stream.device)
            for index, stream in enumerate(resumed_streams)
        ], nested)
    else:
        high_mask = None
    process_out = getattr(getattr(model, "model", None), "process_latent_out", None)
    resume_latent = process_out(packed_resume) if callable(process_out) else packed_resume
    if locked_audio:
        # resume_latent is in the public/native latent representation.  Put
        # the encoded driving track back here so the high-resolution sampler
        # performs its normal H3 audio scaling exactly once before the zero
        # audio mask pins it for every remaining evaluation.
        resume_streams, resume_nested = _streams(resume_latent)
        resume_streams[1] = target_streams[1].to(
            device=resume_streams[1].device,
            dtype=resume_streams[1].dtype,
        )
        resume_latent = _pack(resume_streams, resume_nested)
    zero_noise = _pack([torch.zeros_like(stream) for stream in resumed_streams], nested)
    del lifted_model, high_noise, noisy, video_resume, resumed_streams, auxiliary_resume

    high_calls = 0

    def high_callback(_step, clean, state, _total):
        nonlocal high_calls
        current = high_calls
        high_calls += 1
        if callback is not None:
            callback(transition_step + current, clean, state, total_steps)

    output = comfy.samplers.sample(
        model,
        zero_noise,
        positive,
        negative,
        float(plan.cfg),
        model.load_device,
        sampler,
        sigmas[transition_step:],
        model.model_options,
        latent_image=resume_latent,
        denoise_mask=high_mask,
        callback=high_callback,
        disable_pbar=disable_pbar,
        seed=int(seed),
    )
    if high_calls != total_steps - transition_step:
        raise RuntimeError("SelfLift full-resolution stage returned an unexpected number of evaluations")
    if locked_audio:
        output_streams, output_nested = _streams(output)
        output_streams[1] = target_streams[1].to(device=output_streams[1].device, dtype=output_streams[1].dtype)
        output = _pack(output_streams, output_nested)
    result = dict(normalized_latent)
    result.pop("noise_mask", None)
    result["samples"] = output.to(
        device=comfy.model_management.intermediate_device(),
        dtype=comfy.model_management.intermediate_dtype(),
    )
    return result
