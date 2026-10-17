"""Persist notebook results: figures as PNG, textual/numerical data as JSON.

Paths are anchored to the repo root (not the notebook's working directory), so the
notebooks write to the same ``outputs/`` tree wherever they are executed from.
"""

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURE_DIR = REPO_ROOT / "outputs" / "figures"
DATA_DIR = REPO_ROOT / "outputs" / "data"


def figure_path(name: str) -> Path:
    """Absolute path under outputs/figures for a PNG, creating the directory."""
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURE_DIR / name


def save_json(name: str, data: Any) -> Path:
    """Write ``data`` as pretty JSON under outputs/data and return the path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    path.write_text(json.dumps(data, indent=2, default=str, sort_keys=True))
    return path
