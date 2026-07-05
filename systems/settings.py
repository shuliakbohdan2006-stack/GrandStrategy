from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "saves" / "settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "language": "en",
    "ui_scale": 1.0,
    "fullscreen": False,
    "sound": True,
    "autosave": False,
    "tooltips": True,
    "fps_counter": False,
    "difficulty": "Normal",
}


def load_settings() -> Dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_SETTINGS)
    merged = dict(DEFAULT_SETTINGS)
    merged.update({key: value for key, value in data.items() if key in DEFAULT_SETTINGS})
    return merged


def save_settings(settings: Dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    serializable = dict(DEFAULT_SETTINGS)
    serializable.update({key: settings.get(key, value) for key, value in DEFAULT_SETTINGS.items()})
    SETTINGS_PATH.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")


def apply_settings_to_state(state, settings: Dict[str, Any]) -> None:
    state.settings["autosave"] = bool(settings.get("autosave", False))
    state.settings["language"] = str(settings.get("language", "en"))
    state.settings["ui_scale"] = float(settings.get("ui_scale", 1.0))
    state.settings["fullscreen"] = bool(settings.get("fullscreen", False))
    state.settings["sound"] = bool(settings.get("sound", True))
    state.settings["tooltips"] = bool(settings.get("tooltips", True))
    state.settings["fps_counter"] = bool(settings.get("fps_counter", False))
    state.settings["difficulty"] = str(settings.get("difficulty", "Normal"))
