#!/usr/bin/env python3
"""Articulation-safe 60-degree door qualification for OVEN 125 r16."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

try:
    from isaacsim import SimulationApp
except ImportError:
    from omni.isaac.kit import SimulationApp


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _distance(a, b) -> float:
    return math.sqrt(
        sum((float(a[index]) - float(b[index])) ** 2 for index in range(3))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", type=Path, required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args, _ = parser.parse_known_args()
    original_argv = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True})
    sys.argv = original_argv
    report = {
        "schema_version": "aan.ika_oven_r16_door_probe.v1",
        "status": "blocked",
        "usd": str(args.usd.resolve()),
        "root": args.root,
    }
    try:
        import omni.timeline
        import omni.usd
        from pxr import UsdGeom

        source_hash = _sha(args.usd)
        context = omni.usd.get_context()
        if context.open_stage(str(args.usd.resolve())) is False:
            raise RuntimeError(f"Isaac could not open stage: {args.usd}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(16):
            app.update()
        stage = context.get_stage()
        base_path = args.root.rstrip("/") + "/Instance/Body"
        door_path = args.root.rstrip("/") + "/Instance/Door"
        joint_path = args.root.rstrip("/") + "/Instance/Joints/DoorHinge"

        def matrix(path: str):
            return UsdGeom.Xformable(
                stage.GetPrimAtPath(path)
            ).ComputeLocalToWorldTransform(0)

        def rotation_delta(first, second) -> float:
            return abs(
                float((first.GetInverse() * second).ExtractRotation().GetAngle())
            )

        base_initial = matrix(base_path).ExtractTranslation()
        door_initial = matrix(door_path)
        velocity = stage.GetPrimAtPath(joint_path).GetAttribute(
            "drive:angular:physics:targetVelocity"
        )
        authored_velocity = velocity.Get()
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for _ in range(60):
            app.update()
        velocity.Set(45.0)
        for _ in range(180):
            app.update()
        door_open = matrix(door_path)
        velocity.Set(-45.0)
        for _ in range(220):
            app.update()
        velocity.Set(0.0 if authored_velocity is None else authored_velocity)
        for _ in range(30):
            app.update()
        door_closed = matrix(door_path)
        base_final = matrix(base_path).ExtractTranslation()
        timeline.stop()

        opened_deg = rotation_delta(door_initial, door_open)
        closed_deg = rotation_delta(door_initial, door_closed)
        base_drift = _distance(base_initial, base_final)
        checks = {
            "opens_to_60_band": 58.0 <= opened_deg <= 62.0,
            "closes_to_rest_band": closed_deg <= 3.0,
            "base_translation_drift_le_0p1mm": base_drift <= 1.0e-4,
            "source_unchanged": _sha(args.usd) == source_hash,
        }
        report.update(
            {
                "status": "pass" if all(checks.values()) else "blocked",
                "runtime_version": app.app.get_app_version(),
                "door_joint": joint_path,
                "door_open_rotation_delta_deg": opened_deg,
                "door_closed_residual_deg": closed_deg,
                "base_translation_drift_m": base_drift,
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
