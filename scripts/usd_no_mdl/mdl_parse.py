# -*- coding: utf-8 -*-
"""MDL text parsing utils and regexes."""
import os
import re
from .config import _TEX_EXTS

_RE_BC    = re.compile(r"(?:^|[^a-z])(?:base(?:color)?|albedo|diffuse|_col(?:or)?)", re.I)
_RE_MET   = re.compile(r"(?:metal(?:lic|ness)?)", re.I)
_RE_ROU   = re.compile(r"(?:rough(?:ness)?)", re.I)
_RE_GLOSS = re.compile(r"(?:gloss(?:iness)?|smooth(?:ness)?)", re.I)
_RE_NRM   = re.compile(r"(?:normal|_n\b|[-_\.]n\.)", re.I)
_RE_COLOR_KV = re.compile(
    r"\b(diffuse|base\s*color|albedo|baseColor)\s*:\s*color\s*\(\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*,\s*([0-9.]+)f?\s*\)",
    re.I
)
_RE_GLOSS_KV = re.compile(r"\b(reflect_glossiness|gloss(?:iness)?)\s*:\s*([0-9.]+)f?", re.I)
_RE_ROUGH_KV = re.compile(r"\b(rough(?:ness)?)\s*:\s*([0-9.]+)f?", re.I)
_RE_METAL_KV = re.compile(r"\b(reflection_metalness|metal(?:lic|ness)?)\s*:\s*([0-9.]+)f?", re.I)
_RE_STR_FILE = re.compile(
    r"\"([^\"]+\.(?:png|jpg|jpeg|tga|bmp|exr|tif|tiff|ktx|dds|hdr|psd|gif|webp))\"",
    re.I
)


def parse_mdl_text(mdl_abs_path: str | None) -> dict:
    out = {"diffuse_const": None, "gloss_const": None, "rough_const": None, "metal_const": None, "textures": {}, "errors": []}
    if not mdl_abs_path:
        return out
    try:
        with open(mdl_abs_path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except Exception as e:
        out["errors"].append(f"read_fail:{e}")
        return out

    m = _RE_COLOR_KV.search(txt)
    if m:
        try:
            out["diffuse_const"] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
        except Exception:
            pass
    m = _RE_GLOSS_KV.search(txt)
    if m:
        try:
            out["gloss_const"] = float(m.group(2))
        except Exception:
            pass
    m = _RE_ROUGH_KV.search(txt)
    if m:
        try:
            out["rough_const"] = float(m.group(2))
        except Exception:
            pass
    m = _RE_METAL_KV.search(txt)
    if m:
        try:
            out["metal_const"] = float(m.group(2))
        except Exception:
            pass

    hits = []
    for sm in _RE_STR_FILE.finditer(txt):
        hits.append(sm.group(1))

    for f in hits:
        lname = os.path.basename(f).lower()
        if _RE_NRM.search(lname):
            out["textures"].setdefault("Normal", f)
            continue
        if _RE_MET.search(lname):
            out["textures"].setdefault("Metallic", f)
            continue
        if _RE_ROU.search(lname):
            out["textures"].setdefault("Roughness", f)
            continue
        if _RE_GLOSS.search(lname):
            out["textures"].setdefault("Roughness_fromGloss", f)
            continue
        if _RE_BC.search(lname):
            out["textures"].setdefault("BaseColor", f)
            continue

    return out
