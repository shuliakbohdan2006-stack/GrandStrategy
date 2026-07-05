from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


LANGUAGE_DIR = Path(__file__).resolve().parent
DEFAULT_LANGUAGE = "en"
_current_language = DEFAULT_LANGUAGE
_cache: Dict[str, Dict[str, str]] = {}


def load_language(language_code: str) -> Dict[str, str]:
    if language_code in _cache:
        return _cache[language_code]
    path = LANGUAGE_DIR / f"{language_code}.json"
    if not path.exists():
        _cache[language_code] = {}
        return _cache[language_code]
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        data = {}
    _cache[language_code] = {str(key): str(value) for key, value in data.items()}
    return _cache[language_code]


def set_language(language_code: str) -> None:
    global _current_language
    _current_language = language_code if language_code else DEFAULT_LANGUAGE
    load_language(_current_language)
    load_language(DEFAULT_LANGUAGE)


def tr(key: str) -> str:
    current = load_language(_current_language)
    if key in current:
        return current[key]
    english = load_language(DEFAULT_LANGUAGE)
    return english.get(key, key)
