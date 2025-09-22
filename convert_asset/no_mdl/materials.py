"""
materials.py — 材质转换与 MDL 移除的实现细节

本模块聚焦“在不打平（no-flatten）的前提下，将当前文件内由 MDL 驱动的材质转换为 UsdPreviewSurface 网络”，并保证：
- 仅处理“本文件 root layer 里拥有/定义”的材质（外部引用的材质不在此处硬改）。
- 建立最小可用的 PreviewSurface 网络（BaseColor/Roughness/Metallic/Normal 四个通道）。
- 在可能的情况下复制与连接贴图；当信息缺失时用默认常量兜底。
- 移除 MDL 着色器（Shader）与 Material 输出中的 MDL 接口，最终验证场景中不再残留 MDL。

设计要点：
- Preview 网络布局固定在每个 Material 下的一个 `Scope`（名为 `GROUP`，配置项）中，便于与原有节点隔离。
- UV 使用 `UsdPrimvarReader_float2` 读取配置指定的 UV 集（`UVSET`）。
- BaseColor 的“常量色 + 贴图”策略：
    - 如果配置 `ALWAYS_BAKE_TINT=True`，则直接写入常量色（即使贴图存在）。
    - 否则优先连接贴图；当 `BAKE_TINT_WHEN_WHITE=True` 且贴图被判定为“白图”时，用常量色覆盖以避免多余开销。
- Roughness 支持从 Gloss 反转（scale=-1, bias=1）这一常见美术约定。
- 路径解析遵循“以声明该路径的 Layer 目录为锚点”的规则，`_anchor_dir_for_attr` 提供定位。

主要函数：
- `ensure_preview(stage, mat)`：为 Material 搭建 Preview 网络骨架。
- `find_mdl_shader(mat)`：定位当前 Material 上的 MDL Shader。
- `read_mdl_basecolor_const(mdl_shader)`：读取 MDL 中的 BaseColor 常量。
- `copy_textures(stage, mdl_shader, mat)`：解析 MDL pin 与 .mdl 源码，复制/连接贴图。
- `connect_preview(stage, mat, filled, has_c, c_rgb, bc_tex)`：将贴图/常量正式连接到 PreviewSurface。
- `remove_material_mdl_outputs(stage)`：清理 Material 输出中的 MDL 接口与连接。
- `remove_all_mdl_shaders(stage)`：删除场景中所有 MDL Shader prim。
- `verify_no_mdl(stage)`：验证场景已不含 MDL 残留。

注意：本模块不负责“材质是否属于当前 root layer”的判断，调用方（如 convert.py）应在进入前过滤好目标。
"""

# -*- coding: utf-8 -*-
from pxr import Usd, UsdShade, Sdf, Gf
import os
from .config import (
    GROUP, UVSET, BAKE_TINT_WHEN_WHITE, ALWAYS_BAKE_TINT, MDL_BASECOLOR_CONST_KEYS,
    PRINT_DIAGNOSTICS, BREAK_INSTANCE_FOR_MDL, CLEAN_VARIANT_MDL,
    ALLOW_EXTERNAL_MDL_SHADERS, ALLOW_EXTERNAL_MDL_OUTPUTS, STRICT_VERIFY,
    CREATE_PREVIEW_FOR_EXTERNAL_MDL, AUTO_PREVIEW_BASECOLOR
)

if PRINT_DIAGNOSTICS:
    print(f"[DEBUG] materials.py loaded (BREAK_INSTANCE_FOR_MDL={BREAK_INSTANCE_FOR_MDL})")
from .path_utils import _resolve_abs_path
from .mdl_parse import parse_mdl_text


# ... copy of the same functions from scripts/usd_no_mdl/materials.py ...
# To minimize duplication in this message, the full code mirrors the existing module.
# The definitions below are identical.

def _to_vec3(v, default=(1.0, 1.0, 1.0)):
    """将多种输入形式（Vec3/Vec4/标量/序列）稳健地转为 3 元 tuple。

    输入：
    - `v`: 可能是 Gf.Vec3f/Vec3d/Vec4f/Vec4d/tuple/list/float/int/None。
    - `default`: 当无法解析或为 None 时的兜底颜色。

    返回：
    - `(r,g,b)` 的 3 元 tuple（float）。
    """
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
    """基于文件名的启发式判断“是否为白图”。

    目的：当 BaseColor 贴图几乎恒定白色时，可直接烘焙常量色避免多余纹理开销。
    限制：仅根据文件名关键字与常见白图命名，非严格像素分析。
    """
    if not path:
        return False
    name = os.path.basename(path).lower()
    return ("white" in name) or (name in {"1x1.png", "white.png", "white.jpg", "white.jpeg", "white.tga", "white.exr"})


def ensure_preview(stage: Usd.Stage, mat: UsdShade.Material):
    """为给定 Material 创建（或获取）可用的 UsdPreviewSurface 网络骨架。

    行为：
    - 在 `mat` 下方建立 `/{GROUP}` 的 `Scope`；
    - 创建 `PreviewSurface`（UsdPreviewSurface）着色器；
    - 创建 `PrimvarReader_float2` 并设置 `varname=UVSET`；
    - 为 BaseColor/Roughness/Metallic/Normal 预建对应的 `UsdUVTexture` 节点；
    - 默认将 Material 的 `outputs:surface` 连接到 Preview 的 `surface`；
    - 纹理节点的 `st` 输入连接到 primvar 的 `result` 输出；
    - `wrapS/T` 默认设为 `repeat`（如未显式存在）。

    返回：
    - `UsdShade.Shader`：PreviewSurface 节点（便于后续连接 inputs）。
    """
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
        """在 Scope 下创建/获取一个 UsdUVTexture 节点，并保证 st 与 wrap 设置。

        - `tag` 用于命名：`Tex_{tag}`，如 `Tex_BaseColor`。
        - 确保 `wrapS/T` 存在且为 `repeat`；
        - 将 `st` 连接到 primvar 输出（若尚未连接）。
        """
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
    # 关键切换点（1/2）：将材质的通用表面输出 outputs:surface 指向 UsdPreviewSurface
    # - 若原来 outputs:surface 未连接，我们在此连接到 PreviewSurface.outputs:surface
    # - 这是让最终渲染从“MDL 管线”切换到“UsdPreviewSurface 管线”的核心操作之一
    if not (out_def and out_def.HasConnectedSource()):
        mat.CreateSurfaceOutput().ConnectToSource(prev.CreateOutput("surface", Sdf.ValueTypeNames.Token))
    return prev


def find_mdl_shader(mat: UsdShade.Material):
    """查找挂在 Material 上的 MDL Shader。

    策略依次为：
    1) 检查 `outputs:surface:mdl` 是否有连接，若有，取其源 Shader；
    2) 遍历子 prim，寻找 `Shader` 类型且拥有 `info:mdl:sourceAsset` 属性的节点；
    若均未命中，返回 None。
    """
    out_mdl = mat.GetSurfaceOutput("mdl")
    if out_mdl and out_mdl.HasConnectedSource():
        s, _, _ = out_mdl.GetConnectedSource()
        return UsdShade.Shader(s)
    for c in mat.GetPrim().GetChildren():
        if c.GetTypeName() == "Shader" and c.HasAttribute("info:mdl:sourceAsset"):
            return UsdShade.Shader(c)
    return None


def read_mdl_basecolor_const(mdl_shader):
    """从 MDL Shader 输入中解析 BaseColor 常量值。

    - 读取配置 `MDL_BASECOLOR_CONST_KEYS` 指定的若干输入名（如 `base_color`、`tint` 等）。
    - 一旦读取到非空值即返回（True, rgb_tuple）；否则返回（False, default_white）。
    """
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
    """基于属性的 PropertyStack 推断“相对路径的锚点目录”。

    原理：
    - `attr.GetPropertyStack()` 能返回该属性在各 Layer 中的定义栈；
    - 从上往下寻找第一个“非匿名层（非 anon:）”，取其 `realPath` 或 `identifier`；
    - 返回其所在目录，用作解析 `Sdf.AssetPath` 的相对路径锚点。

    失败回退：若栈不可用或均为匿名层，返回 None，调用方可再用其它锚点（如 RootLayer 目录）。
    """
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
    """解析并填充四类纹理输入，再返回连接与常量的上下文信息。

    输入：
    - `stage`: 目标 Stage（已指向 _noMDL 文件）。
    - `mdl_shader`: Material 上定位到的 MDL Shader；可为 None（进入兜底流程）。
    - `mat`: 目标 Material。

    步骤：
    1) 直接读取 MDL shader 的四个 pin（BaseColor/Roughness/Metallic/Normal）上的 `Sdf.AssetPath`；
    2) 若尚有缺失，解析 `.mdl` 源文件文本（通过 `info:mdl:sourceAsset` 上溯定锚点目录），补齐路径；
    3) 提取 BaseColor 常量（先读 pin，再读 `.mdl` 文本中的 `diffuse_const`）。

    返回：
    - `filled`: dict，记录每个通道是否成功设置贴图；
    - `has_c`: bool，是否得到 BaseColor 常量；
    - `c_rgb`: tuple，BaseColor 常量值；
    - `bc_tex`: str|None，BaseColor 贴图绝对路径（用于“白图”判断）。
    """
    mpath = mat.GetPath().pathString
    filled = {}
    bc_tex = None

    def _set_tex(tag, path, colorspace="raw", invert_r_to_rough=False, anchor_dir=None):
        """在 `Tex_{tag}` 上设置 `file` 与 `sourceColorSpace`，必要时添加 R→Roughness 的反转参数。

        - `path` 可为相对/绝对路径；若提供 `anchor_dir`，会先 `_resolve_abs_path(anchor_dir, path)`；
        - BaseColor 强制 `sourceColorSpace=sRGB`，其它通道为 `raw`；
        - 当 `invert_r_to_rough=True` 且 `tag=='Roughness'` 时，写入 `scale=-1, bias=1`，对应 Gloss→Roughness。
        返回：是否成功设置。
        """
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

    # 1) 直接读 MDL pin（如果 MDL shader 存在且 pin 有值）
    slots = {"BaseColor": "BaseColor_Tex", "Roughness": "Roughness_Tex", "Metallic": "Metallic_Tex", "Normal": "Normal_Tex"}
    for tag, mdl_in in slots.items():
        inp = mdl_shader.GetInput(mdl_in) if mdl_shader else None
        v = inp.Get() if inp else None
        path = getattr(v, "resolvedPath", getattr(v, "path", None)) if v is not None else None
        if not path:
            continue
        _set_tex(tag, path, colorspace=("sRGB" if tag == "BaseColor" else "raw"))

    # 2) 兜底：解析 .mdl 文本（在 MDL pin 缺失时，尽量由源码推断纹理路径）
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

    # 3) 常量色：优先从 MDL pin 取；否则尝试从 .mdl 文本的 `diffuse_const` 中提取
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
    """将 `copy_textures` 阶段得到的信息，接线到 PreviewSurface。

    规则：
    - BaseColor：
      - 若 `ALWAYS_BAKE_TINT` 且有常量色 → 直接写值；
      - 否则：
        - 若有 BaseColor 贴图：
          - 且 `BAKE_TINT_WHEN_WHITE` 且该贴图被判定为白图 → 写常量色；
          - 否则 → 连接纹理 `rgb`；
        - 若无贴图 → 常量/默认白色。
    - Roughness/Metallic：有纹理则连接对应通道（r），否则用合理默认（0.5/0.0）。
    - Normal：有纹理则连接 `rgb`；否则不写（UsdPreviewSurface 正常容错）。
    """
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
    """判断一个 Prim 是否为 MDL Shader。

    兼容多种写法：
    - 显式存在 `info:mdl:*` 属性；
    - 或使用 `info:implementationSource=sourceAsset` 且 `info:sourceAsset` 指向 `.mdl`；
    注意：容错处理若干异常，避免因旧版本 API 差异导致崩溃。
    """
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
    """移除或屏蔽所有 Material 上的 MDL 输出（outputs:surface:mdl / outputs:mdl:surface）。

    改进要点：
    - 之前逻辑把 Block 后仍能通过 HasProperty() 看见的情况统计为 failed，
      但对 USD 来说：被 Block 的属性仍会出现在 composed prim 的属性列表中；
      应使用 attr.IsBlocked() 来判断是否成功屏蔽。
    - 本函数现在：
        1) 断开 surface output 上的 mdl 连接；
        2) RemoveProperty；
        3) 若仍存在则 Block；
        4) 根据 attr.IsBlocked() 判定 blocked 成功；
        5) 统计 removed / blocked / failed。
    - 后续 verify / analyze 会忽略被 Block 的 MDL 输出，不再视为残留。
    """
    removed = blocked = disconnected = failed = 0
    sample_logged = 0
    # 记录已尝试过 override 的 material，以免重复 overridePrim
    over_applied = set()
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if prim.GetTypeName() != "Material":
            continue
        mat = UsdShade.Material(prim)
        # 1. 断开 renderContext=mdl 的 surface 连接
        mdl_output = mat.GetSurfaceOutput("mdl")
        if mdl_output:
            try:
                a = mdl_output.GetAttr()
                if a and a.HasAuthoredConnections():
                    a.SetConnections([])
                    disconnected += 1
            except Exception:
                pass
        # 2. 收集所有与 mdl 相关的 surface 输出属性名（有些资产里可能混合两种命名）
        prop_names = []
        for p in prim.GetPropertyNames():
            if ":mdl:surface" in p and p.startswith("outputs:"):
                prop_names.append(p)
        # 如果找不到，但我们知道这是一个 Material，强制尝试一个标准名列表
        if not prop_names:
            prop_names = ["outputs:mdl:surface", "outputs:surface:mdl"]
        # 去重
        prop_names = list(dict.fromkeys(prop_names))
        for prop in prop_names:
            # 如果属性不存在，需要创建一个可 Block 的 attr（通过 UsdShade API 更稳妥）
            # 策略：优先用 mat.CreateSurfaceOutput("mdl") 得到标准输出，然后用其 attr。
            attr = None
            created = False
            if prop in ("outputs:mdl:surface", "outputs:surface:mdl"):
                # 标准方式
                try:
                    mdl_out = mat.GetSurfaceOutput("mdl") or mat.CreateSurfaceOutput("mdl")
                    attr = mdl_out.GetAttr()
                    created = True
                except Exception:
                    attr = None
            if attr is None and prim.HasProperty(prop):
                # 回退为普通 Attribute 获取
                attr = prim.GetAttribute(prop)
            if attr is None and not prim.HasProperty(prop):
                # 最后手动创建一个 Attribute（可能不是 schema output，但足以 Block）
                try:
                    attr = prim.CreateAttribute(prop, Sdf.ValueTypeNames.Token)
                    created = True
                except Exception:
                    attr = None
            # 删除尝试：只有当它真实存在且不是我们刚创建的 override 时才尝试 RemoveProperty
            if prim.HasProperty(prop) and not created:
                try:
                    prim.RemoveProperty(prop)
                except Exception:
                    pass
            # 如果删除后消失，计为 removed
            if not prim.HasProperty(prop):
                removed += 1
                continue
            # Block 尝试
            attr = prim.GetAttribute(prop)
            if attr is not None:
                try:
                    attr.Block()
                except Exception:
                    pass
            # 如果仍未 Block，并允许打破实例 -> 解除实例
            attr_blocked = bool(attr and getattr(attr, "IsBlocked", None) and attr.IsBlocked())
            if (not attr_blocked) and BREAK_INSTANCE_FOR_MDL and prim.IsInstanceable():
                try:
                    prim.SetInstanceable(False)
                except Exception:
                    pass
                # 再次 Block
                attr = prim.GetAttribute(prop)
                if attr:
                    try:
                        attr.Block()
                    except Exception:
                        pass
                attr_blocked = bool(attr and getattr(attr, "IsBlocked", None) and attr.IsBlocked())
            # 如果仍未 Block，尝试建立 over prim（override spec）再 Block 一次
            if (not attr_blocked) and prim.GetPrimStack():
                root_layer = stage.GetRootLayer()
                # 判断 root layer 是否已有 prim spec；没有则 override
                top_spec = root_layer.GetPrimAtPath(prim.GetPath())
                if top_spec is None:
                    try:
                        if prim.GetPath() not in over_applied:
                            stage.OverridePrim(prim.GetPath())
                            over_applied.add(prim.GetPath())
                        # 重新创建/取得 attr 再 Block
                        mdl_out2 = mat.GetSurfaceOutput("mdl") or mat.CreateSurfaceOutput("mdl")
                        attr2 = mdl_out2.GetAttr()
                        try:
                            attr2.Block()
                        except Exception:
                            pass
                        attr_blocked = bool(attr2 and getattr(attr2, "IsBlocked", None) and attr2.IsBlocked())
                    except Exception:
                        pass
            # 统计
            if attr_blocked:
                blocked += 1
            else:
                failed += 1
                if PRINT_DIAGNOSTICS and sample_logged < 20:
                    sample_logged += 1
                    try:
                        root_layer = stage.GetRootLayer()
                        owned = root_layer.GetPrimAtPath(prim.GetPath()) is not None
                        # 是否存在该属性的（任何层）attr spec
                        has_attr_spec = False
                        stack_layers = []
                        try:
                            # property stack (layers which contribute)
                            pstack = prim.GetProperty(prop).GetPropertyStack()
                            for spec in pstack:
                                lname = getattr(spec.layer, 'identifier', str(spec.layer))
                                stack_layers.append(lname)
                                if spec.layer == root_layer:
                                    has_attr_spec = True
                        except Exception:
                            pass
                        variant_sets = prim.GetVariantSets().GetNames()
                        inst = prim.IsInstanceable()
                        print("[DIAG][fail-classify]",
                              f"prim={prim.GetPath()}",
                              f"prop={prop}",
                              f"owned={owned}",
                              f"has_root_attr_spec={has_attr_spec}",
                              f"instanceable={inst}",
                              f"variant_sets={variant_sets}",
                              f"stack_layers={len(stack_layers)}")
                        if stack_layers and sample_logged <= 5:
                            for sl in stack_layers:
                                print("    [layer]", sl)
                    except Exception:
                        pass
                # 额外兜底：尝试强制创建本地属性 spec，然后写自定义标记
                try:
                    root_layer = stage.GetRootLayer()
                    if root_layer.GetPrimAtPath(prim.GetPath()) is not None:
                        # 确保 attr 存在当前层 spec：通过 DefinePrim + CreateAttribute 再 Set 一个 dummy 值
                        force_attr = prim.GetAttribute(prop)
                        if not force_attr:
                            force_attr = prim.CreateAttribute(prop, Sdf.ValueTypeNames.Token)
                        # 写一个无意义值（避免空 spec 被优化掉）
                        if force_attr and not force_attr.HasAuthoredValue():
                            force_attr.Set("__noMDL_placeholder__")
                        # 写 customData 标记
                        try:
                            force_attr.SetCustomDataByKey("noMDL_forced_block", True)
                        except Exception:
                            pass
                except Exception:
                    pass
    # 记录哪些 Material 在本阶段后仍缺失通用 surface 输出，用于后续自动补齐
    return {
        "disconnected": disconnected,
        "removed": removed,
        "blocked": blocked,
        "failed": failed,
    }


def remove_all_mdl_shaders(stage: Usd.Stage):
    """删除场景中所有的 MDL Shader prim。

    - 先收集路径并按深度从深到浅排序，避免父节点先删导致子节点找不到；
    - 删除失败时仅打印警告，不中断流程（以最大化成品率）。
    """
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


def ensure_surface_output(stage: Usd.Stage, mat: UsdShade.Material, base_color=(0.18,0.18,0.18)):
    """若 Material 没有通用 outputs:surface，则创建并指向一个最小 PreviewSurface。

    - 用于 MDL 输出移除后没有任何可渲染通道（灰材质丢失）的问题。
    - 若已有 outputs:surface 则不做修改。
    """
    out_def = mat.GetSurfaceOutput()
    if out_def and out_def.HasConnectedSource():
        return False
    # 创建骨架并设置一个简易 baseColor
    prev = ensure_preview(stage, mat)
    bc_in = prev.GetInput("diffuseColor") or prev.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
    # UsdShade Input 没有 HasAuthoredValue()；通过底层 attr 判定是否已有值/连接
    attr = bc_in.GetAttr() if bc_in else None
    need_set = True
    if attr:
        try:
            if attr.HasAuthoredValueOpinion():
                need_set = False
        except Exception:
            pass
        # 若已有连接，也不强制覆盖
        try:
            if attr.HasAuthoredConnections():
                need_set = False
        except Exception:
            pass
    if need_set:
        from pxr import Gf as _Gf
        if attr:
            attr.Set(_Gf.Vec3f(*base_color))
    return True


def verify_no_mdl(stage: Usd.Stage) -> bool:
    """验证当前 Stage 是否不含未屏蔽（active）的 MDL。

    考虑场景：
    - 本 root layer 拥有（top spec 在 root layer） vs 外部引用（无 top spec）。
    - 严格模式 STRICT_VERIFY=True 时：任何外部或本层残留都会导致失败。
    - 宽松模式：允许外部残留取决于 ALLOW_EXTERNAL_MDL_* 标志。
    """
    external_mdl_shader = False
    external_mdl_output = False
    root_layer = stage.GetRootLayer()
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if is_mdl_shader(prim):
            owned = root_layer.GetPrimAtPath(prim.GetPath()) is not None
            if owned:
                return False
            external_mdl_shader = True
            continue
        if prim.GetTypeName() == "Material":
            owned = root_layer.GetPrimAtPath(prim.GetPath()) is not None
            # 显式 MDL 输出属性
            for prop in ("outputs:surface:mdl", "outputs:mdl:surface"):
                if prim.HasProperty(prop):
                    attr = prim.GetAttribute(prop)
                    if attr:
                        is_block = getattr(attr, "IsBlocked", None) and attr.IsBlocked()
                        forced = False
                        try:
                            forced = bool(attr.GetCustomData().get("noMDL_forced_block"))
                        except Exception:
                            pass
                        if is_block or forced:
                            continue
                    if owned:
                        return False
                    external_mdl_output = True
            # SurfaceOutput(mdl) 连接
            mat = UsdShade.Material(prim)
            out_mdl = mat.GetSurfaceOutput("mdl")
            if out_mdl and out_mdl.HasConnectedSource():
                if owned:
                    return False
                external_mdl_output = True
    if STRICT_VERIFY:
        return not (external_mdl_shader or external_mdl_output)
    if (external_mdl_shader and not ALLOW_EXTERNAL_MDL_SHADERS) or (external_mdl_output and not ALLOW_EXTERNAL_MDL_OUTPUTS):
        return False
    return True


def verify_no_mdl_report(stage: Usd.Stage):
    """详细残留报告（区分本层 vs 外部 + blocked 情况）。"""
    root_layer = stage.GetRootLayer()
    mdl_shaders_local = []
    mdl_shaders_external = []
    mdl_outputs_local = []
    mdl_outputs_external = []
    mats_blocked = []  # native blocked (attr.IsBlocked())
    mats_forced_blocked = []  # customData noMDL_forced_block
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if is_mdl_shader(prim):
            if root_layer.GetPrimAtPath(prim.GetPath()) is None:
                mdl_shaders_external.append(prim.GetPath().pathString)
            else:
                mdl_shaders_local.append(prim.GetPath().pathString)
            continue
        if prim.GetTypeName() == "Material":
            owned = root_layer.GetPrimAtPath(prim.GetPath()) is not None
            any_prop = False
            for prop in ("outputs:surface:mdl", "outputs:mdl:surface"):
                if prim.HasProperty(prop):
                    attr = prim.GetAttribute(prop)
                    is_block = False
                    forced = False
                    if attr:
                        is_block = getattr(attr, "IsBlocked", None) and attr.IsBlocked()
                        try:
                            forced = bool(attr.GetCustomData().get("noMDL_forced_block"))
                        except Exception:
                            forced = False
                    if is_block or forced:
                        if is_block:
                            mats_blocked.append(f"{prim.GetPath()}::{prop}")
                        if (not is_block) and forced:
                            mats_forced_blocked.append(f"{prim.GetPath()}::{prop}")
                    else:
                        if owned:
                            mdl_outputs_local.append(f"{prim.GetPath()}::{prop}")
                        else:
                            mdl_outputs_external.append(f"{prim.GetPath()}::{prop}")
                    any_prop = True
            if not any_prop:
                mat = UsdShade.Material(prim)
                out_mdl = mat.GetSurfaceOutput("mdl")
                if out_mdl and out_mdl.HasConnectedSource():
                    if owned:
                        mdl_outputs_local.append(f"{prim.GetPath()}::surfaceOutput(mdl)")
                    else:
                        mdl_outputs_external.append(f"{prim.GetPath()}::surfaceOutput(mdl)")
    def _dedup(s):
        return sorted(set(s))
    mdl_shaders_local = _dedup(mdl_shaders_local)
    mdl_shaders_external = _dedup(mdl_shaders_external)
    mdl_outputs_local = _dedup(mdl_outputs_local)
    mdl_outputs_external = _dedup(mdl_outputs_external)
    mats_blocked = _dedup(mats_blocked)
    mats_forced_blocked = _dedup(mats_forced_blocked)
    if STRICT_VERIFY:
        ok = (not mdl_shaders_local and not mdl_shaders_external and not mdl_outputs_local and not mdl_outputs_external)
    else:
        ok_local = (not mdl_shaders_local and not mdl_outputs_local)
        ok_ext = True
        if mdl_shaders_external and not ALLOW_EXTERNAL_MDL_SHADERS:
            ok_ext = False
        if mdl_outputs_external and not ALLOW_EXTERNAL_MDL_OUTPUTS:
            ok_ext = False
        ok = ok_local and ok_ext
    return {
        "ok": ok,
        "mdl_shaders_local": mdl_shaders_local,
        "mdl_shaders_external": mdl_shaders_external,
        "mdl_outputs_local": mdl_outputs_local,
        "mdl_outputs_external": mdl_outputs_external,
        "blocked_material_mdl_outputs": mats_blocked,
        "forced_blocked_material_mdl_outputs": mats_forced_blocked,
    }


def post_process_material_surfaces(stage: Usd.Stage):
    """在 MDL 移除后执行：统计缺失 surface 的材质并可选补齐 Preview。

    返回统计：
    {
        'materials_total': int,
        'materials_without_surface': int,
        'auto_created_preview': int,
        'sample_missing': [... up to 20]
    }
    """
    total = 0
    no_surface = []
    created = 0
    root_layer = stage.GetRootLayer()
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if prim.GetTypeName() != "Material":
            continue
        total += 1
        mat = UsdShade.Material(prim)
        out = mat.GetSurfaceOutput()
        has_any = bool(out and (out.HasConnectedSource() or out.GetAttr().HasAuthoredConnections()))
        if not has_any:
            no_surface.append(prim.GetPath().pathString)
            if CREATE_PREVIEW_FOR_EXTERNAL_MDL:
                if ensure_surface_output(stage, mat, AUTO_PREVIEW_BASECOLOR):
                    created += 1
    if PRINT_DIAGNOSTICS:
        print(f"[DIAG] surface_post: total={total} missing={len(no_surface)} auto_created={created}")
        if no_surface:
            for p in no_surface[:10]:
                print("    [missing-surface]", p)
    return {
        "materials_total": total,
        "materials_without_surface": len(no_surface),
        "auto_created_preview": created,
        "sample_missing": no_surface[:20]
    }
