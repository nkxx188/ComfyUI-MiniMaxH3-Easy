"""A compact MiniMax H3 entry point for ComfyUI.

The node intentionally keeps the graph contract small: one loader bundle, one
mode-aware conditioning node, and standard ComfyUI outputs for the sampler
chain. The browser extension supplies the ordered virtual media inputs.
"""

from __future__ import annotations

import math
import os
import re
import sys
import threading
import base64
import asyncio
import json
import mimetypes
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import torch
import torchaudio

import comfy.model_management
import folder_paths
import node_helpers
import nodes
from comfy_extras import nodes_minimax_h3 as h3


MODE_IMAGE = "image"
MODE_REFERENCE = "reference"
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
MAX_MEDIA = 15
MAX_IMAGES = 9
MAX_VIDEOS = 3
MAX_AUDIOS = 3
MIN_SECONDS = 0.2
MAX_SECONDS = 30.0
PROMPT_GUIDES_DIR = os.path.join(os.path.dirname(__file__), "prompt_guides")
PROMPT_GUIDE_MANIFEST = os.path.join(PROMPT_GUIDES_DIR, "manifest.json")
PROMPT_OPTIMIZER_TIMEOUT_SECONDS = 600
PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS = 50000
PROMPT_OPTIMIZER_CONFIG_VERSION = 1
PROMPT_OPTIMIZER_CONFIG_DEFAULTS = {
    "version": PROMPT_OPTIMIZER_CONFIG_VERSION,
    "api_format": "openai",
    "api_url": "",
    "api_key": "",
    "model": "",
    "read_media": False,
}


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


_PROMPT_OPTIMIZER_CONFIG_LOCK = threading.RLock()
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
    if general.get("base_reference") and mode != MODE_REFERENCE:
        blocks.append("=== H3 BASE REFERENCE GUIDE ===\n" + _read_prompt_guide_text(str(general["base_reference"])))
    if general.get("ref_reference") and mode == MODE_REFERENCE:
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


def _prompt_optimizer_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "prompt_optimizer.json")


def _normalize_prompt_optimizer_config(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = value if isinstance(value, Mapping) else {}
    api_format = str(source.get("api_format") or "openai").strip().lower()
    if api_format not in {"openai", "responses", "gemini"}:
        api_format = "openai"
    read_media = source.get("read_media", False)
    if isinstance(read_media, str):
        read_media = read_media.strip().lower() in {"1", "true", "yes", "on"}
    return {
        "version": PROMPT_OPTIMIZER_CONFIG_VERSION,
        "api_format": api_format,
        "api_url": str(source.get("api_url") or "").strip(),
        "api_key": str(source.get("api_key") or ""),
        "model": str(source.get("model") or "").strip(),
        "read_media": bool(read_media),
    }


def _read_prompt_optimizer_config() -> dict[str, Any]:
    path = _prompt_optimizer_config_path()
    with _PROMPT_OPTIMIZER_CONFIG_LOCK:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
            return dict(PROMPT_OPTIMIZER_CONFIG_DEFAULTS)
    return _normalize_prompt_optimizer_config(payload)


def _write_prompt_optimizer_config(value: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = _normalize_prompt_optimizer_config(value)
    path = _prompt_optimizer_config_path()
    directory = os.path.dirname(path)
    temporary_path = ""
    with _PROMPT_OPTIMIZER_CONFIG_LOCK:
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=".prompt_optimizer.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = handle.name
                json.dump(normalized, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary_path, path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    pass
    return normalized


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
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, Mapping):
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


def _optimizer_http_json(api_url: str, api_key: str, model: str, api_format: str, system_prompt: str, user_prompt: str, media_parts: list[dict[str, Any]] | None = None) -> str:
    url = _normalize_optimizer_url(api_url, api_format, model)
    media_parts = list(media_parts or [])
    if api_format == "gemini":
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
            "generationConfig": {"temperature": 0.35, "maxOutputTokens": PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS},
        }
    elif api_format == "responses":
        headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": f"Bearer {api_key}"}
        user_content: list[dict[str, Any]] = [{"type": "input_text", "text": user_prompt}]
        user_content.extend(media_parts)
        payload = {
            "model": model,
            "instructions": system_prompt,
            "input": [{"role": "user", "content": user_content}],
            "store": False,
            "stream": False,
            "temperature": 0.35,
            "max_output_tokens": PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS,
        }
    else:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        content: str | list[dict[str, Any]]
        if media_parts:
            content = [{"type": "text", "text": user_prompt}, *media_parts]
        else:
            content = user_prompt
        payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": content}], "stream": False, "temperature": 0.35, "max_tokens": PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS}
    request = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=PROMPT_OPTIMIZER_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Prompt optimization API error ({exc.code}): {detail[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Prompt optimization request failed: {exc.reason}") from exc
    if api_format == "gemini":
        candidates = data.get("candidates") if isinstance(data, dict) else None
        if not isinstance(candidates, list) or not candidates:
            feedback = data.get("promptFeedback") if isinstance(data, dict) else None
            reason = feedback.get("blockReason") if isinstance(feedback, dict) else None
            detail = f": {reason}" if reason else ""
            raise RuntimeError(f"Gemini API returned no candidates{detail}")
        candidate = candidates[0] if isinstance(candidates[0], dict) else {}
        parts = candidate.get("content", {}).get("parts", []) if isinstance(candidate.get("content"), dict) else []
        text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("text") is not None)
        if not text.strip():
            finish_reason = candidate.get("finishReason") or candidate.get("finish_reason") or "unknown"
            raise RuntimeError(f"Gemini API returned no text (finish reason: {finish_reason})")
    elif api_format == "responses":
        text = _optimizer_responses_text(data)
    else:
        content = ((data.get("choices") or [{}])[0].get("message", {}) or {}).get("content", "")
        text = content if isinstance(content, str) else "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    text = str(text or "").strip()
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


def _optimizer_media_parts(resources: list[Mapping[str, Any]], api_format: str) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for resource in resources[:MAX_MEDIA]:
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
                "mode": ([MODE_IMAGE, MODE_REFERENCE], {"default": MODE_IMAGE}),
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
        if not str(api_key or "").strip():
            raise ValueError("Prompt optimization API key is required")
        if not str(model or "").strip():
            raise ValueError("Prompt optimization model is required")
        counts = {"image": 0, "video": 0, "audio": 0}
        system = _optimizer_system_prompt(str(scene_guide or "none"), str(mode or MODE_IMAGE), float(seconds), counts)
        return (_optimizer_http_json(str(api_url), str(api_key), str(model), str(api_format or "openai"), system, str(prompt or "")),)


def _register_prompt_optimizer_route() -> bool:
    try:
        from aiohttp import web
        from server import PromptServer
    except Exception:
        return False
    routes = getattr(getattr(PromptServer, "instance", None), "routes", None)
    if routes is None or getattr(_register_prompt_optimizer_route, "_registered", False):
        return bool(getattr(_register_prompt_optimizer_route, "_registered", False))

    @routes.get("/minimax_h3_easy/prompt_optimizer_settings")
    async def _prompt_optimizer_settings_get(request):
        return web.json_response({"ok": True, "settings": _read_prompt_optimizer_config()})

    @routes.post("/minimax_h3_easy/prompt_optimizer_settings")
    async def _prompt_optimizer_settings_post(request):
        try:
            payload = await request.json()
            settings = _write_prompt_optimizer_config(payload if isinstance(payload, dict) else {})
            return web.json_response({"ok": True, "settings": settings})
        except Exception as exc:
            return web.json_response({"ok": False, "error": str(exc)}, status=500)

    @routes.post("/minimax_h3_easy/prompt_optimize")
    async def _prompt_optimize(request):
        try:
            payload = await request.json()
            prompt = str(payload.get("prompt") or "")
            settings = _read_prompt_optimizer_config()
            api_key = str(settings.get("api_key") or "")
            api_url = str(settings.get("api_url") or "")
            model = str(settings.get("model") or "")
            api_format = str(settings.get("api_format") or "openai").lower()
            mode = str(payload.get("mode") or MODE_IMAGE)
            scene_guide = str(payload.get("scene_guide") or "none")
            seconds = min(MAX_SECONDS, max(MIN_SECONDS, float(payload.get("seconds") or 5.0)))
            if api_format not in {"openai", "responses", "gemini"}:
                return web.json_response({"ok": False, "error": "Unsupported API format"}, status=400)
            if not prompt.strip() or not api_key.strip() or not api_url.strip() or not model.strip():
                return web.json_response({"ok": False, "error": "Prompt optimization settings are incomplete"}, status=400)
            raw_counts = payload.get("media_counts") if isinstance(payload.get("media_counts"), dict) else {}
            counts = {kind: max(0, min(MAX_MEDIA, int(raw_counts.get(kind, 0) or 0))) for kind in ("image", "video", "audio")}
            resources = payload.get("resources") if isinstance(payload.get("resources"), list) else []
            media_parts = _optimizer_media_parts(resources, api_format) if bool(settings.get("read_media")) else []
            system = _optimizer_system_prompt(scene_guide, mode, seconds, counts, len(media_parts))
            result = await asyncio.to_thread(_optimizer_http_json, api_url, api_key, model, api_format, system, prompt, media_parts)
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


def _filtered_choices(category: str, needles: tuple[str, ...], fallback: str) -> list[str]:
    names = _collect_weight_names((category,))
    selected = [name for name in names if any(needle.lower() in _normalise_model_name(name).replace(" ", "") for needle in needles)]
    return _sort_model_names(selected) or [fallback]


def _model_choices() -> list[str]:
    return _optional_role_choices("fl2va", ("diffusion_models", "unet", "unet_gguf"))


def _ref_model_choices() -> list[str]:
    return _optional_role_choices("ref2va", ("diffusion_models", "unet", "unet_gguf"))


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


def _video_parts(value: Any) -> tuple[torch.Tensor, dict | None, float]:
    if hasattr(value, "get_components"):
        components = value.get_components()
        return components.images, components.audio, float(components.frame_rate or 24.0)
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


def _empty_image_conditioning(bundle, prompt, width, height, length, first_frame=None, last_frame=None):
    latent, frame_count = h3._empty_av_latent(width, height, length)
    images = []
    keyframes = []
    if first_frame is not None:
        image = h3._resize(first_frame[:1], width, height, "center")
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


class MiniMaxH3Easy:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "generate"
    RETURN_TYPES = ("MODEL", "MINIMAX_H3_CONTEXT")
    RETURN_NAMES = ("model", "h3_context")
    DESCRIPTION = "One MiniMax H3 node for text, image and reference video workflows."

    @classmethod
    def INPUT_TYPES(cls):
        optional = {"media": ("*",)}
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
                "mode": ([MODE_IMAGE, MODE_REFERENCE], {"default": MODE_IMAGE}),
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
                "prompt_optimizer_settings": ("BOOLEAN", {"default": False}),
                "prompt_optimizer_scene_guide": (
                    [str(item.get("id")) for item in (_prompt_guide_manifest().get("scene_guides") or []) if isinstance(item, dict) and item.get("id")] or ["none"],
                    {"default": "none"},
                ),
            },
            "optional": optional,
        }

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
    def generate(cls, h3_bundle, mode, prompt, resolution, aspect_ratio, width, height, seconds, advanced, fps, keyframe_role, ref_image_size, reference_mention_mode, **kwargs):
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
            model = h3_bundle.model_for("ref2va")
            conditioning, latent = _reference_conditioning(h3_bundle, prompt, width, height, length, ref_image_size, items)
        else:
            first_frame, last_frame = cls._keyframes(items, keyframe_role)
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


_register_prompt_optimizer_route_when_ready()


NODE_CLASS_MAPPINGS = {
    "MiniMaxH3EasyLoader": MiniMaxH3EasyLoader,
    "MiniMaxH3EasyModelAdapter": MiniMaxH3EasyModelAdapter,
    "MiniMaxH3Easy": MiniMaxH3Easy,
    "MiniMaxH3EasyOutput": MiniMaxH3EasyOutput,
}
