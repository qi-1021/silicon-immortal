"""存档：JSON，存放在项目 saves/ 下。"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .paths import resource_root,player_data_dir
ROOT = resource_root()
SAVE_DIR = player_data_dir()
SAVE_PATH = SAVE_DIR / "save.json"


def load() -> dict:
    try:
        return json.loads(SAVE_PATH.read_text("utf-8"))
    except Exception:
        return {}


def save(data: dict):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SAVE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(SAVE_PATH)


def clear():
    try:
        SAVE_PATH.unlink()
    except Exception:
        pass
