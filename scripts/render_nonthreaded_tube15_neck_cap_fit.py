#!/usr/bin/env python3
"""Render matched old/new non-threaded 15 mL tube evidence."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=("old", "new"))
    args = parser.parse_args()
    saved = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp(
        {"headless": True, "renderer": "RayTracedLighting", "multi_gpu": False}
    )
    sys.argv = saved
    try:
        import numpy as np
        import omni.replicator.core as rep
        import omni.usd
        from pxr import Usd, UsdGeom, UsdPhysics

        from convert_asset.render.single import (
            _camera_rgba,
            _init_camera,
            _rgba_to_rgb,
            _save_rgb_png,
            _set_camera_look_at,
            _setup_environment,
        )

        args.out.mkdir(parents=True, exist_ok=True)
        report_path = args.out / "render_report.json"
        records = (
            json.loads(report_path.read_text()).get("records", {})
            if report_path.exists()
            else {}
        )
        camera_parameters = {
            "elevation_deg": 12.0,
            "azimuth_deg": -75.0,
            "focal_length_mm": 55.0,
            "resolution": [1024, 1024],
        }
        sources = (("old", args.old.resolve()), ("new", args.new.resolve()))
        if args.only:
            sources = tuple(item for item in sources if item[0] == args.only)
        for label, path in sources:
            context = omni.usd.get_context()
            if not context.open_stage(str(path)):
                raise RuntimeError(f"could not open {path}")
            while context.get_stage_loading_status()[2] > 0:
                app.update()
            for _ in range(20):
                app.update()
            stage = context.get_stage()
            stage.SetEditTarget(stage.GetSessionLayer())
            root = stage.GetDefaultPrim()
            if root.HasAPI(UsdPhysics.RigidBodyAPI):
                UsdPhysics.RigidBodyAPI(root).CreateKinematicEnabledAttr(True)
            _setup_environment(stage)
            box = UsdGeom.BBoxCache(
                Usd.TimeCode.Default(),
                [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
            ).ComputeWorldBound(root).ComputeAlignedBox()
            minimum = np.asarray(box.GetMin(), dtype=float)
            maximum = np.asarray(box.GetMax(), dtype=float)
            center = (minimum + maximum) * 0.5
            diagonal = float(np.linalg.norm(maximum - minimum))
            camera = _init_camera(
                f"NonThreadedTubeFit_{label}",
                camera_parameters["resolution"][0],
                camera_parameters["resolution"][1],
                camera_parameters["focal_length_mm"],
            )
            _set_camera_look_at(
                camera,
                center,
                distance=max(0.22, diagonal * 2.2),
                elevation=camera_parameters["elevation_deg"],
                azimuth=camera_parameters["azimuth_deg"],
            )
            for _ in range(4):
                rep.orchestrator.step(
                    rt_subframes=4, pause_timeline=True, delta_time=0.0
                )
            rgba = _camera_rgba(camera)
            rgb = _rgba_to_rgb(rgba, background_color=(34, 37, 43))
            output = args.out / f"{label}.png"
            if rgb is None or not _save_rgb_png(output, rgb):
                raise RuntimeError(f"could not save {output}")
            records[label] = {
                "source": str(path),
                "source_sha256": _sha(path),
                "image": output.name,
                "image_sha256": _sha(output),
                "bbox_diagonal_m": diagonal,
            }
        report = {
            "schema_version": "aan.nonthreaded_tube15_neck_cap_visual_compare.v1",
            "status": "pass",
            "renderer": "RayTracedLighting",
            "same_camera_parameters": True,
            "camera": camera_parameters,
            "records": records,
            "claim_boundary": "Matched visual comparison only; no independent blind review.",
        }
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
