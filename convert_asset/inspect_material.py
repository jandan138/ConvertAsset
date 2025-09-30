"""Material inspection utilities.

Given a USD file and a Material prim path, extract either its MDL shading
information or its UsdPreviewSurface (preview) network details.

Design goals:
 - Zero mutation (read‑only)
 - Text + optional dict structure for potential JSON output (future)
 - Graceful handling of missing prim / wrong type / missing network

Public API:
    inspect_material(stage, material_path: str, mode: str) -> dict
        mode: 'mdl' | 'usdpreview'

Returned dict (common keys):
    {
      'ok': bool,
      'mode': 'mdl' or 'usdpreview',
      'materialPath': str,
      'message': str (human summary),
      'details': { ... mode specific ... }
    }

Mode specific (mdl):
    details: {
        'hasMdlShader': bool,
        'mdlShaderPath': str|None,
        'sourceAsset': str|None,
        'subIdentifier': str|None,
        'inputs': [ { 'name','type','value','connectedSource' } ],
    }

Mode specific (usdpreview):
    details: {
        'hasPreviewSurface': bool,
        'previewShaderPath': str|None,
        'channels': {
           <channel>: { 'constant': value|None, 'textureShader': path|None,
                        'textureFile': assetPath|None, 'existsOnDisk': bool|None }
        },
        'missingChannels': [...]
    }
"""
from __future__ import annotations
from typing import Any, Dict
import os
from pxr import Usd, UsdShade, Sdf  # type: ignore

INTEREST_PREVIEW_INPUTS = [
    ("diffuseColor", "BaseColor"),
    ("roughness", "Roughness"),
    ("metallic", "Metallic"),
    ("normal", "Normal"),
]


def _prim(stage: Usd.Stage, path: str) -> Usd.Prim | None:
    try:
        return stage.GetPrimAtPath(path)
    except Exception:  # noqa
        return None


def inspect_material(stage: Usd.Stage, material_path: str, mode: str) -> Dict[str, Any]:
    res: Dict[str, Any] = {
        "ok": False,
        "mode": mode,
        "materialPath": material_path,
        "message": "",
        "details": {},
    }
    prim = _prim(stage, material_path)
    if not prim or not prim.IsValid():
        res["message"] = "Material prim not found"
        return res
    if prim.GetTypeName() != "Material":
        # attempt auto-wrap
        try:
            mat = UsdShade.Material(prim)
            if not mat:
                res["message"] = f"Prim is not a Material (type={prim.GetTypeName()})"
                return res
        except Exception:
            res["message"] = f"Prim is not a Material (type={prim.GetTypeName()})"
            return res
    mat = UsdShade.Material(prim)

    if mode == "mdl":
        return _inspect_mdl(stage, mat, res)
    elif mode == "usdpreview":
        return _inspect_preview(stage, mat, res)
    else:
        res["message"] = f"Unsupported mode: {mode}"
        return res


def _inspect_mdl(stage: Usd.Stage, mat: UsdShade.Material, res: Dict[str, Any]):
    # Try surface output(renderContext=mdl)
    out_mdl = mat.GetSurfaceOutput("mdl")
    mdl_shader = None
    if out_mdl and out_mdl.HasConnectedSource():
        s, _, _ = out_mdl.GetConnectedSource()
        mdl_shader = UsdShade.Shader(s)
    else:
        # fallback: iterate children
        for c in mat.GetPrim().GetChildren():
            if c.GetTypeName() == "Shader" and (c.HasAttribute("info:mdl:sourceAsset") or c.HasAttribute("info:mdl:sourceAsset:subIdentifier")):
                mdl_shader = UsdShade.Shader(c)
                break
    details: Dict[str, Any] = {
        "hasMdlShader": bool(mdl_shader),
        "mdlShaderPath": mdl_shader.GetPath().pathString if mdl_shader else None,
        "sourceAsset": None,
        "subIdentifier": None,
        "inputs": [],
    }
    if mdl_shader:
        prim = mdl_shader.GetPrim()
        sa = prim.GetAttribute("info:mdl:sourceAsset")
        sub = prim.GetAttribute("info:mdl:sourceAsset:subIdentifier")
        if sa and sa.HasAuthoredValue():
            v = sa.Get()
            if isinstance(v, Sdf.AssetPath):
                details["sourceAsset"] = v.path
            else:
                details["sourceAsset"] = str(v)
        if sub and sub.HasAuthoredValue():
            details["subIdentifier"] = sub.Get()
        for inp in mdl_shader.GetInputs():
            d = {
                "name": inp.GetBaseName(),
                "type": str(inp.GetTypeName()),
                "value": None,
                "connectedSource": None,
            }
            try:
                if inp.HasConnectedSource():
                    src, outName, srcType = inp.GetConnectedSource()
                    d["connectedSource"] = f"{src.GetPath()}::{outName}" if outName else str(src.GetPath())
                else:
                    val = inp.Get()
                    if isinstance(val, Sdf.AssetPath):
                        d["value"] = val.path
                    else:
                        d["value"] = val
            except Exception:  # noqa
                pass
            details["inputs"].append(d)
        res["ok"] = True
        res["message"] = "MDL shader found" if mdl_shader else "No MDL shader"
    else:
        res["ok"] = False
        res["message"] = "No MDL shader found on material"
    res["details"] = details
    return res


def _inspect_preview(stage: Usd.Stage, mat: UsdShade.Material, res: Dict[str, Any]):
    # Strategy: follow default surface output first.
    preview = None
    out_def = mat.GetSurfaceOutput()
    if out_def and out_def.HasConnectedSource():
        s, outName, _ = out_def.GetConnectedSource()
        shader = UsdShade.Shader(s)
        if shader and shader.GetPrim().GetAttribute("info:id"):
            sid = shader.GetPrim().GetAttribute("info:id").Get()
            if sid == "UsdPreviewSurface":
                preview = shader
    if preview is None:
        # search descendants
        for c in mat.GetPrim().GetChildren():
            if c.GetTypeName() == "Shader":
                attr = c.GetAttribute("info:id")
                if attr and attr.HasAuthoredValue() and attr.Get() == "UsdPreviewSurface":
                    preview = UsdShade.Shader(c)
                    break
    details: Dict[str, Any] = {
        "hasPreviewSurface": bool(preview),
        "previewShaderPath": preview.GetPath().pathString if preview else None,
        "channels": {},
        "missingChannels": [],
    }
    if not preview:
        res["message"] = "No UsdPreviewSurface network found"
        res["details"] = details
        return res

    root_dir = os.path.dirname(stage.GetRootLayer().realPath or "")
    for input_name, tag in INTEREST_PREVIEW_INPUTS:
        entry = {
            "constant": None,
            "textureShader": None,
            "textureFile": None,
            "existsOnDisk": None,
        }
        inp = preview.GetInput(input_name)
        if inp:
            try:
                if inp.HasConnectedSource():
                    src, outName, _ = inp.GetConnectedSource()
                    tex_shader = UsdShade.Shader(src)
                    entry["textureShader"] = tex_shader.GetPath().pathString
                    # attempt file param
                    file_attr = tex_shader.GetInput("file") if tex_shader else None
                    if file_attr:
                        val = file_attr.Get()
                        if isinstance(val, Sdf.AssetPath):
                            ap = val.path
                        else:
                            ap = str(val)
                        entry["textureFile"] = ap
                        if ap:
                            # relative vs absolute existence check (best effort)
                            ap_fs = ap
                            if not os.path.isabs(ap_fs):
                                ap_fs = os.path.join(root_dir, ap)
                            entry["existsOnDisk"] = os.path.exists(ap_fs)
                else:
                    val = inp.Get()
                    entry["constant"] = val
            except Exception:  # noqa
                pass
        details["channels"][input_name] = entry
        if not (entry["constant"] is not None or entry["textureShader"]):
            details["missingChannels"].append(input_name)

    res["ok"] = True
    res["message"] = "PreviewSurface analyzed"
    res["details"] = details
    return res


def format_inspect_result(data: Dict[str, Any]) -> str:
    """Pretty print inspection dict to a human-readable multi-line string."""
    lines = []
    lines.append(f"Mode: {data.get('mode')}")
    lines.append(f"Material: {data.get('materialPath')}")
    lines.append(f"OK: {data.get('ok')} ({data.get('message')})")
    details = data.get("details", {})
    if data.get('mode') == 'mdl':
        lines.append(f"Has MDL Shader: {details.get('hasMdlShader')}")
        if details.get('hasMdlShader'):
            lines.append(f"  Shader Path : {details.get('mdlShaderPath')}")
            lines.append(f"  sourceAsset : {details.get('sourceAsset')}")
            lines.append(f"  subIdentifier: {details.get('subIdentifier')}")
            lines.append("  Inputs:")
            for inp in details.get('inputs', []):
                src = inp.get('connectedSource')
                val = inp.get('value')
                lines.append(f"    - {inp.get('name')} ({inp.get('type')}): " + (src if src else repr(val)))
    elif data.get('mode') == 'usdpreview':
        lines.append(f"Has PreviewSurface: {details.get('hasPreviewSurface')}")
        if details.get('hasPreviewSurface'):
            lines.append(f"  Shader Path : {details.get('previewShaderPath')}")
            lines.append("  Channels:")
            for ch, info in details.get('channels', {}).items():
                if info.get('textureShader'):
                    tex_line = f"tex={info.get('textureShader')} file={info.get('textureFile')} exists={info.get('existsOnDisk')}"
                else:
                    tex_line = f"const={info.get('constant')}"
                lines.append(f"    - {ch}: {tex_line}")
            if details.get('missingChannels'):
                lines.append(f"  Missing channels: {', '.join(details.get('missingChannels'))}")
    return "\n".join(lines)


__all__ = [
    "inspect_material",
    "format_inspect_result",
]
