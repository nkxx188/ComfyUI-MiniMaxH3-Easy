"""Instance-wide, server-side configuration for the prompt optimizer."""

from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
from pathlib import Path
from typing import Any

CONFIG_DIR_NAME = "__minimax_h3_easy"
CONFIG_FILE_NAME = "prompt_optimizer.json"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_VIDEO_MODE = "auto"
DEFAULT_AUDIO_MODE = "auto"
VIDEO_MODES = {"auto", "native", "sampled_frames"}
AUDIO_MODES = {"auto", "input_audio", "video_wrapper"}
_LOCK = threading.RLock()


def _config_path() -> Path:
    import folder_paths

    return Path(folder_paths.get_user_directory()) / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def _read_file() -> dict[str, Any]:
    path = _config_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _env(name: str, fallback: Any) -> Any:
    value = os.environ.get(name)
    return value if value is not None else fallback


def get_optimizer_config() -> dict[str, Any]:
    """Return effective configuration, with environment variables taking priority."""
    with _LOCK:
        saved = _read_file()
    video_mode = str(saved.get("video_mode") or DEFAULT_VIDEO_MODE).strip().lower()
    audio_mode = str(saved.get("audio_mode") or DEFAULT_AUDIO_MODE).strip().lower()
    if video_mode not in VIDEO_MODES:
        video_mode = DEFAULT_VIDEO_MODE
    if audio_mode not in AUDIO_MODES:
        audio_mode = DEFAULT_AUDIO_MODE
    return {
        "base_url": str(_env("MINIMAX_H3_OPTIMIZER_BASE_URL", saved.get("base_url", DEFAULT_BASE_URL)) or "").strip(),
        "model": str(_env("MINIMAX_H3_OPTIMIZER_MODEL", saved.get("model", "")) or "").strip(),
        "api_key": str(_env("MINIMAX_H3_OPTIMIZER_API_KEY", saved.get("api_key", "")) or "").strip(),
        "video_mode": video_mode,
        "audio_mode": audio_mode,
    }


def public_optimizer_config() -> dict[str, Any]:
    config = get_optimizer_config()
    return {
        "base_url": config["base_url"],
        "model": config["model"],
        "api_key_configured": bool(config["api_key"]),
        "api_key_from_environment": "MINIMAX_H3_OPTIMIZER_API_KEY" in os.environ,
        "video_mode": config["video_mode"],
        "audio_mode": config["audio_mode"],
    }


def save_optimizer_config(values: dict[str, Any]) -> dict[str, Any]:
    """Atomically update allowed values. A missing API key leaves it unchanged."""
    if not isinstance(values, dict):
        raise ValueError("Configuration must be a JSON object")
    allowed = {"base_url", "model", "api_key", "clear_api_key", "video_mode", "audio_mode"}
    if set(values) - allowed:
        raise ValueError("Unknown prompt optimizer configuration field")
    with _LOCK:
        saved = _read_file()
        for name, limit in (("base_url", 2_048), ("model", 256)):
            if name in values:
                value = str(values[name] or "").strip()
                if len(value) > limit:
                    raise ValueError(f"{name} is too long")
                saved[name] = value
        if "api_key" in values:
            key = str(values["api_key"] or "").strip()
            if len(key) > 8_192:
                raise ValueError("api_key is too long")
            if key:
                saved["api_key"] = key
        if bool(values.get("clear_api_key")):
            saved.pop("api_key", None)
        if "video_mode" in values:
            mode = str(values["video_mode"] or "").strip().lower()
            if mode not in VIDEO_MODES:
                raise ValueError("Invalid video mode")
            saved["video_mode"] = mode
        if "audio_mode" in values:
            mode = str(values["audio_mode"] or "").strip().lower()
            if mode not in AUDIO_MODES:
                raise ValueError("Invalid audio mode")
            saved["audio_mode"] = mode
        path = _config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(saved, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.chmod(temporary_name, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
            os.replace(temporary_name, path)
            try:
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
    return public_optimizer_config()
