# -*- coding: utf-8 -*-
"""CLI entry for convert_asset utilities."""
import os
import sys
import argparse
import math
try:
    from .no_mdl.path_utils import _to_posix  # noqa: F401
except Exception:  # noqa
    def _to_posix(p: str) -> str:
        return p.replace('\\', '/')
from .mesh.faces import count_mesh_faces


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="convert-asset",
        description="USD conversion utilities (no-MDL copy generator)"
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_nomdl = sub.add_parser("no-mdl", help="Generate *_noMDL.usd siblings recursively")
    p_nomdl.add_argument("src", help="Path to top or single USD file")
    p_nomdl.add_argument("--only-new-usd", action="store_true", help="Only write the new *_noMDL.usd; do not emit sidecar summary/audit files")

    p_faces = sub.add_parser("mesh-faces", help="Count total render mesh faces in a USD stage")
    p_faces.add_argument("src", help="Path to USD file")

    p_simpl = sub.add_parser("mesh-simplify", help="Simplify render meshes using QEM (triangles only)")
    p_simpl.add_argument("src", help="Path to USD file (input)")
    p_simpl.add_argument("--ratio", type=float, default=0.5, help="Target face ratio (0..1], default 0.5")
    p_simpl.add_argument("--max-collapses", type=int, default=None, help="Max face collapses (safety cap)")
    p_simpl.add_argument("--apply", action="store_true", help="Apply changes and export to --out")
    p_simpl.add_argument("--out", default=None, help="Output USD path (required when --apply)")
    p_simpl.add_argument("--target-faces", type=int, default=None, help="Plan ratio to reach total faces <= this value (overrides --ratio)")
    p_simpl.add_argument("--progress", action="store_true", help="Show periodic progress (no console flood)")
    p_simpl.add_argument("--progress-interval-collapses", type=int, default=10000, help="Emit progress every N collapses (default 10000)")
    p_simpl.add_argument("--time-limit", type=float, default=None, help="Per-mesh time limit in seconds (abort mesh when exceeded)")
    p_simpl.add_argument("--backend", choices=["py","cpp"], default="py", help="Simplifier backend: pure Python ('py') or native C++ ('cpp')")
    p_simpl.add_argument("--cpp-exe", default="native/meshqem/build/meshqem", help="Path to C++ meshqem executable when --backend=cpp")

    p_inspect = sub.add_parser("inspect", help="Inspect a Material's MDL or UsdPreviewSurface network")
    p_inspect.add_argument("src", help="Path to USD file")
    p_inspect.add_argument("mode", choices=["mdl", "usdpreview"], help="Inspection mode: mdl or usdpreview")
    p_inspect.add_argument("prim", help="Material prim path (e.g. /Root/Looks/Mat001)")
    p_inspect.add_argument("--json", action="store_true", help="Output JSON (future placeholder)")

    p_export = sub.add_parser("export-mdl-materials", help="Export MDL materials in this file into standalone material USDs")
    p_export.add_argument("src", help="Path to USD file")
    p_export.add_argument("--out-dir-name", default="mdl_materials", help="Folder name under the file's directory to place exported materials")
    p_export.add_argument("--binary", action="store_true", help="Write .usd binary instead of .usda ascii")
    p_export.add_argument("--placement", choices=["authoring", "root"], default="authoring", help="Where to place exports: alongside the authoring (weakest) layer of each material, or under root file directory")
    p_export.add_argument("--no-external", action="store_true", help="Only export materials authored in root layer (skip externally referenced ones)")
    p_export.add_argument("--mode", choices=["mdl", "preview"], default="mdl", help="Export mode: 'mdl' preserves MDL shader and outputs, 'preview' builds UsdPreviewSurface network")
    p_export.add_argument("--emit-ball", action="store_true", help="Also write a small preview scene with a bound sphere next to each exported material")
    p_export.add_argument("--assets-path-mode", choices=["relative", "absolute"], default="relative", help="Rewrite asset paths as relative (default) or absolute in exported materials")

    # thumbnails generation subcommand (requires Isaac Sim runtime)
    p_thumb = sub.add_parser("thumbnails", help="Render multi-view thumbnails of scene instances with background (Isaac Sim)")
    p_thumb.add_argument("src", help="Path to USD file (scene)")
    p_thumb.add_argument("--out", dest="out", default=None, help="Output directory (defaults to <srcdir>/thumbnails/multi_views_with_bg)")
    p_thumb.add_argument("--instance-scope", dest="instance_scope", default="scene/Instances", help="Scope under /World containing instances")
    p_thumb.add_argument("--width", dest="width", type=int, default=600, help="Image width (default 600)")
    p_thumb.add_argument("--height", dest="height", type=int, default=450, help="Image height (default 450)")
    p_thumb.add_argument("--views", dest="views", type=int, default=6, help="Number of views (even number, split top/bottom; default 6)")
    p_thumb.add_argument("--warmup-steps", dest="warmup_steps", type=int, default=1000, help="Simulation warmup steps before rendering (default 1000)")
    p_thumb.add_argument("--render-steps", dest="render_steps", type=int, default=8, help="Render steps per view (default 8)")
    p_thumb.add_argument("--focal-mm", dest="focal_mm", type=float, default=9.0, help="Camera focal length in mm (default 9.0)")
    p_thumb.add_argument("--bbox-threshold", dest="bbox_threshold", type=float, default=0.8, help="Tight/loose 2D bbox area ratio threshold to accept a view (default 0.8)")
    p_thumb.add_argument("--no-bbox-draw", dest="no_bbox_draw", action="store_true", help="Do not draw bbox on saved images")
    p_thumb.add_argument("--skip-model-filter", dest="skip_model_filter", action="store_true", help="Skip filtering using models dir names")

    # If no subcommand provided, default to no-mdl for convenience
    args_ns, extras = parser.parse_known_args(argv)
    if args_ns.cmd is None:
        # Re-parse as no-mdl
        args_ns = parser.parse_args(["no-mdl"] + (argv or []))

    if args_ns.cmd == "no-mdl":
        # Lazy import to avoid requiring pxr unless actually running no-mdl conversion
        # Load processor module first to set runtime switches, then import class
        only_new = bool(getattr(args_ns, "only_new_usd", False))
        if only_new:
            try:
                from .no_mdl import processor as _proc_mod  # type: ignore
                _proc_mod.RUNTIME_ONLY_NEW_USD = True
            except Exception:
                pass
        from .no_mdl.processor import Processor  # pylint: disable=import-error
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        proc = Processor()
        out = proc.process(src)
        print("\n=== SUMMARY ===")
        for k, v in proc.done.items():
            print(_to_posix(k), "->", _to_posix(v))
        print("\nTop-level new file:", out)
        return 0

    if args_ns.cmd == "mesh-faces":
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        try:
            total = count_mesh_faces(src)
        except RuntimeError as e:
            print("ERROR:", e)
            return 3
        print(f"Total render mesh faces: {total}")
        return 0

    if args_ns.cmd == "mesh-simplify":
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        ratio = max(0.0, min(1.0, float(args_ns.ratio)))
        max_collapses = args_ns.max_collapses
        apply = bool(args_ns.apply)
        out = _to_posix(args_ns.out) if args_ns.out else None
        if apply and not out:
            print("--apply requires --out to be specified")
            return 2
        try:
            from .mesh.simplify import simplify_stage_meshes, list_mesh_face_counts  # lazy import
            # Planning: compute ratio from target faces if provided
            if args_ns.target_faces is not None:
                pairs = list_mesh_face_counts(src)
                total_before = sum(fc for _, fc in pairs)
                if total_before == 0:
                    print("No faces found.")
                    return 0
                ratio = min(1.0, max(0.0, float(args_ns.target_faces) / float(total_before)))
                print(f"[PLAN] total faces before={total_before}, target<={args_ns.target_faces}, suggested --ratio={ratio:.6f}")
                # For C++ backend, if not applying, treat this as plan-only and do not run simplification
                if args_ns.backend == "cpp" and not bool(args_ns.apply):
                    return 0
            if args_ns.backend == "py":
                stats = simplify_stage_meshes(
                    src,
                    ratio=ratio,
                    max_collapses=max_collapses,
                    out_path=out,
                    apply=apply,
                    show_progress=bool(args_ns.progress),
                    progress_interval_collapses=int(args_ns.progress_interval_collapses),
                    time_limit_seconds=float(args_ns.time_limit) if args_ns.time_limit is not None else None,
                )
            else:
                # C++ backend path: iterate meshes, call native exe, then export
                from pxr import Usd, UsdGeom  # type: ignore
                from .mesh.backend_cpp import simplify_mesh_with_cpp
                stage = Usd.Stage.Open(src)
                if stage is None:
                    print("Failed to open stage:", src)
                    return 3
                meshes_total = 0
                meshes_tri = 0
                skipped_non_tri = 0
                faces_before = 0
                faces_after = 0
                verts_before = 0
                verts_after = 0
                for prim in stage.Traverse():
                    if not prim.IsActive() or prim.IsInstanceProxy():
                        continue
                    if prim.GetTypeName() != "Mesh":
                        continue
                    img = UsdGeom.Imageable(prim)
                    purpose = img.ComputePurpose()
                    if purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide):
                        continue
                    meshes_total += 1
                    mesh = UsdGeom.Mesh(prim)
                    counts = mesh.GetFaceVertexCountsAttr().Get()
                    if not counts:
                        continue
                    if not all(int(c) == 3 for c in counts):
                        skipped_non_tri += 1
                        continue
                    meshes_tri += 1
                    try:
                        tb, ta, vb, va = simplify_mesh_with_cpp(
                            prim,
                            _to_posix(args_ns.cpp_exe),
                            ratio=ratio,
                            target_faces=None,
                            max_collapses=max_collapses,
                            time_limit=float(args_ns.time_limit) if args_ns.time_limit is not None else None,
                            progress_interval=int(args_ns.progress_interval_collapses),
                            apply=apply,
                            show_output=bool(args_ns.progress),
                        )
                    except RuntimeError as e:
                        # Skip this mesh but continue others
                        print(f"[SKIP cpp] {prim.GetPath()} -> {e}")
                        continue
                    faces_before += tb
                    faces_after += ta
                    verts_before += vb
                    verts_after += va
                if apply and out:
                    stage.Export(out)
                # Print summary similar to Python backend
                mode = "APPLY" if apply else "DRY-RUN"
                print(f"[{mode}] meshes total={meshes_total} tri={meshes_tri} skipped_non_tri={skipped_non_tri}")
                print(f"faces: {faces_before} -> {faces_after}")
                print(f"verts: {verts_before} -> {verts_after}")
                if apply and out:
                    print("Exported:", out)
                return 0
        except RuntimeError as e:
            print("ERROR:", e)
            return 3
        mode = "APPLY" if apply else "DRY-RUN"
        print(f"[{mode}] meshes total={stats.meshes_total} tri={stats.meshes_tri} skipped_non_tri={stats.skipped_non_tri}")
        print(f"faces: {stats.faces_before} -> {stats.faces_after}")
        print(f"verts: {stats.verts_before} -> {stats.verts_after}")
        if apply and out:
            print("Exported:", out)
        return 0

    if args_ns.cmd == "inspect":
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        try:
            from pxr import Usd  # type: ignore
            from .inspect_material import inspect_material, format_inspect_result
            stage = Usd.Stage.Open(src)
            if stage is None:
                print("Failed to open stage:", src)
                return 3
            data = inspect_material(stage, args_ns.prim, args_ns.mode)
            # (Optional future) JSON output path or stdout
            print(format_inspect_result(data))
            return 0 if data.get("ok") else 4
        except RuntimeError as e:
            print("ERROR:", e)
            return 3

    if args_ns.cmd == "export-mdl-materials":
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        try:
            from pxr import Usd  # type: ignore
            from .export_mdl_materials import export_from_stage
            stage = Usd.Stage.Open(src)
            if stage is None:
                print("Failed to open stage:", src)
                return 3
            results = export_from_stage(
                stage,
                out_dir_name=args_ns.out_dir_name,
                ascii_usd=(not args_ns.binary),
                placement=args_ns.placement,
                include_external=(not args_ns.no_external),
                export_mode=args_ns.mode,
                emit_ball=args_ns.emit_ball,
                assets_path_mode=args_ns.assets_path_mode,
            )
            if not results:
                print("No MDL materials in root layer were found. Nothing exported.")
                return 4
            print("Exported materials:")
            for mpath, fpath in results:
                print(" ", mpath, "->", fpath)
            return 0
        except RuntimeError as e:
            print("ERROR:", e)
            return 3

    if args_ns.cmd == "thumbnails":
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        out_dir = _to_posix(args_ns.out) if args_ns.out else None
        try:
            from .thumbnail import run_thumbnail_pipeline
            code = run_thumbnail_pipeline(
                scene_usd_path=src,
                output_dir=out_dir,
                instance_scope=str(args_ns.instance_scope),
                image_width=int(args_ns.width),
                image_height=int(args_ns.height),
                views=int(args_ns.views),
                warmup_steps=int(args_ns.warmup_steps),
                render_steps=int(args_ns.render_steps),
                focal_mm=float(args_ns.focal_mm),
                bbox_threshold=float(args_ns.bbox_threshold),
                draw_bbox=(not bool(args_ns.no_bbox_draw)),
                skip_model_filter=bool(args_ns.skip_model_filter),
            )
            return int(code)
        except RuntimeError as e:
            print("ERROR:", e)
            return 3

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
