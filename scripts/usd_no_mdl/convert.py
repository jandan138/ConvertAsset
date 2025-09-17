# -*- coding: utf-8 -*-
from pxr import Usd, UsdShade
from .config import MATERIAL_ROOT_HINTS
from .materials import find_mdl_shader, ensure_preview, copy_textures, connect_preview, remove_material_mdl_outputs, remove_all_mdl_shaders


def _material_belongs_to_root_layer(stage: Usd.Stage, mat_prim: Usd.Prim) -> bool:
    root = stage.GetRootLayer()
    try:
        return bool(root.GetPrimAtPath(mat_prim.GetPath()))
    except Exception:
        return True


def convert_and_strip_mdl_in_this_file_only(stage: Usd.Stage):
    stats = {"total": 0, "mdl": 0, "preview": 0}

    looks_roots = []
    for hint in MATERIAL_ROOT_HINTS:
        p = stage.GetPrimAtPath(hint)
        if p and p.IsValid():
            looks_roots.append(p)
    if not looks_roots:
        looks_roots = [stage.GetPseudoRoot()]

    mats = []
    for root in looks_roots:
        for prim in Usd.PrimRange(root):
            if prim.GetTypeName() != "Material":
                continue
            if not _material_belongs_to_root_layer(stage, prim):
                continue
            mats.append(prim)

    for prim in mats:
        stats["total"] += 1
        mat = UsdShade.Material(prim)
        mdl = find_mdl_shader(mat)
        if not mdl:
            continue
        stats["mdl"] += 1
        ensure_preview(stage, mat)
        filled, has_c, c_rgb, bc_tex = copy_textures(stage, mdl, mat)
        connect_preview(stage, mat, filled, has_c, c_rgb, bc_tex)
        stats["preview"] += 1

    remove_material_mdl_outputs(stage)
    remove_all_mdl_shaders(stage)

    return stats
