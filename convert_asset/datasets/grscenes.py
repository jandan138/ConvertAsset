# -*- coding: utf-8 -*-
"""GRScenes-style dataset helpers."""
from __future__ import annotations

from pathlib import Path


def find_layout_usds(dataset_root: str | Path, pattern: str = "**/layout.usd") -> list[Path]:
    root = Path(dataset_root)
    if not root.exists():
        raise FileNotFoundError(f"Dataset root not found: {root}")
    return sorted(path for path in root.glob(pattern) if path.is_file())


def scene_id_from_layout(layout_usd_path: str | Path) -> str:
    path = Path(layout_usd_path)
    if path.name == "layout.usd":
        return path.parent.name
    return path.stem

