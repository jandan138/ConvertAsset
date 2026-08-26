#!/usr/bin/env python3
"""One cold Isaac 4.1 gravity-only thread-phase probe on colleague USD."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import traceback
from typing import Any


BODY = "/World/shiguan"
CAP = "/World/cap"
CAP_START_Z_M = 1.104
TARGET_CLOSED_Z_M = 1.075


def classify_phase(
    *,
    relative_z_initial_m: float,
    relative_z_final_m: float,
    body_displacement_m: float,
    maximum_radial_offset_m: float,
    maximum_cap_z_m: float,
    tail_relative_z_span_m: float,
    hard_errors: list[str],
) -> dict[str, Any]:
    descent = relative_z_initial_m - relative_z_final_m
    checks = {
        "gravity_descent_in_expected_range": 0.015 <= descent <= 0.035,
        "closed_band": abs(relative_z_final_m - TARGET_CLOSED_Z_M) <= 0.0051,
        "body_held_by_source_cubes": body_displacement_m <= 0.001,
        "radially_aligned": maximum_radial_offset_m <= 0.005,
        "no_launch": maximum_cap_z_m <= relative_z_initial_m + 0.20,
        "settled_tail": tail_relative_z_span_m <= 0.001,
        "no_hard_errors": not hard_errors,
    }
    return {
        "descent_m": descent,
        "checks": checks,
        "overall_status": "pass" if all(checks.values()) else "blocked",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--yaw-deg", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=480)
    args = parser.parse_args()

    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = saved
    try:
        import carb
        import omni.kit.app
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.timeline
        import omni.usd
        from pxr import Gf, Sdf, Usd, UsdGeom

        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        context = omni.usd.get_context()
        if not context.open_stage(str(args.source.resolve())):
            raise RuntimeError("could not open colleague source")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        cap = stage.GetPrimAtPath(CAP)
        body = stage.GetPrimAtPath(BODY)
        if not cap.IsValid() or not body.IsValid():
            raise RuntimeError("source tube/cap prims are missing")

        translate = cap.GetAttribute("xformOp:translate")
        current = translate.Get()
        translate.Set(Gf.Vec3d(float(current[0]), float(current[1]), CAP_START_Z_M))
        phase_name = "xformOp:rotateZ:threadPhase"
        cap.CreateAttribute(phase_name, Sdf.ValueTypeNames.Double).Set(float(args.yaw_deg))
        order_attr = cap.GetAttribute("xformOpOrder")
        order = list(order_attr.Get() or [])
        if phase_name in order:
            order.remove(phase_name)
        insert_at = 1 if order and order[0] == "xformOp:translate" else 0
        order.insert(insert_at, phase_name)
        order_attr.Set(order)
        cap.GetAttribute("physics:velocity").Set(Gf.Vec3f(0.0))
        cap.GetAttribute("physics:angularVelocity").Set(Gf.Vec3f(0.0))

        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        for _ in range(10):
            app.update()

        def position(path: str):
            matrix = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(
                stage.GetPrimAtPath(path)
            )
            return tuple(float(v) for v in matrix.ExtractTranslation())

        body_initial = position(BODY)
        cap_initial = position(CAP)
        relative_initial = cap_initial[2] - body_initial[2]
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        samples = []
        for index in range(args.updates):
            app.update()
            bp = position(BODY)
            cp = position(CAP)
            samples.append(
                {
                    "update": index,
                    "body": bp,
                    "cap": cp,
                    "relative_z_m": cp[2] - bp[2],
                }
            )
        timeline.stop()
        body_final = samples[-1]["body"]
        cap_final = samples[-1]["cap"]
        relative_final = float(samples[-1]["relative_z_m"])
        body_displacement = math.dist(body_initial, body_final)
        radial = [
            math.hypot(s["cap"][0] - s["body"][0], s["cap"][1] - s["body"][1])
            for s in samples
        ]
        tail = [float(s["relative_z_m"]) for s in samples[-60:]]
        log = log_path.read_text(errors="replace")[log_offset:] if log_path.exists() else ""
        markers = ("CUDA error", "illegal memory access", "PhysX error")
        hard = list(
            dict.fromkeys(
                line for line in log.splitlines() if any(m in line for m in markers)
            )
        )
        result = {
            "schema_version": "aan.original_threaded_tube15_gravity_phase.v1",
            "runtime": str(omni.kit.app.get_app().get_app_version()),
            "source": str(args.source.resolve()),
            "yaw_deg": float(args.yaw_deg),
            "protocol": "session_initial_phase_then_timeline_gravity_only",
            "updates": args.updates,
            "body_initial": body_initial,
            "body_final": body_final,
            "cap_initial": cap_initial,
            "cap_final": cap_final,
            "relative_z_initial_m": relative_initial,
            "relative_z_final_m": relative_final,
            "body_displacement_m": body_displacement,
            "maximum_radial_offset_m": max(radial),
            "maximum_cap_z_m": max(float(s["cap"][2]) for s in samples),
            "minimum_cap_z_m": min(float(s["cap"][2]) for s in samples),
            "tail_relative_z_span_m": max(tail) - min(tail),
            "hard_errors": hard,
            "sampled_trace": samples[::30] + [samples[-1]],
        }
        result.update(
            classify_phase(
                relative_z_initial_m=relative_initial,
                relative_z_final_m=relative_final,
                body_displacement_m=body_displacement,
                maximum_radial_offset_m=max(radial),
                maximum_cap_z_m=result["maximum_cap_z_m"],
                tail_relative_z_span_m=result["tail_relative_z_span_m"],
                hard_errors=hard,
            )
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
        return 0 if result["overall_status"] == "pass" else 2
    except BaseException:
        traceback.print_exc()
        return 3
    finally:
        pass


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    import os

    os._exit(code)
