#!/usr/bin/env python3
"""Probe GUI-like slow cap rotation while leaving Z to PhysX in Isaac 4.1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import traceback
from typing import Any


def classify_against_baseline(
    *,
    baseline_descent_m: float,
    manipulated_descent_m: float,
    relative_z_final_m: float,
    maximum_radial_offset_m: float,
    body_displacement_m: float,
    tail_span_m: float,
    hard_errors: list[str],
) -> dict[str, Any]:
    checks = {
        "extra_descent_over_baseline": manipulated_descent_m - baseline_descent_m >= 0.005,
        "closed_band": 1.070 <= relative_z_final_m <= 1.080,
        "radial_alignment": maximum_radial_offset_m <= 0.005,
        "body_stable": body_displacement_m <= 0.001,
        "tail_stable": tail_span_m <= 0.001,
        "no_hard_errors": not hard_errors,
    }
    return {"checks": checks, "overall_status": "pass" if all(checks.values()) else "blocked"}


def _quat_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--start", choices=("default", "entrance"), required=True)
    parser.add_argument("--direction", type=int, choices=(-1, 0, 1), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--speed-deg-s", type=float, default=15.0)
    args = parser.parse_args()

    from isaacsim import SimulationApp

    saved = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = saved
    try:
        import carb
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.timeline
        import omni.usd
        from omni.isaac.dynamic_control import _dynamic_control
        from pxr import Gf, UsdGeom, Usd

        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        context = omni.usd.get_context()
        if not context.open_stage(str(args.source.resolve())):
            raise RuntimeError("could not open source")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        if args.start == "entrance":
            cap_prim = stage.GetPrimAtPath("/World/cap")
            attr = cap_prim.GetAttribute("xformOp:translate")
            value = attr.Get()
            attr.Set(Gf.Vec3d(float(value[0]), float(value[1]), 1.104))
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)

        def usd_position(path: str):
            matrix = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(
                stage.GetPrimAtPath(path)
            )
            return tuple(float(v) for v in matrix.ExtractTranslation())

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        app.update()
        dc = _dynamic_control.acquire_dynamic_control_interface()
        cap_handle = dc.get_rigid_body("/World/cap")
        initial_pose = dc.get_rigid_body_pose(cap_handle)
        base_quat = (
            float(initial_pose.r.x),
            float(initial_pose.r.y),
            float(initial_pose.r.z),
            float(initial_pose.r.w),
        )
        body_initial = usd_position("/World/shiguan")
        cap_initial = usd_position("/World/cap")
        relative_initial = cap_initial[2] - body_initial[2]
        samples = []
        stopped = False
        stop_update = None
        rotation_deg = 0.0
        max_updates = 360 if args.direction == 0 else 1440
        hold_remaining = 0
        for update in range(max_updates):
            app.update()
            bp = usd_position("/World/shiguan")
            cp = usd_position("/World/cap")
            relative_z = cp[2] - bp[2]
            if args.direction and not stopped:
                rotation_deg += args.direction * args.speed_deg_s / 60.0
                pose = dc.get_rigid_body_pose(cap_handle)
                yaw = math.radians(rotation_deg)
                q = _quat_mul((0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)), base_quat)
                guided = _dynamic_control.Transform(
                    (bp[0], bp[1], float(pose.p.z)), q
                )
                dc.set_rigid_body_pose(cap_handle, guided)
                threshold = 1.075 if args.start == "default" else 1.080
                minimum_rotation = 5.0
                if abs(rotation_deg) >= minimum_rotation and relative_z <= threshold:
                    stopped = True
                    stop_update = update
                    hold_remaining = 120
            elif args.direction and stopped:
                pose = dc.get_rigid_body_pose(cap_handle)
                guided = _dynamic_control.Transform(
                    (bp[0], bp[1], float(pose.p.z)),
                    _quat_mul(
                        (0.0, 0.0, math.sin(math.radians(rotation_deg) / 2.0), math.cos(math.radians(rotation_deg) / 2.0)),
                        base_quat,
                    ),
                )
                dc.set_rigid_body_pose(cap_handle, guided)
                hold_remaining -= 1
            samples.append(
                {
                    "update": update,
                    "rotation_deg": rotation_deg,
                    "body": bp,
                    "cap": cp,
                    "relative_z_m": relative_z,
                }
            )
            radial = math.hypot(cp[0] - bp[0], cp[1] - bp[1])
            if radial > 0.10 or relative_z < 0.90 or (stopped and hold_remaining <= 0):
                break
        timeline.stop()
        final = samples[-1]
        tail = [float(s["relative_z_m"]) for s in samples[-min(60, len(samples)):]]
        log = log_path.read_text(errors="replace")[log_offset:] if log_path.exists() else ""
        markers = ("CUDA error", "illegal memory access", "PhysX error")
        hard = list(dict.fromkeys(line for line in log.splitlines() if any(m in line for m in markers)))
        result = {
            "schema_version": "aan.original_threaded_tube15_slow_manipulator.v1",
            "runtime": "isaac41",
            "start": args.start,
            "direction": args.direction,
            "speed_deg_s": args.speed_deg_s,
            "protocol": "gui_like_yaw_and_xy_alignment_z_from_physx",
            "relative_z_initial_m": relative_initial,
            "relative_z_final_m": float(final["relative_z_m"]),
            "descent_m": relative_initial - float(final["relative_z_m"]),
            "rotation_deg_final": rotation_deg,
            "stop_update": stop_update,
            "body_displacement_m": math.dist(body_initial, final["body"]),
            "maximum_radial_offset_m": max(
                math.hypot(s["cap"][0] - s["body"][0], s["cap"][1] - s["body"][1])
                for s in samples
            ),
            "tail_span_m": max(tail) - min(tail),
            "hard_errors": hard,
            "trace": samples[::30] + [samples[-1]],
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
        return 0
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
