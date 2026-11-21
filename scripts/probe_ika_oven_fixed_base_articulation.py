#!/usr/bin/env python3
"""Isaac runtime probe for an OVEN 125 fixed-base articulation."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from isaacsim import SimulationApp
except ImportError:  # Legacy Kit layout.
    from omni.isaac.kit import SimulationApp


def _distance(a, b) -> float:
    return math.sqrt(
        sum((float(a[index]) - float(b[index])) ** 2 for index in range(3))
    )


def _world_positions(stage, link_paths):
    from pxr import Usd, UsdGeom

    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    return {
        path: tuple(
            cache.GetLocalToWorldTransform(
                stage.GetPrimAtPath(path)
            ).ExtractTranslation()
        )
        for path in link_paths
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", type=Path, required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=180)
    args, _ = parser.parse_known_args()

    app = SimulationApp({"headless": True})
    report = {
        "schema_version": "aan.ika_oven_fixed_base_articulation_probe.v1",
        "status": "blocked",
        "usd": str(args.usd.resolve()),
        "root": args.root,
    }
    try:
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.dynamic_control import _dynamic_control
        from pxr import UsdPhysics

        context = omni.usd.get_context()
        opened = context.open_stage(str(args.usd.resolve()))
        if opened is False:
            raise RuntimeError(f"Isaac could not open stage: {args.usd}")
        for _ in range(10):
            app.update()
        stage = context.get_stage()
        root = stage.GetPrimAtPath(args.root)
        if not root:
            raise RuntimeError(f"articulation root is missing: {args.root}")
        link_paths = [
            str(prim.GetPath())
            for prim in stage.Traverse()
            if prim.GetPath().HasPrefix(root.GetPath())
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
        ]
        initial = _world_positions(stage, link_paths)
        world = World(stage_units_in_meters=1.0)
        articulation = Articulation(prim_path=args.root, name="oven_r16_probe")
        world.scene.add(articulation)
        world.reset()
        articulation.initialize()
        dynamic_control = _dynamic_control.acquire_dynamic_control_interface()
        handle = dynamic_control.get_articulation(args.root)
        for _ in range(args.steps):
            world.step(render=False)
        final = _world_positions(stage, link_paths)
        drift = {path: _distance(initial[path], final[path]) for path in link_paths}
        base_path = args.root.rstrip("/") + "/Instance/Body"
        dof_count = int(articulation.num_dof)
        checks = {
            "articulation_view_initialized": bool(articulation.handles_initialized),
            "dynamic_control_handle_valid": bool(handle),
            "dof_count_is_16": dof_count == 16,
            "base_translation_drift_le_0p1mm": drift.get(base_path, 1.0) <= 1.0e-4,
            "all_link_translation_drift_le_5mm": max(drift.values(), default=1.0)
            <= 0.005,
        }
        report.update(
            {
                "status": "pass" if all(checks.values()) else "blocked",
                "runtime_version": app.app.get_app_version(),
                "steps": args.steps,
                "dof_count": dof_count,
                "link_count": len(link_paths),
                "base_link": base_path,
                "base_translation_drift_m": drift.get(base_path),
                "max_link_translation_drift_m": max(drift.values(), default=None),
                "link_translation_drift_m": drift,
                "checks": checks,
            }
        )
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        app.close()
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
