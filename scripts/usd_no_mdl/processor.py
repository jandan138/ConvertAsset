# -*- coding: utf-8 -*-
from pxr import Usd
import os
from .path_utils import _to_posix, _sibling_noMDL_path, _resolve
from .references import _collect_asset_paths, _rewrite_assets_in_stage
from .convert import convert_and_strip_mdl_in_this_file_only
from .materials import verify_no_mdl


class Processor:
    def __init__(self):
        self.done = {}
        self.in_stack = set()

    def process(self, src_usd_abs: str) -> str:
        src_usd_abs = _to_posix(os.path.abspath(src_usd_abs))
        if src_usd_abs in self.done:
            return self.done[src_usd_abs]
        if src_usd_abs in self.in_stack:
            print("[WARN] cyclic reference? already in stack:", src_usd_abs)
            return self.done.get(src_usd_abs, src_usd_abs)

        self.in_stack.add(src_usd_abs)

        stage = Usd.Stage.Open(src_usd_abs)
        if not stage:
            print("[ERROR] cannot open:", src_usd_abs)
            self.in_stack.remove(src_usd_abs)
            return src_usd_abs

        deps = _collect_asset_paths(stage)
        child_abs_paths = set()
        ldir = os.path.dirname(stage.GetRootLayer().realPath or stage.GetRootLayer().identifier)
        for kind, holder, layer_dir, assetPath, prim_path, extra in deps:
            abs_child = _resolve(ldir, assetPath)
            if not abs_child:
                continue
            ext = os.path.splitext(abs_child)[1].lower()
            if ext in (".usd", ".usda", ".usdc", ".usdz"):
                child_abs_paths.add(abs_child)

        mapping = {}
        for c in sorted(child_abs_paths):
            dst_c = self.process(c)
            mapping[c] = dst_c

        dst_usd_abs = _sibling_noMDL_path(src_usd_abs)
        root_layer = stage.GetRootLayer()
        root_layer.Export(dst_usd_abs)

        dst_stage = Usd.Stage.Open(dst_usd_abs)
        _rewrite_assets_in_stage(dst_stage, mapping)
        stats = convert_and_strip_mdl_in_this_file_only(dst_stage)

        if not dst_stage.GetDefaultPrim():
            world = dst_stage.GetPrimAtPath("/World")
            if world and world.IsValid():
                dst_stage.SetDefaultPrim(world)
            else:
                roots = list(dst_stage.GetPseudoRoot().GetChildren())
                if roots:
                    dst_stage.SetDefaultPrim(roots[0])

        dst_stage.GetRootLayer().Export(dst_usd_abs)

        ok = verify_no_mdl(Usd.Stage.Open(dst_usd_abs))
        print(f"[DONE] {os.path.basename(src_usd_abs)} -> {os.path.basename(dst_usd_abs)} | materials processed: {stats['preview']}/{stats['total']}, noMDL={ok}")

        self.done[src_usd_abs] = dst_usd_abs
        self.in_stack.remove(src_usd_abs)
        return dst_usd_abs
