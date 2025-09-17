# -*- coding: utf-8 -*-
import os
import time
from .config import SUFFIX, ALLOW_OVERWRITE


# _to_posix = None  # avoid lint complaining before function declared

def _to_posix(p: str) -> str:
    return p.replace("\\", "/") if isinstance(p, str) else p


def _relpath(from_dir: str, to_path: str) -> str:
    return _to_posix(os.path.relpath(to_path, start=from_dir))


def _resolve(layer_dir: str, asset_path: str) -> str | None:
    if not asset_path:
        return None
    ap = str(asset_path)
    if os.path.isabs(ap):
        return _to_posix(os.path.normpath(ap))
    return _to_posix(os.path.normpath(os.path.join(layer_dir, ap)))


def _sibling_noMDL_path(src_usd: str) -> str:
    d, b = os.path.split(src_usd)
    stem, ext = os.path.splitext(b)
    out = os.path.join(d, f"{stem}{SUFFIX}{ext or '.usd'}")
    if (not ALLOW_OVERWRITE) and os.path.exists(out):
        ts = time.strftime("%Y%m%d_%H%M%S")
        out = os.path.join(d, f"{stem}{SUFFIX}_{ts}{ext or '.usd'}")
    return _to_posix(out)


def _resolve_abs_path(anchor_dir: str | None, pth: str | None) -> str | None:
    if not pth:
        return None
    if os.path.isabs(pth):
        return _to_posix(os.path.normpath(pth))
    if not anchor_dir:
        return _to_posix(pth)
    return _to_posix(os.path.normpath(os.path.join(anchor_dir, pth)))
