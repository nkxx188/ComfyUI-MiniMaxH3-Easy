"""Built-in MiniMax H3 latent upscaler.

The upscaler is kept in the Easy node package so a context second pass does
not depend on another custom-node repository.  It operates on H3's 24-channel
VAE latent and only changes the spatial grid; the temporal axis is preserved.
"""

from __future__ import annotations

import glob
import logging
import os
import re
import threading
from enum import Enum
from typing import Any, TypedDict

import torch
import torch.nn as nn
import torch.nn.functional as F

import folder_paths
from comfy_api.latest import io


LOGGER = logging.getLogger("MiniMaxH3Easy.latent_upscaler")
MODEL_FOLDER = "latent_upscale_models"
VAE_DOWNSAMPLE = 16
MODEL_CACHE: dict[tuple[str, str, str], nn.Module] = {}
MODEL_CACHE_LOCK = threading.RLock()

LATENT_MEAN = (
    0.858090341091156, -0.9606591463088989, 1.0661640167236328,
    -0.5090325474739075, -0.2727581858634949, -1.3675414323806763,
    -0.2553254961967468, -0.26907554268836975, -0.5376840829849243,
    -0.0464097298681736, 0.6657370328903198, 0.19690127670764923,
    -0.5460608005523682, -0.4035342037677765, -0.23683024978739908,
    0.25928452610969543, -0.30133944749832153, 0.211341992020607,
    -1.1206848621368408, 0.3581933379173279, -0.04225143790245056,
    0.2604829967021942, 0.22864092886447906, 0.7056031823158264,
)
LATENT_STD = (
    1.2223774194717407, 1.2767263650894165, 1.6831774711608887,
    1.7549455165863037, 1.5636216402053833, 2.194143533706665,
    0.9653137922286987, 1.0569885969161987, 0.841948926448822,
    0.7729952931404111, 1.8955937623977661, 0.946841835975647,
    0.7996809482574463, 0.44988900423049927, 0.7197399735450745,
    0.6936293244361877, 2.961095094680786, 2.7694199085235596,
    3.0496184825897217, 2.1088054180145264, 3.276226282119751,
    3.1627357006073, 2.2816812992095947, 2.6127843856811523,
)


def _ensure_model_folder() -> None:
    if MODEL_FOLDER not in folder_paths.folder_names_and_paths:
        folder_paths.add_model_folder_path(
            MODEL_FOLDER,
            os.path.join(folder_paths.models_dir, MODEL_FOLDER),
        )


_ensure_model_folder()


def _model_dirs() -> list[str]:
    try:
        paths = folder_paths.get_folder_paths(MODEL_FOLDER)
    except Exception:
        paths = []
    return [os.fspath(path) for path in paths if os.path.isdir(path)]


def _model_path(name: str) -> str:
    normalized = str(name or "").replace("\\", "/")
    if os.path.isabs(normalized):
        candidate = os.path.realpath(normalized)
        if os.path.isfile(candidate):
            return candidate
    for base in _model_dirs():
        candidate = os.path.realpath(os.path.join(base, normalized))
        if candidate.startswith(os.path.realpath(base) + os.sep) and os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(f"MiniMax H3 latent upscaler model not found: {name}")


def scan_models() -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for base in _model_dirs():
        for pattern in ("*.safetensors", "*.pth", "*.pt"):
            for path in glob.glob(os.path.join(base, pattern)):
                name = os.path.basename(path)
                if name not in seen:
                    seen.add(name)
                    names.append(name)
    names.sort(key=str.casefold)
    return names or [f"(place models in: {_model_dirs()[0] if _model_dirs() else MODEL_FOLDER})"]


def _resolve_device(choice: str) -> torch.device:
    choice = str(choice or "cuda").lower()
    if choice == "cpu":
        return torch.device("cpu")
    if choice == "rocm":
        if getattr(torch.version, "hip", None) is None or not torch.cuda.is_available():
            raise RuntimeError("ROCm was selected, but this PyTorch build cannot access an AMD GPU")
        return torch.device("cuda")
    if choice == "cuda":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    raise ValueError(f"Unsupported latent upscaler device: {choice}")


def _device_label(device: torch.device) -> str:
    if device.type == "cuda" and getattr(torch.version, "hip", None) is not None:
        return f"rocm:{torch.version.hip}"
    if device.type == "cuda":
        return f"cuda:{getattr(torch.version, 'cuda', None) or 'unknown'}"
    return "cpu"


def _normalization_tensors(device: torch.device, dtype: torch.dtype) -> tuple[torch.Tensor, torch.Tensor]:
    mean = torch.tensor(LATENT_MEAN, device=device, dtype=dtype).view(1, -1, 1, 1, 1)
    std = torch.tensor(LATENT_STD, device=device, dtype=dtype).view(1, -1, 1, 1, 1)
    return mean, std


def _group_norm(channels: int) -> nn.GroupNorm:
    groups = min(32, channels)
    while groups > 1 and channels % groups:
        groups -= 1
    return nn.GroupNorm(groups, channels)


def _zero_module(module: nn.Module) -> nn.Module:
    for parameter in module.parameters():
        parameter.detach().zero_()
    return module


class _TemporalConv(nn.Module):
    def __init__(self, channels: int, kernel_size: int = 5):
        super().__init__()
        padding = kernel_size // 2
        self.norm = _group_norm(channels)
        self.dwconv = nn.Conv3d(
            channels, channels, (kernel_size, 1, 1),
            padding=(padding, 0, 0), groups=channels,
        )
        self.pwconv = nn.Conv3d(channels, channels, 1)
        nn.init.zeros_(self.pwconv.weight)
        nn.init.zeros_(self.pwconv.bias)

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        hidden = self.dwconv(F.silu(self.norm(value)))
        return value + self.pwconv(hidden)


class _ResBlock(nn.Module):
    def __init__(self, channels: int, embedding: int, dropout: float = 0.1):
        super().__init__()
        self.in_layers = nn.Sequential(
            _group_norm(channels), nn.SiLU(), nn.Conv3d(channels, channels, 3, padding=1),
        )
        self.emb_layers = nn.Sequential(nn.SiLU(), nn.Linear(embedding, 2 * channels))
        self.out_norm = _group_norm(channels)
        self.out_layers = nn.Sequential(
            nn.SiLU(), nn.Dropout(dropout),
            _zero_module(nn.Conv3d(channels, channels, 3, padding=1)),
        )
        self.skip = nn.Identity()

    def forward(self, value: torch.Tensor, embedding: torch.Tensor) -> torch.Tensor:
        hidden = self.in_layers(value)
        modulation = self.emb_layers(embedding).to(dtype=hidden.dtype)
        while modulation.ndim < hidden.ndim:
            modulation = modulation[..., None]
        scale, shift = modulation.chunk(2, dim=1)
        hidden = self.out_norm(hidden) * (1 + scale) + shift
        return self.skip(value) + self.out_layers(hidden)


class _LatentResizer3D(nn.Module):
    def __init__(
        self,
        in_channels: int = 24,
        in_blocks: int = 12,
        out_blocks: int = 12,
        channels: int = 512,
        dropout: float = 0.1,
        temporal_every: int = 2,
        temporal_kernel: int = 5,
    ):
        super().__init__()
        self.conv_in = nn.Conv3d(in_channels, channels, 3, padding=1)
        self.embed = nn.Sequential(nn.Linear(1, 64), nn.SiLU(), nn.Linear(64, 64))
        self.in_blocks = self._make_blocks(in_blocks, channels, temporal_every, temporal_kernel, dropout)
        self.out_blocks = self._make_blocks(out_blocks, channels, temporal_every, temporal_kernel, dropout)
        self.norm_out = _group_norm(channels)
        self.conv_out = nn.Conv3d(channels, in_channels, 3, padding=1)

    @staticmethod
    def _make_blocks(count: int, channels: int, temporal_every: int, temporal_kernel: int, dropout: float) -> nn.ModuleList:
        blocks: list[nn.Module] = []
        for index in range(count):
            blocks.append(_ResBlock(channels, 64, dropout))
            if temporal_every > 0 and index % temporal_every == 0:
                blocks.append(_TemporalConv(channels, temporal_kernel))
        return nn.ModuleList(blocks)

    def _forward_segment(
        self, value: torch.Tensor, scale: float, target_size: tuple[int, int, int],
    ) -> torch.Tensor:
        embedding = self.embed(torch.tensor([[scale - 1.0]], device=value.device, dtype=value.dtype))
        hidden = self.conv_in(value)
        for block in self.in_blocks:
            hidden = block(hidden, embedding) if isinstance(block, _ResBlock) else block(hidden)
        hidden = F.interpolate(hidden, size=target_size, mode="trilinear", align_corners=False)
        for block in self.out_blocks:
            hidden = block(hidden, embedding) if isinstance(block, _ResBlock) else block(hidden)
        return self.conv_out(F.silu(self.norm_out(hidden)))

    def forward(
        self, value: torch.Tensor, scale: float, target_size: tuple[int, int, int],
        enable_chunking: bool,
    ) -> torch.Tensor:
        source_t = int(value.shape[2])
        if not enable_chunking or source_t <= 24:
            return self._forward_segment(value, scale, target_size)

        temporal_kernel = 5
        for block in self.in_blocks:
            if isinstance(block, _TemporalConv):
                temporal_kernel = int(block.dwconv.kernel_size[0])
                break
        overlap = max(1, temporal_kernel)
        chunk_size = 24
        padded = F.pad(value, (0, 0, 0, 0, overlap, overlap), mode="replicate")
        out = torch.zeros(
            value.shape[0], value.shape[1], source_t, target_size[-2], target_size[-1],
            device=value.device, dtype=value.dtype,
        )
        weights = torch.zeros(1, 1, source_t, 1, 1, device=value.device, dtype=value.dtype)

        for start in range(0, source_t, chunk_size):
            end = min(source_t, start + chunk_size)
            output_start = max(0, start - overlap)
            output_end = min(source_t, end + overlap)
            low = max(0, output_start - overlap)
            high = min(source_t + 2 * overlap, output_end + overlap)
            segment = padded[:, :, low:high]
            segment_out = self._forward_segment(segment, scale, (high - low, target_size[-2], target_size[-1]))
            source_offset = (output_start + overlap) - low
            valid = segment_out[:, :, source_offset:source_offset + output_end - output_start]
            length = output_end - output_start
            blend = torch.ones(length, device=value.device, dtype=value.dtype)
            if start > output_start:
                count = start - output_start
                blend[:count] = torch.arange(1, count + 1, device=value.device, dtype=value.dtype) / (count + 1)
            if output_end > end:
                count = output_end - end
                blend[-count:] = torch.arange(count, 0, -1, device=value.device, dtype=value.dtype) / (count + 1)
            blend = blend.view(1, 1, length, 1, 1)
            out[:, :, output_start:output_end] += valid * blend
            weights[:, :, output_start:output_end] += blend
        return out / weights.clamp_min(1e-8)


def _load_state_dict(path: str) -> dict[str, torch.Tensor]:
    if path.lower().endswith(".safetensors"):
        from safetensors.torch import load_file
        state = load_file(path, device="cpu")
    else:
        state = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and isinstance(state.get("model"), dict):
        state = state["model"]
    if not isinstance(state, dict):
        raise RuntimeError("The latent upscaler checkpoint is not a state-dict")
    state = {str(key): value for key, value in state.items() if isinstance(value, torch.Tensor)}
    if any(key.startswith("upscaler.") for key in state):
        state = {key.removeprefix("upscaler."): value for key, value in state.items() if key.startswith("upscaler.")}
    return {
        key: value.to(dtype=torch.float16) if value.dtype == torch.float8_e4m3fn else value
        for key, value in state.items()
    }


def _architecture(state: dict[str, torch.Tensor]) -> dict[str, Any]:
    config: dict[str, Any] = {
        "in_channels": 24, "in_blocks": 12, "out_blocks": 12, "channels": 512,
        "dropout": 0.1, "temporal_every": 2, "temporal_kernel": 5,
    }
    if "conv_in.weight" in state:
        config["in_channels"] = int(state["conv_in.weight"].shape[1])
        config["channels"] = int(state["conv_in.weight"].shape[0])
    in_ids = {int(match.group(1)) for key in state for match in [re.match(r"in_blocks\.(\d+)\.in_layers\.", key)] if match}
    out_ids = {int(match.group(1)) for key in state for match in [re.match(r"out_blocks\.(\d+)\.in_layers\.", key)] if match}
    if in_ids:
        config["in_blocks"] = len(in_ids)
    if out_ids:
        config["out_blocks"] = len(out_ids)
    temporal_keys = [key for key in state if key.endswith("dwconv.weight")]
    if temporal_keys:
        config["temporal_kernel"] = int(state[temporal_keys[0]].shape[2])
    else:
        config["temporal_every"] = 0
    return config


def _load_model(name: str, device: torch.device, precision: str) -> nn.Module:
    key = (str(name), _device_label(device), str(precision))
    dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}.get(precision)
    if dtype is None:
        raise ValueError(f"Unsupported latent upscaler precision: {precision}")
    with MODEL_CACHE_LOCK:
        model = MODEL_CACHE.get(key)
        if model is not None:
            return model.to(device).eval()
        state = _load_state_dict(_model_path(name))
        model = _LatentResizer3D(**_architecture(state))
        model.load_state_dict(state, strict=True)
        model = model.to(device=device, dtype=dtype).eval().requires_grad_(False)
        MODEL_CACHE[key] = model
        LOGGER.info("Loaded built-in H3 latent upscaler %s on %s (%s)", name, _device_label(device), precision)
        return model


class UpscaleMode(str, Enum):
    SCALE_BY = "scale by multiplier"
    TARGET_DIMENSIONS = "target dimensions"
    MEGAPIXELS = "megapixels"


class UpscaleConfig(TypedDict, total=False):
    mode: str
    scale: float
    width: int
    height: int
    megapixels: float


class MiniMaxH3EasyLatentUpscaler3D(io.ComfyNode):
    """Built-in neural 3D upscaler for MiniMax H3 video latents."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MiniMaxH3EasyLatentUpscaler3D",
            display_name="MiniMax H3 Easy 3D Latent Upscale (Built-in)",
            category="video/MinimaxH3",
            search_aliases=["minimax", "h3", "latent", "upscale", "3d"],
            inputs=[
                io.AnyType.Input("latent", tooltip="Input MiniMax H3 latent."),
                io.Combo.Input("model_name", options=scan_models(), tooltip="Latent upscaler checkpoint."),
                io.DynamicCombo.Input(
                    "mode", tooltip="How the output size is selected.", options=[
                        io.DynamicCombo.Option(UpscaleMode.SCALE_BY, [
                            io.Float.Input("scale", default=2.0, min=1.0, max=4.0, step=0.05),
                        ]),
                        io.DynamicCombo.Option(UpscaleMode.TARGET_DIMENSIONS, [
                            io.Int.Input("width", default=1280, min=64, max=8192, step=8),
                            io.Int.Input("height", default=704, min=64, max=8192, step=8),
                        ]),
                        io.DynamicCombo.Option(UpscaleMode.MEGAPIXELS, [
                            io.Float.Input("megapixels", default=1.0, min=0.1, max=16.0, step=0.1),
                        ]),
                    ],
                ),
                io.Int.Input("align", default=32, min=1, max=512, step=1,
                             tooltip="Output pixel-grid alignment; 32 is recommended for H3."),
                io.Boolean.Input("enable_chunking", default=True,
                                 tooltip="Use temporal overlap blending for long clips."),
                io.Combo.Input("device", options=["cuda", "rocm", "cpu"], default="cuda"),
                io.Combo.Input("precision", options=["fp32", "fp16", "bf16"], default="fp16"),
            ],
            outputs=[io.AnyType.Output("latent", tooltip="Upscaled H3 latent.")],
        )

    @classmethod
    def execute(
        cls,
        latent: dict[str, Any],
        model_name: str,
        mode: UpscaleConfig,
        align: int,
        enable_chunking: bool,
        device: str,
        precision: str,
    ) -> io.NodeOutput:
        if not isinstance(latent, dict) or not isinstance(latent.get("samples"), torch.Tensor):
            raise ValueError("MiniMax H3 Easy 3D Latent Upscale requires a LATENT input")
        if str(model_name).startswith("("):
            raise ValueError("Place a MiniMax H3 latent upscaler checkpoint in models/latent_upscale_models")
        source = latent["samples"]
        if source.ndim not in (4, 5):
            raise ValueError(f"Expected a 4D or 5D latent, got shape {tuple(source.shape)}")
        selected_mode = str(mode.get("mode") or UpscaleMode.SCALE_BY)
        if selected_mode == UpscaleMode.SCALE_BY and abs(float(mode.get("scale", 1.0)) - 1.0) < 1e-6:
            return io.NodeOutput(latent)

        source_dtype = source.dtype
        working_device = _resolve_device(device)
        working_dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}.get(str(precision))
        if working_dtype is None:
            raise ValueError(f"Unsupported latent upscaler precision: {precision}")
        value = source.to(device=working_device, dtype=working_dtype)
        was_image = value.ndim == 4
        if was_image:
            value = value.unsqueeze(2)
        _, _, temporal, height, width = value.shape

        if selected_mode == UpscaleMode.SCALE_BY:
            requested_scale = float(mode.get("scale", 2.0))
            pixel_width = width * VAE_DOWNSAMPLE * requested_scale
            pixel_height = height * VAE_DOWNSAMPLE * requested_scale
            effective_scale = requested_scale
        elif selected_mode == UpscaleMode.TARGET_DIMENSIONS:
            pixel_width = float(mode.get("width", width * VAE_DOWNSAMPLE))
            pixel_height = float(mode.get("height", height * VAE_DOWNSAMPLE))
            effective_scale = ((pixel_width / (width * VAE_DOWNSAMPLE)) + (pixel_height / (height * VAE_DOWNSAMPLE))) / 2
        elif selected_mode == UpscaleMode.MEGAPIXELS:
            pixels = max(0.1, float(mode.get("megapixels", 1.0))) * 1024 * 1024
            aspect = width / max(1, height)
            pixel_height = (pixels / aspect) ** 0.5
            pixel_width = pixel_height * aspect
            effective_scale = ((pixel_width / (width * VAE_DOWNSAMPLE)) + (pixel_height / (height * VAE_DOWNSAMPLE))) / 2
        else:
            raise ValueError(f"Unsupported latent upscale mode: {selected_mode}")

        grid = max(1, int(align))
        output_width = max(1, int(round(round(pixel_width / grid) * grid / VAE_DOWNSAMPLE)))
        output_height = max(1, int(round(round(pixel_height / grid) * grid / VAE_DOWNSAMPLE)))
        if output_width < width or output_height < height:
            raise ValueError("The aligned target would downscale the H3 latent; choose a larger target")
        if output_width == width and output_height == height:
            return io.NodeOutput(latent)

        model = _load_model(str(model_name), working_device, str(precision))
        mean, std = _normalization_tensors(working_device, working_dtype)
        try:
            with torch.inference_mode():
                normalized = (value - mean) / std
                upscaled = model(
                    normalized,
                    effective_scale,
                    (int(temporal), output_height, output_width),
                    bool(enable_chunking),
                )
                upscaled = upscaled * std + mean
        finally:
            if working_device.type == "cuda":
                model.to("cpu")
                torch.cuda.empty_cache()
        if was_image:
            upscaled = upscaled.squeeze(2)
        result = dict(latent)
        result["samples"] = upscaled.to(device="cpu", dtype=source_dtype)
        return io.NodeOutput(result)


NODE_CLASS_MAPPINGS = {"MiniMaxH3EasyLatentUpscaler3D": MiniMaxH3EasyLatentUpscaler3D}
NODE_DISPLAY_NAME_MAPPINGS = {"MiniMaxH3EasyLatentUpscaler3D": "MiniMax H3 Easy 3D Latent Upscale (Built-in)"}
