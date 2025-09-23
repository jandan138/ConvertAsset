# -*- coding: utf-8 -*-
"""
Processor: 递归生成 *_noMDL.usd 的调度器

职责概述：
- 对任意输入 USD（顶层或叶子）执行以下步骤：
    1) 打开源 stage，收集其依赖的子 USD 路径（references/payloads/subLayers/variants/clips）。
    2) 先递归处理所有子 USD，得到“源 -> 目标(_noMDL)”的映射 mapping。
    3) 将当前 root layer 导出为一个并列的 *_noMDL.usd（不 flatten，不内联内容）。
    4) 在新文件上按 mapping 改写所有指向关系（保持组合类型不变，仅改写 assetPath）。
    5) 仅在当前文件执行材质转换与剥离 MDL。
    6) 保存、校验，并记录结果到 self.done 后返回。

关键保证：
- 不 flatten：只复制当前 root layer；子内容不被写入当前文件。
- 结构保持：references/payloads/subLayers/variants/clips 的组合关系保持不变，只改路径。
- 去重与防环：self.done 与 self.in_stack 确保同一文件只处理一次，并防止循环引用导致的无限递归。
"""
from pxr import Usd
import os
from .path_utils import _to_posix, _sibling_noMDL_path, _resolve
from .references import _collect_asset_paths, _rewrite_assets_in_stage
from .convert import convert_and_strip_mdl_in_this_file_only
from .materials import verify_no_mdl, verify_no_mdl_report
from .diagnostics import collect_missing, analyze_mdl, sample_mdl_output_property_stacks
from .config import PRINT_DIAGNOSTICS, STRICT_VERIFY, IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN, TRY_OVERRIDE_EXTERNAL_MATERIALS, WRITE_SUMMARY_TXT, SUMMARY_MISSING_CHILD_LIMIT, ALLOW_EXTERNAL_ONLY_PASS, REQUIRE_NO_MISSING_FOR_EXTERNAL_PASS


class Processor:
    """递归处理 USD，生成对应的 *_noMDL.usd。

    成员：
    - done: dict[str, str]
        已处理过的“源绝对路径 -> 目标 *_noMDL 绝对路径”映射，用于去重和最终汇总。
    - in_stack: set[str]
        当前递归栈中的源路径集合，用于检测环状引用，避免无限递归。
    """

    def __init__(self):
        # 处理完成的映射：src_abs -> dst_abs
        self.done = {}
        # 递归调用栈中的标记，用于环检测
        self.in_stack = set()

    def process(self, src_usd_abs: str, _is_root_call: bool = True) -> str:
        """处理单个 USD 源文件，生成其兄弟 *_noMDL.usd 并返回新文件绝对路径。

        流程：规范路径 -> 防重/防环 -> 打开 Stage -> 收集依赖 -> 先处理子文件
             -> 导出当前 root layer 骨架 -> 改写指向关系 -> 转换材质/剥离 MDL
             -> 兜底 defaultPrim -> 保存与校验 -> 记录映射并返回。
        """
        # 1) 规范化为绝对 POSIX 路径，便于作为字典 key 与日志显示
        src_usd_abs = _to_posix(os.path.abspath(src_usd_abs))

        # 2) 快速返回：已处理过直接复用结果
        if src_usd_abs in self.done:
            return self.done[src_usd_abs]

        # 3) 环检测：若在递归栈中，提示并返回已有结果（若不存在则保守返回自身路径）
        if src_usd_abs in self.in_stack:
            print("[WARN] cyclic reference? already in stack:", src_usd_abs)
            return self.done.get(src_usd_abs, src_usd_abs)

        # 入栈标记当前节点
        self.in_stack.add(src_usd_abs)

        # 4) 打开源 Stage，失败则记录错误并退出当前分支
        stage = Usd.Stage.Open(src_usd_abs)
        if not stage:
            print("[ERROR] cannot open:", src_usd_abs)
            self.in_stack.remove(src_usd_abs)
            return src_usd_abs

        # 5) 收集依赖条目，并筛选出子 USD 的绝对路径集合
        #    deps 是对当前 stage 中所有组合关系的扫描结果，包含：
        #    - sublayers：root layer 的分层文件
        #    - references / payloads：Prim 上的组合引用
        #    - variants：进入每个变体编辑上下文后，变体内的 references/payloads
        #    - clips：时间片段（valueClips）中的资产路径
        #    每个条目统一为一个六元组（kind, holder, layer_dir, assetPath, prim_path, extra）。
        #    字段含义：
        #      kind：条目类型（如 "sublayer"、"reference"、"payload"、"variant_ref"、"variant_payload"、"clip_asset" 等）。
        #      holder：持有者定位信息（例如 ("rootLayer", None) 或 ("prim", "/World/Geom") 或 ("/PrimPath", variantSet, variantName)）。
        #      layer_dir：发现该条目时所处 layer 的目录，用于相对路径解析的参考。
        #      assetPath：条目中出现的资产路径字符串（可能是相对路径）。
        #      prim_path：条目关联的 Prim 路径（如果有）。
        #      extra：ListOp 项或者辅助字段，供改写阶段参考。
        deps = _collect_asset_paths(stage)
        # 使用 set 去重：同一路径可能经由多条组合关系出现多次，避免重复处理与递归
        child_abs_paths = set()
        # ldir：当前 root layer 的目录。realPath 可能为 None（例如匿名层），则回退到 identifier。
        # 注意：虽然 deps 中给出了每条目的 layer_dir，但由于我们要为“当前 root 文件”导出兄弟 *_noMDL，
        # 这里统一以 root layer 的目录为锚点解析相对路径，随后真正写回时会按各自语境再转回相对路径。
        ldir = os.path.dirname(stage.GetRootLayer().realPath or stage.GetRootLayer().identifier)
        if PRINT_DIAGNOSTICS:
            print(f"[DIAG][deps] collected entries={len(deps)} from {os.path.basename(src_usd_abs)}")
        dep_index = 0
        for kind, holder, layer_dir, assetPath, prim_path, extra in deps:
            dep_index += 1
            # 针对每条依赖使用其所在 layer 的目录解析；这是关键修复：
            # 之前统一用 root layer 目录，导致子 layer 自己的相对路径（例如 ../../models/...）被错误解析，从而递归遗漏。
            dep_dir = layer_dir or ldir
            abs_child = _resolve(dep_dir, assetPath)
            if not abs_child:
                if PRINT_DIAGNOSTICS:
                    print(f"[DIAG][deps][{dep_index}] kind={kind} prim={prim_path} asset='{assetPath}' -> skip(empty)")
                continue
            # 如果该解析结果不存在，再尝试 root 目录解析做对比与诊断
            if not os.path.exists(abs_child):
                alt = _resolve(ldir, assetPath)
                if alt != abs_child and os.path.exists(alt):
                    # 说明依赖写的是相对于 root 的路径（或我们误判 layer_dir），采用可存在的版本
                    if PRINT_DIAGNOSTICS:
                        print(f"[DIAG][deps][{dep_index}] kind={kind} prim={prim_path} asset='{assetPath}' resolved1='{abs_child}' missing; fallback root -> '{alt}'")
                    abs_child = alt
                else:
                    if PRINT_DIAGNOSTICS:
                        print(f"[DIAG][deps][{dep_index}] kind={kind} prim={prim_path} asset='{assetPath}' resolved='{abs_child}' missing (no alt)")
            # 仅关心 USD 文件
            ext = os.path.splitext(abs_child)[1].lower()
            if ext in (".usd", ".usda", ".usdc", ".usdz"):
                child_abs_paths.add(abs_child)
                if PRINT_DIAGNOSTICS:
                    print(f"[DIAG][deps][{dep_index}] ACCEPT kind={kind} path={abs_child}")
            else:
                if PRINT_DIAGNOSTICS:
                    print(f"[DIAG][deps][{dep_index}] REJECT ext={ext} path={abs_child}")

        # 6) 先处理所有子文件，建立“源->目标”的映射供当前文件改写之用
        mapping = {}
        missing_children = []
        if PRINT_DIAGNOSTICS:
            print(f"[DIAG][deps] unique child usd candidates={len(child_abs_paths)}")
        for c in sorted(child_abs_paths):
            # 若文件不存在，先记录到 missing 列表，后续诊断输出；不立即递归
            if not os.path.exists(c):
                missing_children.append(c)
                continue
            dst_c = self.process(c, _is_root_call=False)
            mapping[c] = dst_c
        if PRINT_DIAGNOSTICS:
            print(f"[DIAG][deps] processed child count={len(mapping)} missing={len(missing_children)}")

        # 7) 为当前文件生成兄弟 *_noMDL 路径，并导出 root layer 骨架（不内联）
        dst_usd_abs = _sibling_noMDL_path(src_usd_abs)
        root_layer = stage.GetRootLayer()
        root_layer.Export(dst_usd_abs)

        # 8) 打开新 stage，在当前文件上改写指向关系，并进行材质转换
        dst_stage = Usd.Stage.Open(dst_usd_abs)
        _rewrite_assets_in_stage(dst_stage, mapping)
        stats = convert_and_strip_mdl_in_this_file_only(dst_stage)

        # 9) 兜底 defaultPrim：没有时优先 /World，否则取任意根 Prim
        if not dst_stage.GetDefaultPrim():
            world = dst_stage.GetPrimAtPath("/World")
            if world and world.IsValid():
                dst_stage.SetDefaultPrim(world)
            else:
                roots = list(dst_stage.GetPseudoRoot().GetChildren())
                if roots:
                    dst_stage.SetDefaultPrim(roots[0])

        # 10) 保存导出当前文件
        dst_stage.GetRootLayer().Export(dst_usd_abs)

        # 11) 校验当前输出不含 MDL，并输出日志
        reopen_stage = Usd.Stage.Open(dst_usd_abs)
        basic_ok = verify_no_mdl(reopen_stage)
        report = verify_no_mdl_report(reopen_stage)
        diag = analyze_mdl(reopen_stage) if PRINT_DIAGNOSTICS else {}

        # 成功判定策略：
        final_ok = basic_ok
        reason = "strict-pass" if basic_ok else "strict-fail"
        if not basic_ok:
            if not STRICT_VERIFY:
                root_has = bool(diag.get("root_owned_mdl_shaders") or diag.get("root_owned_material_mdl_outputs"))
                if not root_has:
                    final_ok = True
                    reason = "non-strict-root-clean"
            elif STRICT_VERIFY and IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN and missing_children:
                root_has = bool(diag.get("root_owned_mdl_shaders") or diag.get("root_owned_material_mdl_outputs"))
                if not root_has:
                    final_ok = True
                    reason = "strict-ignore-missing-external"

        # 外部-only 放宽：root-owned 全部清理，且 (missing_children 为空 或者 不要求为空)，则判 external-only-pass
        if (not final_ok) and ALLOW_EXTERNAL_ONLY_PASS:
            root_has_any = False
            if diag:
                root_has_any = bool(diag.get("root_owned_mdl_shaders") or diag.get("root_owned_material_mdl_outputs") or diag.get("root_owned_blocked_material_mdl_outputs"))
            no_missing_req = (not REQUIRE_NO_MISSING_FOR_EXTERNAL_PASS) or (REQUIRE_NO_MISSING_FOR_EXTERNAL_PASS and not missing_children)
            if (not root_has_any) and no_missing_req:
                final_ok = True
                reason = "external-only-pass"

        if (not final_ok) and TRY_OVERRIDE_EXTERNAL_MATERIALS:
            print("[WARN] TRY_OVERRIDE_EXTERNAL_MATERIALS enabled but not yet implemented; no action taken.")

        if PRINT_DIAGNOSTICS:
            print("[DIAG] missing_children=", len(missing_children))
            if missing_children:
                for mc in missing_children:
                    print("    -", mc)
            # 兼容旧/新 report 结构
            if "mdl_shaders" in report:  # 旧结构
                shaders_all = len(report["mdl_shaders"])
                outs_all = len(report["materials_with_mdl_outputs"])
                blocked_all = len(report.get("blocked_material_mdl_outputs", []))
                print("[DIAG] mdl_report ok=", report["ok"], "shaders=", shaders_all, "mat_outputs=", outs_all, "blocked=", blocked_all)
                unresolved_have = outs_all > 0
            else:  # 新结构
                shaders_local = len(report.get("mdl_shaders_local", []))
                shaders_ext = len(report.get("mdl_shaders_external", []))
                outs_local = len(report.get("mdl_outputs_local", []))
                outs_ext = len(report.get("mdl_outputs_external", []))
                blocked_all = len(report.get("blocked_material_mdl_outputs", []))
                print(
                    "[DIAG] mdl_report ok=", report["ok"],
                    "local_shaders=", shaders_local, "ext_shaders=", shaders_ext,
                    "local_outs=", outs_local, "ext_outs=", outs_ext,
                    "blocked_native=", blocked_all,
                    "blocked_forced=", len(report.get("forced_blocked_material_mdl_outputs", []))
                )
                unresolved_have = (outs_local + outs_ext) > 0
            if diag:
                print(
                    "[DIAG] root_owned",
                    "shaders=", len(diag.get("root_owned_mdl_shaders", [])),
                    "mat_outputs=", len(diag.get("root_owned_material_mdl_outputs", [])),
                    "blocked=", len(diag.get("root_owned_blocked_material_mdl_outputs", [])),
                )
                print(
                    "[DIAG] external",
                    "shaders=", len(diag.get("external_mdl_shaders", [])),
                    "mat_outputs=", len(diag.get("external_material_mdl_outputs", [])),
                    "blocked=", len(diag.get("external_blocked_material_mdl_outputs", [])),
                )
                if (not report["ok"]) and unresolved_have:
                    samples = sample_mdl_output_property_stacks(reopen_stage, limit=5)
                    if samples:
                        print("[DIAG] sample property stacks (first 5 unresolved mdl outputs):")
                        for s in samples:
                            print("    ", s["path"])
                            for lid in s["layers"]:
                                print("        -", lid)

        print(f"[DONE] {os.path.basename(src_usd_abs)} -> {os.path.basename(dst_usd_abs)} | materials processed: {stats['preview']}/{stats['total']}, noMDL={final_ok} (reason={reason})")

    # 12) 如果是顶层调用并开启 summary，则写出简明 txt。
        if _is_root_call and WRITE_SUMMARY_TXT:
            try:
                root_dir, root_base = os.path.split(src_usd_abs)
                stem, _ext = os.path.splitext(root_base)
                summary_path = os.path.join(root_dir, f"{stem}_noMDL_summary.txt")
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(f"Source USD: {src_usd_abs}\n")
                    f.write(f"Output USD: {dst_usd_abs}\n")
                    f.write(f"Result: {'SUCCESS' if final_ok else 'FAIL'} ({reason})\n")
                    f.write(f"Materials converted (preview/total): {stats['preview']}/{stats['total']}\n")
                    if 'external_overridden_preview' in stats:
                        f.write(f"External materials overridden with preview: {stats['external_overridden_preview']}\n")
                    if stats.get('surface_post'):
                        sp = stats['surface_post']
                        f.write(f"Materials without surface (after): {sp['materials_without_surface']} (auto_created={sp['auto_created_preview']})\n")
                    if 'mdl_shaders_external' in report:
                        f.write(f"External MDL shaders: {len(report.get('mdl_shaders_external', []))}\n")
                        f.write(f"Root-owned MDL shaders: {len(diag.get('root_owned_mdl_shaders', [])) if diag else 0}\n")
                        f.write(f"Forced blocked outputs: {len(report.get('forced_blocked_material_mdl_outputs', []))}\n")
                    else:  # 兼容旧结构
                        f.write(f"MDL shaders: {len(report.get('mdl_shaders', []))}\n")
                        f.write(f"Blocked outputs: {len(report.get('blocked_material_mdl_outputs', []))}\n")
                    # 子文件统计
                    f.write(f"Child USD processed: {len(mapping)}\n")
                    if missing_children:
                        f.write(f"Missing child USD (count={len(missing_children)}):\n")
                        for mc in missing_children[:SUMMARY_MISSING_CHILD_LIMIT]:
                            f.write(f"  - {mc}\n")
                        if len(missing_children) > SUMMARY_MISSING_CHILD_LIMIT:
                            f.write(f"  ... ({len(missing_children)-SUMMARY_MISSING_CHILD_LIMIT} more)\n")
                    # 递归映射概览（限制）
                    if mapping:
                        f.write("Child mapping (first 30):\n")
                        for i, (src_c, dst_c) in enumerate(list(mapping.items())[:30]):
                            f.write(f"  {i+1}. {src_c} -> {dst_c}\n")
                    f.write("\nTimestamp end.\n")
                if PRINT_DIAGNOSTICS:
                    print("[SUMMARY] written:", summary_path)
            except Exception as e:
                print("[SUMMARY][ERROR] failed to write summary txt:", e)

    # 13) 记录结果并出栈
        self.done[src_usd_abs] = dst_usd_abs
        self.in_stack.remove(src_usd_abs)
        return dst_usd_abs
