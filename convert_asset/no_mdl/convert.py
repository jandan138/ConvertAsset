# -*- coding: utf-8 -*-
from pxr import Usd, UsdShade
from .config import MATERIAL_ROOT_HINTS, ALWAYS_SCAN_ALL_MATERIALS, CLEAN_VARIANT_MDL, RESTORE_VARIANT_SELECTION
from .materials import find_mdl_shader, ensure_preview, copy_textures, connect_preview, remove_material_mdl_outputs, remove_all_mdl_shaders


def _material_belongs_to_root_layer(stage: Usd.Stage, mat_prim: Usd.Prim) -> bool:
    root = stage.GetRootLayer()
    try:
        return bool(root.GetPrimAtPath(mat_prim.GetPath()))
    except Exception:
        return True


def _collect_root_materials(stage: Usd.Stage):
    """按当前激活组合收集 root layer 拥有的 Material prim 列表。"""
    looks_roots = []
    if not ALWAYS_SCAN_ALL_MATERIALS:
        for hint in MATERIAL_ROOT_HINTS:
            p = stage.GetPrimAtPath(hint)
            if p and p.IsValid():
                looks_roots.append(p)
        if not looks_roots:
            looks_roots = [stage.GetPseudoRoot()]
    else:
        looks_roots = [stage.GetPseudoRoot()]
    mats = []
    for root in looks_roots:
        for prim in Usd.PrimRange(root):
            if prim.GetTypeName() != "Material":
                continue
            if not _material_belongs_to_root_layer(stage, prim):
                continue
            mats.append(prim)
    return mats


def _convert_active_materials(stage: Usd.Stage, stats: dict, processed_paths: set):
    """在当前激活的组合（含当前 variant selections）下转换所有 root-owned MDL 材质。

    使用 processed_paths 避免对同一个 prim 重复统计（prim path 相同即视为同一材质）。
    """
    mats = _collect_root_materials(stage)
    for prim in mats:
        pstr = prim.GetPath().pathString
        first_time = pstr not in processed_paths
        if first_time:
            stats["total"] += 1
        mat = UsdShade.Material(prim)
        mdl = find_mdl_shader(mat)
        if not mdl:
            continue
        if first_time:
            stats["mdl"] += 1
        ensure_preview(stage, mat)
        filled, has_c, c_rgb, bc_tex = copy_textures(stage, mdl, mat)
        connect_preview(stage, mat, filled, has_c, c_rgb, bc_tex)
        if first_time:
            stats["preview"] += 1
        processed_paths.add(pstr)


def convert_and_strip_mdl_in_this_file_only(stage: Usd.Stage):
    """主入口：转换当前文件（及可选所有 variant）中的 root-owned MDL 材质，并清理 MDL 输出/Shader。

    - 默认（CLEAN_VARIANT_MDL=False）：只处理当前激活组合（原行为）。
    - 若开启 variant 清理：对每个含 VariantSet 的 prim，遍历其各个 variant *单独* 激活并执行转换。
      注意：此实现按『逐个 VariantSet 独立遍历』，未进行多个 VariantSet 的笛卡尔积组合（潜在遗漏组合特有内容）。
      若需要完整组合覆盖，后续可扩展为组合枚举。
    """
    stats = {"total": 0, "mdl": 0, "preview": 0}
    processed = set()

    if not CLEAN_VARIANT_MDL:
        _convert_active_materials(stage, stats, processed)
        remove_material_mdl_outputs(stage)
        remove_all_mdl_shaders(stage)
        return stats

    # Variant 模式
    # 先处理当前激活（保持与旧行为一致）
    _convert_active_materials(stage, stats, processed)
    remove_material_mdl_outputs(stage)
    remove_all_mdl_shaders(stage)

    # 遍历所有带 VariantSet 的 prim
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        vsets = prim.GetVariantSets().GetNames()
        if not vsets:
            continue
        for vs_name in vsets:
            vs = prim.GetVariantSet(vs_name)
            if not vs:
                continue
            original = vs.GetVariantSelection()
            for vname in vs.GetVariantNames():
                if vname == original:
                    continue  # 已处理
                try:
                    vs.SetVariantSelection(vname)
                except Exception:
                    continue
                _convert_active_materials(stage, stats, processed)
                remove_material_mdl_outputs(stage)
                remove_all_mdl_shaders(stage)
            # 恢复原选择
            if RESTORE_VARIANT_SELECTION and original:
                try:
                    vs.SetVariantSelection(original)
                except Exception:
                    pass
    return stats
