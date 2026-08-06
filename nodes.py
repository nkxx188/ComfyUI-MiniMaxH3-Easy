"""A compact MiniMax H3 entry point for ComfyUI.

The node intentionally keeps the graph contract small: one loader bundle, one
mode-aware conditioning node, and standard ComfyUI outputs for the sampler
chain. The browser extension supplies the ordered virtual media inputs.
"""

from __future__ import annotations

import base64
import io
import math
import os
import re
import sys
import threading
import wave
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import torch
import torchaudio
from PIL import Image

import comfy.model_management
import folder_paths
import node_helpers
import nodes
from comfy_extras import nodes_minimax_h3 as h3
from .prompt_optimizer import optimize_prompt as optimize_h3_prompt


MODE_IMAGE = "image"
MODE_REFERENCE = "reference"
KEYFRAME_FIRST = "first"
KEYFRAME_LAST = "last"
REF_IMAGE_1K = "1k"
REF_IMAGE_2K = "2k"
REFERENCE_MENTION_FILENAME = "filename"
REFERENCE_MENTION_INDEX = "index"
OPTIMIZER_IMAGE_EDGE = 1280
OPTIMIZER_VIDEO_FRAME_EDGE = 960
OPTIMIZER_AUDIO_MAX_BYTES = 6 * 1024 * 1024
RESOLUTION_360 = "360P"
RESOLUTION_416 = "416P"
RESOLUTION_480 = "480P"
RESOLUTION_540 = "540P"
RESOLUTION_640 = "640P"
RESOLUTION_720 = "720P"
RESOLUTION_768 = "768P"
RESOLUTION_832 = "832P"
RESOLUTION_928 = "928P"
RESOLUTION_1024 = "1024P"
RESOLUTION_1080 = "1080P"
RESOLUTION_CUSTOM = "custom"
ASPECT_SQUARE = "1:1"
ASPECT_PHOTO_PORTRAIT = "2:3"
ASPECT_PHOTO = "3:2"
ASPECT_STANDARD_PORTRAIT = "3:4"
ASPECT_STANDARD = "4:3"
ASPECT_WIDESCREEN_PORTRAIT = "9:16"
ASPECT_WIDESCREEN = "16:9"
ASPECT_ULTRAWIDE = "21:9"
RESOLUTION_MEGAPIXELS = {
    RESOLUTION_360: 0.2,
    RESOLUTION_416: 0.3,
    RESOLUTION_480: 0.4,
    RESOLUTION_540: 0.5,
    RESOLUTION_640: 0.7,
    RESOLUTION_720: 0.9,
    RESOLUTION_768: 1.0,
    RESOLUTION_832: 1.2,
    RESOLUTION_928: 1.5,
    RESOLUTION_1024: 1.8,
    RESOLUTION_1080: 2.0,
}
RESOLUTIONS = (*RESOLUTION_MEGAPIXELS, RESOLUTION_CUSTOM)
REFERENCE_IMAGE_SHORT_EDGES = {
    REF_IMAGE_1K: 1024,
    REF_IMAGE_2K: h3.REF_IMAGE_SHORT_EDGE,
}
ASPECT_RATIOS = {
    ASPECT_SQUARE: (1, 1),
    ASPECT_PHOTO_PORTRAIT: (2, 3),
    ASPECT_PHOTO: (3, 2),
    ASPECT_STANDARD_PORTRAIT: (3, 4),
    ASPECT_STANDARD: (4, 3),
    ASPECT_WIDESCREEN_PORTRAIT: (9, 16),
    ASPECT_WIDESCREEN: (16, 9),
    ASPECT_ULTRAWIDE: (21, 9),
}
MAX_MEDIA = 15
MAX_IMAGES = 9
MAX_VIDEOS = 3
MAX_AUDIOS = 3
MIN_SECONDS = 4.0
MAX_SECONDS = 20.0
REFERENCE_PLACEHOLDER_RE = re.compile(r"__MINIMAX_H3_REF_(\d+)__")
UNRESOLVED_REFERENCE_RE = re.compile(r"__MINIMAX_H3_UNRESOLVED_REF_[^_]+__")
MODEL_FILE_EXTENSIONS = {".safetensors", ".gguf"}


def _normalise_model_name(name: str) -> str:
    """Turn community naming variants into comparable tokens.

    MiniMax H3 files appear with underscores, dashes, camel case and sometimes
    only a role folder (for example ``FL2VA/model.safetensors``). Matching the
    normalised path rather than one exact filename keeps the loader useful for
    community quantisations without admitting every unrelated model.
    """
    value = str(name or "").replace("\\", "/").lower()
    value = re.sub(r"([a-z])([0-9])", r"\1 \2", value)
    value = re.sub(r"([0-9])([a-z])", r"\1 \2", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _model_tokens(name: str) -> set[str]:
    return set(_normalise_model_name(name).split())


def _is_minimax_h3_name(normalised: str, compact: str, tokens: set[str]) -> bool:
    """Require an explicit MiniMax H3 identity before matching shared roles."""
    return "minimaxh3" in compact or ("minimax" in tokens and "h3" in compact)


def _is_weight_file(name: str) -> bool:
    return os.path.splitext(str(name or ""))[1].lower() in MODEL_FILE_EXTENSIONS


def _is_gguf_file(name: str) -> bool:
    return str(name or "").lower().endswith(".gguf")


def _category_names(category: str) -> list[str]:
    """Read a ComfyUI filename category without assuming it exists."""
    try:
        return [str(name) for name in folder_paths.get_filename_list(category)]
    except Exception:
        return []


def _category_paths(category: str) -> list[str]:
    try:
        entry = folder_paths.folder_names_and_paths.get(category)
        if not entry:
            return []
        paths = entry[0]
        if isinstance(paths, (str, os.PathLike)):
            paths = [paths]
        return [os.fspath(path) for path in paths]
    except Exception:
        return []


def _filesystem_weight_names(categories: tuple[str, ...]) -> list[str]:
    """Find GGUF files even when ComfyUI has no GGUF extension category yet."""
    names: list[str] = []
    for category in categories:
        for base in _category_paths(category):
            if not os.path.isdir(base):
                continue
            try:
                for root, _dirs, files in os.walk(base):
                    for filename in files:
                        if os.path.splitext(filename)[1].lower() not in MODEL_FILE_EXTENSIONS:
                            continue
                        full_path = os.path.join(root, filename)
                        relative = os.path.relpath(full_path, base).replace(os.sep, "/")
                        names.append(relative)
            except OSError:
                continue
    return names


@lru_cache(maxsize=16)
def _collect_weight_names(categories: tuple[str, ...]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for category in categories:
        for name in _category_names(category):
            if not _is_weight_file(name):
                continue
            key = name.replace("\\", "/")
            if key not in seen:
                seen.add(key)
                names.append(key)
    # The normal ComfyUI categories may not advertise .gguf until the optional
    # GGUF node is loaded, so supplement them from the actual model folders.
    for name in _filesystem_weight_names(categories):
        key = name.replace("\\", "/")
        if key not in seen:
            seen.add(key)
            names.append(key)
    return names


def _has_role(name: str, role: str) -> bool:
    normalised = _normalise_model_name(name)
    compact = normalised.replace(" ", "")
    tokens = set(normalised.split())
    if role == "fl2va":
        if "minimax" not in tokens and "h3" not in compact:
            return False
        if "ref2va" in compact or "ref2v" in compact:
            return False
        return "fl2va" in compact or "fl2v" in compact
    if role == "ref2va":
        if "minimax" not in tokens and "h3" not in compact:
            return False
        return "ref2va" in compact or "ref2v" in compact
    if role == "text_encoder":
        if ("qwen3vl" in compact or ("qwen3" in tokens and "vl" in tokens)) and (
            "32b" in tokens or "32" in tokens
        ):
            return True
        # Some community H3 exports omit "minimax_h3" from the encoder
        # filename but retain the characteristic INT8/ConvRot or NVFP4/AWQ
        # variant naming.
        if (
            "qwen3" in tokens
            and "vl" in tokens
            and ("32b" in tokens or "32" in tokens)
            and (("int8" in tokens and "convrot" in tokens) or ("nvfp4" in tokens and "awq" in tokens))
        ):
            return True
        # A few community exports use only text_encoder.safetensors, but keep
        # the match scoped to an H3-named path to avoid generic CLIP files.
        return "text encoder" in normalised and ("minimax" in tokens or "h3" in compact)
    if role == "video_vae":
        is_minimax_h3 = _is_minimax_h3_name(normalised, compact, tokens)
        is_video_vae = (
            ("video" in tokens and "vae" in tokens)
            or "videovae" in compact
            # Diffusers-style exports may use MiniMax-H3/vae/... without the
            # word "video". In H3, an unqualified VAE is the visual VAE.
            or ("vae" in tokens and "audio" not in tokens and "audiovae" not in compact)
        )
        return is_minimax_h3 and is_video_vae and "tae" not in tokens and "approx" not in tokens
    if role == "audio_vae":
        is_minimax_h3 = _is_minimax_h3_name(normalised, compact, tokens)
        is_audio_vae = (
            ("audio" in tokens and "vae" in tokens)
            or "audiovae" in compact
        )
        return is_minimax_h3 and is_audio_vae and "tae" not in tokens and "approx" not in tokens
    return False


def _sort_model_names(names: list[str]) -> list[str]:
    def sort_key(name: str) -> tuple[int, int, str]:
        normalised = _normalise_model_name(name)
        # Keep safetensors first for the native path, followed by GGUF. Within
        # each group use a deterministic name order for stable workflows.
        extension_rank = 1 if _is_gguf_file(name) else 0
        official_rank = 0 if "minimax" in normalised and "h3" in normalised else 1
        return extension_rank, official_rank, normalised

    return sorted(names, key=sort_key)


def _role_choices(role: str, categories: tuple[str, ...], fallback: str) -> list[str]:
    names = _collect_weight_names(categories)
    selected = [name for name in names if _has_role(name, role)]
    return _sort_model_names(selected) or [fallback]


def _filtered_choices(category: str, needles: tuple[str, ...], fallback: str) -> list[str]:
    names = _collect_weight_names((category,))
    selected = [name for name in names if any(needle.lower() in _normalise_model_name(name).replace(" ", "") for needle in needles)]
    return _sort_model_names(selected) or [fallback]


def _model_choices() -> list[str]:
    return _role_choices("fl2va", ("diffusion_models", "unet", "unet_gguf"), "minimax_h3_fl2va_pruned_int8_convrot.safetensors")


def _ref_model_choices() -> list[str]:
    return _role_choices("ref2va", ("diffusion_models", "unet", "unet_gguf"), "minimax_h3_ref2va_pruned_int8_convrot.safetensors")


def _clip_choices() -> list[str]:
    return _role_choices("text_encoder", ("text_encoders", "clip", "clip_gguf"), "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors")


def _vae_choices(needles: tuple[str, ...], fallback: str) -> list[str]:
    role = "video_vae" if any("video" in needle.lower() for needle in needles) else "audio_vae"
    return _role_choices(role, ("vae",), fallback)


@lru_cache(maxsize=16)
def _registered_node_class(*names: str):
    """Find an optional custom-node class without importing it unconditionally."""
    mappings = getattr(nodes, "NODE_CLASS_MAPPINGS", {})
    for name in names:
        node_class = mappings.get(name) if hasattr(mappings, "get") else None
        if node_class is not None:
            return node_class
        node_class = getattr(nodes, name, None)
        if node_class is not None:
            return node_class
    for module in tuple(sys.modules.values()):
        if module is None:
            continue
        for name in names:
            node_class = getattr(module, name, None)
            if node_class is not None:
                return node_class
    return None


def _load_gguf_unet(model_name: str):
    loader_class = _registered_node_class("UnetLoaderGGUF", "UNETLoaderGGUF", "UnetLoaderGGUFAdvanced")
    if loader_class is None:
        raise RuntimeError(
            "检测到 GGUF MiniMax H3 主模型，但当前 ComfyUI 未安装 GGUF 加载节点。"
            "请安装 ComfyUI-GGUF 后重启 ComfyUI。"
        )
    loader = loader_class()
    return loader.load_unet(model_name)[0]


def _load_text_encoder(text_encoder: str):
    if not _is_gguf_file(text_encoder):
        return nodes.CLIPLoader().load_clip(text_encoder, "minimax", "default")[0]

    loader_class = _registered_node_class("CLIPLoaderGGUF", "CLIPLoaderGGUFAdvanced")
    if loader_class is None:
        raise RuntimeError(
            "检测到 GGUF MiniMax H3 文本编码器，但当前 ComfyUI 未安装 GGUF 加载节点。"
            "请安装 ComfyUI-GGUF 后重启 ComfyUI。"
        )
    loader = loader_class()
    try:
        return loader.load_clip(text_encoder, "minimax")[0]
    except TypeError:
        return loader.load_clip(text_encoder, type="minimax")[0]


@dataclass
class MiniMaxH3Bundle:
    fl2va_model_name: str
    ref2va_model_name: str
    clip_name: str
    video_vae_name: str
    audio_vae_name: str
    clip: Any
    video_vae: Any
    audio_vae: Any

    def __post_init__(self) -> None:
        self._model = None
        self._model_kind = ""
        self._lock = threading.RLock()

    def model_for(self, kind: str):
        kind = "ref2va" if kind == "ref2va" else "fl2va"
        with self._lock:
            if self._model is not None and self._model_kind == kind:
                return self._model

            if self._model is not None:
                self._model = None
                self._model_kind = ""
                comfy.model_management.soft_empty_cache()

            model_name = self.ref2va_model_name if kind == "ref2va" else self.fl2va_model_name
            if _is_gguf_file(model_name):
                self._model = _load_gguf_unet(model_name)
            else:
                self._model, = nodes.UNETLoader().load_unet(model_name, "default")
            self._model_kind = kind
            return self._model


@dataclass(frozen=True)
class MiniMaxH3Context:
    conditioning: Any
    latent: Any
    video_vae: Any
    audio_vae: Any
    fps: float


@dataclass(frozen=True)
class _MediaInput:
    input_index: int
    media_type: str
    value: Any


class MiniMaxH3EasyLoader:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "load"
    RETURN_TYPES = ("MINIMAX_H3_BUNDLE",)
    RETURN_NAMES = ("h3_bundle",)
    DESCRIPTION = "Load the MiniMax H3 transformers, text encoder and both AV VAEs as one bundle."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fl2va_model": (_model_choices(),),
                "ref2va_model": (_ref_model_choices(),),
                "text_encoder": (_clip_choices(),),
                "video_vae": (_vae_choices(("minimax_h3_video_vae",), "minimax_h3_video_vae_fp16.safetensors"),),
                "audio_vae": (_vae_choices(("minimax_h3_audio_vae",), "minimax_h3_audio_vae_fp32.safetensors"),),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return "|".join(str(kwargs.get(key, "")) for key in ("fl2va_model", "ref2va_model", "text_encoder", "video_vae", "audio_vae"))

    def load(self, fl2va_model, ref2va_model, text_encoder, video_vae, audio_vae):
        clip = _load_text_encoder(text_encoder)
        video_vae_obj, = nodes.VAELoader().load_vae(video_vae)
        audio_vae_obj, = nodes.VAELoader().load_vae(audio_vae)
        return (MiniMaxH3Bundle(
            fl2va_model_name=fl2va_model,
            ref2va_model_name=ref2va_model,
            clip_name=text_encoder,
            video_vae_name=video_vae,
            audio_vae_name=audio_vae,
            clip=clip,
            video_vae=video_vae_obj,
            audio_vae=audio_vae_obj,
        ),)


def _infer_media_type(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, torch.Tensor):
        return "image"
    if isinstance(value, dict) and "waveform" in value:
        return "audio"
    if hasattr(value, "get_components"):
        return "video"
    return "video"


def _audio_sample_rate(audio: dict) -> int:
    return int(audio.get("sample_rate") or audio.get("samplerate") or audio.get("sampler_rate") or 32000)


def _video_parts(value: Any) -> tuple[torch.Tensor, dict | None, float]:
    if hasattr(value, "get_components"):
        components = value.get_components()
        return components.images, components.audio, float(components.frame_rate or 24.0)
    if isinstance(value, dict):
        frames = value.get("images")
        if frames is None:
            frames = value.get("frames")
        if isinstance(frames, torch.Tensor):
            return frames, value.get("audio"), float(value.get("fps") or value.get("frame_rate") or 24.0)
    if isinstance(value, torch.Tensor) and value.ndim == 4:
        return value, None, 24.0
    raise ValueError("Unsupported reference video payload")


def _optimizer_image_data_url(image: torch.Tensor, max_edge: int) -> str:
    if not isinstance(image, torch.Tensor) or image.ndim not in {3, 4}:
        raise ValueError("Prompt optimizer received an invalid image")
    frame = image[0] if image.ndim == 4 else image
    frame = frame.detach().float().cpu().clamp(0, 1)
    if frame.shape[-1] == 1:
        frame = frame.repeat(1, 1, 3)
    if frame.shape[-1] < 3:
        raise ValueError("Prompt optimizer received an unsupported image format")
    array = (frame[..., :3] * 255.0).round().to(torch.uint8).numpy()
    picture = Image.fromarray(array, mode="RGB")
    if max(picture.size) > max_edge:
        picture.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    picture.save(output, format="JPEG", quality=86, optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _optimizer_audio_data_url(audio: dict) -> str:
    if not isinstance(audio, dict) or not isinstance(audio.get("waveform"), torch.Tensor):
        raise ValueError("Prompt optimizer received invalid audio")
    waveform = audio["waveform"].detach().float().cpu()
    if waveform.ndim == 3:
        waveform = waveform[0]
    elif waveform.ndim == 1:
        waveform = waveform.unsqueeze(0)
    if waveform.ndim != 2:
        raise ValueError("Prompt optimizer received an unsupported audio shape")
    waveform = waveform[:2]
    sample_rate = _audio_sample_rate(audio)
    max_samples = max(1, (OPTIMIZER_AUDIO_MAX_BYTES - 44) // (2 * waveform.shape[0]))
    waveform = waveform[:, :max_samples].clamp(-1, 1)
    pcm = (waveform.transpose(0, 1).contiguous() * 32767.0).round().to(torch.int16)
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(waveform.shape[0])
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.numpy().tobytes())
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{encoded}"


def _optimizer_media_items(
    items: list[_MediaInput], mode: str, keyframe_role: str
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if mode != MODE_REFERENCE:
        images = [item.value for item in items if item.media_type == "image"]
        if len(images) == 2 and keyframe_role == KEYFRAME_LAST:
            images = [images[1], images[0]]
        for index, image in enumerate(images, start=1):
            role = "first frame" if index == 1 and (len(images) > 1 or keyframe_role != KEYFRAME_LAST) else "last frame"
            result.append({
                "type": "image",
                "label": f"Picture {index} ({role})",
                "data_url": _optimizer_image_data_url(image, OPTIMIZER_IMAGE_EDGE),
            })
        return result

    for item in items:
        token = f"__MINIMAX_H3_REF_{item.input_index}__"
        if item.media_type == "image":
            result.append({
                "type": "image",
                "label": token,
                "data_url": _optimizer_image_data_url(item.value, OPTIMIZER_IMAGE_EDGE),
            })
            continue
        if item.media_type == "audio":
            result.append({
                "type": "audio",
                "label": token,
                "data_url": _optimizer_audio_data_url(item.value),
            })
            continue
        frames, soundtrack, _source_fps = _video_parts(item.value)
        if not isinstance(frames, torch.Tensor) or frames.ndim != 4 or not frames.shape[0]:
            raise ValueError("Prompt optimizer received an invalid video")
        indexes = sorted({round((frames.shape[0] - 1) * ratio) for ratio in (0.12, 0.5, 0.88)})
        for sample_index, frame_index in enumerate(indexes, start=1):
            result.append({
                "type": "image",
                "label": f"{token} sampled video frame {sample_index}/{len(indexes)}",
                "data_url": _optimizer_image_data_url(frames[frame_index], OPTIMIZER_VIDEO_FRAME_EDGE),
            })
        if soundtrack is not None:
            result.append({
                "type": "audio",
                "label": f"audio track from {token}",
                "data_url": _optimizer_audio_data_url(soundtrack),
            })
    return result[:32]


def _resample_video_frames(frames: torch.Tensor, source_fps: float) -> torch.Tensor:
    if not source_fps or abs(source_fps - h3.FPS) < 0.01:
        return frames
    count = max(1, round(frames.shape[0] * h3.FPS / source_fps))
    indexes = torch.linspace(0, frames.shape[0] - 1, count, device=frames.device).round().long()
    return frames[indexes]


def _encode_reference_audio(audio_vae, audio: dict):
    waveform = audio["waveform"]
    sample_rate = _audio_sample_rate(audio)
    vae_sample_rate = int(getattr(audio_vae, "audio_sample_rate", 32000))
    if sample_rate != vae_sample_rate:
        waveform = torchaudio.functional.resample(waveform, sample_rate, vae_sample_rate)
    latent = audio_vae.encode(waveform[:1].movedim(1, -1))
    return latent, latent.shape[-1]


def _resolve_reference_prompt(
    prompt: str,
    tag_by_input: dict[int, str],
    soundtrack_pairs: list[tuple[int, int]],
    video_count: int,
    standalone_audio_count: int,
) -> str:
    if UNRESOLVED_REFERENCE_RE.search(str(prompt or "")):
        raise ValueError("Prompt contains a disconnected media reference. Reconnect the media or remove the @ reference.")
    resolved = REFERENCE_PLACEHOLDER_RE.sub(
        lambda match: tag_by_input.get(int(match.group(1)), ""),
        str(prompt or ""),
    )
    if soundtrack_pairs and (video_count > 1 or standalone_audio_count > 0):
        provenance = [
            f"<Audio {audio_index}> is the synchronized audio track of <Video {video_index}>."
            for audio_index, video_index in soundtrack_pairs
        ]
        return "\n".join((*provenance, resolved))
    return resolved


def _align_canvas_dimension(value: float) -> int:
    return max(h3.CANVAS_MULTIPLE, round(float(value) / h3.CANVAS_MULTIPLE) * h3.CANVAS_MULTIPLE)


def _canvas_dimensions(resolution: str, aspect_ratio: str, custom_width: int, custom_height: int) -> tuple[int, int]:
    if str(resolution) == RESOLUTION_CUSTOM:
        return _align_canvas_dimension(custom_width), _align_canvas_dimension(custom_height)

    megapixels = RESOLUTION_MEGAPIXELS.get(str(resolution), RESOLUTION_MEGAPIXELS[RESOLUTION_480])
    ratio_w, ratio_h = ASPECT_RATIOS.get(str(aspect_ratio), ASPECT_RATIOS[ASPECT_WIDESCREEN])
    total_pixels = megapixels * 1024 * 1024
    scale = math.sqrt(total_pixels / (ratio_w * ratio_h))
    return _align_canvas_dimension(ratio_w * scale), _align_canvas_dimension(ratio_h * scale)


def _frame_length(seconds: float, fps: float) -> int:
    target_frames = max(5.0, float(seconds) * float(fps))
    block_count = max(0, round((target_frames - 5) / 17))
    return block_count * 17 + 5


def _empty_image_conditioning(bundle, prompt, width, height, length, first_frame=None, last_frame=None):
    latent, frame_count = h3._empty_av_latent(width, height, length)
    images = []
    keyframes = []
    if first_frame is not None:
        image = h3._resize(first_frame[:1], width, height, "disabled")
        images.append(image)
        keyframes.append({"resolved_frame_index": 0, "image": image})
    if last_frame is not None:
        image = h3._resize(last_frame[:1], width, height, "center")
        images.append(image)
        keyframes.append({"resolved_frame_index": frame_count - 1, "image": image})

    tokens = bundle.clip.tokenize(prompt, images=images)
    conditioning = bundle.clip.encode_from_tokens_scheduled(tokens)
    if keyframes:
        for keyframe in keyframes:
            keyframe["latent"] = bundle.video_vae.encode(keyframe.pop("image"))
        conditioning = node_helpers.conditioning_set_values(conditioning, {
            "minimax_keyframes": keyframes,
            "minimax_frame_count": frame_count,
        })
    return conditioning, latent


def _reference_conditioning(bundle, prompt, width, height, length, ref_image_size, items: list[_MediaInput]):
    latent, frame_count = h3._empty_av_latent(width, height, length)
    ref_items = []
    ref_blocks = []
    tag_by_input: dict[int, str] = {}
    soundtrack_pairs: list[tuple[int, int]] = []
    images = [item for item in items if item.media_type == "image"]
    videos = [item for item in items if item.media_type == "video"]
    audios = [item for item in items if item.media_type == "audio"]
    audio_ordinal = 0

    # Match the official H3 presentation order: images, videos (with each
    # synchronized soundtrack immediately before its video), standalone audio.
    for picture_ordinal, item in enumerate(images, start=1):
        image = item.value
        if not isinstance(image, torch.Tensor) or image.ndim != 4:
            raise ValueError("Image references must be IMAGE tensors")
        image_h, image_w = image.shape[1], image.shape[2]
        short_edge_limit = REFERENCE_IMAGE_SHORT_EDGES.get(str(ref_image_size), REFERENCE_IMAGE_SHORT_EDGES[REF_IMAGE_1K])
        scale = min(1.0, short_edge_limit / max(1, min(image_w, image_h)))
        target_w = max(h3.CANVAS_MULTIPLE, round(image_w * scale / h3.CANVAS_MULTIPLE) * h3.CANVAS_MULTIPLE)
        target_h = max(h3.CANVAS_MULTIPLE, round(image_h * scale / h3.CANVAS_MULTIPLE) * h3.CANVAS_MULTIPLE)
        resized = h3._resize(image[:1], target_w, target_h, "disabled")
        ref_items.append({"type": "image", "data": resized})
        ref_blocks.append({"kind": "image", "latent_h": target_h // 16, "latent_w": target_w // 16, "latent": bundle.video_vae.encode(resized)})
        tag_by_input[item.input_index] = f"<Picture {picture_ordinal}>"

    for video_ordinal, item in enumerate(videos, start=1):
        frames, soundtrack, source_fps = _video_parts(item.value)
        frames = _resample_video_frames(frames, source_fps)
        video_h, video_w = frames.shape[1], frames.shape[2]
        canvas_w, canvas_h = h3.adapt_canvas(video_w, video_h)
        if video_w * video_h < canvas_w * canvas_h:
            canvas_w = max(h3.CANVAS_MULTIPLE, round(video_w / h3.CANVAS_MULTIPLE) * h3.CANVAS_MULTIPLE)
            canvas_h = max(h3.CANVAS_MULTIPLE, round(video_h / h3.CANVAS_MULTIPLE) * h3.CANVAS_MULTIPLE)
        frames = h3._resize(frames, canvas_w, canvas_h, "disabled")
        if frames.shape[0] > frame_count:
            frames = frames[:frame_count]
        count = frames.shape[0]
        if count < 5:
            raise ValueError("Reference videos need at least 5 frames")
        while count % 17 != 5:
            count -= 1
        frames = frames[:count]
        video_latent = bundle.video_vae.encode(frames)
        audio_latent = None
        audio_t = 0
        if soundtrack is not None:
            audio_latent, audio_t = _encode_reference_audio(bundle.audio_vae, soundtrack)
            audio_ordinal += 1
            soundtrack_pairs.append((audio_ordinal, video_ordinal))
            ref_items.append({"type": "audio"})
        sample_indexes = list(range(0, frames.shape[0], h3.FPS // 2))
        ref_items.append({
            "type": "video",
            "data": frames[sample_indexes],
            "timestamps": [i / 2.0 for i in range(len(sample_indexes))],
        })
        ref_blocks.append({
            "kind": "video_audio" if audio_t else "video",
            "latent_t": video_latent.shape[2],
            "latent_h": canvas_h // 16,
            "latent_w": canvas_w // 16,
            "ref_audio_t": audio_t,
            "latent": video_latent,
            "audio_latent": audio_latent,
        })
        tag_by_input[item.input_index] = f"<Video {video_ordinal}>"

    for item in audios:
        if not isinstance(item.value, dict) or "waveform" not in item.value:
            raise ValueError("Audio references must be AUDIO payloads")
        audio_latent, audio_t = _encode_reference_audio(bundle.audio_vae, item.value)
        audio_ordinal += 1
        ref_items.append({"type": "audio"})
        ref_blocks.append({"kind": "audio", "ref_audio_t": audio_t, "audio_latent": audio_latent})
        tag_by_input[item.input_index] = f"<Audio {audio_ordinal}>"

    if not ref_items or all(item.get("type") == "audio" for item in ref_items):
        raise ValueError("Reference mode needs at least one image or video")

    resolved_prompt = _resolve_reference_prompt(
        prompt,
        tag_by_input,
        soundtrack_pairs,
        len(videos),
        len(audios),
    )

    tokens = bundle.clip.tokenize(resolved_prompt, minimax_ref_items=ref_items)
    conditioning = bundle.clip.encode_from_tokens_scheduled(tokens)
    conditioning = node_helpers.conditioning_set_values(conditioning, {"minimax_refs": ref_blocks})
    return conditioning, latent


class MiniMaxH3Easy:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "generate"
    RETURN_TYPES = ("MODEL", "MINIMAX_H3_CONTEXT")
    RETURN_NAMES = ("model", "h3_context")
    DESCRIPTION = "One MiniMax H3 node for text, image and reference video workflows."

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "media": ("*",),
            "optimizer_base_url": ("STRING", {"default": ""}),
            "optimizer_model": ("STRING", {"default": ""}),
            "optimizer_api_key": ("STRING", {"default": ""}),
        }
        for index in range(1, MAX_MEDIA + 1):
            optional[f"media_{index}"] = ("*",)
            optional[f"media_type_{index}"] = ("STRING", {"default": ""})
        return {
            "required": {
                "h3_bundle": ("MINIMAX_H3_BUNDLE",),
                "mode": ([MODE_IMAGE, MODE_REFERENCE], {"default": MODE_IMAGE}),
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
                "resolution": (list(RESOLUTIONS), {"default": RESOLUTION_480}),
                "aspect_ratio": (list(ASPECT_RATIOS), {"default": ASPECT_WIDESCREEN}),
                "width": ("INT", {"default": 1344, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "height": ("INT", {"default": 768, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "seconds": ("FLOAT", {"default": 5.0, "min": MIN_SECONDS, "max": MAX_SECONDS, "step": 1.0}),
                "advanced": ("BOOLEAN", {"default": False}),
                "fps": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 120.0, "step": 1.0}),
                "keyframe_role": ([KEYFRAME_FIRST, KEYFRAME_LAST], {"default": KEYFRAME_FIRST}),
                "ref_image_size": ([REF_IMAGE_1K, REF_IMAGE_2K], {"default": REF_IMAGE_1K}),
                "reference_mention_mode": ([REFERENCE_MENTION_FILENAME, REFERENCE_MENTION_INDEX], {"default": REFERENCE_MENTION_INDEX}),
                "optimize_prompt": ("BOOLEAN", {"default": False}),
            },
            "optional": optional,
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @staticmethod
    def _collect_media(kwargs: dict) -> list[_MediaInput]:
        items = []
        direct = kwargs.get("media")
        if direct is not None:
            items.append(_MediaInput(0, _infer_media_type(direct), direct))
        for index in range(1, MAX_MEDIA + 1):
            value = kwargs.get(f"media_{index}")
            if value is None:
                continue
            media_type = str(kwargs.get(f"media_type_{index}") or "").strip().lower()
            resolved_type = media_type if media_type in {"image", "video", "audio"} else _infer_media_type(value)
            items.append(_MediaInput(index, resolved_type, value))
        return items

    @staticmethod
    def _keyframes(items, role):
        images = [item.value for item in items if item.media_type == "image"]
        if any(item.media_type != "image" for item in items):
            raise ValueError("Image mode accepts image resources only")
        if len(images) > 2:
            raise ValueError("Image mode accepts at most two images")
        if not images:
            return None, None
        if len(images) == 1:
            if role == KEYFRAME_LAST:
                return None, images[0]
            return images[0], None
        if role == KEYFRAME_LAST:
            return images[1], images[0]
        return images[0], images[1]

    @classmethod
    def generate(cls, h3_bundle, mode, prompt, resolution, aspect_ratio, width, height, seconds, advanced, fps, keyframe_role, ref_image_size, reference_mention_mode, optimize_prompt, **kwargs):
        if not isinstance(h3_bundle, MiniMaxH3Bundle):
            raise ValueError("Connect a MiniMax H3 Easy Loader bundle")
        mode = str(mode)
        keyframe_role = KEYFRAME_LAST if str(keyframe_role) == KEYFRAME_LAST else KEYFRAME_FIRST
        width, height = _canvas_dimensions(resolution, aspect_ratio, width, height)
        seconds = min(MAX_SECONDS, max(MIN_SECONDS, float(seconds)))
        length = _frame_length(seconds, fps)
        items = cls._collect_media(kwargs)
        if mode == MODE_REFERENCE and items:
            if len(items) > MAX_MEDIA:
                raise ValueError("Reference mode accepts at most fifteen media resources")
            counts = {"image": 0, "video": 0, "audio": 0}
            for item in items:
                if item.media_type not in counts:
                    raise ValueError("Unsupported media resource")
                counts[item.media_type] += 1
            if counts["image"] > MAX_IMAGES or counts["video"] > MAX_VIDEOS or counts["audio"] > MAX_AUDIOS:
                raise ValueError("Reference mode media limits are 9 images, 3 videos and 3 audio clips")
            if counts["image"] == 0 and counts["video"] == 0:
                raise ValueError("Reference mode needs an image or video in addition to audio")
            if bool(optimize_prompt):
                prompt = optimize_h3_prompt(
                    prompt=prompt,
                    mode=MODE_REFERENCE,
                    base_url=kwargs.get("optimizer_base_url", ""),
                    model=kwargs.get("optimizer_model", ""),
                    api_key=kwargs.get("optimizer_api_key", ""),
                    media_items=_optimizer_media_items(items, MODE_REFERENCE, keyframe_role),
                    duration=seconds,
                )
            model = h3_bundle.model_for("ref2va")
            conditioning, latent = _reference_conditioning(h3_bundle, prompt, width, height, length, ref_image_size, items)
        else:
            first_frame, last_frame = cls._keyframes(items, keyframe_role)
            if bool(optimize_prompt):
                prompt = optimize_h3_prompt(
                    prompt=prompt,
                    mode=MODE_IMAGE,
                    base_url=kwargs.get("optimizer_base_url", ""),
                    model=kwargs.get("optimizer_model", ""),
                    api_key=kwargs.get("optimizer_api_key", ""),
                    media_items=_optimizer_media_items(items, MODE_IMAGE, keyframe_role),
                    duration=seconds,
                )
            model = h3_bundle.model_for("fl2va")
            conditioning, latent = _empty_image_conditioning(h3_bundle, prompt, width, height, length, first_frame, last_frame)
        context = MiniMaxH3Context(
            conditioning=conditioning,
            latent=latent,
            video_vae=h3_bundle.video_vae,
            audio_vae=h3_bundle.audio_vae,
            fps=float(fps),
        )
        return model, context


class MiniMaxH3EasyOutput:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "unpack"
    RETURN_TYPES = ("CONDITIONING", "LATENT", "VAE", "VAE", "FLOAT")
    RETURN_NAMES = ("positive", "latent", "video_vae", "audio_vae", "fps")
    DESCRIPTION = "Unpack the non-model outputs from a MiniMax H3 Easy context."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "h3_context": ("MINIMAX_H3_CONTEXT",),
            },
        }

    @staticmethod
    def unpack(h3_context):
        if not isinstance(h3_context, MiniMaxH3Context):
            raise ValueError("Connect the H3 Context output from a MiniMax H3 Easy node")
        return (
            h3_context.conditioning,
            h3_context.latent,
            h3_context.video_vae,
            h3_context.audio_vae,
            h3_context.fps,
        )


NODE_CLASS_MAPPINGS = {
    "MiniMaxH3EasyLoader": MiniMaxH3EasyLoader,
    "MiniMaxH3Easy": MiniMaxH3Easy,
    "MiniMaxH3EasyOutput": MiniMaxH3EasyOutput,
}
