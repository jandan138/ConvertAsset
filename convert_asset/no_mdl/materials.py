# -*- coding: utf-8 -*-
from pxr import Usd, UsdShade, Sdf, Gf
import os
from .config import GROUP, UVSET, BAKE_TINT_WHEN_WHITE, ALWAYS_BAKE_TINT, MDL_BASECOLOR_CONST_KEYS
from .path_utils import _resolve_abs_path
from .mdl_parse import parse_mdl_text


# ... copy of the same functions from scripts/usd_no_mdl/materials.py ...
# To minimize duplication in this message, the full code mirrors the existing module.
# The definitions below are identical.

def _to_vec3(v, default=(1.0, 1.0, 1.0)):
    if v is None:
        return default
    if isinstance(v, (Gf.Vec3f, Gf.Vec3d)):
        return (float(v[0]), float(v[1]), float(v[2]))
    if isinstance(v, (Gf.Vec4f, Gf.Vec4d)):
        return (float(v[0]), float(v[1]), float(v[2]))
    if isinstance(v, (tuple, list)) and len(v) >= 3:
        return (float(v[0]), float(v[1]), float(v[2]))
    try:
        f = float(v)
        return (f, f, f)
    except Exception:
        return default


def _is_white_tex(path: str) -> bool:
    if not path:
        return False
    name = os.path.basename(path).lower()
    return ("white" in name) or (name in {"1x1.png", "white.png", "white.jpg", "white.jpeg", "white.tga", "white.exr"})


def ensure_preview(stage: Usd.Stage, mat: UsdShade.Material):
    mpath = mat.GetPath().pathString
    scope_path = f"{mpath}/{GROUP}"
    if not stage.GetPrimAtPath(scope_path).IsValid():
        stage.DefinePrim(scope_path, "Scope")
    prev = UsdShade.Shader.Define(stage, f"{scope_path}/PreviewSurface")
    prev.CreateIdAttr("UsdPreviewSurface")
    # Primvar
    uvr = UsdShade.Shader.Define(stage, f"{scope_path}/Primvar_{UVSET}")
    uvr.CreateIdAttr("UsdPrimvarReader_float2")
    uvr.CreateInput("varname", Sdf.ValueTypeNames.Token).Set(UVSET)
    uv_out = uvr.CreateOutput("result", Sdf.ValueTypeNames.Float2)

    def mk_tex(tag):
        t = UsdShade.Shader.Define(stage, f"{scope_path}/Tex_{tag}")
        t.CreateIdAttr("UsdUVTexture")
        for wrap in ("wrapS", "wrapT"):
            if not t.GetInput(wrap):
                t.CreateInput(wrap, Sdf.ValueTypeNames.Token).Set("repeat")
            
        st_in = t.GetInput("st") or t.CreateInput("st", Sdf.ValueTypeNames.Float2)
        if not st_in.HasConnectedSource():
            st_in.ConnectToSource(uv_out)
        return t

    for tag in ["BaseColor", "Roughness", "Metallic", "Normal"]:
        mk_tex(tag)

    out_def = mat.GetSurfaceOutput()
    if not (out_def and out_def.HasConnectedSource()):
        mat.CreateSurfaceOutput().ConnectToSource(prev.CreateOutput("surface", Sdf.ValueTypeNames.Token))
    return prev


def find_mdl_shader(mat: UsdShade.Material):
    out_mdl = mat.GetSurfaceOutput("mdl")
    if out_mdl and out_mdl.HasConnectedSource():
        s, _, _ = out_mdl.GetConnectedSource()
        return UsdShade.Shader(s)
    for c in mat.GetPrim().GetChildren():
        if c.GetTypeName() == "Shader" and c.HasAttribute("info:mdl:sourceAsset"):
            return UsdShade.Shader(c)
    return None


def read_mdl_basecolor_const(mdl_shader):
    if not mdl_shader:
        return False, (1.0, 1.0, 1.0)
    for key in MDL_BASECOLOR_CONST_KEYS:
        i = mdl_shader.GetInput(key)
        if i:
            v = i.Get()
            if v is not None:
                return True, _to_vec3(v)
    return False, (1.0, 1.0, 1.0)


def _anchor_dir_for_attr(attr):
    try:
        stack = attr.GetPropertyStack(Usd.TimeCode.Default())
    except Exception:
        return None
    for spec in stack:
        lid = getattr(spec.layer, "identifier", "")
        if not str(lid).startswith("anon:"):
            real = getattr(spec.layer, "realPath", None) or lid
            return os.path.dirname(real)
    return None


def copy_textures(stage: Usd.Stage, mdl_shader, mat: UsdShade.Material):
    mpath = mat.GetPath().pathString
    filled = {}
    bc_tex = None

    def _set_tex(tag, path, colorspace="raw", invert_r_to_rough=False, anchor_dir=None):
        nonlocal bc_tex
        if not path:
            return False
        ap = _resolve_abs_path(anchor_dir, path) if anchor_dir else path
        tex_prim = stage.GetPrimAtPath(f"{mpath}/{GROUP}/Tex_{tag}")
        if not tex_prim:
            return False
        sh = UsdShade.Shader(tex_prim)
        fin = sh.GetInput("file") or sh.CreateInput("file", Sdf.ValueTypeNames.Asset)
        if fin.Get() != ap:
            fin.Set(ap)
        scs = sh.GetInput("sourceColorSpace") or sh.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token)
        scs.Set("sRGB" if tag == "BaseColor" else "raw")
        if tag == "BaseColor":
            bc_tex = ap
        if invert_r_to_rough and tag == "Roughness":
            prim = sh.GetPrim()
            if prim.HasProperty("inputs:scale"):
                prim.RemoveProperty("inputs:scale")
            if prim.HasProperty("inputs:bias"):
                prim.RemoveProperty("inputs:bias")
            sh.CreateInput("scale", Sdf.ValueTypeNames.Float).Set(-1.0)
            sh.CreateInput("bias", Sdf.ValueTypeNames.Float).Set(1.0)
        filled[tag] = True
        return True

    # 1) 直接读 MDL pin
    slots = {"BaseColor": "BaseColor_Tex", "Roughness": "Roughness_Tex", "Metallic": "Metallic_Tex", "Normal": "Normal_Tex"}
    for tag, mdl_in in slots.items():
        inp = mdl_shader.GetInput(mdl_in) if mdl_shader else None
        v = inp.Get() if inp else None
        path = getattr(v, "resolvedPath", getattr(v, "path", None)) if v is not None else None
        if not path:
            continue
        _set_tex(tag, path, colorspace=("sRGB" if tag == "BaseColor" else "raw"))

    # 2) 兜底：解析 .mdl 文本
    need_tags = [t for t in ("BaseColor", "Roughness", "Metallic", "Normal") if not filled.get(t)]
    if need_tags:
        sa_attr = mdl_shader.GetPrim().GetAttribute("info:mdl:sourceAsset") if mdl_shader else None
        sa_val = sa_attr.Get() if sa_attr else None
        mdl_rel = getattr(sa_val, "path", None) if sa_val else None
        anchor_dir = _anchor_dir_for_attr(sa_attr) if sa_attr else None
        mdl_abs = _resolve_abs_path(anchor_dir, mdl_rel) if mdl_rel else None
        parsed = parse_mdl_text(mdl_abs) if (mdl_abs and os.path.exists(mdl_abs)) else {}
        tex = parsed.get("textures", {}) if parsed else {}
        if (not filled.get("BaseColor")) and "BaseColor" in tex:
            _set_tex("BaseColor", tex["BaseColor"], colorspace="sRGB", anchor_dir=anchor_dir)
        if not filled.get("Roughness"):
            if "Roughness" in tex:
                _set_tex("Roughness", tex["Roughness"], colorspace="raw", invert_r_to_rough=False, anchor_dir=anchor_dir)
            elif "Roughness_fromGloss" in tex:
                _set_tex("Roughness", tex["Roughness_fromGloss"], colorspace="raw", invert_r_to_rough=True, anchor_dir=anchor_dir)
        if (not filled.get("Metallic")) and "Metallic" in tex:
            _set_tex("Metallic", tex["Metallic"], colorspace="raw", anchor_dir=anchor_dir)
        if (not filled.get("Normal")) and "Normal" in tex:
            _set_tex("Normal", tex["Normal"], colorspace="raw", anchor_dir=anchor_dir)

    # 3) 常量色
    has_c, c_rgb = read_mdl_basecolor_const(mdl_shader)
    if not has_c:
        try:
            sa_attr = mdl_shader.GetPrim().GetAttribute("info:mdl:sourceAsset")
            sa_val = sa_attr.Get() if sa_attr else None
            mdl_rel = getattr(sa_val, "path", None) if sa_val else None
            anchor_dir = _anchor_dir_for_attr(sa_attr) if sa_attr else None
            mdl_abs = _resolve_abs_path(anchor_dir, mdl_rel) if mdl_rel else None
            parsed = parse_mdl_text(mdl_abs) if (mdl_abs and os.path.exists(mdl_abs)) else {}
            if parsed.get("diffuse_const") is not None:
                c_rgb = _to_vec3(parsed["diffuse_const"])
                has_c = True
        except Exception:
            pass

    return filled, has_c, c_rgb, bc_tex


def connect_preview(stage: Usd.Stage, mat: UsdShade.Material, filled, has_c, c_rgb, bc_tex):
    mpath = mat.GetPath().pathString
    prev = UsdShade.Shader.Get(stage, f"{mpath}/{GROUP}/PreviewSurface")
    if not prev:
        return

    def tex_shader(tag):
        prim = stage.GetPrimAtPath(f"{mpath}/{GROUP}/Tex_{tag}")
        return UsdShade.Shader(prim) if prim and prim.IsValid() else None

    # diffuse
    base_sh = tex_shader("BaseColor")
    diff_in = prev.GetInput("diffuseColor") or prev.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
    if diff_in.HasConnectedSource():
        diff_in.DisconnectSource()
    if ALWAYS_BAKE_TINT and has_c:
        diff_in.Set(Gf.Vec3f(*c_rgb))
    else:
        if base_sh and filled.get("BaseColor"):
            if BAKE_TINT_WHEN_WHITE and has_c and _is_white_tex(bc_tex):
                diff_in.Set(Gf.Vec3f(*c_rgb))
            else:
                rgb_out = base_sh.GetOutput("rgb") or base_sh.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
                diff_in.ConnectToSource(rgb_out)
        else:
            diff_in.Set(Gf.Vec3f(*(c_rgb if has_c else (1.0, 1.0, 1.0))))

    # roughness
    rough_sh = tex_shader("Roughness")
    rough_in = prev.GetInput("roughness") or prev.CreateInput("roughness", Sdf.ValueTypeNames.Float)
    if filled.get("Roughness") and rough_sh:
        r_out = rough_sh.GetOutput("r") or rough_sh.CreateOutput("r", Sdf.ValueTypeNames.Float)
        rough_in.ConnectToSource(r_out)
    else:
        rough_in.Set(0.5)

    # metallic
    metal_sh = tex_shader("Metallic")
    metal_in = prev.GetInput("metallic") or prev.CreateInput("metallic", Sdf.ValueTypeNames.Float)
    if filled.get("Metallic") and metal_sh:
        r_out = metal_sh.GetOutput("r") or metal_sh.CreateOutput("r", Sdf.ValueTypeNames.Float)
        metal_in.ConnectToSource(r_out)
    else:
        metal_in.Set(0.0)

    # normal
    normal_sh = tex_shader("Normal")
    norm_in = prev.GetInput("normal") or prev.CreateInput("normal", Sdf.ValueTypeNames.Normal3f)
    if filled.get("Normal") and normal_sh:
        rgb_out = normal_sh.GetOutput("rgb") or normal_sh.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        norm_in.ConnectToSource(rgb_out)


def is_mdl_shader(prim: Usd.Prim) -> bool:
    if prim.GetTypeName() != "Shader":
        return False
    if prim.HasAttribute("info:mdl:sourceAsset") or prim.HasAttribute("info:mdl:sourceAsset:subIdentifier"):
        return True
    try:
        impl = prim.GetAttribute("info:implementationSource")
        if impl and impl.HasAuthoredValue() and impl.Get() == "sourceAsset":
            for attrName in ("info:mdl:sourceAsset", "info:sourceAsset"):
                a = prim.GetAttribute(attrName)
                if not a:
                    continue
                ap = a.Get()
                if isinstance(ap, Sdf.AssetPath):
                    p = (ap.resolvedPath or ap.path or "").lower()
                    if p.endswith(".mdl"):
                        return True
    except Exception:
        pass
    return False


def remove_material_mdl_outputs(stage: Usd.Stage):
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if prim.GetTypeName() != "Material":
            continue
        mat = UsdShade.Material(prim)
        out_mdl = mat.GetSurfaceOutput("mdl")
        if out_mdl:
            try:
                attr = out_mdl.GetAttr()
                if attr and attr.HasAuthoredConnections():
                    attr.SetConnections([])
            except Exception:
                pass
            for prop in ("outputs:surface:mdl", "outputs:mdl:surface"):
                if prim.HasProperty(prop):
                    try:
                        prim.RemoveProperty(prop)
                    except Exception:
                        pass


def remove_all_mdl_shaders(stage: Usd.Stage):
    to_remove = []
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        try:
            if is_mdl_shader(prim):
                to_remove.append(prim.GetPath())
        except Exception:
            pass
    to_remove.sort(key=lambda p: len(str(p)), reverse=True)
    for p in to_remove:
        try:
            stage.RemovePrim(p)
        except Exception as e:
            print("[WARN] fail to remove:", p, e)


def verify_no_mdl(stage: Usd.Stage) -> bool:
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if is_mdl_shader(prim):
            return False
        if prim.GetTypeName() == "Material":
            if prim.HasProperty("outputs:surface:mdl") or prim.HasProperty("outputs:mdl:surface"):
                return False
            mat = UsdShade.Material(prim)
            out_mdl = mat.GetSurfaceOutput("mdl")
            if out_mdl and out_mdl.HasConnectedSource():
                return False
    return True
