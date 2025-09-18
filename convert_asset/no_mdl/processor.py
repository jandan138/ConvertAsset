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
from .materials import verify_no_mdl


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

    def process(self, src_usd_abs: str) -> str:
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
        deps = _collect_asset_paths(stage)
        child_abs_paths = set()
        ldir = os.path.dirname(stage.GetRootLayer().realPath or stage.GetRootLayer().identifier)
        for kind, holder, layer_dir, assetPath, prim_path, extra in deps:
            # 解析 assetPath 为绝对路径；不关心非 USD 扩展的条目
            abs_child = _resolve(ldir, assetPath)
            if not abs_child:
                continue
            ext = os.path.splitext(abs_child)[1].lower()
            if ext in (".usd", ".usda", ".usdc", ".usdz"):
                child_abs_paths.add(abs_child)

        # 6) 先处理所有子文件，建立“源->目标”的映射供当前文件改写之用
        mapping = {}
        for c in sorted(child_abs_paths):
            dst_c = self.process(c)
            mapping[c] = dst_c

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
        ok = verify_no_mdl(Usd.Stage.Open(dst_usd_abs))
        print(f"[DONE] {os.path.basename(src_usd_abs)} -> {os.path.basename(dst_usd_abs)} | materials processed: {stats['preview']}/{stats['total']}, noMDL={ok}")

        # 12) 记录结果并出栈
        self.done[src_usd_abs] = dst_usd_abs
        self.in_stack.remove(src_usd_abs)
        return dst_usd_abs
