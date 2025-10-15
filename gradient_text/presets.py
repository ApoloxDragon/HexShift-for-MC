from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


APP_DIR_NAME = "gradient_text"
PRESETS_FILE = "presets.json"


def _presets_dir() -> Path:
    # Prefer %APPDATA% on Windows, else fallback to user home
    base = os.environ.get("APPDATA")
    if base:
        p = Path(base) / APP_DIR_NAME
    else:
        p = Path.home() / f".{APP_DIR_NAME}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def presets_path() -> Path:
    return _presets_dir() / PRESETS_FILE


def load_presets() -> Dict[str, Any]:
    path = presets_path()
    if not path.exists():
        return {"version": 1, "presets": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "presets" not in data:
            return {"version": 1, "presets": {}}
        if "version" not in data:
            data["version"] = 1
        if not isinstance(data["presets"], dict):
            data["presets"] = {}
        return data
    except Exception:
        return {"version": 1, "presets": {}}


def save_presets(data: Dict[str, Any]) -> None:
    path = presets_path()
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def list_preset_names() -> List[str]:
    return sorted(load_presets().get("presets", {}).keys())


def get_preset(name: str) -> Optional[Dict[str, Any]]:
    data = load_presets()
    return data.get("presets", {}).get(name)


def put_preset(name: str, preset: Dict[str, Any]) -> None:
    data = load_presets()
    data.setdefault("presets", {})[name] = preset
    save_presets(data)


def delete_preset(name: str) -> None:
    data = load_presets()
    if name in data.get("presets", {}):
        del data["presets"][name]
        save_presets(data)

