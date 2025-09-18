"""
references.py — 收集与改写 USD 组合关系（references/payloads/sublayers/variants/clips）

模块职责（与 processor/materials 的关系）：
- 本模块只做两件事：
    1) 遍历一个 Stage，收集其中所有“指向其它资产文件”的组合关系条目（含 sublayers、references、payloads、variants 内部的两者，以及 clips）。
    2) 在一个目标 Stage 上，按“源->目标”的路径映射，改写这些条目的 assetPath，同时尽可能保持原有的组合类型与顺序（不 flatten，不改变结构）。

- 与 `processor.py`：
    `Processor` 会先用 `_collect_asset_paths` 收集当前文件的依赖，递归处理子文件并获得“源->*_noMDL”映射，然后调用 `_rewrite_assets_in_stage` 在当前文件副本上批量改写 assetPath。

- 与 `materials.py`：
    `references.py` 负责“场景结构层面”的改写（让组合指向 *_noMDL 文件），而 `materials.py` 负责“材质网络层面”的改写（把 MDL 切换为 UsdPreviewSurface 并剥离 MDL 残留）。两者分工互补。

设计要点：
- 兼容性：旧版本 USD 可能没有稳定的 `GetReferences()` 列表访问；因此收集阶段优先从 Prim 的 metadata（`references`/`payloads`）读取 ListOp，再在改写阶段优先使用 API（Clear/Add），失败时回退写回 metadata。
- 锚点规则：路径解析一律先相对于 root layer 目录做绝对化，写回时再转回相对于各自 layer 目录的相对路径，保持原工程的相对引用习惯。
- 变体安全：进入每个 Variant 的编辑上下文收集/改写；若启用 `RESTORE_VARIANT_SELECTION`，在退出时把原 variant selection 还原，避免污染作者意图。
- Clips 支持：对 `valueClips` 中的 `clipAssetPaths` 与 `manifestAssetPath` 做映射改写。

输入/输出约定：
- `_collect_asset_paths(stage)` 返回一个列表，每一项为六元组：
    (kind, holder, layer_dir, assetPath, prim_path, extra)
    其中：
    - kind: "sublayer" | "reference" | "payload" | "variant_ref" | "variant_payload" | "clip_asset" | "clip_manifest" 等
    - holder: 定位信息（例如 ("rootLayer", None) 或 ("prim", "/PrimPath") 或 ("/PrimPath", vsName, vName)）
    - layer_dir: 发现该条目所在 layer 的目录（用于相对路径解析）
    - assetPath: 原始的资产路径字符串（可能为相对路径）
    - prim_path: 所属 Prim 的路径（若有）
    - extra: 对于 references/payloads 是其 ListOp item（Sdf.Reference/Sdf.Payload），对于 clips 是字段名字符串

- `_rewrite_assets_in_stage(stage, mapping_src2dst)` 不返回值，直接在传入的 stage 上改写所有可改写的条目，依据 mapping 将绝对源路径替换为对应的目标路径（并尽可能生成相对路径写回）。
"""

# -*- coding: utf-8 -*-
from pxr import Usd, Sdf
import os
from .config import RESTORE_VARIANT_SELECTION
from .path_utils import _resolve, _relpath


def _listop_items(listop):
    """把一个 ListOp（或 None）展开为普通列表。

    背景：USD 的组合字段（如 references/payloads）底层是 ListOp，可能有多种“操作”（显式、添加、前置、后置）。
    我们将其统一合并为简单列表以便遍历；顺序在这里不是关键，因为改写时会整体清空再按新列表追加。
    """
    if not listop:
        return []
    items = []
    for name in ("GetExplicitItems", "GetAddedItems", "GetPrependedItems", "GetAppendedItems"):
        if hasattr(listop, name):
            items.extend(getattr(listop, name)())
    return items


def _collect_asset_paths(stage: Usd.Stage):
    """扫描 stage，收集所有“指向其它资产文件”的条目，返回六元组列表。

    注意：这里只“读”信息，不做任何修改；并且优先通过 metadata 获取 ListOp，
    以兼容某些 USD 版本对 References/Payloads API 的差异。
    """
    items = []
    layer = stage.GetRootLayer()
    ldir = os.path.dirname(layer.realPath or layer.identifier)

    # 1) Root layer 的 sublayers
    for sl in layer.subLayerPaths:
        if sl:
            items.append(("sublayer", ("rootLayer", None), ldir, sl, None, None))

    # 2) Prim 上的 references/payloads/clips，以及 variants 内部的两者
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if not prim.IsValid():
            continue
        # 2.1) references（通过 metadata ListOp 读取，兼容旧 API）
        ref_lo = prim.GetMetadata("references")
        for r in _listop_items(ref_lo):
            items.append(("reference", ("prim", str(prim.GetPath())), ldir, r.assetPath, prim.GetPath(), r))
        # 2.2) payloads（字段名可能是 payloads 或 payload，做容错）
        pay_lo = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
        for p in _listop_items(pay_lo):
            items.append(("payload", ("prim", str(prim.GetPath())), ldir, p.assetPath, prim.GetPath(), p))
        # 2.3) valueClips
        try:
            if prim.HasAuthoredMetadata("clips"):
                clips = prim.GetMetadata("clips")
                if isinstance(clips, dict):
                    cap = clips.get("clipAssetPaths")
                    if isinstance(cap, list):
                        for ap in cap:
                            items.append(("clip_asset", ("prim", str(prim.GetPath())), ldir, ap, prim.GetPath(), "clipAssetPaths"))
                    man = clips.get("manifestAssetPath")
                    if man:
                        items.append(("clip_manifest", ("prim", str(prim.GetPath())), ldir, man, prim.GetPath(), "manifestAssetPath"))
        except Exception:
            # 某些旧版本或异常数据可能导致访问 clips 抛错，忽略之。
            pass

        # 2.4) 进入各个变体，收集变体内的 references/payloads
        vsets = prim.GetVariantSets()
        for vs_name in vsets.GetNames():
            vs = vsets.GetVariantSet(vs_name)
            orig_sel = vs.GetVariantSelection()
            for vname in vs.GetVariantNames():
                with vs.GetVariantEditContext(vname):
                    ref_lo2 = prim.GetMetadata("references")
                    for r in _listop_items(ref_lo2):
                        items.append(("variant_ref", (str(prim.GetPath()), vs_name, vname), ldir, r.assetPath, prim.GetPath(), r))
                    pay_lo2 = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
                    for p in _listop_items(pay_lo2):
                        items.append(("variant_payload", (str(prim.GetPath()), vs_name, vname), ldir, p.assetPath, prim.GetPath(), p))
            # 可配置地恢复原选择，避免影响上层逻辑
            if RESTORE_VARIANT_SELECTION and orig_sel:
                vs.SetVariantSelection(orig_sel)

    return items


def _rewrite_assets_in_stage(stage: Usd.Stage, mapping_src2dst: dict):
    """在给定 stage 上，按映射批量改写所有可改写的资产路径。

    策略：
    - sublayers：直接改 root layer 的 subLayerPaths 列表。
    - references/payloads：优先走 API（Clear+Add），失败回退写 metadata（以兼容旧版 USD）。
    - clips：逐项检查 `clipAssetPaths` 与 `manifestAssetPath`，命中则替换。
    - variants：进入变体编辑上下文后重复上述逻辑，最后可选恢复原 variant selection。
    """
    layer = stage.GetRootLayer()
    ldir = os.path.dirname(layer.realPath or layer.identifier)

    # 1) sublayers：按映射替换为相对路径写回
    changed = False
    new_subs = []
    for sl in layer.subLayerPaths:
        abs_sl = _resolve(ldir, sl)
        if abs_sl and abs_sl in mapping_src2dst:
            new_rel = _relpath(ldir, mapping_src2dst[abs_sl])
            new_subs.append(new_rel)
            changed = True
        else:
            new_subs.append(sl)
    if changed:
        layer.subLayerPaths = new_subs

    # 2) 遍历 Prim：改写 references/payloads/clips；再进入变体重复
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if not prim.IsValid():
            continue

        # 2.1) references：metadata 读，API 写；失败则写回 metadata
        ref_api = prim.GetReferences()
        ref_lo = prim.GetMetadata("references")
        items_lo = _listop_items(ref_lo)
        if items_lo:
            new_items = []
            updated = False
            for it in items_lo:
                ap = _resolve(ldir, it.assetPath)
                if ap and ap in mapping_src2dst:
                    it = Sdf.Reference(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                    updated = True
                new_items.append(it)
            if updated:
                try:
                    ref_api.ClearReferences()
                    for it in new_items:
                        ref_api.AddReference(it)
                except Exception:
                    # Fallback: 直接写回 metadata，保障功能可用
                    prim.SetMetadata("references", new_items)

        # 2.2) payloads：同 references 逻辑
        pay_api = prim.GetPayloads()
        pay_lo = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
        items_lo = _listop_items(pay_lo)
        if items_lo:
            new_items = []
            updated = False
            for it in items_lo:
                ap = _resolve(ldir, it.assetPath)
                if ap and ap in mapping_src2dst:
                    it = Sdf.Payload(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                    updated = True
                new_items.append(it)
            if updated:
                try:
                    pay_api.ClearPayloads()
                    for it in new_items:
                        pay_api.AddPayload(it)
                except Exception:
                    prim.SetMetadata("payloads", new_items)

        # 2.3) clips：改写 clipAssetPaths / manifestAssetPath
        try:
            if prim.HasAuthoredMetadata("clips"):
                clips = prim.GetMetadata("clips")
                if isinstance(clips, dict):
                    changed = False
                    cap = clips.get("clipAssetPaths", None)
                    if cap and isinstance(cap, list):
                        new_cap = []
                        for ap in cap:
                            abs_ap = _resolve(ldir, ap)
                            if abs_ap and abs_ap in mapping_src2dst:
                                new_cap.append(_relpath(ldir, mapping_src2dst[abs_ap]))
                                changed = True
                            else:
                                new_cap.append(ap)
                        clips["clipAssetPaths"] = new_cap
                    man = clips.get("manifestAssetPath", None)
                    if man:
                        abs_man = _resolve(ldir, man)
                        if abs_man and abs_man in mapping_src2dst:
                            clips["manifestAssetPath"] = _relpath(ldir, mapping_src2dst[abs_man])
                            changed = True
                    if changed:
                        prim.SetMetadata("clips", clips)
        except Exception:
            # 容错：旧版本/异常数据时，clips 可能不可访问
            pass

        # 2.4) 变体上下文内重复改写 references/payloads
        vsets = prim.GetVariantSets()
        for vs_name in vsets.GetNames():
            vs = vsets.GetVariantSet(vs_name)
            orig_sel = vs.GetVariantSelection()
            for vname in vs.GetVariantNames():
                with vs.GetVariantEditContext(vname):
                    # references in variant
                    ref_api = prim.GetReferences()
                    ref_lo = prim.GetMetadata("references")
                    items_lo = _listop_items(ref_lo)
                    if items_lo:
                        new_items = []
                        updated = False
                        for it in items_lo:
                            ap = _resolve(ldir, it.assetPath)
                            if ap and ap in mapping_src2dst:
                                it = Sdf.Reference(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                                updated = True
                            new_items.append(it)
                        if updated:
                            try:
                                ref_api.ClearReferences()
                                for it in new_items:
                                    ref_api.AddReference(it)
                            except Exception:
                                prim.SetMetadata("references", new_items)

                    # payloads in variant
                    pay_api = prim.GetPayloads()
                    pay_lo = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
                    items_lo = _listop_items(pay_lo)
                    if items_lo:
                        new_items = []
                        updated = False
                        for it in items_lo:
                            ap = _resolve(ldir, it.assetPath)
                            if ap and ap in mapping_src2dst:
                                it = Sdf.Payload(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                                updated = True
                            new_items.append(it)
                        if updated:
                            try:
                                pay_api.ClearPayloads()
                                for it in new_items:
                                    pay_api.AddPayload(it)
                            except Exception:
                                prim.SetMetadata("payloads", new_items)
            if RESTORE_VARIANT_SELECTION and orig_sel:
                vs.SetVariantSelection(orig_sel)
