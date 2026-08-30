"""A compact MiniMax H3 entry point for ComfyUI.

The node intentionally keeps the graph contract small: one loader bundle, one
mode-aware conditioning node, and standard ComfyUI outputs for the sampler
chain. The browser extension supplies the ordered virtual media inputs.
"""

from __future__ import annotations

import gc
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import hashlib
import base64
import asyncio
import json
import mimetypes
import tempfile
import urllib.parse
import urllib.request
import uuid
import weakref
from collections import OrderedDict
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import torch
import torchaudio
import requests
import psutil

import comfy.sample
import comfy.utils
import comfy.model_management
import folder_paths
import node_helpers
import nodes
from comfy_api.latest import InputImpl
from comfy_extras import nodes_audio, nodes_custom_sampler
from comfy_extras import nodes_minimax_h3 as h3
from .h3_latent_upscaler import MiniMaxH3EasyLatentUpscaler3D, scan_models as scan_latent_upscaler_models


MODE_IMAGE = "image"
MODE_REFERENCE = "reference"
MODE_DIGITAL_HUMAN = "digital_human"
MODE_SEGMENTS = "context_segments"
CONTEXT_AUDIO_GENERATED = "generated"
CONTEXT_AUDIO_DIGITAL_HUMAN = MODE_DIGITAL_HUMAN
KEYFRAME_FIRST = "first"
KEYFRAME_LAST = "last"
REF_IMAGE_1K = "1k"
REF_IMAGE_15K = "1.5k"
REF_IMAGE_2K = "2k"
REF_IMAGE_MATCH = "match"
REF_IMAGE_ORIGINAL = "original"
REFERENCE_MENTION_FILENAME = "filename"
REFERENCE_MENTION_INDEX = "index"
NONE_MODEL = "none"
NONE_MODEL_DISPLAY_VALUES = (NONE_MODEL, "None", "无")
NONE_MODEL_ALIASES = {value.lower() for value in NONE_MODEL_DISPLAY_VALUES}
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
REFERENCE_IMAGE_AREAS = {
    REF_IMAGE_1K: 1024 * 1024,
    REF_IMAGE_15K: 1536 * 1536,
    REF_IMAGE_2K: 2048 * 2048,
}
REFERENCE_SIZE_SEARCH_RADIUS = 16
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
ASPECT_SELECTOR_LABELS = {
    ASPECT_SQUARE: "1:1 (Square)",
    ASPECT_PHOTO_PORTRAIT: "2:3 (Portrait Photo)",
    ASPECT_PHOTO: "3:2 (Photo)",
    ASPECT_STANDARD_PORTRAIT: "3:4 (Portrait Standard)",
    ASPECT_STANDARD: "4:3 (Standard)",
    ASPECT_WIDESCREEN_PORTRAIT: "9:16 (Portrait Widescreen)",
    ASPECT_WIDESCREEN: "16:9 (Widescreen)",
    ASPECT_ULTRAWIDE: "21:9 (Ultrawide)",
}
MAX_MEDIA = 15
MAX_IMAGES = 9
MAX_VIDEOS = 3
MAX_AUDIOS = 3
MEDIA_BUNDLE_TYPE = "MINIMAX_H3_MEDIA_BUNDLE"
SEGMENT_RESULT_TYPE = "MINIMAX_H3_SEGMENTS"
MIN_SECONDS = 0.2
MAX_SECONDS = 30.0
REFERENCE_VIDEO_CACHE_MAX_ENTRIES = 2
REFERENCE_VIDEO_CACHE_HARD_LIMIT_BYTES = 2 * 1024 ** 3
REFERENCE_VIDEO_CACHE_RESERVE_BYTES = 2 * 1024 ** 3
REFERENCE_VIDEO_CACHE_AVAILABLE_FRACTION = 0.125
# Keep the reference-video cache implementation available for future tuning,
# but disable it by default until its memory behavior is better validated.
REFERENCE_VIDEO_CACHE_ENABLED = False
SEGMENT_MAX_COUNT = 30
SEGMENT_MAX_MEDIA = MAX_MEDIA * 3
SEGMENT_MAX_IMAGES = MAX_IMAGES * 3
SEGMENT_MAX_VIDEOS = MAX_VIDEOS * 3
SEGMENT_MAX_AUDIOS = MAX_AUDIOS * 3
SEGMENT_MIN_CONTEXT_FRAMES = 5
SEGMENT_DEFAULT_CONTEXT_FRAMES = 5
SEGMENT_MAX_CONTEXT_FRAMES = 141
SEGMENT_CONTEXT_GUIDE_FRAME_GRID = (5, 22, 39, 56, 73)
SEGMENT_CONTEXT_AV_FRAME_GRID = (39, 90, 141)
SEGMENT_CONTEXT_FRAME_GRID = SEGMENT_CONTEXT_GUIDE_FRAME_GRID
SEGMENT_FRAME_PER_TOKEN = (1, 4, 4, 4, 4)
# Keep a short, phase-aligned visual handoff at the outgoing edge. One H3
# temporal token can cover four frames, which is too little for the first
# generated body token to infer motion reliably from every scene.
SEGMENT_GUIDE_HANDOFF_VIDEO_TOKENS = 2
CONTEXT_CONTINUITY_GUIDE = "guide"
CONTEXT_CONTINUITY_LATENT = "latent_guide"
CONTEXT_CONTINUITY_SOFT_AV = "soft_av"
CONTEXT_CONTINUITY_HARD_AV = "hard_av"
CONTEXT_CONTINUITY_AV_MODES = (CONTEXT_CONTINUITY_SOFT_AV, CONTEXT_CONTINUITY_HARD_AV)
CONTEXT_CONTINUITY_MODES = (
    CONTEXT_CONTINUITY_LATENT,
    CONTEXT_CONTINUITY_GUIDE,
    CONTEXT_CONTINUITY_SOFT_AV,
    CONTEXT_CONTINUITY_HARD_AV,
)


class _H3TerminalProgress:
    """Render compact context progress without flooding ComfyUI's log."""

    WIDTH = 24

    def __init__(self, label: str, total: int):
        self.label = str(label)
        self.total = max(1, int(total))
        self.current = -1
        self.stage = ""
        self.interactive = bool(getattr(sys.stdout, "isatty", lambda: False)())
        self._last_length = 0

    def _line(self, current: int, stage: str) -> str:
        current = max(0, min(self.total, int(current)))
        filled = round(self.WIDTH * current / self.total)
        bar = "#" * filled + "-" * (self.WIDTH - filled)
        return f"[MiniMax H3] {self.label} [{bar}] {current}/{self.total} | {stage}"

    def update(self, current: int, stage: str) -> None:
        current = max(0, min(self.total, int(current)))
        stage = str(stage or "")
        if current == self.current and stage == self.stage:
            return
        line = self._line(current, stage)
        if self.interactive:
            padding = max(0, self._last_length - len(line))
            sys.stdout.write("\r" + line + (" " * padding))
            sys.stdout.flush()
            self._last_length = len(line)
        else:
            print(line, flush=True)
        self.current = current
        self.stage = stage

    def finish(self, stage: str = "completed") -> None:
        self.update(self.total, stage)
        if self.interactive:
            sys.stdout.write("\n")
            sys.stdout.flush()


SEGMENT_REFINE_WHOLE = "whole_segment"
SEGMENT_REFINE_TILED = "tiled_low_vram"
SEGMENT_REFINE_EXECUTION_MODES = (
    SEGMENT_REFINE_WHOLE,
    SEGMENT_REFINE_TILED,
)
# Keep the canonical divider narrow enough to avoid splitting prompt prose, but
# accept the harmless escaping that chat agents sometimes add while emitting a
# markdown-like divider (for example ``\---`` or ``---\``).
SEGMENT_DIVIDER_PATTERN = re.compile(
    r"(?m)^[ \t\u00a0]*(?:\\[ \t\u00a0]*)?-{3,}(?:[ \t\u00a0]*\\)?[ \t\u00a0]*$"
)
SEGMENT_DIVIDER_INVISIBLE = "\ufeff\u200b\u200c\u200d\u2060"
SEGMENT_TAG_PATTERN = re.compile(r"<(Picture|Video|Audio)\s+([0-9]{1,2})\s*>", re.IGNORECASE)
OPTIMIZER_THINK_BLOCK_PATTERN = re.compile(
    r"^[\s\\]*<think\b[^>]*>.*?</think\s*>", re.IGNORECASE | re.DOTALL
)
OPTIMIZER_THINK_CLOSE_LINE_PATTERN = re.compile(
    r"(?im)^[ \t]*</think\s*>[ \t]*$"
)
PROMPT_GUIDES_DIR = os.path.join(os.path.dirname(__file__), "prompt_guides")
PROMPT_GUIDE_MANIFEST = os.path.join(PROMPT_GUIDES_DIR, "manifest.json")
PROMPT_OPTIMIZER_TIMEOUT_SECONDS = 600
PROMPT_OPTIMIZER_ON_RUN_TIMEOUT_SECONDS = 120
PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS = 50000
CONTEXT_PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS = 128000
CONTEXT_PROMPT_OPTIMIZER_MEDIA_MAX_RESOURCES = 10
CONTEXT_PROMPT_OPTIMIZER_MEDIA_MAX_BYTES = 96 * 1024 * 1024
CONTEXT_PROMPT_OPTIMIZER_DEFAULT_CONCURRENCY = 3
CONTEXT_PROMPT_OPTIMIZER_MAX_CONCURRENCY = 20
CONTEXT_PROMPT_OPTIMIZER_WHOLE = "whole_sequence"
CONTEXT_PROMPT_OPTIMIZER_PER_SEGMENT = "per_segment"
CONTEXT_PROMPT_OPTIMIZER_MODES = (
    CONTEXT_PROMPT_OPTIMIZER_WHOLE,
    CONTEXT_PROMPT_OPTIMIZER_PER_SEGMENT,
)
# Bump whenever the optimizer contract changes so an older auto-optimized
# result cannot silently bypass the new continuity rules.
PROMPT_OPTIMIZER_MARKER_VERSION = 6


def _reference_aligned_size(image_w: int, image_h: int, scale: float) -> tuple[int, int]:
    """Choose H3-aligned dimensions near the scaled area without stretching refs."""
    multiple = h3.CANVAS_MULTIPLE
    scaled_w = max(float(multiple), image_w * scale)
    scaled_h = max(float(multiple), image_h * scale)
    target_area = scaled_w * scaled_h
    aspect = image_w / max(1, image_h)
    center_h_units = max(1, round(scaled_h / multiple))
    best = None

    for h_units in range(
        max(1, center_h_units - REFERENCE_SIZE_SEARCH_RADIUS),
        center_h_units + REFERENCE_SIZE_SEARCH_RADIUS + 1,
    ):
        ideal_w_units = h_units * aspect
        min_w_units = max(1, math.floor(ideal_w_units) - 2)
        max_w_units = max(min_w_units, math.ceil(ideal_w_units) + 2)
        for w_units in range(min_w_units, max_w_units + 1):
            target_w = w_units * multiple
            target_h = h_units * multiple
            ratio_error = abs((target_w / target_h) / aspect - 1.0)
            area_error = abs((target_w * target_h) / target_area - 1.0)
            score = ratio_error * 20.0 + area_error
            candidate = (score, ratio_error, area_error, target_w, target_h)
            if best is None or candidate < best:
                best = candidate

    return best[3], best[4]


def _original_reference_size(image_w: int, image_h: int) -> tuple[int, int]:
    """Keep original references unscaled, except for H3's required grid alignment."""
    multiple = h3.CANVAS_MULTIPLE
    target_w = (image_w // multiple) * multiple
    target_h = (image_h // multiple) * multiple
    if target_w >= multiple and target_h >= multiple:
        return target_w, target_h

    # A smaller-than-grid source cannot be crop-aligned. Scale it uniformly to
    # the smallest usable H3 size rather than rejecting an otherwise valid input.
    scale = max(multiple / max(1, image_w), multiple / max(1, image_h))
    return _reference_aligned_size(image_w, image_h, scale)


_SEQUENCE_RUN_LOCK = threading.RLock()
_SEQUENCE_ACTIVE_RUN_LOCKS: dict[str, threading.Lock] = {}
_SEQUENCE_ACTIVE_RUN_LOCKS_GUARD = threading.RLock()
REFERENCE_PLACEHOLDER_RE = re.compile(r"__MINIMAX_H3_REF_(\d+)__")
UNRESOLVED_REFERENCE_RE = re.compile(r"__MINIMAX_H3_UNRESOLVED_REF_[^_]+__")
REFERENCE_TAG_PATTERN = re.compile(r"<\s*(picture|video|audio)\s+(\d+)\s*>", re.IGNORECASE)
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


def _collect_weight_names(categories: tuple[str, ...]) -> list[str]:
    """Collect the current model filenames advertised by ComfyUI.

    Model folders can be refreshed while ComfyUI is running. Keeping this
    result cached made the Easy Loader retain the first snapshot for the
    lifetime of the process, so newly downloaded models did not appear even
    after ComfyUI refreshed its own filename lists.
    """
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


def _is_none_model(value: Any) -> bool:
    return str(value or "").strip().lower() in NONE_MODEL_ALIASES


def _read_prompt_guide_text(relative_path: str) -> str:
    path = os.path.realpath(os.path.join(PROMPT_GUIDES_DIR, str(relative_path or "")))
    root = os.path.realpath(PROMPT_GUIDES_DIR)
    if not path.startswith(root + os.sep) or not os.path.isfile(path):
        raise ValueError(f"Prompt guide file not found: {relative_path}")
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


@lru_cache(maxsize=1)
def _prompt_guide_manifest() -> dict[str, Any]:
    try:
        with open(PROMPT_GUIDE_MANIFEST, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _prompt_guide_bundle(scene_guide: str, mode: str, seconds: float, media_counts: Mapping[str, int]) -> str:
    manifest = _prompt_guide_manifest()
    general = manifest.get("general") if isinstance(manifest.get("general"), dict) else {}
    blocks = [
        "You are the MiniMax H3 Prompt Optimizer inside a ComfyUI node.",
        "Return only the final prompt text. Do not add explanations, markdown fences, titles, or commentary.",
        "Use the complete prompt guide text below. Preserve all official field names, section order, labels, timing notation, dialogue language, and reference tags.",
        f"Node context: mode={mode}; duration_seconds={float(seconds):.2f}; media_counts={dict(media_counts)}.",
    ]
    if general.get("path"):
        blocks.append("=== H3 GENERAL PROMPT GUIDE ===\n" + _read_prompt_guide_text(str(general["path"])))
    if general.get("base_reference") and mode not in (MODE_REFERENCE, MODE_DIGITAL_HUMAN):
        blocks.append("=== H3 BASE REFERENCE GUIDE ===\n" + _read_prompt_guide_text(str(general["base_reference"])))
    if general.get("ref_reference") and mode in (MODE_REFERENCE, MODE_DIGITAL_HUMAN):
        blocks.append("=== H3 FULL-REFERENCE GUIDE ===\n" + _read_prompt_guide_text(str(general["ref_reference"])))
    if scene_guide and scene_guide != "none":
        for item in manifest.get("scene_guides") or []:
            if isinstance(item, dict) and str(item.get("id")) == scene_guide and item.get("path"):
                scene_path = str(item["path"])
                blocks.append("=== SELECTED SCENE PROMPT GUIDE ===\n" + _read_prompt_guide_text(scene_path))
                reference_dir = os.path.join(PROMPT_GUIDES_DIR, os.path.dirname(scene_path), "references")
                if os.path.isdir(reference_dir):
                    for root, _dirs, filenames in os.walk(reference_dir):
                        for filename in sorted(filenames):
                            if os.path.splitext(filename)[1].lower() not in {".md", ".txt"}:
                                continue
                            relative = os.path.relpath(os.path.join(root, filename), PROMPT_GUIDES_DIR).replace(os.sep, "/")
                            blocks.append(f"=== SELECTED SCENE REFERENCE: {relative} ===\n" + _read_prompt_guide_text(relative))
                break
    return "\n\n".join(blocks)


def _prompt_optimizer_flag(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _workflow_prompt_optimizer_settings(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    api_format = str(kwargs.get("prompt_optimizer_api_format") or "openai").strip().lower()
    if api_format not in {"openai", "responses", "gemini"}:
        api_format = "openai"
    return {
        "enabled": _prompt_optimizer_flag(kwargs.get("prompt_optimizer")),
        "api_format": api_format,
        "api_url": str(kwargs.get("prompt_optimizer_api_url") or "").strip(),
        "api_key": str(kwargs.get("prompt_optimizer_api_key") or ""),
        "model": str(kwargs.get("prompt_optimizer_model") or "").strip(),
        "scene_guide": str(kwargs.get("prompt_optimizer_scene_guide") or "none"),
        "read_media": _prompt_optimizer_flag(kwargs.get("prompt_optimizer_read_media")),
        "optimize_on_run": _prompt_optimizer_flag(kwargs.get("prompt_optimizer_optimize_on_run")),
    }


def _prompt_optimizer_api_key_required(api_format: str) -> bool:
    return str(api_format or "openai").strip().lower() == "gemini"


def _prompt_optimizer_settings_complete(api_url: str, api_key: str, model: str, api_format: str) -> bool:
    return bool(
        str(api_url or "").strip()
        and str(model or "").strip()
        and (str(api_key or "").strip() or not _prompt_optimizer_api_key_required(api_format))
    )


_OPTIMIZER_KNOWN_ENDPOINT_SUFFIXES = (
    "/v1/chat/completions",
    "/chat/completions",
    "/v1/responses",
    "/responses",
)
_OPTIMIZER_GEMINI_ENDPOINT_RE = re.compile(
    r"/(v1beta|v1)/models/[^/?:#]+?:(generateContent|streamGenerateContent)$",
    flags=re.I,
)


def _normalize_optimizer_base_url(api_url: str) -> str:
    base = str(api_url or "").strip()
    if not base:
        raise ValueError("Prompt optimization API URL is required")
    if not re.match(r"^https?://", base, flags=re.I):
        base = "https://" + base
    parsed = urllib.parse.urlsplit(base)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), parsed.query, ""))


def _optimizer_endpoint_kind(value: str) -> str:
    lower = urllib.parse.urlsplit(str(value or "")).path.rstrip("/").lower()
    if lower.endswith("/chat/completions"):
        return "chat"
    if lower.endswith("/responses"):
        return "responses"
    if _OPTIMIZER_GEMINI_ENDPOINT_RE.search(lower):
        return "gemini"
    return ""


def _normalize_gemini_model_id(model: str) -> str:
    """Accept a bare model ID, ``models/<id>``, or a full Gemini model URL."""
    raw = urllib.parse.unquote(str(model or "").strip())
    if not raw:
        raise ValueError("Prompt optimization model is required")
    if "://" in raw:
        raw = urllib.parse.urlsplit(raw).path
    raw = raw.split("?", 1)[0].split("#", 1)[0].strip().strip("/")
    match = re.search(r"(?:^|/)models/([^/:]+)(?::[A-Za-z]+)?$", raw, flags=re.I)
    if match:
        raw = match.group(1)
    else:
        if raw.lower().startswith("models/"):
            raw = raw[7:]
        raw = raw.rsplit("/", 1)[-1]
        raw = re.sub(r":(?:generateContent|streamGenerateContent)$", "", raw, flags=re.I)
    raw = raw.strip()
    if not raw:
        raise ValueError("Prompt optimization model is required")
    return raw


def _gemini_url_with_query(url: str, query: str) -> str:
    # ``alt=sse`` belongs to streamGenerateContent and would corrupt the JSON
    # response expected from generateContent. Preserve other proxy parameters.
    pairs = [(key, value) for key, value in urllib.parse.parse_qsl(query, keep_blank_values=True) if key.lower() != "alt"]
    encoded = urllib.parse.urlencode(pairs)
    return url + (f"?{encoded}" if encoded else "")


def _normalize_gemini_optimizer_url(api_url: str, model: str) -> str:
    base = _normalize_optimizer_base_url(api_url)
    parsed = urllib.parse.urlsplit(base)
    clean = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))
    lower = clean.lower()
    model_id = urllib.parse.quote(_normalize_gemini_model_id(model), safe=".-_")

    endpoint_match = _OPTIMIZER_GEMINI_ENDPOINT_RE.search(lower)
    if endpoint_match and lower.endswith(endpoint_match.group(0)):
        version = endpoint_match.group(1)
        clean = clean[: endpoint_match.start()].rstrip("/")
        url = f"{clean}/{version}/models/{model_id}:generateContent"
        return _gemini_url_with_query(url, parsed.query)

    if lower.endswith("/v1beta/models") or lower.endswith("/v1/models"):
        url = f"{clean}/{model_id}:generateContent"
    elif lower.endswith("/v1beta") or lower.endswith("/v1"):
        url = f"{clean}/models/{model_id}:generateContent"
    elif lower.endswith("/models"):
        url = f"{clean}/{model_id}:generateContent"
    else:
        url = f"{clean}/v1beta/models/{model_id}:generateContent"
    return _gemini_url_with_query(url, parsed.query)


def _strip_optimizer_endpoint(base: str) -> str:
    lower = base.lower()
    for suffix in _OPTIMIZER_KNOWN_ENDPOINT_SUFFIXES:
        if lower.endswith(suffix):
            return base[: len(base) - len(suffix)].rstrip("/")
    match = _OPTIMIZER_GEMINI_ENDPOINT_RE.search(lower)
    if match and lower.endswith(match.group(0)):
        return base[: match.start()].rstrip("/")
    return base


def _optimizer_url_with_query(url: str, query: str) -> str:
    return url + (f"?{query}" if query else "")


def _normalize_optimizer_url(api_url: str, api_format: str, model: str) -> str:
    if api_format == "gemini":
        return _normalize_gemini_optimizer_url(api_url, model)
    base = _normalize_optimizer_base_url(api_url)
    parsed = urllib.parse.urlsplit(base)
    clean = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))
    endpoint = "/v1/responses" if api_format == "responses" else "/v1/chat/completions"
    base_kind = _optimizer_endpoint_kind(clean)
    endpoint_kind = _optimizer_endpoint_kind(endpoint)
    if base_kind == endpoint_kind == "chat":
        return _optimizer_url_with_query(clean, parsed.query)
    if base_kind == endpoint_kind == "responses":
        return _optimizer_url_with_query(clean, parsed.query)
    base = _strip_optimizer_endpoint(clean)
    if base.lower().endswith("/v1") and endpoint.lower().startswith("/v1/"):
        endpoint = endpoint[3:]
    return _optimizer_url_with_query(base + endpoint, parsed.query)


def _optimizer_responses_text(data: Any) -> str:
    if not isinstance(data, Mapping):
        return ""
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    output = data.get("output")
    chunks: list[str] = []
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, Mapping):
                continue
            # Responses reasoning is a separate output item. Its optional
            # summary is not the prompt we asked the model to return.
            item_type = str(item.get("type") or "").lower()
            if item_type in {"reasoning", "thinking", "thought"}:
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, Mapping):
                    continue
                part_type = str(part.get("type") or "").lower()
                if part_type in {"reasoning", "thinking", "thought", "summary_text"}:
                    continue
                value = part.get("text")
                if isinstance(value, str):
                    chunks.append(value)
                elif isinstance(value, Mapping) and isinstance(value.get("value"), str):
                    chunks.append(value["value"])
    if chunks:
        return "".join(chunks)
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {}) if isinstance(choices[0], Mapping) else {}
        content = message.get("content", "") if isinstance(message, Mapping) else ""
        if isinstance(content, str):
            return content
    return ""


def _optimizer_part_is_thought(part: Mapping[str, Any]) -> bool:
    """Return whether a provider content part is model reasoning."""
    def flag(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    if flag(part.get("thought")) or flag(part.get("is_thought")):
        return True
    part_type = str(part.get("type") or "").strip().lower()
    if part_type in {"reasoning", "thinking", "thought", "summary_text"}:
        return True
    # A few OpenAI-compatible gateways use an explicit reasoning flag rather
    # than the standard content-part type.
    return flag(part.get("reasoning")) or flag(part.get("thinking"))


def _optimizer_chat_content_text(content: Any) -> str:
    """Extract visible assistant text from string or multipart content."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    chunks: list[str] = []
    for part in content:
        if not isinstance(part, Mapping) or _optimizer_part_is_thought(part):
            continue
        value = part.get("text")
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, Mapping) and isinstance(value.get("value"), str):
            chunks.append(value["value"])
    return "".join(chunks)


def _strip_optimizer_thoughts(text: Any) -> str:
    """Remove model reasoning blocks before prompt text reaches the node.

    Reasoning-capable models may put an internal chain of thought in a
    ``<think>...</think>`` block even when the request asks for only the final
    prompt. Some Qwen thinking-only templates provide the opening ``<think>``
    in the input and return only ``</think>`` in the completion, so that form
    is handled by keeping the text after the final closing tag. Keep the
    cleanup narrow while leaving ordinary prompt markup untouched.
    """
    value = str(text or "")
    if not value:
        return ""
    value = OPTIMIZER_THINK_BLOCK_PATTERN.sub("", value)
    # If the provider omitted the opening tag, Qwen thinking-only responses
    # commonly put the closing tag on its own line. Only handle that strict
    # shape; an inline ``</think>`` may be legitimate prompt text and must not
    # cause the preceding user content to be discarded.
    close_match = OPTIMIZER_THINK_CLOSE_LINE_PATTERN.search(value)
    if close_match:
        value = value[close_match.end():]
    return value.strip()


def _optimizer_http_json(
    api_url: str,
    api_key: str,
    model: str,
    api_format: str,
    system_prompt: str,
    user_prompt: str,
    media_parts: list[dict[str, Any]] | None = None,
    timeout_seconds: float = PROMPT_OPTIMIZER_TIMEOUT_SECONDS,
    max_output_tokens: int = PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS,
) -> str:
    url = _normalize_optimizer_url(api_url, api_format, model)
    api_key = str(api_key or "").strip()
    media_parts = list(media_parts or [])
    output_budget = max(1, int(max_output_tokens or PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS))
    if api_format == "gemini":
        if not api_key:
            raise ValueError("Prompt optimization API key is required for Gemini Native")
        headers = {"Content-Type": "application/json", "Accept": "application/json", "x-goog-api-key": api_key}
        # Some Gemini-compatible channels accept the native payload and return
        # candidates but silently ignore systemInstruction. Keep the complete
        # Prompt Guide and the user's source prompt in the same user text part,
        # matching the node's previously verified working Gemini request.
        instruction_and_prompt = (
            system_prompt
            + "\n\n=== USER PROMPT TO OPTIMIZE ===\n"
            + user_prompt
            + "\n\nFollow the Prompt Guide above and return only the final rewritten MiniMax H3 prompt."
        )
        parts = [{"text": instruction_and_prompt}] + media_parts
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0.35, "maxOutputTokens": output_budget},
        }
    elif api_format == "responses":
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        user_content: list[dict[str, Any]] = [{"type": "input_text", "text": user_prompt}]
        user_content.extend(media_parts)
        payload = {
            "model": model,
            "instructions": system_prompt,
            "input": [{"role": "user", "content": user_content}],
            "store": False,
            "stream": False,
            "temperature": 0.35,
            "max_output_tokens": output_budget,
        }
    else:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        content: str | list[dict[str, Any]]
        if media_parts:
            content = [{"type": "text", "text": user_prompt}, *media_parts]
        else:
            content = user_prompt
        payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": content}], "stream": False, "temperature": 0.35, "max_tokens": output_budget}
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=max(1.0, float(timeout_seconds)),
        )
        response.raise_for_status()
        data = response.json()
    except requests.HTTPError as exc:
        response = exc.response
        status_code = response.status_code if response is not None else "unknown"
        detail = response.text if response is not None else str(exc)
        raise RuntimeError(f"Prompt optimization API error ({status_code}): {detail[:1000]}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Prompt optimization request failed: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError("Prompt optimization API returned invalid JSON") from exc
    if api_format == "gemini":
        candidates = data.get("candidates") if isinstance(data, dict) else None
        if not isinstance(candidates, list) or not candidates:
            feedback = data.get("promptFeedback") if isinstance(data, dict) else None
            reason = feedback.get("blockReason") if isinstance(feedback, dict) else None
            detail = f": {reason}" if reason else ""
            raise RuntimeError(f"Gemini API returned no candidates{detail}")
        candidate = candidates[0] if isinstance(candidates[0], dict) else {}
        parts = candidate.get("content", {}).get("parts", []) if isinstance(candidate.get("content"), dict) else []
        text = "".join(
            str(part.get("text", ""))
            for part in parts
            if isinstance(part, Mapping)
            and not _optimizer_part_is_thought(part)
            and part.get("text") is not None
        )
        if not text.strip():
            finish_reason = candidate.get("finishReason") or candidate.get("finish_reason") or "unknown"
            raise RuntimeError(f"Gemini API returned no text (finish reason: {finish_reason})")
    elif api_format == "responses":
        text = _optimizer_responses_text(data)
    else:
        message = ((data.get("choices") or [{}])[0].get("message", {}) or {})
        if not isinstance(message, Mapping):
            message = {}
        # reasoning_content / thinking are separate fields on some
        # reasoning-capable OpenAI-compatible responses. Only use visible content.
        text = _optimizer_chat_content_text(message.get("content", ""))
    text = _strip_optimizer_thoughts(text)
    if not text:
        raise RuntimeError("Prompt optimization API returned an empty response")
    return text


def _optimizer_asset_path(asset: Mapping[str, Any]) -> str | None:
    filename = str(asset.get("filename") or "").strip()
    if not filename or os.path.isabs(filename):
        return None
    storage = str(asset.get("storage") or "input").lower()
    roots = {
        "input": folder_paths.get_input_directory(),
        "output": folder_paths.get_output_directory(),
        "temp": folder_paths.get_temp_directory(),
    }
    root = os.path.realpath(roots.get(storage, roots["input"]))
    subfolder = str(asset.get("subfolder") or "").replace("\\", "/").strip("/")
    candidate = os.path.realpath(os.path.join(root, subfolder, filename))
    if candidate != root and not candidate.startswith(root + os.sep):
        return None
    return candidate if os.path.isfile(candidate) else None


def _optimizer_media_parts(
    resources: list[Mapping[str, Any]],
    api_format: str,
    maximum: int = MAX_MEDIA,
) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for resource in resources[:max(0, int(maximum))]:
        asset = resource.get("asset") if isinstance(resource.get("asset"), Mapping) else {}
        path = _optimizer_asset_path(asset)
        media_type = str(resource.get("type") or "").lower()
        if not path or media_type not in {"image", "video", "audio"}:
            continue
        try:
            if os.path.getsize(path) > 32 * 1024 * 1024:
                continue
            with open(path, "rb") as handle:
                encoded = base64.b64encode(handle.read()).decode("ascii")
            mime = mimetypes.guess_type(path)[0] or {"image": "image/jpeg", "video": "video/mp4", "audio": "audio/wav"}[media_type]
            if api_format == "gemini":
                parts.append({"inlineData": {"mimeType": mime, "data": encoded}})
            elif media_type == "image":
                data_url = f"data:{mime};base64,{encoded}"
                if api_format == "responses":
                    parts.append({"type": "input_image", "image_url": data_url})
                else:
                    parts.append({"type": "image_url", "image_url": {"url": data_url}})
        except (OSError, ValueError):
            continue
    return parts


def _optimizer_resource_tag(resource: Mapping[str, Any]) -> str:
    """Normalize a resource tag so per-segment media selection is type-aware."""
    raw = str(resource.get("tag") or "").strip()
    match = REFERENCE_TAG_PATTERN.fullmatch(raw)
    if not match:
        return raw
    kind = match.group(1).capitalize()
    return f"<{kind} {int(match.group(2))}>"


def _optimizer_media_read_allowed(resources: list[Mapping[str, Any]]) -> bool:
    """Keep multimodal optimizer requests bounded before encoding any files."""
    if len(resources) > CONTEXT_PROMPT_OPTIMIZER_MEDIA_MAX_RESOURCES:
        return False
    total_bytes = 0
    for resource in resources:
        asset = resource.get("asset") if isinstance(resource.get("asset"), Mapping) else {}
        path = _optimizer_asset_path(asset)
        if not path:
            continue
        try:
            size = int(os.path.getsize(path))
        except OSError:
            continue
        if size > 32 * 1024 * 1024:
            return False
        total_bytes += size
        if total_bytes > CONTEXT_PROMPT_OPTIMIZER_MEDIA_MAX_BYTES:
            return False
    return True


def _optimizer_segment_resources(
    segment_prompt: str,
    resources: list[Mapping[str, Any]],
    items: list[_MediaInput] | None = None,
) -> tuple[str, list[Mapping[str, Any]]]:
    """Resolve a segment's placeholders, then select only its referenced media."""
    resolved = _runtime_optimizer_prompt(segment_prompt, resources, items or [])
    wanted = {
        f"<{kind.capitalize()} {int(ordinal)}>"
        for kind, ordinal in REFERENCE_TAG_PATTERN.findall(resolved)
    }
    if wanted:
        selected = [resource for resource in resources if _optimizer_resource_tag(resource) in wanted]
        return resolved, selected
    return resolved, list(resources) if _optimizer_media_read_allowed(resources) else []


def _optimizer_single_segment_rules(segment_index: int, segment_count: int, seconds: float) -> str:
    return (
        "\n\n=== CONTEXT SINGLE-BLOCK OPTIMIZATION RULES (CONTEXT NODE ONLY) ===\n"
        "Optimize only the current block supplied in the user message. Earlier original blocks are "
        "context for continuity and are read-only; never rewrite, summarize, or output them. Return "
        "only one natural standalone MiniMax H3 prompt for the current block, with no numbering, title, "
        "commentary, markdown fence, or segment label. Do not mention previous/next clips, continuation, "
        "stitching, or prompt planning in the returned prompt. Preserve the user's media tags and add a "
        "tag only when the current block genuinely relies on that connected resource.\n"
        f"This is block {int(segment_index) + 1} of {int(segment_count)}, paced for {float(seconds):g} seconds."
    )


def _optimizer_single_segment_user_prompt(
    current_prompt: str,
    previous_prompts: list[str],
) -> str:
    parts = []
    if previous_prompts:
        parts.append("=== PREVIOUS ORIGINAL BLOCKS (READ-ONLY CONTEXT) ===")
        parts.extend(f"[Original block {index}]\n{text}" for index, text in enumerate(previous_prompts, start=1))
    parts.append("=== CURRENT ORIGINAL BLOCK TO OPTIMIZE ===")
    parts.append(str(current_prompt or ""))
    parts.append("Return only the optimized current block.")
    return "\n\n".join(parts)


def _normalize_optimized_single_segment(text: str) -> str:
    cleaned = re.sub(r"^```(?:text)?\s*", "", str(text or ""), flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    parts = split_prompt_segments(cleaned)
    if len(parts) != 1 or not parts[0].strip():
        raise ValueError("Optimized single-segment response must contain exactly one block")
    return parts[0].strip()


def _media_counts_from_kwargs(kwargs: Mapping[str, Any]) -> dict[str, int]:
    counts = {"image": 0, "video": 0, "audio": 0}
    for index in range(1, MAX_MEDIA + 1):
        kind = str(kwargs.get(f"media_type_{index}") or "").lower()
        if kind in counts and kwargs.get(f"media_{index}") is not None:
            counts[kind] += 1
    direct = kwargs.get("media")
    if direct is not None:
        counts[_infer_media_type(direct)] += 1
    return counts


def _optimizer_system_prompt(
    scene_guide: str,
    mode: str,
    seconds: float,
    media_counts: Mapping[str, int],
    attached_media_count: int = 0,
) -> str:
    prompt = _prompt_guide_bundle(scene_guide, mode, seconds, media_counts)
    actual_count = max(0, int(attached_media_count or 0))
    if actual_count:
        prompt += (
            "\n\n=== MEDIA EVIDENCE RULE ===\n"
            f"Actual media parts attached to this request: {actual_count}.\n"
            "The presence of a media part in the request does not prove that you can perceive it. "
            "Use visual, video, or audio details only when they are directly observable to your model in the attached media parts. "
            "If your model or API does not support the media modality, treat that media as unavailable. "
            "Do not invent or confidently describe details for any referenced media that is not actually attached. "
            "For a media tag without corresponding attached evidence, preserve the tag and infer only from the original user prompt and explicit instructions, never from an imagined asset."
        )
    else:
        prompt += (
            "\n\n=== MEDIA EVIDENCE RULE ===\n"
            "No actual media file was attached to this request. Do not invent, hallucinate, or confidently describe the content of any image, video, or audio reference. "
            "Preserve media reference tags when needed, but infer only from the original user prompt and explicit instructions. Never fabricate a subject, appearance, action, setting, sound, or other media detail."
        )
    return prompt


def _runtime_optimizer_resources(value: Any, maximum: int = MAX_MEDIA) -> list[Mapping[str, Any]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError):
            return []
    if not isinstance(value, list):
        return []
    return [item for item in value[:max(0, int(maximum))] if isinstance(item, Mapping)]


def _runtime_optimizer_marker(value: Any) -> Mapping[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}
    return value if isinstance(value, Mapping) else {}


def _optimizer_sha256(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _runtime_optimizer_resource_signature(
    resources: list[Mapping[str, Any]],
    items: list[_MediaInput],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    count = max(len(resources), len(items))
    for index in range(count):
        resource = resources[index] if index < len(resources) else {}
        item = items[index] if index < len(items) else None
        asset = resource.get("asset") if isinstance(resource.get("asset"), Mapping) else {}
        entry: dict[str, Any] = {
            "type": str(resource.get("type") or getattr(item, "media_type", "") or ""),
            "tag": str(resource.get("tag") or ""),
            "name": str(resource.get("name") or ""),
            "asset": {
                "filename": str(asset.get("filename") or ""),
                "subfolder": str(asset.get("subfolder") or ""),
                "storage": str(asset.get("storage") or ""),
            },
        }
        path = _optimizer_asset_path(asset) if asset else None
        if path:
            try:
                stat = os.stat(path)
                entry["file"] = {"size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)}
            except OSError:
                pass
        result.append(entry)
    return result


def _runtime_optimizer_context_hash(
    settings: Mapping[str, Any],
    mode: str,
    seconds: float,
    scene_guide: str,
    counts: Mapping[str, int],
    resources: list[Mapping[str, Any]],
    items: list[_MediaInput],
    extra: str = "",
) -> str:
    guide_fingerprint = _optimizer_sha256(
        _optimizer_system_prompt(scene_guide, mode, seconds, counts, 0)
    )
    payload = {
        "version": PROMPT_OPTIMIZER_MARKER_VERSION,
        "guide": guide_fingerprint,
        "api_format": str(settings.get("api_format") or "openai").lower(),
        "api_url": str(settings.get("api_url") or "").strip(),
        "model": str(settings.get("model") or "").strip(),
        "read_media": bool(settings.get("read_media")),
        "resources": _runtime_optimizer_resource_signature(resources, items),
    }
    if extra:
        payload["extra"] = str(extra)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _optimizer_sha256(canonical)


def _runtime_optimizer_prompt(
    prompt: str,
    resources: list[Mapping[str, Any]],
    items: list[_MediaInput],
) -> str:
    fallback_counts = {"image": 0, "video": 0, "audio": 0}
    fallback_tags: list[str] = []
    tag_prefixes = {"image": "Picture", "video": "Video", "audio": "Audio"}
    for item in items:
        media_type = item.media_type if item.media_type in fallback_counts else "video"
        fallback_counts[media_type] += 1
        fallback_tags.append(f"<{tag_prefixes[media_type]} {fallback_counts[media_type]}>")

    def replace(match: re.Match) -> str:
        index = int(match.group(1)) - 1
        if 0 <= index < len(resources):
            tag = str(resources[index].get("tag") or "").strip()
            if tag:
                return tag
        if 0 <= index < len(fallback_tags):
            return fallback_tags[index]
        return match.group(0)

    return REFERENCE_PLACEHOLDER_RE.sub(replace, str(prompt or ""))


def _segment_expected_count(seconds_spec: Any) -> int:
    raw = str(seconds_spec or "").replace("\uff0c", ",")
    return len([item for item in raw.split(",") if item.strip()])


def _optimizer_segment_rules(segment_count: int, seconds_spec: str, source_prompt: str = "") -> str:
    """Return adaptive rules for the context-segment optimizer only."""
    source_parts = split_prompt_segments(source_prompt)
    has_storyboard = len(source_parts) >= 2
    requested = max(2, int(segment_count))
    if has_storyboard:
        mode_rules = (
            "The user already supplied a multi-segment draft. Treat each divider-delimited part "
            "as an intentional clip description, preserve its order, clip-specific action, camera idea, text, "
            "and local sound, and improve those parts in place. Do not collapse the draft into a "
            "generic repeated template and do not invent extra story beats merely to fill space. "
            "Build a compact continuity map first, then repeat only the immutable facts or carried "
            "states that a standalone shot needs. If a detail is unique to one shot, keep it unique.\n"
            "When a later shot depends on an earlier event, state the resulting physical condition "
            "directly in that later shot (for example, say that a glowing star is already held in "
            "the raised right hand). Natural continuity language is allowed when the current shot "
            "also names the referent; continuity should be clear without forcing identical wording "
            "or repeating every global detail verbatim."
        )
    else:
        mode_rules = (
            "The user supplied one idea or one undivided prompt. First derive a compact global "
            "continuity map, then design a clear beginning, development, and ending across the "
            f"requested {requested} shots. Each generated shot must carry enough of that map to "
            "work when copied alone, but do not pad every shot with irrelevant boilerplate. Make "
            "the action and state transition evolve rather than repeating one static description.\n"
            "When connected Media resources exist but the user's undivided idea contains no per-shot "
            "references, make a relevance pass while designing the shots. This is mandatory output behavior: "
            "in every block, explicitly write the applicable @ media reference for every connected image, "
            "video, or audio resource that the block uses for identity, appearance, wardrobe, setting, style, "
            "action, camera, sound, or continuity. Media references are local to a block: a later block must "
            "write its own @ reference whenever it uses that media and must never rely on an earlier block's "
            "reference being inherited. If a resource defines a persistent subject, scene, look, or soundtrack "
            "across the sequence, repeat its reference in every block that depends on it. Do not add a "
            "reference to a block where that resource is genuinely unused, and do not add references merely "
            "because media are connected."
        )
    return (
        "\n\n=== CONTEXT MULTI-CLIP OPTIMIZATION RULES (CONTEXT NODE ONLY) ===\n"
        "These rules apply only to the MiniMax H3 Easy Context Segments node. Do not alter the "
        "ordinary image/reference prompt optimization contract.\n"
        "The final output is a list of ordinary standalone video prompts. Internally you may plan "
        "a connected sequence, but the prompt text itself must not talk about segments, shots, "
        "previous or next clips, continuation, stitching, or prompt planning. Do not add labels such "
        "as \"Shot 1\", \"Segment 2\", or \"the next clip\". Each block should read naturally as "
        "a normal single-clip MiniMax H3 prompt.\n"
        f"{mode_rules}\n"
        f"Return exactly {requested} standalone prompt blocks, separated ONLY by a line containing "
        "three hyphens (---). No numbering, titles, commentary, or markdown fences.\n"
        "1. Before writing, identify the minimum continuity anchors: subject identity and appearance, "
        "wardrobe, visual style, location/geography, time and lighting, palette, persistent props, "
        "typography rules, audio bed, and emotional direction. Carry an anchor into a shot when it "
        "is needed to identify the scene or interpret the action; omit irrelevant repetition.\n"
        "2. Every block must contain enough visual and audible information to stand on its own. "
        "When a carried prop, pose, expression, text state, or spatial condition matters, describe "
        "that concrete state naturally in the current block. Do not assume the model can read the "
        "other blocks.\n"
        "3. Use natural language rather than mechanical continuity formulas. Avoid vague references "
        "such as \"same rooftop\", \"as before\", or \"the captured star\" when the referent is "
        "important, but do not ban ordinary pronouns or smooth cinematic phrasing when the current "
        "block already makes the referent clear.\n"
        f"4. Planned clip durations are: {str(seconds_spec or '').strip()} seconds at 24 fps. Pace "
        "each block to its duration and preserve meaningful differences in action density, camera, "
        "and sound between blocks.\n"
        "5. Keep audio continuity adaptive: preserve the global music/ambience identity where it is "
        "present, while allowing local sound changes, silence, accents, or transitions when the "
        "story calls for them. Do not mechanically repeat a full audio paragraph if it adds nothing.\n"
        "6. Media correspondence is determined by the user's original prompt and your understanding "
        "of the attached media, not by a separate hard-coded allocation algorithm. Preserve explicit "
        "@ references or <Picture N>/<Video N>/<Audio N> tags without renumbering or reordering them. "
        "For an undivided prompt, use the explicit per-block relevance rule above: every block must "
        "carry the references it relies on, while genuinely unused media remain omitted. Never invent a "
        "media tag that has no corresponding connected resource. If media content is unavailable, "
        "do not fabricate details.\n"
        "7. Keep dialogue inside <d>...</d> blocks and preserve its original language."
    )


def _optimizer_digital_human_rules() -> str:
    return (
        "\n\n=== DIGITAL HUMAN AUDIO RULES ===\n"
        "The connected Media audio is the single global driving track for lip-sync and performance. "
        "Do not treat it as a reference-audio asset and do not add <Audio N> tags solely to represent "
        "that driving track. Keep visual <Picture N> and <Video N> references wherever the current "
        "prompt relies on those assets; in a multi-clip output repeat a visual reference in each block "
        "that needs it. Describe dialogue, speaker turns, and mouth/body performance naturally from "
        "the user's instructions, without inventing a second soundtrack. This rule overrides any "
        "generic instruction to tag a globally connected audio resource in every block."
    )


def _normalize_optimized_segments(text: str, expected_count: int) -> str:
    cleaned = re.sub(r"^```(?:text)?\s*", "", str(text or ""), flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    parts = split_prompt_segments(cleaned)
    if len(parts) != max(2, int(expected_count)):
        raise ValueError(
            f"Optimized response has {len(parts)} segments; expected {expected_count}"
        )
    if any(not part for part in parts):
        raise ValueError("Optimized response contains an empty segment")
    return "\n\n---\n\n".join(parts)


def _optimizer_resource_counts(resources: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"image": 0, "video": 0, "audio": 0}
    for resource in resources:
        media_type = str(resource.get("type") or "").lower()
        if media_type in counts:
            counts[media_type] += 1
    return counts


def _optimizer_context_segment_call(
    *,
    api_url: str,
    api_key: str,
    model: str,
    api_format: str,
    scene_guide: str,
    mode: str,
    current_prompt: str,
    previous_prompts: list[str],
    segment_index: int,
    segment_count: int,
    seconds: float,
    resources: list[Mapping[str, Any]],
    items: list[_MediaInput] | None,
    read_media: bool,
) -> str:
    resolved_prompt, selected_resources = _optimizer_segment_resources(
        current_prompt, resources, items or []
    )
    if not read_media or not _optimizer_media_read_allowed(selected_resources):
        selected_resources = []
    media_parts = _optimizer_media_parts(
        selected_resources, api_format, CONTEXT_PROMPT_OPTIMIZER_MEDIA_MAX_RESOURCES
    )
    system = _optimizer_system_prompt(
        scene_guide,
        mode,
        float(seconds),
        _optimizer_resource_counts(selected_resources),
        len(media_parts),
    )
    system += _optimizer_single_segment_rules(segment_index, segment_count, seconds)
    if mode == MODE_DIGITAL_HUMAN:
        system += _optimizer_digital_human_rules()
    optimized = _optimizer_http_json(
        api_url,
        api_key,
        model,
        api_format,
        system,
        _optimizer_single_segment_user_prompt(resolved_prompt, previous_prompts),
        media_parts,
        timeout_seconds=PROMPT_OPTIMIZER_ON_RUN_TIMEOUT_SECONDS,
        max_output_tokens=CONTEXT_PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS,
    )
    return _normalize_optimized_single_segment(optimized)


def _optimize_context_segments_sync(
    *,
    source_prompt: str,
    scene_guide: str,
    mode: str,
    seconds: float,
    segment_seconds: str,
    resources: list[Mapping[str, Any]],
    items: list[_MediaInput],
    settings: Mapping[str, Any],
    concurrency: int,
) -> str:
    """Optimize existing context blocks in parallel while preserving source order."""
    source_parts = split_prompt_segments(source_prompt)
    if len(source_parts) < 2:
        return source_prompt
    try:
        durations = parse_segment_seconds(segment_seconds, len(source_parts))
    except ValueError:
        durations = [float(seconds)] * len(source_parts)
    worker_count = max(1, min(CONTEXT_PROMPT_OPTIMIZER_MAX_CONCURRENCY, int(concurrency or CONTEXT_PROMPT_OPTIMIZER_DEFAULT_CONCURRENCY)))
    api_url = str(settings.get("api_url") or "").strip()
    api_key = str(settings.get("api_key") or "").strip()
    model = str(settings.get("model") or "").strip()
    api_format = str(settings.get("api_format") or "openai").lower()
    read_media = bool(settings.get("read_media"))
    results = list(source_parts)

    def run(index: int) -> tuple[int, str]:
        return index, _optimizer_context_segment_call(
            api_url=api_url,
            api_key=api_key,
            model=model,
            api_format=api_format,
            scene_guide=scene_guide,
            mode=mode,
            current_prompt=source_parts[index],
            previous_prompts=source_parts[:index],
            segment_index=index,
            segment_count=len(source_parts),
            seconds=durations[index],
            resources=resources,
            items=items,
            read_media=read_media,
        )

    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="h3-prompt") as executor:
        futures = [executor.submit(run, index) for index in range(len(source_parts))]
        for future in as_completed(futures):
            try:
                index, value = future.result()
                results[index] = value
            except Exception as exc:
                print(f"[MiniMax H3 Easy] Context segment prompt optimization skipped: {exc}")
    return "\n\n---\n\n".join(results)


@dataclass(frozen=True)
class _RuntimePromptOptimization:
    prompt: str
    marker: Mapping[str, Any] | None = None


def _optimize_prompt_on_run(
    prompt: str,
    mode: str,
    seconds: float,
    items: list[_MediaInput],
    settings: Mapping[str, Any],
    resource_payload: Any,
    marker_payload: Any,
    prompt_connected: bool,
    segment_spec: tuple[int, str] | None = None,
    context_optimizer_mode: str = CONTEXT_PROMPT_OPTIMIZER_WHOLE,
    context_optimizer_concurrency: int = CONTEXT_PROMPT_OPTIMIZER_DEFAULT_CONCURRENCY,
) -> _RuntimePromptOptimization:
    source_prompt = str(prompt or "")
    if (
        not _prompt_optimizer_flag(settings.get("enabled"))
        or not _prompt_optimizer_flag(settings.get("optimize_on_run"))
        or not source_prompt.strip()
        or bool(prompt_connected)
    ):
        return _RuntimePromptOptimization(source_prompt)

    api_url = str(settings.get("api_url") or "").strip()
    api_key = str(settings.get("api_key") or "").strip()
    model = str(settings.get("model") or "").strip()
    api_format = str(settings.get("api_format") or "openai").lower()
    scene_guide = str(settings.get("scene_guide") or "none")
    if not _prompt_optimizer_settings_complete(api_url, api_key, model, api_format):
        return _RuntimePromptOptimization(source_prompt)

    counts = {"image": 0, "video": 0, "audio": 0}
    for item in items:
        if item.media_type in counts:
            counts[item.media_type] += 1

    try:
        resource_limit = SEGMENT_MAX_MEDIA if segment_spec is not None else MAX_MEDIA
        resources = _runtime_optimizer_resources(resource_payload, resource_limit)
        source_parts = split_prompt_segments(source_prompt) if segment_spec is not None else []
        requested_scope = str(context_optimizer_mode or CONTEXT_PROMPT_OPTIMIZER_WHOLE)
        effective_scope = (
            CONTEXT_PROMPT_OPTIMIZER_PER_SEGMENT
            if requested_scope == CONTEXT_PROMPT_OPTIMIZER_PER_SEGMENT and len(source_parts) >= 2
            else CONTEXT_PROMPT_OPTIMIZER_WHOLE
        )
        context_hash = _runtime_optimizer_context_hash(
            settings,
            str(mode or MODE_IMAGE),
            float(seconds),
            str(scene_guide or "none"),
            counts,
            resources,
            items,
            extra=(
                f"seg:{segment_spec[0]}:{segment_spec[1]}:{effective_scope}:"
                f"{max(1, min(CONTEXT_PROMPT_OPTIMIZER_MAX_CONCURRENCY, int(context_optimizer_concurrency or CONTEXT_PROMPT_OPTIMIZER_DEFAULT_CONCURRENCY)))}"
                if segment_spec is not None
                else "",
            ),
        )
        request_prompt = _runtime_optimizer_prompt(source_prompt, resources, items)
        marker = _runtime_optimizer_marker(marker_payload)
        if (
            int(marker.get("version") or 0) == PROMPT_OPTIMIZER_MARKER_VERSION
            and str(marker.get("prompt_sha256") or "") == _optimizer_sha256(request_prompt)
            and str(marker.get("context_sha256") or "") == context_hash
        ):
            return _RuntimePromptOptimization(source_prompt)

        if effective_scope == CONTEXT_PROMPT_OPTIMIZER_PER_SEGMENT:
            cleaned = _optimize_context_segments_sync(
                source_prompt=source_prompt,
                scene_guide=str(scene_guide or "none"),
                mode=str(mode or MODE_IMAGE),
                seconds=float(seconds),
                segment_seconds=segment_spec[1],
                resources=resources,
                items=items,
                settings=settings,
                concurrency=context_optimizer_concurrency,
            )
            return _RuntimePromptOptimization(
                cleaned,
                {
                    "version": PROMPT_OPTIMIZER_MARKER_VERSION,
                    "prompt_sha256": _optimizer_sha256(_runtime_optimizer_prompt(cleaned, resources, items)),
                    "context_sha256": context_hash,
                },
            )

        read_media = bool(settings.get("read_media"))
        if segment_spec is not None and not _optimizer_media_read_allowed(resources):
            read_media = False
        media_parts = _optimizer_media_parts(resources, api_format, resource_limit) if read_media else []
        system = _optimizer_system_prompt(
            str(scene_guide or "none"),
            str(mode or MODE_IMAGE),
            float(seconds),
            counts,
            len(media_parts),
        )
        if segment_spec is not None:
            system += _optimizer_segment_rules(segment_spec[0], segment_spec[1], request_prompt)
        if str(mode or "") == MODE_DIGITAL_HUMAN:
            system += _optimizer_digital_human_rules()
        optimized = _optimizer_http_json(
            api_url,
            api_key,
            model,
            api_format,
            system,
            request_prompt,
            media_parts,
            timeout_seconds=PROMPT_OPTIMIZER_ON_RUN_TIMEOUT_SECONDS,
            max_output_tokens=(
                CONTEXT_PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS
                if segment_spec is not None
                else PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS
            ),
        )
        cleaned = re.sub(r"^```(?:text)?\s*", "", str(optimized or ""), flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        if not cleaned:
            return _RuntimePromptOptimization(source_prompt)
        if segment_spec is not None:
            cleaned = _normalize_optimized_segments(cleaned, segment_spec[0])
        return _RuntimePromptOptimization(
            cleaned,
            {
                "version": PROMPT_OPTIMIZER_MARKER_VERSION,
                "prompt_sha256": _optimizer_sha256(_runtime_optimizer_prompt(cleaned, resources, items)),
                "context_sha256": context_hash,
            },
        )
    except Exception as exc:
        print(f"[MiniMax H3 Easy] Prompt optimization skipped; using the original prompt: {exc}")
        return _RuntimePromptOptimization(source_prompt)


class MiniMaxH3PromptOptimizer:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "optimize"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("optimized_prompt",)
    OUTPUT_NODE = True
    DESCRIPTION = "Optimize a MiniMax H3 prompt with the complete node-adapted Prompt Guide."

    @classmethod
    def INPUT_TYPES(cls):
        manifest = _prompt_guide_manifest()
        scene_items = manifest.get("scene_guides") if isinstance(manifest.get("scene_guides"), list) else []
        choices = [str(item.get("id")) for item in scene_items if isinstance(item, dict) and item.get("id")] or ["none"]
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "mode": ([MODE_IMAGE, MODE_REFERENCE, MODE_DIGITAL_HUMAN], {"default": MODE_IMAGE}),
                "seconds": ("FLOAT", {"default": 5.0, "min": MIN_SECONDS, "max": MAX_SECONDS, "step": 0.1}),
                "scene_guide": (choices, {"default": "none"}),
                "api_format": (["openai", "responses", "gemini"], {"default": "openai"}),
                "api_url": ("STRING", {"default": ""}),
                "api_key": ("STRING", {"default": "", "multiline": False, "password": True}),
                "model": ("STRING", {"default": ""}),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def optimize(self, prompt, mode, seconds, scene_guide, api_format, api_url, api_key, model):
        api_format = str(api_format or "openai").strip().lower()
        if _prompt_optimizer_api_key_required(api_format) and not str(api_key or "").strip():
            raise ValueError("Prompt optimization API key is required for Gemini Native")
        if not str(model or "").strip():
            raise ValueError("Prompt optimization model is required")
        counts = {"image": 0, "video": 0, "audio": 0}
        system = _optimizer_system_prompt(str(scene_guide or "none"), str(mode or MODE_IMAGE), float(seconds), counts)
        return (_optimizer_http_json(str(api_url), str(api_key), str(model), api_format, system, str(prompt or "")),)


def _register_prompt_optimizer_route() -> bool:
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return False
    routes = getattr(getattr(PromptServer, "instance", None), "routes", None)
    if routes is None or getattr(_register_prompt_optimizer_route, "_registered", False):
        return bool(getattr(_register_prompt_optimizer_route, "_registered", False))

    @routes.post("/minimax_h3_easy/prompt_optimize")
    async def _prompt_optimize(request):
        try:
            payload = await request.json()
            prompt = str(payload.get("prompt") or "")
            api_key = str(payload.get("api_key") or "")
            api_url = str(payload.get("api_url") or "")
            model = str(payload.get("model") or "")
            api_format = str(payload.get("api_format") or "openai").lower()
            mode = str(payload.get("mode") or MODE_IMAGE)
            audio_mode = str(payload.get("audio_mode") or CONTEXT_AUDIO_GENERATED)
            optimizer_mode = MODE_DIGITAL_HUMAN if mode == MODE_SEGMENTS and audio_mode == CONTEXT_AUDIO_DIGITAL_HUMAN else mode
            scene_guide = str(payload.get("scene_guide") or "none")
            seconds = min(MAX_SECONDS, max(MIN_SECONDS, float(payload.get("seconds") or 5.0)))
            if api_format not in {"openai", "responses", "gemini"}:
                return web.json_response({"ok": False, "error": "Unsupported API format"}, status=400)
            if not prompt.strip() or not _prompt_optimizer_settings_complete(api_url, api_key, model, api_format):
                return web.json_response({"ok": False, "error": "Prompt optimization settings are incomplete"}, status=400)
            raw_counts = payload.get("media_counts") if isinstance(payload.get("media_counts"), dict) else {}
            resource_limit = SEGMENT_MAX_MEDIA if mode == MODE_SEGMENTS else MAX_MEDIA
            counts = {kind: max(0, min(resource_limit, int(raw_counts.get(kind, 0) or 0))) for kind in ("image", "video", "audio")}
            resources = payload.get("resources") if isinstance(payload.get("resources"), list) else []
            resources = [item for item in resources[:resource_limit] if isinstance(item, Mapping)]
            optimizer_scope = str(payload.get("optimizer_mode") or CONTEXT_PROMPT_OPTIMIZER_WHOLE)
            segment_count = max(0, int(payload.get("segment_count") or 0))
            segment_index = max(0, int(payload.get("segment_index") or 0))
            previous_prompts = payload.get("previous_prompts") if isinstance(payload.get("previous_prompts"), list) else []
            previous_prompts = [str(item) for item in previous_prompts]
            segment_seconds_raw = str(payload.get("segment_seconds") or "")
            expected_segments = _segment_expected_count(segment_seconds_raw) if mode == MODE_SEGMENTS else 0
            if (
                mode == MODE_SEGMENTS
                and optimizer_scope == CONTEXT_PROMPT_OPTIMIZER_PER_SEGMENT
                and segment_count >= 2
                and segment_index < segment_count
            ):
                try:
                    durations = parse_segment_seconds(segment_seconds_raw, segment_count)
                except ValueError:
                    durations = [float(seconds)] * segment_count
                result = await asyncio.to_thread(
                    _optimizer_context_segment_call,
                    api_url=api_url,
                    api_key=api_key,
                    model=model,
                    api_format=api_format,
                    scene_guide=scene_guide,
                    mode=optimizer_mode,
                    current_prompt=prompt,
                    previous_prompts=previous_prompts[:segment_index],
                    segment_index=segment_index,
                    segment_count=segment_count,
                    seconds=durations[segment_index],
                    resources=resources,
                    items=None,
                    read_media=_prompt_optimizer_flag(payload.get("read_media")),
                )
                return web.json_response({"ok": True, "prompt": result, "segment_index": segment_index})

            read_media = _prompt_optimizer_flag(payload.get("read_media"))
            if mode == MODE_SEGMENTS and not _optimizer_media_read_allowed(resources):
                read_media = False
            media_parts = _optimizer_media_parts(resources, api_format, resource_limit) if read_media else []
            system = _optimizer_system_prompt(scene_guide, optimizer_mode, seconds, counts, len(media_parts))
            if expected_segments >= 2:
                system += _optimizer_segment_rules(expected_segments, segment_seconds_raw, prompt)
            if optimizer_mode == MODE_DIGITAL_HUMAN:
                system += _optimizer_digital_human_rules()
            result = await asyncio.to_thread(
                _optimizer_http_json,
                api_url,
                api_key,
                model,
                api_format,
                system,
                prompt,
                media_parts,
                max_output_tokens=(
                    CONTEXT_PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS
                    if mode == MODE_SEGMENTS
                    else PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS
                ),
            )
            if expected_segments >= 2:
                result = _normalize_optimized_segments(result, expected_segments)
            return web.json_response({"ok": True, "prompt": result})
        except Exception as exc:
            return web.json_response({"ok": False, "error": str(exc)}, status=500)

    _register_prompt_optimizer_route._registered = True
    return True


def _register_prompt_optimizer_route_when_ready() -> None:
    if _register_prompt_optimizer_route():
        return

    def wait_for_server() -> None:
        # ComfyUI creates PromptServer shortly after custom-node imports. Retry
        # for a bounded period without delaying node import.
        for _ in range(2400):
            if _register_prompt_optimizer_route():
                return
            threading.Event().wait(0.05)

    threading.Thread(target=wait_for_server, daemon=True, name="MiniMaxH3PromptOptimizerRoute").start()


def _role_choices(role: str, categories: tuple[str, ...], fallback: str) -> list[str]:
    names = _collect_weight_names(categories)
    selected = [name for name in names if _has_role(name, role)]
    return _sort_model_names(selected) or [fallback]


def _optional_role_choices(role: str, categories: tuple[str, ...]) -> list[str]:
    names = _collect_weight_names(categories)
    selected = _sort_model_names([name for name in names if _has_role(name, role)])
    # ComfyUI validates combo values before invoking the node. The frontend
    # localizes the sentinel to either "None" or "无", so all display values
    # must also be accepted by the server-side combo definition.
    return [*selected, *NONE_MODEL_DISPLAY_VALUES]


def _all_weight_choices(categories: tuple[str, ...], fallback: str, optional: bool = False) -> list[str]:
    """List all weights in the supplied ComfyUI folders without filename roles.

    Community and hosted ComfyUI environments often rename or relocate H3
    checkpoints.  Exposing the folder contents verbatim keeps this combo
    compatible with those model pickers; the selected file is still validated
    by the native ComfyUI loader when it is loaded.
    """
    selected = _sort_model_names(_collect_weight_names(categories))
    if optional:
        return [*selected, *NONE_MODEL_DISPLAY_VALUES]
    return selected or [fallback]


def _filtered_choices(category: str, needles: tuple[str, ...], fallback: str) -> list[str]:
    names = _collect_weight_names((category,))
    selected = [name for name in names if any(needle.lower() in _normalise_model_name(name).replace(" ", "") for needle in needles)]
    return _sort_model_names(selected) or [fallback]


def _model_choices() -> list[str]:
    return _all_weight_choices(("diffusion_models", "unet", "unet_gguf"), "", optional=True)


def _ref_model_choices() -> list[str]:
    return _all_weight_choices(("diffusion_models", "unet", "unet_gguf"), "", optional=True)


def _clip_choices() -> list[str]:
    return _all_weight_choices(
        ("text_encoders", "clip", "clip_gguf"),
        "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    )


def _vae_choices(needles: tuple[str, ...], fallback: str) -> list[str]:
    return _all_weight_choices(("vae",), fallback)


def _validate_h3_vae_roles(video_vae: Any, audio_vae: Any, video_name: str, audio_name: str) -> None:
    """Fail early when the two explicitly named VAE slots are swapped."""
    video_dim = getattr(video_vae, "latent_dim", None)
    audio_dim = getattr(audio_vae, "latent_dim", None)
    if video_dim != 3:
        raise ValueError(
            "MiniMax H3 Loader video VAE slot must contain a video VAE "
            f"(latent_dim=3), but {video_name!r} is not a video VAE."
        )
    if audio_dim != 2:
        raise ValueError(
            "MiniMax H3 Loader audio VAE slot must contain an audio VAE "
            f"(latent_dim=2), but {audio_name!r} is not an audio VAE."
        )


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
    fl2va_model_obj: Any = None
    ref2va_model_obj: Any = None

    def __post_init__(self) -> None:
        self._model = None
        self._model_kind = ""
        self._model_name = ""
        self._lock = threading.RLock()

    def _model_name_for(self, kind: str) -> str:
        """Return the preferred model, falling back to the other H3 model.

        FL2VA and REF2VA are exposed as separate choices when both are
        installed, but a user may intentionally install only one of them for
        testing. In that case, let the remaining transformer serve either
        generation path instead of rejecting the mode before execution.
        """
        requested_kind = "ref2va" if kind == "ref2va" else "fl2va"
        preferred = self.ref2va_model_name if requested_kind == "ref2va" else self.fl2va_model_name
        if not _is_none_model(preferred):
            return preferred

        fallback = self.fl2va_model_name if requested_kind == "ref2va" else self.ref2va_model_name
        if not _is_none_model(fallback):
            return fallback

        if requested_kind == "ref2va":
            raise ValueError("Reference Video mode requires at least one MiniMax H3 transformer model.")
        raise ValueError("Text-to-video and I2V or First/Last Frame mode require at least one MiniMax H3 transformer model.")

    def _model_object_for(self, kind: str):
        """Return an already-loaded transformer, falling back to the other role."""
        requested_kind = "ref2va" if kind == "ref2va" else "fl2va"
        preferred = self.ref2va_model_obj if requested_kind == "ref2va" else self.fl2va_model_obj
        if preferred is not None:
            return preferred
        fallback = self.fl2va_model_obj if requested_kind == "ref2va" else self.ref2va_model_obj
        return fallback

    def model_for(self, kind: str):
        kind = "ref2va" if kind == "ref2va" else "fl2va"
        with self._lock:
            supplied_model = self._model_object_for(kind)
            if supplied_model is not None:
                return supplied_model
            model_name = self._model_name_for(kind)
            if self._model is not None and self._model_name == model_name:
                return self._model

            if self._model is not None:
                self._model = None
                self._model_kind = ""
                self._model_name = ""
                comfy.model_management.soft_empty_cache()

            if _is_gguf_file(model_name):
                self._model = _load_gguf_unet(model_name)
            else:
                self._model, = nodes.UNETLoader().load_unet(model_name, "default")
            self._model_kind = kind
            self._model_name = model_name
            return self._model


@dataclass(frozen=True)
class _MiniMaxH3KeyframeSource:
    resolved_frame_index: int
    image: torch.Tensor


@dataclass(frozen=True)
class MiniMaxH3Context:
    conditioning: Any
    latent: Any
    video_vae: Any
    audio_vae: Any
    fps: float
    aspect_ratio: str
    keyframe_sources: tuple[_MiniMaxH3KeyframeSource, ...] = ()
    segment_plan: Any = None
    source_audio: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class MiniMaxH3SegmentSample:
    """One delivered segment kept on CPU between sampling and post-processing."""

    video_latent: torch.Tensor
    audio_latent: torch.Tensor
    head_frames: int
    delivery_frames: int


@dataclass(frozen=True)
class MiniMaxH3SegmentResult:
    """Demand-driven intermediate output of the context sampler."""

    plan: Mapping[str, Any]
    samples: tuple[MiniMaxH3SegmentSample, ...]


@dataclass(frozen=True)
class _MediaInput:
    input_index: int
    media_type: str
    value: Any


@dataclass(frozen=True)
class MiniMaxH3MediaBundle:
    """Native multi-input transport used by API-friendly workflows."""

    items: tuple[_MediaInput, ...]


MEDIA_LOADER_GROUPS = (
    # The loader is an unrestricted media library. Downstream nodes apply the
    # relevant single-shot or context-sequence budget when they consume it.
    ("image", None),
    ("audio", None),
    ("video", None),
)
def _media_loader_normalize_state(value: Any) -> dict[str, list[dict[str, str]]]:
    """Parse the canvas-managed media list without accepting arbitrary paths."""
    result = {kind: [] for kind, _maximum in MEDIA_LOADER_GROUPS}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            value = {}
    if not isinstance(value, Mapping):
        return result
    for kind, maximum in MEDIA_LOADER_GROUPS:
        entries = value.get(f"{kind}s")
        if not isinstance(entries, list):
            continue
        seen = set()
        for raw in entries:
            filename = str(raw.get("filename") if isinstance(raw, Mapping) else raw or "").strip()
            # Input-relative POSIX paths keep workflow JSON portable and make
            # ComfyUI's normal input-directory safeguards applicable here too.
            filename = filename.replace("\\", "/").lstrip("/")
            if not filename or "\x00" in filename or os.path.isabs(filename):
                continue
            parts = [part for part in filename.split("/") if part and part != "."]
            if not parts or any(part == ".." for part in parts):
                continue
            normalized = "/".join(parts)
            if normalized in seen:
                continue
            seen.add(normalized)
            result[kind].append({"filename": normalized})
            if maximum is not None and len(result[kind]) >= maximum:
                break
    return result


def _media_loader_state_json(value: Any) -> str:
    return json.dumps(_media_loader_normalize_state(value), ensure_ascii=True, separators=(",", ":"))


def _media_loader_input_path(filename: str) -> str:
    # folder_paths performs the final containment check against ComfyUI/input.
    path = folder_paths.get_annotated_filepath(filename, folder_paths.get_input_directory())
    if not os.path.isfile(path):
        raise ValueError(f"Media Loader cannot find input file: {filename}")
    return path


def _media_loader_load_audio(path: str) -> dict[str, Any]:
    try:
        # Match ComfyUI's native LoadAudio node. Its PyAV decoder supports the
        # same files without requiring the optional TorchCodec package that
        # newer torchaudio releases use for torchaudio.load().
        waveform, sample_rate = nodes_audio.load(path)
    except Exception as exc:
        raise ValueError(f"Media Loader could not read audio file {os.path.basename(path)!r}: {exc}") from exc
    if not isinstance(waveform, torch.Tensor) or waveform.ndim != 2 or waveform.shape[-1] < 1:
        raise ValueError(f"Media Loader found no usable audio samples in {os.path.basename(path)!r}")
    return {
        "waveform": waveform.unsqueeze(0).to(device="cpu", dtype=torch.float32).contiguous(),
        "sample_rate": int(sample_rate),
    }


def _media_loader_load_video(path: str) -> dict[str, Any]:
    """Decode a selected video into a Comfy-cacheable media payload."""
    try:
        components = InputImpl.VideoFromFile(path).get_components()
    except Exception as exc:
        raise ValueError(
            f"Media Loader could not read video file {os.path.basename(path)!r}: {exc}"
        ) from exc

    frames = components.images
    if not isinstance(frames, torch.Tensor) or frames.ndim != 4 or frames.shape[0] < 1:
        raise ValueError(
            f"Media Loader found no usable video frames in {os.path.basename(path)!r}"
        )
    frames = frames.detach().to(device="cpu").contiguous()

    audio = components.audio
    cached_audio = None
    waveform = audio.get("waveform") if isinstance(audio, Mapping) else None
    if isinstance(waveform, torch.Tensor):
        cached_audio = {
            "waveform": waveform.detach().to(device="cpu").contiguous(),
            "sample_rate": _audio_sample_rate(audio),
        }

    return {
        "images": frames,
        "audio": cached_audio,
        "fps": float(components.frame_rate or 24.0),
    }


class MiniMaxH3EasyMediaLoader:
    """Canvas-first ordered media manager for MiniMax H3 reference inputs."""

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "load"
    RETURN_TYPES = (MEDIA_BUNDLE_TYPE,)
    RETURN_NAMES = ("media_bundle",)
    DESCRIPTION = "Load ordered image, audio, and video references from ComfyUI input. Video components are decoded once and reused through ComfyUI's node cache."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "media_state": ("STRING", {"default": "", "multiline": False}),
            },
        }

    @classmethod
    def IS_CHANGED(cls, media_state="", **_kwargs):
        state = _media_loader_normalize_state(media_state)
        signature = []
        for kind, _maximum in MEDIA_LOADER_GROUPS:
            for entry in state[kind]:
                filename = entry["filename"]
                try:
                    stat = os.stat(_media_loader_input_path(filename))
                    signature.append((kind, filename, stat.st_mtime_ns, stat.st_size))
                except (OSError, ValueError):
                    signature.append((kind, filename, None, None))
        return repr(signature)

    @classmethod
    def VALIDATE_INPUTS(cls, media_state="", **_kwargs):
        state = _media_loader_normalize_state(media_state)
        for kind, _maximum in MEDIA_LOADER_GROUPS:
            for entry in state[kind]:
                try:
                    _media_loader_input_path(entry["filename"])
                except ValueError as exc:
                    return str(exc)
        return True

    def load(self, media_state=""):
        state = _media_loader_normalize_state(media_state)
        items: list[_MediaInput] = []
        input_index = 0
        for media_type, _maximum in MEDIA_LOADER_GROUPS:
            for entry in state[media_type]:
                filename = entry["filename"]
                path = _media_loader_input_path(filename)
                if media_type == "image":
                    value = nodes.LoadImage().load_image(filename)[0]
                elif media_type == "audio":
                    value = _media_loader_load_audio(path)
                else:
                    value = _media_loader_load_video(path)
                input_index += 1
                items.append(_MediaInput(input_index, media_type, value))
        return (MiniMaxH3MediaBundle(tuple(items)),)


class MiniMaxH3EasyMediaBridge:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "pack"
    RETURN_TYPES = (MEDIA_BUNDLE_TYPE,)
    RETURN_NAMES = ("media_bundle",)
    DESCRIPTION = "Collect explicit image, video and audio inputs for API-friendly MiniMax H3 workflows."

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for index in range(1, MAX_IMAGES + 1):
            optional[f"image_{index}"] = ("*",)
        for index in range(1, MAX_VIDEOS + 1):
            optional[f"video_{index}"] = ("*",)
        for index in range(1, MAX_AUDIOS + 1):
            optional[f"audio_{index}"] = ("*",)
        return {
            "required": {
                "image_count": ("INT", {"default": 1, "min": 0, "max": MAX_IMAGES, "step": 1}),
                "video_count": ("INT", {"default": 0, "min": 0, "max": MAX_VIDEOS, "step": 1}),
                "audio_count": ("INT", {"default": 0, "min": 0, "max": MAX_AUDIOS, "step": 1}),
            },
            "optional": optional,
        }

    def pack(self, image_count: int, video_count: int, audio_count: int, **kwargs):
        items: list[_MediaInput] = []
        input_index = 0
        groups = (
            ("image", image_count, MAX_IMAGES),
            ("video", video_count, MAX_VIDEOS),
            ("audio", audio_count, MAX_AUDIOS),
        )
        for media_type, raw_count, maximum in groups:
            try:
                count = max(0, min(maximum, int(raw_count)))
            except (TypeError, ValueError):
                count = 0
            for index in range(1, count + 1):
                value = kwargs.get(f"{media_type}_{index}")
                if value is None:
                    continue
                input_index += 1
                items.append(_MediaInput(input_index, media_type, value))
        return (MiniMaxH3MediaBundle(tuple(items)),)


class MiniMaxH3EasyLoader:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "load"
    RETURN_TYPES = ("MINIMAX_H3_BUNDLE",)
    RETURN_NAMES = ("h3_bundle",)
    DESCRIPTION = "Load either or both MiniMax H3 transformers, plus the text encoder and both AV VAEs."

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
        if _is_none_model(fl2va_model) and _is_none_model(ref2va_model):
            raise ValueError("Select at least one MiniMax H3 transformer: FL2VA or REF2VA.")
        clip = _load_text_encoder(text_encoder)
        video_vae_obj, = nodes.VAELoader().load_vae(video_vae)
        audio_vae_obj, = nodes.VAELoader().load_vae(audio_vae)
        _validate_h3_vae_roles(video_vae_obj, audio_vae_obj, video_vae, audio_vae)
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


class MiniMaxH3EasyModelAdapter:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "assemble"
    RETURN_TYPES = ("MINIMAX_H3_BUNDLE",)
    RETURN_NAMES = ("h3_bundle",)
    DESCRIPTION = "Assemble standard ComfyUI MODEL, CLIP and VAE outputs into a MiniMax H3 bundle."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_encoder": ("CLIP",),
                "video_vae": ("VAE",),
                "audio_vae": ("VAE",),
            },
            "optional": {
                "fl2va_model": ("MODEL",),
                "ref2va_model": ("MODEL",),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @staticmethod
    def assemble(text_encoder, video_vae, audio_vae, fl2va_model=None, ref2va_model=None):
        if fl2va_model is None and ref2va_model is None:
            raise ValueError("Connect at least one transformer MODEL: FL2VA or REF2VA.")
        _validate_h3_vae_roles(video_vae, audio_vae, "connected video VAE", "connected audio VAE")
        return (MiniMaxH3Bundle(
            fl2va_model_name=NONE_MODEL,
            ref2va_model_name=NONE_MODEL,
            clip_name="connected",
            video_vae_name="connected",
            audio_vae_name="connected",
            clip=text_encoder,
            video_vae=video_vae,
            audio_vae=audio_vae,
            fl2va_model_obj=fl2va_model,
            ref2va_model_obj=ref2va_model,
        ),)


def _infer_media_type(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, torch.Tensor):
        return "image"
    if isinstance(value, Mapping) and "waveform" in value:
        return "audio"
    if hasattr(value, "get_components"):
        return "video"
    return "video"


def _audio_sample_rate(audio: Mapping) -> int:
    return int(audio.get("sample_rate") or audio.get("samplerate") or audio.get("sampler_rate") or 32000)


@dataclass(frozen=True)
class _ReferenceVideoCacheEntry:
    """One file-backed VIDEO decoded into reusable CPU components."""

    frames: torch.Tensor
    audio: Mapping | None
    fps: float
    byte_size: int


_REFERENCE_VIDEO_CACHE_LOCK = threading.RLock()
_REFERENCE_VIDEO_CACHE: OrderedDict[tuple[str, int, int, float, float], _ReferenceVideoCacheEntry] = OrderedDict()
_REFERENCE_VIDEO_CACHE_BYTES = 0
_REFERENCE_VIDEO_CACHE_SCOPE: tuple[tuple[str, int, int, float, float], ...] | None = None


def _tensor_bytes(value: Any) -> int:
    if not isinstance(value, torch.Tensor):
        return 0
    return int(value.numel()) * int(value.element_size())


def _reference_video_cache_bytes(frames: torch.Tensor, audio: Mapping | None) -> int:
    waveform = audio.get("waveform") if isinstance(audio, Mapping) else None
    return _tensor_bytes(frames) + _tensor_bytes(waveform)


def _reference_video_cache_budget_bytes() -> int:
    """Reserve most free RAM for ComfyUI and keep this cache deliberately small."""
    try:
        # Include retained entries when calculating the cap so a cache insert
        # is not evicted immediately merely because it consumed RAM.
        available = int(psutil.virtual_memory().available) + _REFERENCE_VIDEO_CACHE_BYTES
    except Exception:
        return 0
    if available <= REFERENCE_VIDEO_CACHE_RESERVE_BYTES:
        return 0
    return min(
        REFERENCE_VIDEO_CACHE_HARD_LIMIT_BYTES,
        int((available - REFERENCE_VIDEO_CACHE_RESERVE_BYTES) * REFERENCE_VIDEO_CACHE_AVAILABLE_FRACTION),
    )


def _reference_video_cache_key(value: Any) -> tuple[str, int, int, float, float] | None:
    """Identify stable local-file video inputs without hashing media bytes."""
    if not hasattr(value, "get_stream_source"):
        return None
    try:
        source = value.get_stream_source()
        if not isinstance(source, (str, os.PathLike)):
            return None
        path = os.path.normcase(os.path.realpath(os.fspath(source)))
        stat = os.stat(path)
        start_time, duration = (0.0, 0.0)
        if hasattr(value, "get_active_trim_window"):
            start_time, duration = value.get_active_trim_window()
        return (
            path,
            int(stat.st_mtime_ns),
            int(stat.st_size),
            round(float(start_time), 6),
            round(float(duration), 6),
        )
    except (OSError, TypeError, ValueError):
        return None


def _cache_entry_on_cpu(frames: torch.Tensor, audio: Mapping | None, fps: float) -> _ReferenceVideoCacheEntry:
    cached_frames = frames.detach().to(device="cpu").contiguous() if frames.device.type != "cpu" else frames
    cached_audio: Mapping | None = audio
    waveform = audio.get("waveform") if isinstance(audio, Mapping) else None
    if isinstance(waveform, torch.Tensor) and waveform.device.type != "cpu":
        cached_audio = dict(audio)
        cached_audio["waveform"] = waveform.detach().to(device="cpu").contiguous()
    return _ReferenceVideoCacheEntry(
        frames=cached_frames,
        audio=cached_audio,
        fps=fps,
        byte_size=_reference_video_cache_bytes(cached_frames, cached_audio),
    )


def _remove_reference_video_cache_entry(key: tuple[str, int, int, float, float]) -> None:
    global _REFERENCE_VIDEO_CACHE_BYTES
    entry = _REFERENCE_VIDEO_CACHE.pop(key, None)
    if entry is not None:
        _REFERENCE_VIDEO_CACHE_BYTES = max(0, _REFERENCE_VIDEO_CACHE_BYTES - entry.byte_size)


def _prune_reference_video_cache(budget: int) -> None:
    while _REFERENCE_VIDEO_CACHE and (
        len(_REFERENCE_VIDEO_CACHE) > REFERENCE_VIDEO_CACHE_MAX_ENTRIES
        or _REFERENCE_VIDEO_CACHE_BYTES > budget
    ):
        _remove_reference_video_cache_entry(next(iter(_REFERENCE_VIDEO_CACHE)))


def _get_reference_video_cache_entry(
    key: tuple[str, int, int, float, float],
) -> tuple[_ReferenceVideoCacheEntry | None, int, bool]:
    """Return a cache hit plus its current budget and file invalidation state."""
    with _REFERENCE_VIDEO_CACHE_LOCK:
        budget = _reference_video_cache_budget_bytes()
        _prune_reference_video_cache(budget)
        invalidated = False
        for cached_key in tuple(_REFERENCE_VIDEO_CACHE):
            if cached_key[0] == key[0] and cached_key[1:3] != key[1:3]:
                _remove_reference_video_cache_entry(cached_key)
                invalidated = True
        entry = _REFERENCE_VIDEO_CACHE.pop(key, None)
        if entry is not None:
            _REFERENCE_VIDEO_CACHE[key] = entry
        return entry, budget, invalidated


def _store_reference_video_cache_entry(
    key: tuple[str, int, int, float, float], entry: _ReferenceVideoCacheEntry
) -> bool:
    global _REFERENCE_VIDEO_CACHE_BYTES
    with _REFERENCE_VIDEO_CACHE_LOCK:
        budget = _reference_video_cache_budget_bytes()
        _prune_reference_video_cache(budget)
        if not entry.byte_size or entry.byte_size > budget:
            return False
        _remove_reference_video_cache_entry(key)
        while _REFERENCE_VIDEO_CACHE and (
            len(_REFERENCE_VIDEO_CACHE) >= REFERENCE_VIDEO_CACHE_MAX_ENTRIES
            or _REFERENCE_VIDEO_CACHE_BYTES + entry.byte_size > budget
        ):
            _remove_reference_video_cache_entry(next(iter(_REFERENCE_VIDEO_CACHE)))
        _REFERENCE_VIDEO_CACHE[key] = entry
        _REFERENCE_VIDEO_CACHE_BYTES += entry.byte_size
        return True


def _reference_video_cache_label(key: tuple[str, int, int, float, float]) -> str:
    return os.path.basename(key[0]) or key[0]


def _sync_reference_video_cache_scope(items: list[_MediaInput]) -> None:
    """Keep only videos used by the current Easy run."""
    global _REFERENCE_VIDEO_CACHE_SCOPE
    if not REFERENCE_VIDEO_CACHE_ENABLED:
        with _REFERENCE_VIDEO_CACHE_LOCK:
            for key in tuple(_REFERENCE_VIDEO_CACHE):
                _remove_reference_video_cache_entry(key)
            _REFERENCE_VIDEO_CACHE_SCOPE = None
        return
    current = tuple(sorted(
        key
        for item in items
        if item.media_type == "video"
        for key in (_reference_video_cache_key(item.value),)
        if key is not None
    ))
    with _REFERENCE_VIDEO_CACHE_LOCK:
        if current == _REFERENCE_VIDEO_CACHE_SCOPE:
            return
        removed = 0
        for key in tuple(_REFERENCE_VIDEO_CACHE):
            if key not in current:
                _remove_reference_video_cache_entry(key)
                removed += 1
        previous = _REFERENCE_VIDEO_CACHE_SCOPE
        _REFERENCE_VIDEO_CACHE_SCOPE = current
    if removed:
        if not current:
            print(f"[MiniMax H3 Easy] Reference video decode cache cleared: {removed} old video(s)")
        else:
            print(f"[MiniMax H3 Easy] Reference video decode cache switched: cleared {removed} old video(s)")
    elif previous is not None and previous != current:
        print("[MiniMax H3 Easy] Reference video decode cache scope changed")


def _video_parts(value: Any) -> tuple[torch.Tensor, dict | None, float]:
    if hasattr(value, "get_components"):
        key = _reference_video_cache_key(value) if REFERENCE_VIDEO_CACHE_ENABLED else None
        if key is not None:
            cached, budget, invalidated = _get_reference_video_cache_entry(key)
            label = _reference_video_cache_label(key)
            if cached is not None:
                print(f"[MiniMax H3 Easy] Reference video decode cache hit: {label}")
                return cached.frames, cached.audio, cached.fps
            if invalidated:
                print(f"[MiniMax H3 Easy] Reference video decode cache invalidated: {label}")
            print(f"[MiniMax H3 Easy] Reference video decode cache miss: {label}")
        components = value.get_components()
        frames = components.images
        audio = components.audio
        fps = float(components.frame_rate or 24.0)
        if key is not None and isinstance(frames, torch.Tensor):
            entry = _cache_entry_on_cpu(frames, audio, fps)
            if _store_reference_video_cache_entry(key, entry):
                print(f"[MiniMax H3 Easy] Reference video decode cache stored: {label}")
            else:
                print(
                    "[MiniMax H3 Easy] Reference video decode cache skipped-too-large: "
                    f"{label} ({entry.byte_size / (1024 ** 2):.0f} MiB; budget {budget / (1024 ** 2):.0f} MiB)"
                )
        return frames, audio, fps
    if isinstance(value, Mapping):
        frames = value.get("images")
        if frames is None:
            frames = value.get("frames")
        if isinstance(frames, torch.Tensor):
            return frames, value.get("audio"), float(value.get("fps") or value.get("frame_rate") or 24.0)
    if isinstance(value, torch.Tensor) and value.ndim == 4:
        return value, None, 24.0
    raise ValueError("Unsupported reference video payload")


def _resample_video_frames(frames: torch.Tensor, source_fps: float) -> torch.Tensor:
    if not source_fps or abs(source_fps - h3.FPS) < 0.01:
        return frames
    count = max(1, round(frames.shape[0] * h3.FPS / source_fps))
    indexes = torch.linspace(0, frames.shape[0] - 1, count, device=frames.device).round().long()
    return frames[indexes]


def _encode_reference_audio(audio_vae, audio: Mapping):
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
    # A workflow may intentionally contain fewer/more @ references than the
    # currently connected media. Resolve valid placeholders, but preserve
    # stale internal placeholders so the user's original reference is not
    # silently discarded; the downstream model decides how to handle it.
    source_prompt = str(prompt or "")
    resolved = REFERENCE_PLACEHOLDER_RE.sub(
        lambda match: tag_by_input.get(int(match.group(1)), ""),
        source_prompt,
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


def _segment_context_frame_count(
    value: Any,
    allowed_grid: tuple[int, ...] = SEGMENT_CONTEXT_FRAME_GRID,
) -> int:
    """Validate the discrete MiniMax H3 context temporal grid."""
    try:
        requested = int(value)
    except (TypeError, ValueError) as exc:
        choices = ", ".join(str(item) for item in allowed_grid)
        raise ValueError(f"Context frames must be one of: {choices}") from exc
    if requested not in allowed_grid:
        choices = ", ".join(str(item) for item in allowed_grid)
        raise ValueError(f"Context frames must be one of: {choices}; got {requested}")
    return requested


def _segment_context_frame_count_for_mode(value: Any, continuity_mode: Any) -> int:
    mode = str(continuity_mode or CONTEXT_CONTINUITY_LATENT)
    allowed = SEGMENT_CONTEXT_AV_FRAME_GRID if mode in CONTEXT_CONTINUITY_AV_MODES else SEGMENT_CONTEXT_GUIDE_FRAME_GRID
    return _segment_context_frame_count(value, allowed)


def _segment_latent_streams(latent: Mapping[str, Any]) -> tuple[torch.Tensor, torch.Tensor]:
    samples = latent.get("samples") if isinstance(latent, Mapping) else None
    return _segment_av_streams(samples, "Sequence expected a MiniMax H3 AV latent")


def _segment_av_streams(samples: Any, missing_message: str) -> tuple[torch.Tensor, torch.Tensor]:
    if hasattr(samples, "unbind"):
        streams = list(samples.unbind())
    elif isinstance(samples, (tuple, list)):
        streams = list(samples)
    else:
        raise ValueError(missing_message)
    if len(streams) < 2 or not all(isinstance(stream, torch.Tensor) for stream in streams[:2]):
        raise ValueError("Sequence H3 latent does not contain both video and audio streams")
    video, audio = streams[0], streams[1]
    if video.ndim != 5 or audio.ndim != 4:
        raise ValueError("Sequence H3 latent streams have unsupported shapes")
    return video, audio


def _segment_pack_latent(video: torch.Tensor, audio: torch.Tensor) -> dict[str, Any]:
    """Pack CPU video/audio streams back into the AV latent container."""
    if not isinstance(video, torch.Tensor) or not isinstance(audio, torch.Tensor):
        raise ValueError("MiniMax H3 segment result is missing one of its AV latent streams")
    try:
        from comfy.nested_tensor import NestedTensor
    except Exception:
        NestedTensor = None
    if NestedTensor is not None:
        return {"samples": NestedTensor((video, audio))}
    return {"samples": (video, audio)}


def _segment_pack_av(
    video: torch.Tensor,
    audio: torch.Tensor,
    video_mask: torch.Tensor | None = None,
    audio_mask: torch.Tensor | None = None,
) -> dict[str, Any]:
    """Pack H3 AV streams and an optional paired denoise mask."""
    result = _segment_pack_latent(video, audio)
    if video_mask is None and audio_mask is None:
        return result
    if not isinstance(video_mask, torch.Tensor) or not isinstance(audio_mask, torch.Tensor):
        raise ValueError("Segment AV masks must include both video and audio streams")
    result["noise_mask"] = _segment_pack_latent(video_mask, audio_mask)["samples"]
    return result


def _fit_audio_latent(audio_latent: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Fit an encoded audio track to the target H3 audio grid without resampling."""
    if not isinstance(audio_latent, torch.Tensor) or audio_latent.ndim != 4:
        raise ValueError("Digital Human audio encoding is invalid")
    if audio_latent.shape[:3] != target.shape[:3]:
        raise ValueError("Digital Human audio encoding has an incompatible channel layout")
    wanted = int(target.shape[-1])
    value = audio_latent[..., :wanted]
    if value.shape[-1] < wanted:
        if value.shape[-1] <= 0:
            value = torch.zeros_like(target)
        else:
            value = torch.cat([value, value[..., -1:].repeat(1, 1, 1, wanted - value.shape[-1])], dim=-1)
    return value.to(device=target.device, dtype=target.dtype).contiguous()


def _lock_audio_latent(latent: Mapping[str, Any], audio_latent: torch.Tensor) -> dict[str, Any]:
    """Insert an external track and prevent H3 from denoising its audio stream."""
    video, audio = _segment_latent_streams(latent)
    audio = _fit_audio_latent(audio_latent, audio)
    video_mask = torch.ones(
        (video.shape[0], 1, video.shape[2], video.shape[3], video.shape[4]),
        device=video.device,
        dtype=video.dtype,
    )
    audio_mask = torch.zeros(
        (audio.shape[0], 1, audio.shape[2], audio.shape[3]),
        device=audio.device,
        dtype=audio.dtype,
    )
    return _segment_pack_av(video, audio, video_mask, audio_mask)


def _segment_noise_mask_streams(latent: Mapping[str, Any]) -> tuple[torch.Tensor | None, torch.Tensor | None]:
    mask = latent.get("noise_mask") if isinstance(latent, Mapping) else None
    if mask is None:
        return None, None
    return _segment_av_streams(mask, "Segment AV noise mask is invalid")


def _segment_tile_axis(size: int, requested: int, overlap: int) -> list[tuple[int, int, int]]:
    """Return (offset, size, overlap-with-previous) tile spans for one latent axis."""
    size = max(1, int(size))
    tile = max(1, min(size, int(requested)))
    overlap = max(0, min(tile - 1, int(overlap)))
    if size <= tile:
        return [(0, size, 0)]

    stride = max(1, tile - overlap)
    offsets = list(range(0, max(1, size - tile + 1), stride))
    last = max(0, size - tile)
    if offsets[-1] != last:
        offsets.append(last)

    spans: list[tuple[int, int, int]] = []
    previous_end = 0
    for index, offset in enumerate(offsets):
        length = min(tile, size - offset)
        actual_overlap = max(0, previous_end - offset) if index else 0
        spans.append((offset, length, actual_overlap))
        previous_end = max(previous_end, offset + length)
    return spans


def _segment_tile_blend(
    height: int,
    width: int,
    top_overlap: int,
    left_overlap: int,
    fade: int,
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    """Build the tile-side blend/denoise mask for already written seam bands."""
    horizontal = torch.ones(width, device=device, dtype=dtype)
    vertical = torch.ones(height, device=device, dtype=dtype)

    def ramp(values: torch.Tensor, overlap_size: int) -> None:
        if overlap_size <= 0:
            return
        fade_size = min(max(0, int(fade)), overlap_size)
        frozen = overlap_size - fade_size
        if frozen:
            values[:frozen] = 0.0
        if fade_size:
            values[frozen:overlap_size] = torch.linspace(
                0.0,
                1.0,
                fade_size + 1,
                device=device,
                dtype=dtype,
            )[1:]
        elif frozen < overlap_size:
            values[:overlap_size] = 0.0

    ramp(horizontal, left_overlap)
    ramp(vertical, top_overlap)
    return torch.minimum(vertical[:, None], horizontal[None, :]).view(1, 1, 1, height, width)


def _segment_crop_keyframe_conditioning(
    conditioning: Any,
    source_height: int,
    source_width: int,
    top: int,
    left: int,
    tile_height: int,
    tile_width: int,
) -> Any:
    """Crop only full-canvas H3 keyframe latents; reference media stays intact."""
    if not isinstance(conditioning, (list, tuple)):
        return conditioning
    cropped_conditioning = []
    for embedding, metadata in conditioning:
        values = dict(metadata)
        keyframes = list(values.get("minimax_keyframes") or [])
        if keyframes:
            cropped_keyframes = []
            for keyframe in keyframes:
                entry = dict(keyframe)
                keyframe_latent = entry.get("latent")
                if (
                    isinstance(keyframe_latent, torch.Tensor)
                    and keyframe_latent.ndim == 5
                    and int(keyframe_latent.shape[-2]) == int(source_height)
                    and int(keyframe_latent.shape[-1]) == int(source_width)
                ):
                    entry["latent"] = keyframe_latent[
                        :, :, :, top:top + tile_height, left:left + tile_width
                    ].contiguous()
                cropped_keyframes.append(entry)
            values["minimax_keyframes"] = cropped_keyframes
        cropped_conditioning.append([embedding, values])
    return cropped_conditioning


def _segment_context_keyframes(
    bundle: MiniMaxH3Bundle,
    frames: torch.Tensor,
    width: int,
    height: int,
    context_frames: int,
) -> tuple[list[dict[str, Any]], int]:
    """Encode one complete RGB context tail as one native H3 Guide block."""
    if not isinstance(frames, torch.Tensor) or frames.ndim != 4 or frames.shape[0] < 1:
        raise ValueError("Segment context has no usable video frames")
    requested = _segment_context_frame_count(context_frames)
    available = min(requested, int(frames.shape[0]))
    tail = frames[-available:]
    if tail.shape[0] < requested:
        # When a previous clip is shorter than the requested context, pad the
        # missing history at the front so the real tail remains at the boundary.
        tail = torch.cat([tail[:1].repeat(requested - tail.shape[0], 1, 1, 1), tail], dim=0)
    tail = h3._resize(tail, width, height, "center")
    latent = bundle.video_vae.encode(tail)
    if not isinstance(latent, torch.Tensor) or latent.ndim != 5 or latent.shape[2] < 1:
        raise RuntimeError("MiniMax H3 video VAE returned an unsupported segment context latent")
    frame_per_token = tuple(getattr(h3, "FRAME_PER_TOKEN", SEGMENT_FRAME_PER_TOKEN))
    covered_frames = sum(
        int(frame_per_token[index % len(frame_per_token)])
        for index in range(int(latent.shape[2]))
    )
    return [{"resolved_frame_index": 0, "latent": latent}], covered_frames


def _segment_context_keyframes_from_latent(
    latent: torch.Tensor, context_frames: int,
) -> tuple[list[dict[str, Any]], int]:
    """Build context guides directly from a delivered H3 video latent.

    This avoids the lossy RGB -> VAE round trip for segments produced by the
    same renderer. External media and the first segment still use the RGB
    guide path above.
    """
    if not isinstance(latent, torch.Tensor) or latent.ndim != 5 or latent.shape[2] < 1:
        raise ValueError("Segment latent context has no usable video latent")
    requested = _segment_context_frame_count(context_frames)
    wanted_tokens = int(h3.temporal_shape(requested)[1])
    available = int(latent.shape[2])
    if available >= wanted_tokens:
        tail = latent[:, :, -wanted_tokens:]
    else:
        tail = torch.cat(
            [latent[:, :, :1].repeat(1, 1, wanted_tokens - available, 1, 1), latent],
            dim=2,
        )
    frame_per_token = tuple(getattr(h3, "FRAME_PER_TOKEN", SEGMENT_FRAME_PER_TOKEN))
    covered_frames = sum(
        int(frame_per_token[index % len(frame_per_token)])
        for index in range(int(tail.shape[2]))
    )
    return [{"resolved_frame_index": 0, "latent": tail.detach().to("cpu").contiguous()}], covered_frames


def _segment_prefix_latent(latent: torch.Tensor, token_count: int) -> torch.Tensor:
    """Return a boundary prefix, padding short histories at the front."""
    if not isinstance(latent, torch.Tensor) or latent.ndim < 3:
        raise ValueError("Segment AV prefix has no usable latent")
    token_count = max(1, int(token_count))
    available = int(latent.shape[2])
    if available >= token_count:
        return latent[:, :, -token_count:]
    return torch.cat(
        [latent[:, :, :1].repeat((1, 1, token_count - available) + (1,) * (latent.ndim - 3)), latent],
        dim=2,
    )


def _segment_apply_av_prefix(
    latent: Mapping[str, Any],
    video_reference: torch.Tensor | None,
    audio_reference: Mapping[str, Any] | None,
    context_frames: int,
    continuity_mode: str,
) -> dict[str, Any]:
    """Seed and mask the overlapping AV prefix for Soft/Hard AV continuity.

    The stock ComfyUI sampler interprets a zero denoise mask as "hold the
    supplied latent". H3's packed AV sampler preserves the two stream masks
    separately, so the boundary is kept in both video and audio space.
    """
    if continuity_mode not in CONTEXT_CONTINUITY_AV_MODES:
        return dict(latent)
    video, audio = _segment_latent_streams(latent)
    video = video.clone()
    audio = audio.clone()
    video_prefix_tokens = min(
        int(video.shape[2]),
        int(h3.temporal_shape(context_frames)[1]),
    )
    audio_prefix_steps = min(
        int(audio.shape[-1]),
        int(h3.temporal_shape(context_frames)[2]),
    )

    if isinstance(video_reference, torch.Tensor):
        prefix = _segment_prefix_latent(video_reference, video_prefix_tokens)
        video[:, :, :video_prefix_tokens] = prefix.to(device=video.device, dtype=video.dtype)

    if isinstance(audio_reference, Mapping) and isinstance(audio_reference.get("audio_latent"), torch.Tensor):
        reference_audio = audio_reference["audio_latent"]
        if reference_audio.ndim == 4 and reference_audio.shape[-1] > 0:
            # Source-audio references cover the whole target slice; their
            # leading steps are the overlap. Generated references already
            # contain exactly the overlap and take the same path.
            prefix = reference_audio[..., :audio_prefix_steps]
            if prefix.shape[-1] < audio_prefix_steps:
                prefix = torch.cat(
                    [prefix, prefix[..., -1:].repeat(1, 1, 1, audio_prefix_steps - prefix.shape[-1])],
                    dim=-1,
                )
            audio[:, :, :, :audio_prefix_steps] = prefix.to(device=audio.device, dtype=audio.dtype)

    video_mask = torch.ones(
        (video.shape[0], 1, video.shape[2], video.shape[3], video.shape[4]),
        device=video.device,
        dtype=video.dtype,
    )
    audio_mask = torch.ones(
        (audio.shape[0], 1, audio.shape[2], audio.shape[3]),
        device=audio.device,
        dtype=audio.dtype,
    )
    if isinstance(video_reference, torch.Tensor) and video_prefix_tokens > 0:
        video_mask[:, :, :video_prefix_tokens] = 0.0
    if isinstance(audio_reference, Mapping) and audio_prefix_steps > 0:
        audio_mask[:, :, :, :audio_prefix_steps] = 0.0
        if continuity_mode == CONTEXT_CONTINUITY_SOFT_AV and audio_prefix_steps > 0:
            # Soft AV keeps the picture boundary exact and releases only the
            # final eight audio ticks with the upstream half-cosine handoff.
            feather_steps = min(8, audio_prefix_steps)
            hard_steps = audio_prefix_steps - feather_steps
            indices = torch.arange(
                1,
                feather_steps + 1,
                device=audio_mask.device,
                dtype=audio_mask.dtype,
            )
            release = 0.5 - 0.5 * torch.cos(
                torch.pi * indices / float(feather_steps)
            )
            audio_mask[:, :, :, hard_steps:audio_prefix_steps] = release.view(
                1, 1, 1, feather_steps
            )

    try:
        from comfy.nested_tensor import NestedTensor
    except Exception:
        NestedTensor = None
    result = dict(latent)
    if NestedTensor is not None:
        result["samples"] = NestedTensor((video, audio))
        result["noise_mask"] = NestedTensor((video_mask, audio_mask))
    else:
        result["samples"] = (video, audio)
        result["noise_mask"] = (video_mask, audio_mask)
    return result


def _segment_apply_guide_handoff(
    latent: Mapping[str, Any],
    video_reference: torch.Tensor | None,
    audio_reference: Mapping[str, Any] | None,
    context_frames: int,
) -> dict[str, Any]:
    """Stabilize a visual-guide boundary without turning it into AV prefix mode.

    The guide workflow intentionally leaves most of the repeated visual head
    open so H3 can redraw it and avoid recursive degradation. The final two
    video tokens of that hidden head are different: pinning them gives the
    model both an exact phase-aligned boundary and a short motion direction to
    continue from. Generated audio has no equivalent speaker embedding, so its
    carried overlap is pinned in full. This carries boundary timing only; it
    is not a speaker or singer identity lock.
    """
    video, audio = _segment_latent_streams(latent)
    video = video.clone()
    audio = audio.clone()
    video_mask = torch.ones(
        (video.shape[0], 1, video.shape[2], video.shape[3], video.shape[4]),
        device=video.device,
        dtype=video.dtype,
    )
    audio_mask = torch.ones(
        (audio.shape[0], 1, audio.shape[2], audio.shape[3]),
        device=audio.device,
        dtype=audio.dtype,
    )

    video_prefix_tokens = min(
        int(video.shape[2]),
        int(h3.temporal_shape(context_frames)[1]),
    )
    if isinstance(video_reference, torch.Tensor) and video_prefix_tokens > 0:
        prefix = _segment_prefix_latent(video_reference, video_prefix_tokens)
        # Keep a short outgoing edge, not just one token. The final token is
        # the temporal boundary, but its preceding token carries the motion
        # direction needed by the first newly generated body token. Earlier
        # context tokens remain denoisable, preserving Guide's refresh path.
        edge_start = max(
            0,
            video_prefix_tokens - min(
                SEGMENT_GUIDE_HANDOFF_VIDEO_TOKENS,
                video_prefix_tokens,
            ),
        )
        video[:, :, edge_start:video_prefix_tokens] = prefix[:, :, edge_start:video_prefix_tokens].to(
            device=video.device,
            dtype=video.dtype,
        )
        video_mask[:, :, edge_start:video_prefix_tokens] = 0.0

    audio_prefix_steps = min(
        int(audio.shape[-1]),
        int(h3.temporal_shape(context_frames)[2]),
    )
    if (
        isinstance(audio_reference, Mapping)
        and isinstance(audio_reference.get("audio_latent"), torch.Tensor)
        and audio_prefix_steps > 0
    ):
        reference_audio = audio_reference["audio_latent"]
        if reference_audio.ndim == 4 and reference_audio.shape[-1] > 0:
            prefix = reference_audio[..., :audio_prefix_steps]
            if prefix.shape[-1] < audio_prefix_steps:
                prefix = torch.cat(
                    [
                        prefix,
                        prefix[..., -1:].repeat(
                            1, 1, 1, audio_prefix_steps - prefix.shape[-1]
                        ),
                    ],
                    dim=-1,
                )
            audio[:, :, :, :audio_prefix_steps] = prefix.to(
                device=audio.device,
                dtype=audio.dtype,
            )
            audio_mask[:, :, :, :audio_prefix_steps] = 0.0

    if not bool(torch.any(video_mask < 1.0)) and not bool(torch.any(audio_mask < 1.0)):
        return dict(latent)
    return _segment_pack_av(video, audio, video_mask, audio_mask)


def _segment_context_audio_reference(
    sampled: Mapping[str, Any], source_end_frame: int, context_frames: int,
) -> dict[str, Any] | None:
    """Return the previous tail audio for a native frame-zero Guide."""
    _video, audio = _segment_latent_streams(sampled)
    requested_frames = max(1, int(context_frames))
    audio_steps_per_frame = 40.0 / float(h3.FPS)
    requested_steps = max(1, round(requested_frames * audio_steps_per_frame))
    total_steps = int(audio.shape[-1])
    source_end_frame = max(1, int(source_end_frame))
    source_end_steps = round(source_end_frame * audio_steps_per_frame)
    if source_end_steps < requested_steps or total_steps < source_end_steps:
        return None
    return {
        "audio_latent": audio[..., source_end_steps - requested_steps:source_end_steps].detach().to("cpu").contiguous(),
    }


def _segment_source_audio_reference(
    bundle: MiniMaxH3Bundle,
    source_audio: Mapping[str, Any] | None,
    source_start_frame: int,
    delivery_frames: int,
) -> dict[str, Any] | None:
    """Encode one timeline slice of the independent external source track."""
    sliced = _segment_trim_audio(source_audio, source_start_frame, delivery_frames)
    if sliced is None:
        return None
    audio_latent, audio_steps = _encode_reference_audio(bundle.audio_vae, sliced)
    if not isinstance(audio_latent, torch.Tensor) or audio_steps <= 0:
        return None
    return {"audio_latent": audio_latent.detach().to("cpu").contiguous()}


def _segment_add_context_conditioning(
    conditioning: Any,
    keyframes: list[dict[str, Any]],
    frame_count: int,
    audio_reference: Mapping[str, Any] | None = None,
) -> Any:
    if not keyframes and not isinstance(audio_reference, Mapping):
        return conditioning
    out = []
    for embedding, metadata in conditioning:
        values = dict(metadata)
        existing = list(values.get("minimax_keyframes") or [])
        guides = [dict(item) for item in keyframes]
        if isinstance(audio_reference, Mapping) and isinstance(audio_reference.get("audio_latent"), torch.Tensor):
            # Native Add Guide accepts visual and audio conditions on the same
            # keyframe. Keep an independent source track anchored at frame zero;
            # reference-media blocks remain separate in ``minimax_refs``.
            if guides:
                guides[0]["audio_latent"] = audio_reference["audio_latent"]
            else:
                guides = [{
                    "resolved_frame_index": 0,
                    "audio_latent": audio_reference["audio_latent"],
                }]
        if guides:
            # Match MiniMaxH3AddGuide exactly: preserve existing keyframes and
            # append the newly added guide instead of changing their order.
            values["minimax_keyframes"] = existing + guides
        out.append([embedding, values])
    return out


def _segment_target_length(delivery_frames: int, context_frames: int = 0) -> int:
    required = max(5, int(delivery_frames) + max(0, int(context_frames)))
    while required % 17 != 5:
        required += 1
    return required


def _segment_trim_audio(audio: Mapping[str, Any] | None, start_frames: int, delivery_frames: int) -> dict[str, Any] | None:
    if not isinstance(audio, Mapping) or not isinstance(audio.get("waveform"), torch.Tensor):
        return None
    waveform = audio["waveform"]
    if waveform.ndim != 3:
        return None
    sample_rate = _audio_sample_rate(audio)
    start = max(0, round(float(start_frames) * sample_rate / float(h3.FPS)))
    end = max(start, round(float(start_frames + delivery_frames) * sample_rate / float(h3.FPS)))
    trimmed = waveform[..., start:min(end, waveform.shape[-1])]
    expected = end - start
    if trimmed.shape[-1] < expected:
        trimmed = torch.nn.functional.pad(trimmed, (0, expected - trimmed.shape[-1]))
    return {"waveform": trimmed.contiguous(), "sample_rate": sample_rate}


@lru_cache(maxsize=1)
def _segment_ffmpeg_path() -> str:
    """Resolve the same portable FFmpeg executable used by ComfyUI video nodes."""
    forced = os.environ.get("VHS_FORCE_FFMPEG_PATH")
    if forced and os.path.isfile(forced):
        return forced
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        bundled = get_ffmpeg_exe()
        if bundled and os.path.isfile(bundled):
            return bundled
    except Exception:
        pass
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    raise RuntimeError(
        "FFmpeg is required for streaming Context Segment export. "
        "Install imageio-ffmpeg or make ffmpeg available on PATH."
    )


def _segment_rgb_frame_bytes(frame: torch.Tensor) -> bytes:
    """Convert one HWC image frame without materializing the full timeline."""
    if not isinstance(frame, torch.Tensor) or frame.ndim != 3 or frame.shape[-1] < 3:
        raise ValueError("Context Segment decoder produced an invalid RGB frame")
    rgb = frame[..., :3].detach().to(device="cpu", dtype=torch.float32).clamp(0.0, 1.0)
    return (rgb.mul(255.0).round().to(torch.uint8).contiguous().numpy()).tobytes()


def _segment_audio_bytes(audio: Mapping[str, Any]) -> tuple[int, int, bytes]:
    """Convert one audio chunk to interleaved float32 PCM for the streaming mux."""
    waveform = audio.get("waveform") if isinstance(audio, Mapping) else None
    if not isinstance(waveform, torch.Tensor):
        raise ValueError("Context Segment audio decoder produced no waveform")
    if waveform.ndim == 3:
        if waveform.shape[0] != 1:
            raise ValueError("Context Segment audio streaming expects a single batch")
        waveform = waveform[0]
    if waveform.ndim != 2:
        raise ValueError("Context Segment audio decoder produced an invalid waveform")
    channels = int(waveform.shape[0])
    sample_rate = _audio_sample_rate(audio)
    pcm = waveform.detach().to(device="cpu", dtype=torch.float32).clamp(-1.0, 1.0)
    pcm = pcm.transpose(0, 1).contiguous().numpy()
    return channels, sample_rate, pcm.tobytes()


class _H3PCMWriter:
    """Small incremental float32 PCM writer used to avoid concatenating audio."""

    def __init__(self, path: str):
        self.path = path
        self._handle = open(path, "wb")
        self._channels = 0
        self._sample_rate = 0

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def write(self, audio: Mapping[str, Any]) -> None:
        channels, sample_rate, pcm = _segment_audio_bytes(audio)
        if self._channels == 0:
            self._channels = channels
            self._sample_rate = sample_rate
        elif (channels, sample_rate) != (self._channels, self._sample_rate):
            raise ValueError("Context Segment audio chunks changed channel count or sample rate")
        self._handle.write(pcm)

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


def _segment_cleanup_temp_dir(path: str | None) -> None:
    if path and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


def split_prompt_segments(text: str) -> list[str]:
    """Split pasted/editor text on standalone divider lines.

    Prompts frequently arrive by copy/paste from an agent or markdown editor.
    Normalize desktop/newline variants and invisible formatting marks first,
    then canonicalize an optionally escaped divider before splitting. The
    match remains line-based, so ordinary hyphens inside a prompt are safe.
    """
    normalized = str(text or "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u2028", "\n").replace("\u2029", "\n")
    for marker in SEGMENT_DIVIDER_INVISIBLE:
        normalized = normalized.replace(marker, "")
    normalized = "\n".join(
        "---" if SEGMENT_DIVIDER_PATTERN.fullmatch(line.replace("\u00a0", " ")) else line
        for line in normalized.split("\n")
    )
    parts = [part.strip() for part in SEGMENT_DIVIDER_PATTERN.split(normalized)]
    while len(parts) > 1 and not parts[-1]:
        parts.pop()
    return [part for part in parts if part]


def parse_segment_seconds(value: Any, segment_count: int) -> list[float]:
    raw = str(value or "").replace("\uff0c", ",")
    entries = [item.strip() for item in raw.split(",") if item.strip()]
    if not entries:
        raise ValueError("Context Segment mode needs per-segment seconds, for example 10,8,5")
    if len(entries) != segment_count:
        raise ValueError(
            f"Segment seconds count ({len(entries)}) does not match the {segment_count} prompt segments"
        )
    seconds_list = []
    for index, item in enumerate(entries, start=1):
        try:
            seconds = float(item)
        except ValueError:
            raise ValueError(f"Segment {index} seconds is not a number: {item!r}")
        if not MIN_SECONDS <= seconds <= MAX_SECONDS:
            raise ValueError(
                f"Segment {index} seconds must be between {MIN_SECONDS:g} and {MAX_SECONDS:g}"
            )
        seconds_list.append(seconds)
    return seconds_list


def _segment_expand_media_placeholders(text: str, items: list[_MediaInput]) -> str:
    """Resolve frontend @-mention placeholders before per-shot tag binding."""
    counters = {"image": 0, "video": 0, "audio": 0}
    tags_by_position: dict[int, str] = {}
    tags_by_type: dict[str, list[str]] = {"image": [], "video": [], "audio": []}
    prefixes = {"image": "Picture", "video": "Video", "audio": "Audio"}
    for position, item in enumerate(items, start=1):
        media_type = str(item.media_type or "").lower()
        if media_type not in prefixes:
            continue
        counters[media_type] += 1
        tag = f"<{prefixes[media_type]} {counters[media_type]}>"
        tags_by_position[position] = tag
        tags_by_type[media_type].append(tag)

    resolved = REFERENCE_PLACEHOLDER_RE.sub(
        lambda match: tags_by_position.get(int(match.group(1)), match.group(0)),
        str(text or ""),
    )

    def replace_unresolved(match: re.Match) -> str:
        raw = match.group(0).lower()
        media_type = "image" if "_image__" in raw else "video" if "_video__" in raw else "audio"
        queue = tags_by_type.get(media_type) or []
        return queue.pop(0) if queue else match.group(0)

    return UNRESOLVED_REFERENCE_RE.sub(replace_unresolved, resolved)


def bind_segment_media(text: str, items: list[_MediaInput]) -> tuple[list[_MediaInput], str]:
    """Resolve <Picture/Video/Audio N> tags of one segment against global ordinals.

    Returns the referenced media subset plus the segment text rewritten with
    compact local numbering so H3 sees tags that match the subset order.
    """
    text = _segment_expand_media_placeholders(text, items)
    pools = {
        "picture": [item for item in items if item.media_type == "image"],
        "video": [item for item in items if item.media_type == "video"],
        "audio": [item for item in items if item.media_type == "audio"],
    }
    counters = {"picture": 0, "video": 0, "audio": 0}
    assigned: dict[int, int] = {}
    chosen: list[_MediaInput] = []

    def replace(match: re.Match) -> str:
        kind = match.group(1).lower()
        pool = pools.get(kind) or []
        ordinal = int(match.group(2))
        if not 1 <= ordinal <= len(pool):
            return match.group(0)
        item = pool[ordinal - 1]
        marker = id(item)
        if marker in assigned:
            return f"<{match.group(1).capitalize()} {assigned[marker]}>"
        counters[kind] += 1
        assigned[marker] = counters[kind]
        chosen.append(item)
        return f"<{match.group(1).capitalize()} {counters[kind]}>"

    rewritten = SEGMENT_TAG_PATTERN.sub(replace, str(text or ""))
    return chosen, rewritten


def _empty_image_conditioning(bundle, prompt, width, height, length, first_frame=None, last_frame=None):
    latent, frame_count = h3._empty_av_latent(width, height, length)
    images = []
    keyframes = []
    keyframe_sources = []
    if first_frame is not None:
        source = first_frame[:1]
        image = h3._resize(source, width, height, "center")
        images.append(image)
        keyframes.append({"resolved_frame_index": 0, "image": image})
        keyframe_sources.append(_MiniMaxH3KeyframeSource(0, source))
    if last_frame is not None:
        source = last_frame[:1]
        image = h3._resize(source, width, height, "center")
        images.append(image)
        keyframes.append({"resolved_frame_index": frame_count - 1, "image": image})
        keyframe_sources.append(_MiniMaxH3KeyframeSource(frame_count - 1, source))

    tokens = bundle.clip.tokenize(prompt, images=images)
    conditioning = bundle.clip.encode_from_tokens_scheduled(tokens)
    if keyframes:
        for keyframe in keyframes:
            keyframe["latent"] = bundle.video_vae.encode(keyframe.pop("image"))
        conditioning = node_helpers.conditioning_set_values(conditioning, {
            "minimax_keyframes": keyframes,
            "minimax_frame_count": frame_count,
        })
    return conditioning, latent, tuple(keyframe_sources)


def _reference_conditioning(
    bundle, prompt, width, height, length, ref_image_size,
    items: list[_MediaInput], *, include_audio: bool = True,
):
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
        size_mode = str(ref_image_size or REF_IMAGE_1K)
        if size_mode == REF_IMAGE_ORIGINAL:
            # H3 patchifies reference latents in 2x2 blocks, so their source
            # pixels must land on a 32-pixel grid. Preserve the original image
            # without padding or stretching by center-cropping only the small
            # remainder; already aligned images pass through unchanged.
            target_w, target_h = _original_reference_size(image_w, image_h)
            if target_w == image_w and target_h == image_h:
                resized = image[:1]
            elif image_w >= h3.CANVAS_MULTIPLE and image_h >= h3.CANVAS_MULTIPLE:
                top = (image_h - target_h) // 2
                left = (image_w - target_w) // 2
                resized = image[:1, top:top + target_h, left:left + target_w, :]
            else:
                resized = h3._resize(image[:1], target_w, target_h, "disabled")
            z = bundle.video_vae.encode(resized)
            ref_items.append({"type": "image", "data": resized})
            ref_blocks.append({
                "kind": "image",
                "latent_h": int(z.shape[-2]),
                "latent_w": int(z.shape[-1]),
                "latent": z,
            })
            tag_by_input[item.input_index] = f"<Picture {picture_ordinal}>"
            continue
        if size_mode == REF_IMAGE_MATCH:
            target_area = width * height
        else:
            target_area = REFERENCE_IMAGE_AREAS.get(size_mode, REFERENCE_IMAGE_AREAS[REF_IMAGE_1K])
        # Use one uniform scale factor for both axes so no non-uniform
        # stretching is introduced before H3's internal size alignment.
        scale = min(1.0, math.sqrt(target_area / max(1, image_w * image_h)))
        target_w, target_h = _reference_aligned_size(image_w, image_h, scale)
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
        if include_audio and soundtrack is not None:
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

    for item in audios if include_audio else []:
        if not isinstance(item.value, Mapping) or "waveform" not in item.value:
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


def _validate_reference_media(items: list[_MediaInput], scope: str = "Reference mode") -> None:
    """Validate the H3 reference budget applied to one actual conditioning call."""
    if len(items) > MAX_MEDIA:
        raise ValueError(f"{scope} accepts at most fifteen media resources")
    counts = {"image": 0, "video": 0, "audio": 0}
    for item in items:
        if item.media_type not in counts:
            raise ValueError(f"{scope} received an unsupported media resource")
        counts[item.media_type] += 1
    if counts["image"] > MAX_IMAGES or counts["video"] > MAX_VIDEOS or counts["audio"] > MAX_AUDIOS:
        raise ValueError(f"{scope} media limits are 9 images, 3 videos and 3 audio clips")
    if counts["image"] == 0 and counts["video"] == 0:
        raise ValueError(f"{scope} needs an image or video in addition to audio")


def _extract_digital_human_audio(items: list[_MediaInput], scope: str) -> tuple[list[_MediaInput], Mapping[str, Any]]:
    """Split one Media audio driver from the visual references."""
    audios = [item for item in items if item.media_type == "audio"]
    if len(audios) != 1:
        raise ValueError(f"{scope} digital human mode needs exactly one audio resource in Media")
    source = audios[0].value
    if not isinstance(source, Mapping) or not isinstance(source.get("waveform"), torch.Tensor):
        raise ValueError(f"{scope} digital human audio must be a valid AUDIO payload")
    waveform = source["waveform"]
    if waveform.ndim != 3 or waveform.shape[-1] < 1:
        raise ValueError(f"{scope} digital human audio is empty")
    normalized = {
        "waveform": waveform.detach().to("cpu").contiguous(),
        "sample_rate": _audio_sample_rate(source),
    }
    return [item for item in items if item.media_type in {"image", "video"}], normalized


def _validate_context_media_library(items: list[_MediaInput]) -> None:
    """Validate the library shared by all context blocks, not one H3 call."""
    counts = {"image": 0, "video": 0, "audio": 0}
    for item in items:
        if item.media_type not in counts:
            raise ValueError("Context Segments received an unsupported media resource")
        counts[item.media_type] += 1
    if (
        len(items) > SEGMENT_MAX_MEDIA
        or counts["image"] > SEGMENT_MAX_IMAGES
        or counts["video"] > SEGMENT_MAX_VIDEOS
        or counts["audio"] > SEGMENT_MAX_AUDIOS
    ):
        raise ValueError(
            "Context Segments supports up to 27 images, 9 videos, and 9 audio clips "
            "(45 media resources total) across the full sequence"
        )


class MiniMaxH3Easy:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "generate"
    RETURN_TYPES = ("MODEL", "MINIMAX_H3_CONTEXT")
    RETURN_NAMES = ("model", "h3_context")
    DESCRIPTION = "One MiniMax H3 node for text, image, reference-video, and digital-human workflows."

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "media": ("*",),
            "prompt_optimizer_resources": ("STRING", {"default": "", "hidden": True}),
            "prompt_optimizer_marker": ("STRING", {"default": "", "hidden": True}),
            "prompt_optimizer_prompt_connected": ("BOOLEAN", {"default": False, "hidden": True}),
        }
        for index in range(1, MAX_MEDIA + 1):
            # Transport-only inputs used by the virtual multi-wire frontend.
            # Keep them in INPUT_TYPES so ComfyUI execution can resolve the
            # linked media objects, but mark them hidden as a server-side
            # fallback: even if the web extension fails to initialize, users
            # must never see thirty internal sockets/widgets on the node.
            optional[f"media_{index}"] = ("*", {"hidden": True})
            optional[f"media_type_{index}"] = ("STRING", {"default": "", "hidden": True})
        return {
            "required": {
                "h3_bundle": ("MINIMAX_H3_BUNDLE",),
                "mode": ([MODE_IMAGE, MODE_REFERENCE, MODE_DIGITAL_HUMAN], {"default": MODE_IMAGE}),
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
                "resolution": (list(RESOLUTIONS), {"default": RESOLUTION_480}),
                "aspect_ratio": (list(ASPECT_RATIOS), {"default": ASPECT_WIDESCREEN}),
                "width": ("INT", {"default": 1344, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "height": ("INT", {"default": 768, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "seconds": ("FLOAT", {"default": 5.0, "min": MIN_SECONDS, "max": MAX_SECONDS, "step": 0.1}),
                "advanced": ("BOOLEAN", {"default": False}),
                "fps": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 120.0, "step": 1.0}),
                "keyframe_role": ([KEYFRAME_FIRST, KEYFRAME_LAST], {"default": KEYFRAME_FIRST}),
                "ref_image_size": ([REF_IMAGE_MATCH, REF_IMAGE_1K, REF_IMAGE_15K, REF_IMAGE_2K, REF_IMAGE_ORIGINAL], {"default": REF_IMAGE_1K}),
                "reference_mention_mode": ([REFERENCE_MENTION_FILENAME, REFERENCE_MENTION_INDEX], {"default": REFERENCE_MENTION_INDEX}),
                "prompt_optimizer": ("BOOLEAN", {"default": False}),
                "prompt_optimizer_api_format": (["openai", "responses", "gemini"], {"default": "openai"}),
                "prompt_optimizer_api_url": ("STRING", {"default": ""}),
                "prompt_optimizer_api_key": ("STRING", {"default": "", "multiline": False, "password": True}),
                "prompt_optimizer_model": ("STRING", {"default": ""}),
                "prompt_optimizer_scene_guide": (
                    [str(item.get("id")) for item in (_prompt_guide_manifest().get("scene_guides") or []) if isinstance(item, dict) and item.get("id")] or ["none"],
                    {"default": "none"},
                ),
                "prompt_optimizer_read_media": ("BOOLEAN", {"default": False}),
                "prompt_optimizer_optimize_on_run": ("BOOLEAN", {"default": False}),
            },
            "optional": optional,
        }

    @staticmethod
    def _collect_media(kwargs: dict, maximum: int = MAX_MEDIA) -> list[_MediaInput]:
        items = []
        direct = kwargs.get("media")
        if isinstance(direct, MiniMaxH3MediaBundle):
            if any(kwargs.get(f"media_{index}") is not None for index in range(1, max(0, int(maximum)) + 1)):
                raise ValueError("Media Loader/Bridge and virtual media inputs cannot be used together")
            return list(direct.items)
        elif direct is not None:
            items.append(_MediaInput(0, _infer_media_type(direct), direct))
        for index in range(1, max(0, int(maximum)) + 1):
            value = kwargs.get(f"media_{index}")
            if value is None:
                continue
            if isinstance(value, MiniMaxH3MediaBundle):
                raise ValueError("Connect a media bundle to the Media input, not a virtual media input")
            media_type = str(kwargs.get(f"media_type_{index}") or "").strip().lower()
            resolved_type = media_type if media_type in {"image", "video", "audio"} else _infer_media_type(value)
            items.append(_MediaInput(index, resolved_type, value))
        return items

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        settings = _workflow_prompt_optimizer_settings(kwargs)
        if settings["enabled"] and settings["optimize_on_run"]:
            return float("nan")
        return False

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
    def generate(cls, h3_bundle, mode, prompt, resolution, aspect_ratio, width, height, seconds, advanced, fps, keyframe_role, ref_image_size, reference_mention_mode, **kwargs):
        if not isinstance(h3_bundle, MiniMaxH3Bundle):
            raise ValueError("Connect a MiniMax H3 Easy Loader bundle")
        mode = str(mode)
        keyframe_role = KEYFRAME_LAST if str(keyframe_role) == KEYFRAME_LAST else KEYFRAME_FIRST
        width, height = _canvas_dimensions(resolution, aspect_ratio, width, height)
        seconds = min(MAX_SECONDS, max(MIN_SECONDS, float(seconds)))
        length = _frame_length(seconds, fps)
        items = cls._collect_media(kwargs)
        _sync_reference_video_cache_scope(items)
        source_audio = None
        # Digital Human is an audio-driven variant of reference-to-video. If
        # no audio is supplied, keep the connected visual references and use
        # the ordinary reference path instead of failing before sampling.
        if mode == MODE_DIGITAL_HUMAN and not any(item.media_type == "audio" for item in items):
            mode = MODE_REFERENCE
        settings = _workflow_prompt_optimizer_settings(kwargs)
        optimization = _optimize_prompt_on_run(
            prompt,
            mode,
            seconds,
            items,
            settings,
            kwargs.get("prompt_optimizer_resources"),
            kwargs.get("prompt_optimizer_marker"),
            bool(kwargs.get("prompt_optimizer_prompt_connected", False)),
        )
        prompt = optimization.prompt
        if mode == MODE_DIGITAL_HUMAN:
            visual_items, source_audio = _extract_digital_human_audio(items, "MiniMax H3 Easy")
            _validate_reference_media(visual_items, "MiniMax H3 Easy digital human mode")
            prompt = re.sub(r"<Audio\s+\d+>", "", prompt, flags=re.IGNORECASE)
            model = h3_bundle.model_for("ref2va")
            conditioning, latent = _reference_conditioning(
                h3_bundle, prompt, width, height, length, ref_image_size,
                visual_items, include_audio=False,
            )
            audio_latent, _audio_steps = _encode_reference_audio(h3_bundle.audio_vae, source_audio)
            latent = _lock_audio_latent(latent, audio_latent)
            keyframe_sources = ()
        elif mode == MODE_REFERENCE and items:
            _validate_reference_media(items)
            model = h3_bundle.model_for("ref2va")
            conditioning, latent = _reference_conditioning(h3_bundle, prompt, width, height, length, ref_image_size, items)
            keyframe_sources = ()
        else:
            first_frame, last_frame = cls._keyframes(items, keyframe_role)
            model = h3_bundle.model_for("fl2va")
            conditioning, latent, keyframe_sources = _empty_image_conditioning(
                h3_bundle,
                prompt,
                width,
                height,
                length,
                first_frame,
                last_frame,
            )
        context = MiniMaxH3Context(
            conditioning=conditioning,
            latent=latent,
            video_vae=h3_bundle.video_vae,
            audio_vae=h3_bundle.audio_vae,
            fps=float(fps),
            aspect_ratio=aspect_ratio,
            keyframe_sources=keyframe_sources,
            source_audio=source_audio if mode == MODE_DIGITAL_HUMAN else None,
        )
        result = (model, context)
        if optimization.marker:
            return {
                "ui": {
                    "auto_optimized_prompt": [prompt],
                    "auto_optimization_marker": [json.dumps(optimization.marker, sort_keys=True, separators=(",", ":"))],
                },
                "result": result,
            }
        return result


class MiniMaxH3EasyContextSegments:
    """Build a multi-shot context plan for MiniMaxH3EasySegmentRender."""

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "generate"
    RETURN_TYPES = ("MODEL", "MINIMAX_H3_CONTEXT")
    RETURN_NAMES = ("model", "h3_context")
    DESCRIPTION = (
        "Prepare a Context Segment plan for MiniMax H3. Select the audio mode; Digital Human "
        "uses one Media audio track as a locked external driver, or falls back to normal "
        "generated-audio/reference processing when no audio is supplied. Connect the H3 Context "
        "output to MiniMax H3 Easy Segment Sample."
    )

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "media": ("*",),
            "prompt_optimizer_resources": ("STRING", {"default": "", "hidden": True}),
            "prompt_optimizer_marker": ("STRING", {"default": "", "hidden": True}),
            "prompt_optimizer_prompt_connected": ("BOOLEAN", {"default": False, "hidden": True}),
        }
        for index in range(1, SEGMENT_MAX_MEDIA + 1):
            optional[f"media_{index}"] = ("*", {"hidden": True})
            optional[f"media_type_{index}"] = ("STRING", {"default": "", "hidden": True})
        return {
            "required": {
                "h3_bundle": ("MINIMAX_H3_BUNDLE",),
                "mode": ([MODE_SEGMENTS], {"default": MODE_SEGMENTS}),
                "audio_mode": ([CONTEXT_AUDIO_GENERATED, CONTEXT_AUDIO_DIGITAL_HUMAN], {"default": CONTEXT_AUDIO_GENERATED}),
                "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
                "resolution": (list(RESOLUTIONS), {"default": RESOLUTION_480}),
                "aspect_ratio": (list(ASPECT_RATIOS), {"default": ASPECT_WIDESCREEN}),
                "width": ("INT", {"default": 1344, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "height": ("INT", {"default": 768, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "seconds": ("FLOAT", {"default": 5.0, "min": MIN_SECONDS, "max": MAX_SECONDS * SEGMENT_MAX_COUNT, "step": 0.1}),
                "segment_seconds": ("STRING", {"default": ""}),
                "context_length": ("INT", {
                    "default": SEGMENT_DEFAULT_CONTEXT_FRAMES,
                    "min": SEGMENT_MIN_CONTEXT_FRAMES,
                    "max": SEGMENT_MAX_CONTEXT_FRAMES,
                    "step": 17,
                }),
                "continuity_mode": (list(CONTEXT_CONTINUITY_MODES), {"default": CONTEXT_CONTINUITY_LATENT}),
                "advanced": ("BOOLEAN", {"default": True}),
                "fps": ("FLOAT", {"default": 24.0, "min": 24.0, "max": 24.0, "step": 1.0}),
                "keyframe_role": ([KEYFRAME_FIRST, KEYFRAME_LAST], {"default": KEYFRAME_FIRST}),
                "ref_image_size": ([REF_IMAGE_MATCH, REF_IMAGE_1K, REF_IMAGE_15K, REF_IMAGE_2K, REF_IMAGE_ORIGINAL], {"default": REF_IMAGE_1K}),
                "reference_mention_mode": ([REFERENCE_MENTION_FILENAME, REFERENCE_MENTION_INDEX], {"default": REFERENCE_MENTION_INDEX}),
                "prompt_optimizer": ("BOOLEAN", {"default": False}),
                "prompt_optimizer_api_format": (["openai", "responses", "gemini"], {"default": "openai"}),
                "prompt_optimizer_api_url": ("STRING", {"default": ""}),
                "prompt_optimizer_api_key": ("STRING", {"default": "", "multiline": False, "password": True}),
                "prompt_optimizer_model": ("STRING", {"default": ""}),
                "prompt_optimizer_scene_guide": (
                    [str(item.get("id")) for item in (_prompt_guide_manifest().get("scene_guides") or []) if isinstance(item, dict) and item.get("id")] or ["none"],
                    {"default": "none"},
                ),
                "prompt_optimizer_read_media": ("BOOLEAN", {"default": False}),
                "prompt_optimizer_optimize_on_run": ("BOOLEAN", {"default": False}),
                "context_prompt_optimizer_mode": (
                    list(CONTEXT_PROMPT_OPTIMIZER_MODES),
                    {"default": CONTEXT_PROMPT_OPTIMIZER_WHOLE},
                ),
                "context_prompt_optimizer_concurrency": (
                    "INT",
                    {
                        "default": CONTEXT_PROMPT_OPTIMIZER_DEFAULT_CONCURRENCY,
                        "min": 1,
                        "max": CONTEXT_PROMPT_OPTIMIZER_MAX_CONCURRENCY,
                        "step": 1,
                    },
                ),
            },
            "optional": optional,
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @staticmethod
    def _collect_media(kwargs: dict) -> list[_MediaInput]:
        return MiniMaxH3Easy._collect_media(kwargs, SEGMENT_MAX_MEDIA)

    @staticmethod
    def _prepare_segments(
        h3_bundle, prompt_text, items, source_audio, audio_mode, width, height,
        aspect_ratio, seconds_spec, context_length, continuity_mode, ref_image_size,
    ):
        segments = split_prompt_segments(prompt_text)
        if not segments:
            raise ValueError("Context Segment mode needs at least one prompt segment")
        if len(segments) > SEGMENT_MAX_COUNT:
            raise ValueError(f"Context Segment mode accepts at most {SEGMENT_MAX_COUNT} segments")
        seconds_list = parse_segment_seconds(seconds_spec, len(segments))
        shots = []
        normalized_continuity_mode = (
            str(continuity_mode)
            if str(continuity_mode) in CONTEXT_CONTINUITY_MODES
            else CONTEXT_CONTINUITY_LATENT
        )
        resolved_context_length = _segment_context_frame_count_for_mode(
            context_length, normalized_continuity_mode
        )
        normalized_audio_mode = (
            str(audio_mode)
            if str(audio_mode) in {CONTEXT_AUDIO_GENERATED, CONTEXT_AUDIO_DIGITAL_HUMAN}
            else CONTEXT_AUDIO_GENERATED
        )
        uses_media = source_audio is not None
        for index, (text, seconds) in enumerate(zip(segments, seconds_list), start=1):
            media, rewritten = bind_segment_media(text, items)
            if normalized_audio_mode == CONTEXT_AUDIO_DIGITAL_HUMAN:
                media = [item for item in media if item.media_type in {"image", "video"}]
                rewritten = re.sub(r"<Audio\s+\d+>", "", rewritten, flags=re.IGNORECASE)
            if media:
                _validate_reference_media(media, f"Context Segment {index}")
                uses_media = True
            shots.append({
                "index": index,
                "prompt": rewritten,
                "seconds": seconds,
                "delivery_frames": _frame_length(seconds, h3.FPS),
                "media": media,
            })
        plan = {
            "bundle": h3_bundle,
            "width": width,
            "height": height,
            "fps": float(h3.FPS),
            "context_length": resolved_context_length,
            "continuity_mode": normalized_continuity_mode,
            "audio_mode": normalized_audio_mode,
            "source_audio": source_audio,
            "model_role": "ref2va" if uses_media else "fl2va",
            "ref_image_size": ref_image_size,
            "shots": shots,
        }
        model = h3_bundle.model_for(plan["model_role"])
        context = MiniMaxH3Context(
            conditioning=None,
            latent=None,
            video_vae=h3_bundle.video_vae,
            audio_vae=h3_bundle.audio_vae,
            fps=float(h3.FPS),
            aspect_ratio=aspect_ratio,
            keyframe_sources=(),
            segment_plan=plan,
            source_audio=source_audio,
        )
        return (model, context)

    @classmethod
    def generate(cls, h3_bundle, mode, audio_mode, prompt, resolution, aspect_ratio, width, height, seconds, segment_seconds, context_length, continuity_mode, advanced, fps, keyframe_role, ref_image_size, reference_mention_mode, context_prompt_optimizer_mode, context_prompt_optimizer_concurrency, **kwargs):
        if not isinstance(h3_bundle, MiniMaxH3Bundle):
            raise ValueError("Connect a MiniMax H3 Easy Loader bundle")
        width, height = _canvas_dimensions(resolution, aspect_ratio, width, height)
        items = cls._collect_media(kwargs)
        _validate_context_media_library(items)
        audio_mode = str(audio_mode or CONTEXT_AUDIO_GENERATED)
        source_audio = None
        if audio_mode == CONTEXT_AUDIO_DIGITAL_HUMAN:
            if any(item.media_type == "audio" for item in items):
                visual_items, source_audio = _extract_digital_human_audio(items, "Context Segments")
                items = visual_items + [item for item in items if item.media_type == "audio"]
            else:
                # Without an external driver, context generation should use
                # its normal reference/generated-audio path as a fallback.
                audio_mode = CONTEXT_AUDIO_GENERATED
        elif audio_mode != CONTEXT_AUDIO_GENERATED:
            audio_mode = CONTEXT_AUDIO_GENERATED
        seconds_spec = str(segment_seconds or "")
        expected = _segment_expected_count(seconds_spec)
        try:
            total_seconds = sum(parse_segment_seconds(seconds_spec, expected))
        except ValueError:
            total_seconds = MIN_SECONDS
        settings = _workflow_prompt_optimizer_settings(kwargs)
        optimization = _optimize_prompt_on_run(
            prompt,
            MODE_DIGITAL_HUMAN if audio_mode == CONTEXT_AUDIO_DIGITAL_HUMAN else (MODE_REFERENCE if SEGMENT_TAG_PATTERN.search(prompt) else MODE_IMAGE),
            min(MAX_SECONDS * SEGMENT_MAX_COUNT, max(MIN_SECONDS, total_seconds)),
            items,
            settings,
            kwargs.get("prompt_optimizer_resources"),
            kwargs.get("prompt_optimizer_marker"),
            bool(kwargs.get("prompt_optimizer_prompt_connected", False)),
            segment_spec=(expected, seconds_spec) if expected >= 2 else None,
            context_optimizer_mode=str(context_prompt_optimizer_mode or CONTEXT_PROMPT_OPTIMIZER_WHOLE),
            context_optimizer_concurrency=int(context_prompt_optimizer_concurrency or CONTEXT_PROMPT_OPTIMIZER_DEFAULT_CONCURRENCY),
        )
        result = cls._prepare_segments(
            h3_bundle,
            optimization.prompt,
            items,
            source_audio,
            audio_mode,
            width,
            height,
            aspect_ratio,
            seconds_spec,
            context_length,
            continuity_mode,
            ref_image_size,
        )
        if optimization.marker:
            return {
                "ui": {
                    "auto_optimized_prompt": [optimization.prompt],
                    "auto_optimization_marker": [json.dumps(optimization.marker, sort_keys=True, separators=(",", ":"))],
                },
                "result": result,
            }
        return result


class MiniMaxH3EasyOutput:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "unpack"
    RETURN_TYPES = ("CONDITIONING", "LATENT", "VAE", "VAE", "FLOAT", "AUDIO")
    RETURN_NAMES = ("positive", "latent", "video_vae", "audio_vae", "fps", "driving_audio")
    DESCRIPTION = "Unpack MiniMax H3 conditioning, AV latent, VAEs, FPS, and the optional Digital Human driving audio."

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
            h3_context.source_audio,
        )


class MiniMaxH3EasySegmentRender:
    """Sample a Context Segment chain and emit a post-processing intermediate."""

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "render_chain"
    RETURN_TYPES = (SEGMENT_RESULT_TYPE,)
    RETURN_NAMES = ("segments",)
    DESCRIPTION = (
        "Sample the Context Segment plan with guide continuity. Connect the result to "
        "Segment Decode for a preview or Segment Refine for per-segment second-pass refinement."
    )

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Every queue is a distinct segment run with fresh sampling.
        return float("nan")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "h3_context": ("MINIMAX_H3_CONTEXT",),
                "model": ("MODEL",),
                "sampler": ("SAMPLER",),
                "sigmas": ("SIGMAS",),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 4294967295,
                        "control_after_generate": True,
                    },
                ),
            },
        }

    @staticmethod
    def _sample_one(
        model,
        conditioning,
        latent,
        sampler,
        sigmas,
        seed,
        progress,
        start_step,
        total_steps,
        noise=None,
    ):
        guider = nodes_custom_sampler.Guider_Basic(model)
        guider.set_conds(conditioning)
        if noise is None:
            noise = comfy.sample.prepare_noise(latent["samples"], int(seed))
        step_count = max(1, int(sigmas.shape[-1]) - 1)

        def callback(step, _x0, _x, _total_steps):
            comfy.model_management.throw_exception_if_processing_interrupted()
            progress.update_absolute(start_step + min(step + 1, step_count), total_steps)

        sampled = guider.sample(
            noise,
            latent["samples"],
            sampler,
            sigmas,
            # Context AV modes attach a nested video/audio denoise mask to
            # the latent. Forward it so the sampler can preserve the copied
            # prefix instead of regenerating the whole segment.
            denoise_mask=latent.get("noise_mask"),
            callback=callback,
            disable_pbar=True,
            seed=int(seed),
        )
        progress.update_absolute(start_step + step_count, total_steps)
        return {"samples": sampled}

    @staticmethod
    def _covered_frames(tokens: int) -> int:
        frame_per_token = tuple(getattr(h3, "FRAME_PER_TOKEN", SEGMENT_FRAME_PER_TOKEN))
        return sum(
            int(frame_per_token[index % len(frame_per_token)])
            for index in range(max(0, int(tokens)))
        )

    @classmethod
    def render_chain(cls, h3_context, model, sampler, sigmas, seed):
        plan = getattr(h3_context, "segment_plan", None)
        shots = plan.get("shots") if isinstance(plan, Mapping) else None
        if not shots:
            raise ValueError(
                "Connect the H3 Context output of a MiniMax H3 Easy Context Segments node"
            )
        bundle = plan.get("bundle")
        if not isinstance(bundle, MiniMaxH3Bundle):
            raise ValueError("The segment plan has no MiniMax H3 bundle")
        width = int(plan["width"])
        height = int(plan["height"])
        continuity_mode = str(plan.get("continuity_mode") or CONTEXT_CONTINUITY_LATENT)
        if continuity_mode not in CONTEXT_CONTINUITY_MODES:
            continuity_mode = CONTEXT_CONTINUITY_LATENT
        context_length = _segment_context_frame_count_for_mode(
            plan.get("context_length", SEGMENT_DEFAULT_CONTEXT_FRAMES),
            continuity_mode,
        )
        source_audio = plan.get("source_audio")
        digital_human = str(plan.get("audio_mode") or CONTEXT_AUDIO_GENERATED) == CONTEXT_AUDIO_DIGITAL_HUMAN
        steps_per_shot = max(1, int(sigmas.shape[-1]) - 1)
        total_steps = max(1, len(shots) * steps_per_shot)
        progress = comfy.utils.ProgressBar(total_steps)
        terminal_progress = _H3TerminalProgress("Context Render", len(shots))

        segment_samples = []
        tail_frames = None
        delivered_video_latent = None
        audio_reference = None
        timeline_frame = 0

        for position, shot in enumerate(shots):
            terminal_progress.update(position, f"segment {position + 1} sampling")
            delivery_frames = max(5, int(shot.get("delivery_frames") or 5))
            # Native Add Guide samples a target that starts with the guide
            # prefix. The workflow discards that repeated/noisy prefix before
            # delivering the new segment. Keep the same temporal handoff for
            # RGB Guide; latent/AV modes use the same prefix as their explicit
            # overlapping latent region.
            hidden_prefix_frames = context_length if position else 0
            sample_length = _segment_target_length(delivery_frames, hidden_prefix_frames)
            # The H3 frame grid may add padding at the end of the sampled
            # latent. Delivery below takes exactly the requested new frames
            # after the repeated guide prefix, ignoring grid padding.
            head_frames = hidden_prefix_frames
            prompt_text = str(shot.get("prompt") or "")
            items = list(shot.get("media") or [])
            source_audio_reference = _segment_source_audio_reference(
                bundle,
                source_audio,
                max(0, timeline_frame - head_frames),
                head_frames + delivery_frames,
            ) if source_audio is not None else None
            if digital_human and source_audio_reference is None:
                raise ValueError("Context Segments digital human audio does not cover this segment")
            if items:
                conditioning, latent = _reference_conditioning(
                    bundle, prompt_text, width, height, sample_length,
                    plan.get("ref_image_size"), items, include_audio=not digital_human,
                )
            else:
                conditioning, latent, _sources = _empty_image_conditioning(
                    bundle, prompt_text, width, height, sample_length,
                )
            audio_context_reference = None if digital_human else (
                source_audio_reference if source_audio_reference is not None else audio_reference
            )
            # Match ComfyUI's native Add Guide workflow: RGB Guide carries
            # only the visual tail. An external driving track is already
            # locked into the target AV latent, while generated audio is not
            # used as a second audio guide condition at the same boundary.
            if continuity_mode == CONTEXT_CONTINUITY_GUIDE:
                audio_context_reference = None
            # Keep the node seed user-controlled across every context segment.
            shot_seed = int(seed) % 4294967296
            guides = []
            if (
                delivered_video_latent is not None
                and continuity_mode == CONTEXT_CONTINUITY_LATENT
            ):
                guides, _covered = _segment_context_keyframes_from_latent(
                    delivered_video_latent, context_length,
                )
            elif tail_frames is not None and continuity_mode == CONTEXT_CONTINUITY_GUIDE:
                guides, _covered = _segment_context_keyframes(
                    bundle, tail_frames, width, height, context_length,
                )
            conditioning = _segment_add_context_conditioning(
                conditioning,
                guides,
                h3.temporal_shape(sample_length)[0],
                audio_context_reference,
            )
            if delivered_video_latent is not None and continuity_mode == CONTEXT_CONTINUITY_LATENT:
                latent = _segment_apply_guide_handoff(
                    latent,
                    delivered_video_latent,
                    audio_context_reference,
                    context_length,
                )
            if delivered_video_latent is not None and continuity_mode in CONTEXT_CONTINUITY_AV_MODES:
                latent = _segment_apply_av_prefix(
                    latent,
                    delivered_video_latent,
                    audio_context_reference,
                    context_length,
                    continuity_mode,
                )
            if digital_human:
                latent = _lock_audio_latent(latent, source_audio_reference["audio_latent"])

            sampled = cls._sample_one(
                model, conditioning, latent, sampler, sigmas,
                shot_seed, progress, position * steps_per_shot, total_steps,
            )
            video_stream, audio_stream = _segment_latent_streams(sampled)
            video_prefix = h3.temporal_shape(head_frames)[1] if head_frames else 0
            video_length = h3.temporal_shape(delivery_frames)[1]
            delivered_video_latent = video_stream[:, :, video_prefix:video_prefix + video_length].detach().to("cpu").contiguous()

            if continuity_mode == CONTEXT_CONTINUITY_GUIDE:
                # RGB Guide needs the delivered tail before the next segment is sampled.
                images = nodes.VAEDecode().decode(bundle.video_vae, sampled)[0]
                delivered = images[head_frames:head_frames + delivery_frames].detach().to("cpu").contiguous()
                keep = min(context_length, int(delivered.shape[0]))
                tail_frames = (
                    delivered[-keep:].detach().to("cpu").contiguous()
                    if position + 1 < len(shots)
                    else None
                )
                # Do not retain the whole RGB segment in the intermediate result. The
                # decoder can decode it once more when exporting, keeping chain memory
                # bounded by the current segment and its context tail.
                del images, delivered

            segment_samples.append(
                MiniMaxH3SegmentSample(
                    video_latent=video_stream.detach().to("cpu").contiguous(),
                    audio_latent=audio_stream.detach().to("cpu").contiguous(),
                    head_frames=head_frames,
                    delivery_frames=delivery_frames,
                )
            )
            audio_reference = (
                None
                if source_audio is not None
                else _segment_context_audio_reference(sampled, head_frames + delivery_frames, context_length)
            )
            timeline_frame += delivery_frames
            if continuity_mode != CONTEXT_CONTINUITY_GUIDE:
                # Latent/AV continuity never needs decoded pixels between shots.
                tail_frames = None
            terminal_progress.update(position + 1, f"segment {position + 1} completed")
            del sampled

        terminal_progress.finish()
        return (MiniMaxH3SegmentResult(plan=plan, samples=tuple(segment_samples)),)


class MiniMaxH3EasySegmentRefine:
    """Refine a context chain one segment at a time.

    Each segment rebuilds its own prompt/reference conditioning.  The previous
    refined segment supplies continuity, while the first-pass audio stream is
    kept as the default timeline audio.
    """

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "refine_chain"
    RETURN_TYPES = (SEGMENT_RESULT_TYPE,)
    RETURN_NAMES = ("refined_segments",)
    DESCRIPTION = (
        "Run a resolution-aware second pass per context segment. Each segment keeps its own "
        "prompt and media references, then passes its refined tail to the next segment. "
        "Use tiled_low_vram to sample a high-resolution segment in spatial tiles."
    )

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def _upscale_model_choices(cls) -> list[str]:
        try:
            choices = list(scan_latent_upscaler_models())
            return choices or ["(no latent upscaler models)"]
        except Exception:
            return ["(no latent upscaler models)"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "refine_mode": (["pixel_resize", "latent_upscale"], {"default": "pixel_resize"}),
                "h3_context": ("MINIMAX_H3_CONTEXT",),
                "segments": (SEGMENT_RESULT_TYPE,),
                "model": ("MODEL",),
                "sampler": ("SAMPLER",),
                "sigmas": ("SIGMAS",),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 4294967295,
                        "control_after_generate": True,
                    },
                ),
                "refine_execution": (list(SEGMENT_REFINE_EXECUTION_MODES), {"default": SEGMENT_REFINE_WHOLE}),
                "target_width": ("INT", {"default": 0, "min": 0, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "target_height": ("INT", {"default": 0, "min": 0, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "latent_upscale_model": (cls._upscale_model_choices(),),
                "latent_upscale_scale": ("FLOAT", {"default": 1.3, "min": 1.0, "max": 4.0, "step": 0.1}),
                "latent_upscale_device": (["cuda", "cpu"], {"default": "cuda"}),
                "latent_upscale_precision": (["fp32", "fp16", "bf16"], {"default": "fp16"}),
                "tile_width": ("INT", {"default": 512, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "tile_height": ("INT", {"default": 512, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "tile_overlap": ("INT", {"default": 128, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
                "tile_fade": ("INT", {"default": 32, "min": 0, "max": nodes.MAX_RESOLUTION, "step": 32}),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, refine_mode="pixel_resize", latent_upscale_model=None):
        """Do not validate the hidden latent-model widget for pixel resize.

        ComfyUI validates combo values before execution. A workflow can retain
        an old latent-upscaler filename even after that checkpoint is removed,
        but that value is irrelevant to pixel resize and must not block the run.
        Latent-upscale mode keeps the explicit model requirement below.
        """
        mode = str(refine_mode or "pixel_resize").strip().lower()
        if mode in {"pixel_resize", "pixel resize"}:
            return True
        if mode == "latent_upscale":
            if not latent_upscale_model or str(latent_upscale_model).startswith("("):
                return "Select an H3 latent upscaler model for latent_upscale mode"
            return True
        return f"Unsupported segment refine mode: {refine_mode}"

    @staticmethod
    def _fit_time_tokens(stream: torch.Tensor, wanted: int, time_dim: int) -> torch.Tensor:
        wanted = max(1, int(wanted))
        available = int(stream.shape[time_dim])
        if available <= 0:
            raise ValueError("Segment refine received an empty latent stream")
        if available >= wanted:
            slices = [slice(None)] * stream.ndim
            slices[time_dim] = slice(0, wanted)
            return stream[tuple(slices)].contiguous()
        slices = [slice(None)] * stream.ndim
        slices[time_dim] = slice(available - 1, available)
        last = stream[tuple(slices)]
        repeats = [1] * stream.ndim
        repeats[time_dim] = wanted - available
        return torch.cat([stream, last.repeat(*repeats)], dim=time_dim).contiguous()

    @staticmethod
    def _delivered_streams(sample: MiniMaxH3SegmentSample) -> tuple[torch.Tensor, torch.Tensor]:
        video = sample.video_latent
        audio = sample.audio_latent
        video_prefix = h3.temporal_shape(sample.head_frames)[1] if sample.head_frames else 0
        audio_prefix = h3.temporal_shape(sample.head_frames)[2] if sample.head_frames else 0
        video_length = h3.temporal_shape(sample.delivery_frames)[1]
        audio_length = h3.temporal_shape(sample.delivery_frames)[2]
        video = video[:, :, video_prefix:video_prefix + video_length]
        audio = audio[..., audio_prefix:audio_prefix + audio_length]
        return (
            MiniMaxH3EasySegmentRefine._fit_time_tokens(video, video_length, 2),
            MiniMaxH3EasySegmentRefine._fit_time_tokens(audio, audio_length, 3),
        )

    @classmethod
    def _refine_source_video(
        cls,
        sample: MiniMaxH3SegmentSample,
        head_frames: int,
        delivery_frames: int,
    ) -> torch.Tensor:
        """Keep the hidden temporal prefix while preparing a refine source.

        Pixel/VAE and learned latent resize paths both have temporal receptive
        fields.  Feeding only the delivered body makes every later segment
        look like a new clip at that transform boundary.  Keep the exact
        prefix plus body here, then crop it again after the transform.
        """
        video_prefix = h3.temporal_shape(head_frames)[1] if head_frames else 0
        video_length = h3.temporal_shape(delivery_frames)[1]
        wanted = video_prefix + video_length
        return cls._fit_time_tokens(sample.video_latent, wanted, 2)

    @classmethod
    def _crop_refine_video_body(
        cls,
        video_latent: torch.Tensor,
        head_frames: int,
        delivery_frames: int,
    ) -> torch.Tensor:
        """Remove the temporary refine prefix after a temporal transform."""
        video_prefix = h3.temporal_shape(head_frames)[1] if head_frames else 0
        video_length = h3.temporal_shape(delivery_frames)[1]
        video = cls._fit_time_tokens(video_latent, video_prefix + video_length, 2)
        return video[:, :, video_prefix:video_prefix + video_length].contiguous()

    @staticmethod
    def _decode_video_body(bundle: MiniMaxH3Bundle, video_latent: torch.Tensor) -> torch.Tensor:
        decoded = nodes.VAEDecode().decode(bundle.video_vae, {"samples": video_latent})[0]
        return decoded.detach().to("cpu").contiguous()

    @classmethod
    def _prepare_video_body(
        cls,
        bundle: MiniMaxH3Bundle,
        source_video: torch.Tensor,
        plan: Mapping[str, Any],
        refine_mode: str,
        target_width: int,
        target_height: int,
        latent_upscale_model: str,
        latent_upscale_scale: float,
        latent_upscale_device: str,
        latent_upscale_precision: str,
        head_frames: int,
        delivery_frames: int,
        sampling_model=None,
    ) -> tuple[torch.Tensor, int, int]:
        base_width = int(plan["width"])
        base_height = int(plan["height"])
        if refine_mode == "pixel_resize":
            width = _align_canvas_dimension(target_width or base_width)
            height = _align_canvas_dimension(target_height or base_height)
            images = cls._decode_video_body(bundle, source_video)
            resized = h3._resize(images, width, height, "center")
            encoded = bundle.video_vae.encode(resized)
            if not isinstance(encoded, torch.Tensor) or encoded.ndim != 5:
                raise RuntimeError("Segment refine pixel resize did not produce a video latent")
            return (
                cls._crop_refine_video_body(encoded, head_frames, delivery_frames)
                .detach()
                .to("cpu")
                .contiguous(),
                width,
                height,
            )

        if refine_mode != "latent_upscale":
            raise ValueError(f"Unsupported segment refine mode: {refine_mode}")
        if not latent_upscale_model or str(latent_upscale_model).startswith("("):
            raise ValueError("Select an H3 latent upscaler model for latent_upscale mode")
        if str(latent_upscale_device).lower() in {"cuda", "rocm"} and sampling_model is not None:
            # The H3 denoiser is not needed during learned latent upscaling.
            # Let ComfyUI reload it for sampling instead of holding both models
            # in VRAM at the same time.
            try:
                comfy.model_management.unload_model_and_clones(
                    sampling_model,
                    unload_additional_models=False,
                )
                comfy.model_management.soft_empty_cache()
            except Exception:
                pass
        # The built-in 3D node keeps the segment path independent from any
        # separately installed latent-upscaler custom node.
        result = MiniMaxH3EasyLatentUpscaler3D.execute(
            {"samples": source_video},
            str(latent_upscale_model),
            {"mode": "scale by multiplier", "scale": float(latent_upscale_scale)},
            32,
            True,
            str(latent_upscale_device),
            str(latent_upscale_precision),
        )[0]
        upscaled = result.get("samples") if isinstance(result, Mapping) else None
        if not isinstance(upscaled, torch.Tensor) or upscaled.ndim != 5:
            raise RuntimeError("H3 latent upscaler returned an invalid video latent")
        upscaled = cls._crop_refine_video_body(upscaled, head_frames, delivery_frames)
        return upscaled.detach().to("cpu").contiguous(), int(upscaled.shape[-1]) * 16, int(upscaled.shape[-2]) * 16

    @staticmethod
    def _audio_reference_from_previous(
        video_body: torch.Tensor | None,
        audio_body: torch.Tensor | None,
        delivery_frames: int,
        context_frames: int,
    ) -> Mapping[str, Any] | None:
        if video_body is None or audio_body is None:
            return None
        try:
            return _segment_context_audio_reference(
                _segment_pack_latent(video_body, audio_body),
                int(delivery_frames),
                int(context_frames),
            )
        except Exception:
            return None

    @staticmethod
    def _build_base_latent(
        target_width: int,
        target_height: int,
        sample_length: int,
        delivery_frames: int,
        head_frames: int,
        video_body: torch.Tensor,
        audio_body: torch.Tensor,
    ) -> dict[str, Any]:
        latent, _frame_count = h3._empty_av_latent(
            target_width, target_height, sample_length,
        )
        video, audio = _segment_latent_streams(latent)
        video = video.detach().to("cpu").clone()
        audio = audio.detach().to("cpu").clone()
        video_prefix = h3.temporal_shape(head_frames)[1] if head_frames else 0
        audio_prefix = h3.temporal_shape(head_frames)[2] if head_frames else 0
        video_length = h3.temporal_shape(delivery_frames)[1]
        audio_length = h3.temporal_shape(delivery_frames)[2]
        video[:, :, video_prefix:video_prefix + video_length] = MiniMaxH3EasySegmentRefine._fit_time_tokens(
            video_body, video_length, 2,
        ).to(dtype=video.dtype)
        audio[..., audio_prefix:audio_prefix + audio_length] = MiniMaxH3EasySegmentRefine._fit_time_tokens(
            audio_body, audio_length, 3,
        ).to(dtype=audio.dtype)
        return _segment_pack_latent(video, audio)

    @staticmethod
    def _tiled_pass_count(width: int, height: int, tile_width: int, tile_height: int, tile_overlap: int) -> int:
        width_latent = max(1, int(width) // 16)
        height_latent = max(1, int(height) // 16)
        tile_width_latent = max(1, int(tile_width) // 16)
        tile_height_latent = max(1, int(tile_height) // 16)
        overlap_latent = max(0, int(tile_overlap) // 16)
        return max(
            1,
            len(_segment_tile_axis(height_latent, tile_height_latent, overlap_latent))
            * len(_segment_tile_axis(width_latent, tile_width_latent, overlap_latent)),
        )

    @classmethod
    def _planned_refine_size(
        cls,
        plan: Mapping[str, Any],
        first_pass: MiniMaxH3SegmentSample,
        refine_mode: str,
        target_width: int,
        target_height: int,
        latent_upscale_scale: float,
    ) -> tuple[int, int]:
        """Resolve the canvas size without loading a model, for progress planning."""
        base_width = int(plan["width"])
        base_height = int(plan["height"])
        if refine_mode == "pixel_resize":
            return (
                _align_canvas_dimension(target_width or base_width),
                _align_canvas_dimension(target_height or base_height),
            )
        if refine_mode != "latent_upscale":
            raise ValueError(f"Unsupported segment refine mode: {refine_mode}")
        source_video, _source_audio = cls._delivered_streams(first_pass)
        scale = float(latent_upscale_scale)
        grid = 32
        latent_width = max(1, int(round(round(source_video.shape[-1] * 16 * scale / grid) * grid / 16)))
        latent_height = max(1, int(round(round(source_video.shape[-2] * 16 * scale / grid) * grid / 16)))
        return latent_width * 16, latent_height * 16

    @staticmethod
    def _tiled_sample(
        model,
        conditioning,
        latent: Mapping[str, Any],
        sampler,
        sigmas,
        seed: int,
        progress,
        start_step: int,
        total_steps: int,
        tile_width: int,
        tile_height: int,
        tile_overlap: int,
        tile_fade: int,
    ) -> dict[str, Any]:
        """Second-pass one context segment in spatial tiles without repeating noise.

        The context node already makes each user segment the temporal work unit.
        Here we only tile its spatial latent, crop full-canvas context keyframes
        with it, and use crop coordinates from one full noise field. This keeps
        segment-specific prompt/media conditioning intact while bounding VRAM.
        """
        for name, value in (
            ("tile_width", tile_width),
            ("tile_height", tile_height),
            ("tile_overlap", tile_overlap),
            ("tile_fade", tile_fade),
        ):
            if int(value) <= 0 and name != "tile_fade":
                raise ValueError(f"{name} must be positive for tiled_low_vram refinement")
            if int(value) % 32:
                raise ValueError(f"{name} must be a multiple of 32 pixels for tiled_low_vram refinement")
        if int(tile_overlap) >= int(tile_width) or int(tile_overlap) >= int(tile_height):
            raise ValueError("tile_overlap must be smaller than both tile_width and tile_height")
        if int(tile_fade) > int(tile_overlap):
            raise ValueError("tile_fade must not exceed tile_overlap")

        source_video, source_audio = _segment_latent_streams(latent)
        source_video = source_video.detach().to("cpu").contiguous()
        source_audio = source_audio.detach().to("cpu").contiguous()
        noise = comfy.sample.prepare_noise(latent["samples"], int(seed))
        noise_video, noise_audio = _segment_av_streams(
            noise,
            "Could not prepare an H3 AV noise field for tiled refinement",
        )
        noise_video = noise_video.detach().to("cpu").contiguous()
        noise_audio = noise_audio.detach().to("cpu").contiguous()

        source_video_mask, _source_audio_mask = _segment_noise_mask_streams(latent)
        if source_video_mask is None:
            source_video_mask = torch.ones(
                (source_video.shape[0], 1, source_video.shape[2], source_video.shape[3], source_video.shape[4]),
                dtype=source_video.dtype,
                device=source_video.device,
            )
        else:
            source_video_mask = source_video_mask.detach().to(
                device=source_video.device,
                dtype=source_video.dtype,
            ).contiguous()
        # Audio is a timeline asset in context refinement. It conditions video
        # sampling but is not regenerated separately for every spatial tile.
        source_audio_mask = torch.zeros(
            (source_audio.shape[0], 1, source_audio.shape[2], source_audio.shape[3]),
            dtype=source_audio.dtype,
            device=source_audio.device,
        )

        tile_width_latent = max(1, int(tile_width) // 16)
        tile_height_latent = max(1, int(tile_height) // 16)
        overlap_latent = max(0, int(tile_overlap) // 16)
        fade_latent = max(0, int(tile_fade) // 16)
        rows = _segment_tile_axis(source_video.shape[-2], tile_height_latent, overlap_latent)
        columns = _segment_tile_axis(source_video.shape[-1], tile_width_latent, overlap_latent)
        assembled = source_video.clone()
        step_count = max(1, int(sigmas.shape[-1]) - 1)
        tile_index = 0

        for top, current_height, top_overlap in rows:
            for left, current_width, left_overlap in columns:
                tile_video = source_video[
                    :, :, :, top:top + current_height, left:left + current_width
                ].clone()
                previous = assembled[
                    :, :, :, top:top + current_height, left:left + current_width
                ].clone()
                if top_overlap:
                    tile_video[:, :, :, :top_overlap, :] = previous[:, :, :, :top_overlap, :]
                if left_overlap:
                    tile_video[:, :, :, :, :left_overlap] = previous[:, :, :, :, :left_overlap]

                seam_blend = _segment_tile_blend(
                    current_height,
                    current_width,
                    top_overlap,
                    left_overlap,
                    fade_latent,
                    device=source_video.device,
                    dtype=source_video.dtype,
                )
                tile_video_mask = source_video_mask[
                    :, :, :, top:top + current_height, left:left + current_width
                ] * seam_blend
                tile_noise = _segment_pack_latent(
                    noise_video[:, :, :, top:top + current_height, left:left + current_width],
                    noise_audio,
                )["samples"]
                tile_latent = _segment_pack_av(
                    tile_video,
                    source_audio,
                    tile_video_mask,
                    source_audio_mask,
                )
                tile_conditioning = _segment_crop_keyframe_conditioning(
                    conditioning,
                    source_video.shape[-2],
                    source_video.shape[-1],
                    top,
                    left,
                    current_height,
                    current_width,
                )
                sampled = MiniMaxH3EasySegmentRender._sample_one(
                    model,
                    tile_conditioning,
                    tile_latent,
                    sampler,
                    sigmas,
                    seed,
                    progress,
                    start_step + tile_index * step_count,
                    total_steps,
                    noise=tile_noise,
                )
                sampled_video, _sampled_audio = _segment_latent_streams(sampled)
                sampled_video = sampled_video.detach().to("cpu").contiguous()
                assembled[
                    :, :, :, top:top + current_height, left:left + current_width
                ] = previous * (1.0 - seam_blend) + sampled_video * seam_blend
                tile_index += 1
                del sampled

        return _segment_pack_latent(assembled, source_audio)

    @classmethod
    def refine_chain(
        cls,
        h3_context,
        segments,
        model,
        sampler,
        sigmas,
        seed,
        refine_mode,
        refine_execution,
        target_width,
        target_height,
        latent_upscale_model,
        latent_upscale_scale,
        latent_upscale_device,
        latent_upscale_precision,
        tile_width,
        tile_height,
        tile_overlap,
        tile_fade,
    ):
        if not isinstance(h3_context, MiniMaxH3Context):
            raise ValueError("Connect the H3 Context output from MiniMax H3 Easy Context Segments")
        if not isinstance(segments, MiniMaxH3SegmentResult):
            raise ValueError("Connect the first-pass output from MiniMax H3 Easy Segment Sample")
        plan = segments.plan
        if not isinstance(plan, Mapping) or not isinstance(plan.get("bundle"), MiniMaxH3Bundle):
            raise ValueError("The segment result has no usable MiniMax H3 bundle")
        bundle = plan["bundle"]
        shots = list(plan.get("shots") or [])
        if len(shots) != len(segments.samples):
            raise ValueError("Segment refine plan and segment result contain different segment counts")
        continuity_mode = str(plan.get("continuity_mode") or CONTEXT_CONTINUITY_LATENT)
        if continuity_mode not in CONTEXT_CONTINUITY_MODES:
            continuity_mode = CONTEXT_CONTINUITY_LATENT
        context_length = _segment_context_frame_count_for_mode(
            plan.get("context_length", SEGMENT_DEFAULT_CONTEXT_FRAMES),
            continuity_mode,
        )
        source_audio = plan.get("source_audio")
        digital_human = str(plan.get("audio_mode") or CONTEXT_AUDIO_GENERATED) == CONTEXT_AUDIO_DIGITAL_HUMAN
        execution = str(refine_execution or SEGMENT_REFINE_WHOLE)
        if execution not in SEGMENT_REFINE_EXECUTION_MODES:
            raise ValueError(f"Unsupported segment refine execution mode: {execution}")
        steps_per_segment = max(1, int(sigmas.shape[-1]) - 1)
        planned_passes = len(shots)
        if execution == SEGMENT_REFINE_TILED:
            planned_passes = sum(
                cls._tiled_pass_count(
                    *cls._planned_refine_size(
                        plan,
                        first_pass,
                        str(refine_mode),
                        int(target_width),
                        int(target_height),
                        float(latent_upscale_scale),
                    ),
                    int(tile_width),
                    int(tile_height),
                    int(tile_overlap),
                )
                for first_pass in segments.samples
            )
        total_steps = max(1, planned_passes * steps_per_segment)
        progress = comfy.utils.ProgressBar(total_steps)
        terminal_progress = _H3TerminalProgress("Segment Refine", len(shots))
        completed_steps = 0
        refined_samples = []
        previous_video = None
        previous_audio = None
        previous_delivery_frames = 0
        previous_tail_frames = None
        timeline_frame = 0

        for position, (shot, first_pass) in enumerate(zip(shots, segments.samples)):
            terminal_progress.update(
                position,
                f"segment {position + 1} {'tiled refine' if execution == SEGMENT_REFINE_TILED else 'refine'}",
            )
            delivery_frames = max(5, int(shot.get("delivery_frames") or first_pass.delivery_frames))
            # The native Guide workflow samples the repeated guide prefix and
            # crops it from the delivered segment after sampling.
            head_frames = context_length if position else 0
            sample_length = _segment_target_length(delivery_frames, head_frames)
            _, source_audio_latent = cls._delivered_streams(first_pass)
            source_video = cls._refine_source_video(first_pass, head_frames, delivery_frames)
            video_body, resolved_width, resolved_height = cls._prepare_video_body(
                bundle,
                source_video,
                plan,
                str(refine_mode),
                int(target_width),
                int(target_height),
                str(latent_upscale_model),
                float(latent_upscale_scale),
                str(latent_upscale_device),
                str(latent_upscale_precision),
                head_frames,
                delivery_frames,
                model,
            )

            prompt_text = str(shot.get("prompt") or "")
            items = list(shot.get("media") or [])
            if items:
                conditioning, _unused_latent = _reference_conditioning(
                    bundle,
                    prompt_text,
                    resolved_width,
                    resolved_height,
                    sample_length,
                    plan.get("ref_image_size"),
                    items,
                    include_audio=not digital_human,
                )
            else:
                conditioning, _unused_latent, _sources = _empty_image_conditioning(
                    bundle,
                    prompt_text,
                    resolved_width,
                    resolved_height,
                    sample_length,
                )
            latent = cls._build_base_latent(
                resolved_width,
                resolved_height,
                sample_length,
                delivery_frames,
                head_frames,
                video_body,
                source_audio_latent,
            )

            source_audio_reference = _segment_source_audio_reference(
                bundle,
                source_audio,
                max(0, timeline_frame - head_frames),
                head_frames + delivery_frames,
            ) if source_audio is not None else None
            if digital_human and source_audio_reference is None:
                raise ValueError("Context Segments digital human audio does not cover this segment")
            previous_audio_reference = cls._audio_reference_from_previous(
                previous_video,
                previous_audio,
                previous_delivery_frames,
                context_length,
            ) if position else None
            audio_reference = None if digital_human else (source_audio_reference or previous_audio_reference)
            # Keep RGB Guide equivalent to native MiniMaxH3AddGuide: the
            # carried condition is visual-only. Driving audio remains locked
            # in the AV latent itself and generated audio is not added as a
            # second boundary guide.
            if continuity_mode == CONTEXT_CONTINUITY_GUIDE:
                audio_reference = None

            guides = []
            if previous_video is not None and continuity_mode == CONTEXT_CONTINUITY_LATENT:
                guides, _covered = _segment_context_keyframes_from_latent(
                    previous_video, context_length,
                )
            elif previous_tail_frames is not None and continuity_mode == CONTEXT_CONTINUITY_GUIDE:
                guides, _covered = _segment_context_keyframes(
                    bundle,
                    previous_tail_frames,
                    resolved_width,
                    resolved_height,
                    context_length,
                )
            conditioning = _segment_add_context_conditioning(
                conditioning,
                guides,
                h3.temporal_shape(sample_length)[0],
                audio_reference,
            )
            if previous_video is not None and continuity_mode in (
                CONTEXT_CONTINUITY_LATENT,
                CONTEXT_CONTINUITY_GUIDE,
            ):
                latent = _segment_apply_guide_handoff(
                    latent,
                    previous_video,
                    audio_reference,
                    context_length,
                )
            if previous_video is not None and continuity_mode in CONTEXT_CONTINUITY_AV_MODES:
                latent = _segment_apply_av_prefix(
                    latent,
                    previous_video,
                    audio_reference,
                    context_length,
                    continuity_mode,
                )
            if digital_human:
                latent = _lock_audio_latent(latent, source_audio_reference["audio_latent"])

            shot_seed = int(seed) % 4294967296
            if execution == SEGMENT_REFINE_TILED:
                sampled = cls._tiled_sample(
                    model,
                    conditioning,
                    latent,
                    sampler,
                    sigmas,
                    shot_seed,
                    progress,
                    completed_steps,
                    total_steps,
                    int(tile_width),
                    int(tile_height),
                    int(tile_overlap),
                    int(tile_fade),
                )
                sampling_passes = cls._tiled_pass_count(
                    resolved_width,
                    resolved_height,
                    int(tile_width),
                    int(tile_height),
                    int(tile_overlap),
                )
            else:
                sampled = MiniMaxH3EasySegmentRender._sample_one(
                    model,
                    conditioning,
                    latent,
                    sampler,
                    sigmas,
                    shot_seed,
                    progress,
                    completed_steps,
                    total_steps,
                )
                sampling_passes = 1
            completed_steps += sampling_passes * steps_per_segment
            sampled_video, _sampled_audio = _segment_latent_streams(sampled)
            video_prefix = h3.temporal_shape(head_frames)[1] if head_frames else 0
            video_length = h3.temporal_shape(delivery_frames)[1]
            delivered_video = sampled_video[:, :, video_prefix:video_prefix + video_length].detach().to("cpu").contiguous()
            input_video, input_audio = _segment_latent_streams(latent)
            audio_prefix = h3.temporal_shape(head_frames)[2] if head_frames else 0
            audio_length = h3.temporal_shape(delivery_frames)[2]
            refined_audio = input_audio.detach().to("cpu").clone()
            if isinstance(audio_reference, Mapping) and audio_prefix > 0:
                reference_audio = audio_reference.get("audio_latent")
                if isinstance(reference_audio, torch.Tensor):
                    reference_audio = cls._fit_time_tokens(reference_audio, audio_prefix, 3)
                    refined_audio[..., :audio_prefix] = reference_audio.to(dtype=refined_audio.dtype)
            delivered_audio = refined_audio[..., audio_prefix:audio_prefix + audio_length].detach().to("cpu").contiguous()

            if continuity_mode == CONTEXT_CONTINUITY_GUIDE:
                decoded_full = cls._decode_video_body(bundle, sampled_video)
                delivered_tail = decoded_full[head_frames:head_frames + delivery_frames].contiguous()
                keep = min(context_length, int(delivered_tail.shape[0]))
                previous_tail_frames = (
                    delivered_tail[-keep:].detach().to("cpu").contiguous()
                    if position + 1 < len(shots)
                    else None
                )
                # The next segment only needs the tail. Do not retain the full decoded
                # RGB segment in every sample; Segment Decode will stream-decode it.
                del decoded_full, delivered_tail
            else:
                previous_tail_frames = None

            refined_samples.append(
                MiniMaxH3SegmentSample(
                    video_latent=sampled_video.detach().to("cpu").contiguous(),
                    audio_latent=refined_audio,
                    head_frames=head_frames,
                    delivery_frames=delivery_frames,
                )
            )
            previous_video = delivered_video
            previous_audio = delivered_audio
            previous_delivery_frames = delivery_frames
            timeline_frame += delivery_frames
            terminal_progress.update(position + 1, f"segment {position + 1} completed")
            del sampled

        refined_plan = dict(plan)
        refined_plan["refine_mode"] = str(refine_mode)
        refined_plan["refine_execution"] = execution
        if execution == SEGMENT_REFINE_TILED:
            refined_plan["tile_width"] = int(tile_width)
            refined_plan["tile_height"] = int(tile_height)
            refined_plan["tile_overlap"] = int(tile_overlap)
            refined_plan["tile_fade"] = int(tile_fade)
        refined_plan["refine_width"] = int(resolved_width) if refined_samples else int(plan["width"])
        refined_plan["refine_height"] = int(resolved_height) if refined_samples else int(plan["height"])
        refined_plan["refine_stage"] = int(plan.get("refine_stage") or 0) + 1
        terminal_progress.finish()
        return (MiniMaxH3SegmentResult(plan=refined_plan, samples=tuple(refined_samples)),)


class MiniMaxH3EasySegmentDecode:
    """Decode delivered segments through a bounded-memory streaming file."""

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "decode_segments"
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("preview",)
    DESCRIPTION = "Decode Context Segment frames one segment at a time and return the complete VIDEO with muxed audio."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "segments": (SEGMENT_RESULT_TYPE,),
            }
        }

    @classmethod
    def _decode_streaming(cls, segments, bundle, source_audio, progress, terminal_progress):
        """Decode one segment at a time and feed a persistent FFmpeg encoder."""
        if not segments.samples:
            raise ValueError("The segment result contains no delivered video frames")

        temp_root = folder_paths.get_temp_directory()
        stream_dir = tempfile.mkdtemp(prefix="minimax_h3_segments_", dir=temp_root)
        raw_video_path = os.path.join(stream_dir, "video.mp4")
        raw_audio_path = os.path.join(stream_dir, "audio.f32le")
        final_video_path = os.path.join(stream_dir, "final.mp4")
        video_process = None
        audio_writer = None
        audio_channels = 0
        audio_sample_rate = 0
        preview_frame = None
        delivered_total = sum(sample.delivery_frames for sample in segments.samples)

        def start_video(frame: torch.Tensor):
            height, width = int(frame.shape[0]), int(frame.shape[1])
            args = [
                _segment_ffmpeg_path(), "-y", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "rgb24",
                "-s", f"{width}x{height}", "-r", str(h3.FPS), "-i", "-",
                "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", raw_video_path,
            ]
            return subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        try:
            for index, sample in enumerate(segments.samples, start=1):
                terminal_progress.update(index - 1, f"segment {index} decoding")
                latent = _segment_pack_latent(sample.video_latent, sample.audio_latent)
                decoded_full = None
                delivered = None
                try:
                    decoded_full = nodes.VAEDecode().decode(bundle.video_vae, latent)[0]
                    delivered = decoded_full[
                        sample.head_frames:sample.head_frames + sample.delivery_frames
                    ].detach().to("cpu").contiguous()
                    if preview_frame is None:
                        preview_frame = delivered[:1].detach().to("cpu").contiguous()
                    if video_process is None:
                        video_process = start_video(delivered[0])
                    for frame in delivered:
                        video_process.stdin.write(_segment_rgb_frame_bytes(frame))
                finally:
                    del decoded_full
                    del delivered

                if source_audio is None:
                    audio = nodes_audio.vae_decode_audio(bundle.audio_vae, latent)
                    trimmed = _segment_trim_audio(audio, sample.head_frames, sample.delivery_frames)
                    if trimmed is not None:
                        if audio_writer is None:
                            audio_writer = _H3PCMWriter(raw_audio_path)
                        audio_writer.write(trimmed)
                        audio_channels = audio_writer._channels
                        audio_sample_rate = audio_writer.sample_rate
                    del audio
                del latent
                gc.collect()
                progress.update_absolute(index, max(1, len(segments.samples)))
                terminal_progress.update(index, f"segment {index} completed")

            if video_process is None or preview_frame is None:
                raise ValueError("The segment result produced no decodable video frames")
            video_process.stdin.close()
            stderr = video_process.stderr.read()
            return_code = video_process.wait()
            if return_code != 0:
                detail = stderr.decode("utf-8", "replace").strip()
                raise RuntimeError(f"Streaming Context Segment video encode failed: {detail}")
            video_process = None

            if source_audio is not None:
                trimmed_source = _segment_trim_audio(source_audio, 0, delivered_total)
                if trimmed_source is not None:
                    audio_writer = _H3PCMWriter(raw_audio_path)
                    audio_writer.write(trimmed_source)
                    audio_channels = audio_writer._channels
                    audio_sample_rate = audio_writer.sample_rate
            if audio_writer is not None:
                audio_writer.close()
                audio_writer = None

            output_path = raw_video_path
            if os.path.isfile(raw_audio_path) and os.path.getsize(raw_audio_path) > 0:
                if not audio_channels or not audio_sample_rate:
                    raise RuntimeError("Unable to determine streamed audio format")
                mux_args = [
                    _segment_ffmpeg_path(), "-y", "-loglevel", "error",
                    "-i", raw_video_path,
                    "-f", "f32le", "-ar", str(audio_sample_rate), "-ac", str(audio_channels),
                    "-i", raw_audio_path,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-c:a", "aac", "-t", f"{delivered_total / float(h3.FPS):.6f}",
                    "-movflags", "+faststart", final_video_path,
                ]
                mux = subprocess.run(mux_args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if mux.returncode != 0:
                    detail = mux.stderr.decode("utf-8", "replace").strip()
                    raise RuntimeError(f"Streaming Context Segment audio mux failed: {detail}")
                output_path = final_video_path

            stream_video = InputImpl.VideoFromFile(output_path)
            setattr(stream_video, "_h3_stream_temp_dir", stream_dir)
            weakref.finalize(stream_video, _segment_cleanup_temp_dir, stream_dir)
            return (stream_video,)
        except Exception:
            if video_process is not None:
                try:
                    video_process.kill()
                    video_process.wait()
                except Exception:
                    pass
            if audio_writer is not None:
                audio_writer.close()
            _segment_cleanup_temp_dir(stream_dir)
            raise

    @classmethod
    def decode_segments(cls, segments):
        if not isinstance(segments, MiniMaxH3SegmentResult):
            raise ValueError("Connect the segments output from MiniMax H3 Easy Segment Sample")
        plan = segments.plan
        bundle = plan.get("bundle") if isinstance(plan, Mapping) else None
        if not isinstance(bundle, MiniMaxH3Bundle):
            raise ValueError("The segment result has no MiniMax H3 bundle")
        source_audio = plan.get("source_audio")
        progress = comfy.utils.ProgressBar(max(1, len(segments.samples)))
        terminal_progress = _H3TerminalProgress("Segment Decode", len(segments.samples))
        result = cls._decode_streaming(segments, bundle, source_audio, progress, terminal_progress)
        terminal_progress.finish()
        return result


class MiniMaxH3EasyAspectRatio:
    """Expose Easy's resolved aspect ratio for downstream resolution controls."""

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "extract"
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("aspect_ratio",)
    DESCRIPTION = "Keep downstream resolution selectors aligned with MiniMax H3 Easy without copying width or height."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "h3_context": ("MINIMAX_H3_CONTEXT",),
            },
        }

    @staticmethod
    def extract(h3_context):
        if not isinstance(h3_context, MiniMaxH3Context):
            raise ValueError("Connect the H3 Context output from a MiniMax H3 Easy node")
        try:
            return (ASPECT_SELECTOR_LABELS[h3_context.aspect_ratio],)
        except KeyError as exc:
            raise ValueError(f"Unsupported MiniMax H3 aspect ratio: {h3_context.aspect_ratio}") from exc


class MiniMaxH3EasySecondPassConditioning:
    """Rebuild resolution-bound keyframes for a second-pass video latent."""

    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "rebuild"
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("second_pass_positive",)
    DESCRIPTION = "Re-encode I2V/FL2V keyframes at the second-pass resolution while preserving text and reference-media conditioning."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "h3_context": ("MINIMAX_H3_CONTEXT",),
                "second_pass_video_latent": ("LATENT",),
            },
        }

    @staticmethod
    def _target_dimensions(second_pass_video_latent):
        if not isinstance(second_pass_video_latent, Mapping):
            raise ValueError("Connect the video-only LATENT produced by the second-pass VAE Encode node")
        samples = second_pass_video_latent.get("samples")
        if not isinstance(samples, torch.Tensor) or samples.ndim != 5:
            raise ValueError("Second-pass input must be a video-only LATENT tensor with shape [B, C, T, H, W]")
        if samples.shape[1] != 24:
            raise ValueError("Connect the 24-channel video LATENT before Concat AV Latent, not the combined AV latent")
        return int(samples.shape[-1]) * 16, int(samples.shape[-2]) * 16, samples.shape[-2:]

    @classmethod
    def rebuild(cls, h3_context, second_pass_video_latent):
        if not isinstance(h3_context, MiniMaxH3Context):
            raise ValueError("Connect the H3 Context output from a MiniMax H3 Easy node")

        conditioning = node_helpers.conditioning_set_values(h3_context.conditioning, {})
        if not h3_context.keyframe_sources:
            return (conditioning,)

        target_width, target_height, target_latent_shape = cls._target_dimensions(second_pass_video_latent)
        keyframes = []
        for source in h3_context.keyframe_sources:
            if not isinstance(source.image, torch.Tensor) or source.image.ndim != 4:
                raise ValueError("The original MiniMax H3 keyframe source is unavailable; run the Easy node again")
            resized = h3._resize(source.image[:1], target_width, target_height, "center")
            latent = h3_context.video_vae.encode(resized)
            if not isinstance(latent, torch.Tensor) or latent.ndim != 5 or latent.shape[-2:] != target_latent_shape:
                raise ValueError(
                    "The rebuilt MiniMax H3 keyframe does not match the second-pass video latent resolution"
                )
            keyframes.append({
                "resolved_frame_index": source.resolved_frame_index,
                "latent": latent,
            })

        conditioning = node_helpers.conditioning_set_values(conditioning, {"minimax_keyframes": keyframes})
        return (conditioning,)


_register_prompt_optimizer_route_when_ready()


NODE_CLASS_MAPPINGS = {
    "MiniMaxH3EasyLoader": MiniMaxH3EasyLoader,
    "MiniMaxH3EasyModelAdapter": MiniMaxH3EasyModelAdapter,
    "MiniMaxH3EasyMediaLoader": MiniMaxH3EasyMediaLoader,
    "MiniMaxH3EasyMediaBridge": MiniMaxH3EasyMediaBridge,
    "MiniMaxH3Easy": MiniMaxH3Easy,
    "MiniMaxH3EasyContextSegments": MiniMaxH3EasyContextSegments,
    "MiniMaxH3EasyOutput": MiniMaxH3EasyOutput,
    "MiniMaxH3EasySegmentRender": MiniMaxH3EasySegmentRender,
    "MiniMaxH3EasySegmentRefine": MiniMaxH3EasySegmentRefine,
    "MiniMaxH3EasySegmentDecode": MiniMaxH3EasySegmentDecode,
    "MiniMaxH3EasyAspectRatio": MiniMaxH3EasyAspectRatio,
    "MiniMaxH3EasySecondPassConditioning": MiniMaxH3EasySecondPassConditioning,
}
