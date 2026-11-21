#!/usr/bin/env python3
"""Qualify and promote the compact oven cart under a 100 kg appliance load."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/task09_r13_compact_oven_cart_20260831"
DEFAULT_ISAAC = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/"
    "embodied-eval-os-isaacsim41-py310/bin/python"
)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def evaluate_load_report(report: dict[str, Any]) -> dict[str, Any]:
    initial = report.get("initial_xyz_m", [])
    mid = report.get("mid_xyz_m", [])
    final = report.get("final_xyz_m", [])
    expected = float(report.get("expected_rest_z_m", math.nan))
    valid = all(
        len(value) == 3
        and all(isinstance(item, (int, float)) and math.isfinite(float(item)) for item in value)
        for value in (initial, mid, final)
    ) and math.isfinite(expected)
    height_error = abs(float(final[2]) - expected) if valid else math.inf
    lateral_drift = (
        math.hypot(float(final[0]) - float(initial[0]), float(final[1]) - float(initial[1]))
        if valid
        else math.inf
    )
    last_window_motion = (
        math.sqrt(sum((float(final[i]) - float(mid[i])) ** 2 for i in range(3)))
        if valid
        else math.inf
    )
    passed = bool(
        valid
        and float(report.get("mass_kg", 0.0)) == 100.0
        and height_error <= 0.01
        and lateral_drift <= 0.01
        and last_window_motion <= 0.005
    )
    return {
        "status": "pass" if passed else "blocked",
        "height_error_m": height_error,
        "lateral_drift_m": lateral_drift,
        "last_window_motion_m": last_window_motion,
    }


def _worker(usd: Path, report_path: Path) -> int:
    try:
        from isaacsim import SimulationApp
    except ImportError:
        from omni.isaac.kit import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    import omni.usd
    from omni.isaac.core import World
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    context = omni.usd.get_context()
    if not context.open_stage(str(usd.resolve())):
        raise RuntimeError("cannot open cart package")
    app.update()
    stage = context.get_stage()
    stage.SetEditTarget(Usd.EditTarget(stage.GetSessionLayer()))
    if not stage.GetPrimAtPath("/World/PhysicsScene").IsValid():
        scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(9.81)
    cube = UsdGeom.Cube.Define(stage, "/World/__task09_r13_oven_load")
    cube.CreateSizeAttr(1.0)
    cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.855))
    cube.AddScaleOp().Set(Gf.Vec3f(0.70, 0.652, 0.10))
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim()).CreateCollisionEnabledAttr(True)
    UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim()).CreateRigidBodyEnabledAttr(True)
    UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(100.0)

    world = World(stage_units_in_meters=1.0)
    world.reset()

    def xyz() -> list[float]:
        value = UsdGeom.Xformable(cube.GetPrim()).ComputeLocalToWorldTransform(0).ExtractTranslation()
        return [float(value[index]) for index in range(3)]

    initial = xyz()
    for _ in range(480):
        world.step(render=False)
    mid = xyz()
    for _ in range(120):
        world.step(render=False)
    final = xyz()
    raw = {
        "schema_version": "aan.task09_r13_oven_cart_100kg_load.v1",
        "runtime": "isaac41",
        "mass_kg": 100.0,
        "load_footprint_m": [0.70, 0.652],
        "expected_rest_z_m": 0.805,
        "initial_xyz_m": initial,
        "mid_xyz_m": mid,
        "final_xyz_m": final,
    }
    raw.update(evaluate_load_report(raw))
    _write_json(report_path, raw)
    app.close()
    return 0 if raw["status"] == "pass" else 5


def qualify(output: Path = DEFAULT_OUTPUT, *, isaac: Path = DEFAULT_ISAAC) -> Path:
    output = output.resolve()
    asset = output / "package/asset.usd"
    aan_report = output / "qualification/aan_runtime/report.json"
    if json.loads(aan_report.read_text(encoding="utf-8")).get("status") != "pass":
        raise ValueError("AAN six-probe static-support qualification did not pass")
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    reports = []
    for index in range(3):
        report = output / f"qualification/oven_load/run_{index:02d}.json"
        completed = subprocess.run(
            [
                str(isaac),
                str(Path(__file__).resolve()),
                "--worker",
                "--usd",
                str(asset),
                "--report",
                str(report),
            ],
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        (report.parent / f"run_{index:02d}.stdout.log").write_bytes(completed.stdout)
        (report.parent / f"run_{index:02d}.stderr.log").write_bytes(completed.stderr)
        if not report.is_file():
            raise RuntimeError(f"load worker {index} emitted no report")
        reports.append(json.loads(report.read_text(encoding="utf-8")))
    passed = all(report.get("status") == "pass" for report in reports)
    aggregate = {
        "schema_version": "aan.task09_r13_oven_cart_qualification.v1",
        "status": "pass" if passed else "blocked",
        "runtime": "isaac41",
        "aan_six_probe_report": "../aan_runtime/report.json",
        "aan_six_probe_sha256": _sha(aan_report),
        "oven_load_runs": reports,
        "claim_boundary": (
            "The package supports the declared 0.70 x 0.652 m, 100 kg appliance load "
            "on the compact cart surface. Real structural strength is not calibrated."
        ),
    }
    aggregate_path = output / "qualification/full_report.json"
    _write_json(aggregate_path, aggregate)
    manifest_path = output / "package/evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["overall_status"] = "pass" if passed else "blocked"
    manifest["claims"]["oven_load_support_qualified"] = passed
    manifest["qualification"] = {
        "status": aggregate["status"],
        "report": "../../qualification/full_report.json",
        "report_sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if passed:
        _write_json(
            output / "promotion_receipt.json",
            {
                "schema_version": "aan.static_support_promotion_receipt.v1",
                "status": "promoted",
                "asset_id": "scientific_workbench_task09_r13_compact_oven_cart",
                "runtime": "isaac41",
                "asset_sha256": _sha(asset),
                "qualification_sha256": _sha(aggregate_path),
                "claims": manifest["claims"],
            },
        )
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac-python", type=Path, default=DEFAULT_ISAAC)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--usd", type=Path)
    parser.add_argument("--report", type=Path)
    args, _ = parser.parse_known_args(argv)
    if args.worker:
        if args.usd is None or args.report is None:
            parser.error("--worker requires --usd and --report")
        return _worker(args.usd, args.report)
    print(qualify(args.output, isaac=args.isaac_python))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
