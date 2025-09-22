# -*- coding: utf-8 -*-
"""diagnostics.py — 辅助诊断与报告工具

提供：
- collect_missing(children_paths): 过滤出磁盘上不存在的 USD 候选路径
- analyze_mdl(stage): 统计 Stage 中 MDL 相关残留（按拥有层粗分）

说明：
这些函数不改变 Stage，只做只读扫描，供 processor 在最终日志里输出更细粒度信息。
"""
from __future__ import annotations
from pxr import Usd, Sdf
import os
from .convert import _material_belongs_to_root_layer  # reuse ownership logic
from .materials import is_mdl_shader

_USD_EXTS = {".usd", ".usda", ".usdc", ".usdz"}

def collect_missing(paths):
    """返回给定绝对路径列表中，文件不存在或不可读的子集。"""
    missing = []
    for p in paths:
        try:
            if not p:
                continue
            # usdz 仍用存在性判断；目录不予考虑
            if not os.path.exists(p):
                missing.append(p)
        except Exception:
            missing.append(p)
    return missing

def analyze_mdl(stage: Usd.Stage):
    """扫描 Stage 中所有 MDL 残留并按『root layer 拥有 vs 外部』分类。

    Block 状态的 MDL 输出不会计入残留（但会单独列出 blocked_* 供参考）。

    返回 dict：
      total_mdl_shaders
      total_mdl_material_outputs
      root_owned_mdl_shaders
      external_mdl_shaders
      root_owned_material_mdl_outputs
      external_material_mdl_outputs
      root_owned_blocked_material_mdl_outputs
      external_blocked_material_mdl_outputs
    """
    root_owned_mdl_shaders = []
    external_mdl_shaders = []
    root_owned_material_mdl_outputs = []
    external_material_mdl_outputs = []
    root_owned_blocked = []
    external_blocked = []

    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        try:
            if is_mdl_shader(prim):
                (root_owned_mdl_shaders if _material_belongs_to_root_layer(stage, prim) else external_mdl_shaders).append(prim.GetPath().pathString)
                continue
            if prim.GetTypeName() == "Material":
                for prop in ("outputs:surface:mdl", "outputs:mdl:surface"):
                    if not prim.HasProperty(prop):
                        continue
                    attr = prim.GetAttribute(prop)
                    is_blocked = False
                    forced = False
                    if attr:
                        is_blocked = bool(getattr(attr, "IsBlocked", None) and attr.IsBlocked())
                        try:
                            forced = bool(attr.GetCustomData().get("noMDL_forced_block"))
                        except Exception:
                            forced = False
                    effective_blocked = is_blocked or forced
                    if _material_belongs_to_root_layer(stage, prim):
                        if effective_blocked:
                            root_owned_blocked.append(f"{prim.GetPath()}::{prop}")
                        else:
                            root_owned_material_mdl_outputs.append(f"{prim.GetPath()}::{prop}")
                    else:
                        if effective_blocked:
                            external_blocked.append(f"{prim.GetPath()}::{prop}")
                        else:
                            external_material_mdl_outputs.append(f"{prim.GetPath()}::{prop}")
        except Exception:
            pass

    return {
        "total_mdl_shaders": len(root_owned_mdl_shaders) + len(external_mdl_shaders),
        "total_mdl_material_outputs": len(root_owned_material_mdl_outputs) + len(external_material_mdl_outputs),
        "root_owned_mdl_shaders": root_owned_mdl_shaders,
        "external_mdl_shaders": external_mdl_shaders,
        "root_owned_material_mdl_outputs": root_owned_material_mdl_outputs,
        "external_material_mdl_outputs": external_material_mdl_outputs,
        "root_owned_blocked_material_mdl_outputs": root_owned_blocked,
        "external_blocked_material_mdl_outputs": external_blocked,
    }

def sample_mdl_output_property_stacks(stage: Usd.Stage, limit=10):
    """采样若干仍存在（未 Block）的 MDL 输出，打印它们的 property stack 来源层，帮助判断为何删除失败。

    返回 list[ dict ] 结构，其中每项包含：
      path: prim path + ::prop
      layers: [ layerIdentifier ... ]
    """
    samples = []
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if len(samples) >= limit:
            break
        if prim.GetTypeName() != "Material":
            continue
        for prop in ("outputs:surface:mdl", "outputs:mdl:surface"):
            if not prim.HasProperty(prop):
                continue
            attr = prim.GetAttribute(prop)
            forced = False
            is_blocked = False
            if attr:
                is_blocked = bool(getattr(attr, "IsBlocked", None) and attr.IsBlocked())
                try:
                    forced = bool(attr.GetCustomData().get("noMDL_forced_block"))
                except Exception:
                    forced = False
            if attr and (is_blocked or forced):
                continue  # 忽略已屏蔽
            # 收集 stack
            stack_layers = []
            try:
                for spec in attr.GetPropertyStack(Usd.TimeCode.Default()):
                    lid = getattr(spec.layer, "realPath", None) or getattr(spec.layer, "identifier", "")
                    stack_layers.append(lid)
            except Exception:
                pass
            samples.append({
                "path": f"{prim.GetPath()}::{prop}",
                "layers": stack_layers,
            })
            if len(samples) >= limit:
                break
    return samples
