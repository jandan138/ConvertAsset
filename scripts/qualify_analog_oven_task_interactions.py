#!/usr/bin/env python3
"""Qualify the analog oven's reviewed articulated-state gates in Isaac 4.1.

The probe commands and reads back articulation state in a short-lived runtime.
It does not claim robot contact, task success, benchmark score, or calibrated
real-world appliance physics.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


OVEN_ROOT = "/World/AnalogGravityConvectionOven"
OVEN_SOURCE = f"{OVEN_ROOT}/Source"
PROFILE_SCHEMA = "aan.articulated_device_profile.v1"
REPORT_SCHEMA = "aan.articulation_runtime_qualification.v1"
LOCKED_GROUPS = (1, 2, 3, 6, 7, 8, 9, 10)
TASK_GATES = (
    "main_door_state_cycle",
    "temperature_dial_state_cycle",
    "power_rocker_state_cycle",
    "locked_joint_stability",
    "sample_shelf_support",
)
OVEN_DOF_GROUP_ORDER = (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 2)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "unbounded"
    try:
        return [_json_value(float(component)) for component in value]
    except (TypeError, ValueError):
        return str(value)


def _write_report(out_dir: Path, report: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.json"
    path.write_text(
        json.dumps(
            _json_value(report),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "report.sha256.json").write_text(
        json.dumps(
            {"report": path.name, "report_sha256": _sha(path)},
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _expected_dof_mapping() -> list[tuple[int, str, str]]:
    result = []
    for dof_index, group in enumerate(OVEN_DOF_GROUP_ORDER):
        joint_name = "PrismaticJoint" if group in {6, 7, 8, 9} else "RevoluteJoint"
        result.append((dof_index, joint_name, f"{OVEN_SOURCE}/group_{group}/{joint_name}"))
    return result


def _state_cycle_gate(
    *,
    semantic: str,
    target: float,
    target_band: tuple[float, float],
    target_observed: float,
    reset_observed: float,
    reset_band: tuple[float, float],
) -> dict[str, Any]:
    target_pass = target_band[0] <= target_observed <= target_band[1]
    reset_pass = reset_band[0] <= reset_observed <= reset_band[1]
    return {
        "status": "pass" if target_pass and reset_pass else "blocked",
        "method": "Isaac articulation state command/readback cycle",
        "semantic": semantic,
        "commanded_target": target,
        "observed_target": target_observed,
        "required_target_band": list(target_band),
        "observed_reset": reset_observed,
        "required_reset_band": list(reset_band),
        "target_readback_pass": target_pass,
        "reset_readback_pass": reset_pass,
        "claim_boundary": "State travel/readback only; no robot-contact claim.",
    }


def _runtime_profile_gate(observed: object) -> dict[str, Any]:
    value = str(observed or "")
    passed = value == "4.1" or value.startswith("4.1.")
    return {
        "status": "pass" if passed else "blocked",
        "expected_version": "4.1",
        "observed_kit_version": value or None,
    }


def _drive_snapshot(stage: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for prim in stage.Traverse():
        for attribute in prim.GetAttributes():
            if attribute.GetName().startswith("drive:"):
                value = attribute.Get()
                result[str(attribute.GetPath())] = _json_value(
                    list(value) if hasattr(value, "__iter__") and not isinstance(value, str) else value
                )
    return dict(sorted(result.items()))


def _command_cycle(
    articulation: Any,
    world: Any,
    *,
    np: Any,
    index: int,
    target: float,
    target_band: tuple[float, float],
    reset_target: float,
    reset_band: tuple[float, float],
    semantic: str,
) -> dict[str, Any]:
    positions = np.asarray(articulation.get_joint_positions(), dtype=float)
    positions[index] = target
    articulation.set_joint_positions(positions)
    target_observed = float(
        np.asarray(articulation.get_joint_positions(), dtype=float)[index]
    )
    world.step(render=False)
    positions = np.asarray(articulation.get_joint_positions(), dtype=float)
    positions[index] = reset_target
    articulation.set_joint_positions(positions)
    reset_observed = float(
        np.asarray(articulation.get_joint_positions(), dtype=float)[index]
    )
    world.step(render=False)
    return _state_cycle_gate(
        semantic=semantic,
        target=target,
        target_band=target_band,
        target_observed=target_observed,
        reset_observed=reset_observed,
        reset_band=reset_band,
    )


def _run(args: argparse.Namespace) -> dict[str, Any]:
    manifest = _json(args.manifest)
    profile = _json(args.device_profile)
    source = manifest.get("source")
    entrypoints = manifest.get("entrypoints")
    if manifest.get("overall_status") != "pass":
        raise ValueError("prequalification manifest must pass")
    if not isinstance(source, dict) or profile.get("source_sha256") != source.get("sha256"):
        raise ValueError("device profile source hash does not match manifest")
    if profile.get("schema_version") != PROFILE_SCHEMA:
        raise ValueError("unsupported device profile")
    if not isinstance(entrypoints, dict) or entrypoints.get("asset_entry_prim") != OVEN_ROOT:
        raise ValueError("manifest does not expose the reviewed oven root")

    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    try:
        import numpy as np
        import omni.kit.app
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from pxr import Usd, UsdGeom, UsdPhysics

        asset = args.package / "asset.usd"
        asset_sha_before = _sha(asset)
        context = omni.usd.get_context()
        if not context.open_stage(str(asset)):
            raise RuntimeError(f"could not open oven package: {asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(60):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Isaac did not provide an open stage")
        kit_app = omni.kit.app.get_app()
        runtime_gate = _runtime_profile_gate(
            kit_app.get_app_version() if kit_app is not None else None
        )
        if runtime_gate["status"] != "pass":
            raise RuntimeError("Isaac runtime is not 4.1")

        world = World(stage_units_in_meters=1.0, physics_dt=0.01, rendering_dt=0.01)
        articulation = Articulation(OVEN_ROOT, name="analog_oven_qualification")
        world.scene.add(articulation)
        world.reset()
        app.update()
        for _ in range(60):
            world.step(render=False)
        if not articulation.handles_initialized or articulation.num_dof != 11:
            raise RuntimeError(
                f"expected 11 initialized oven DOFs, found {articulation.num_dof}"
            )

        expected = _expected_dof_mapping()
        names = list(articulation.dof_names)
        raw_dof_paths = articulation._articulation_view._dof_paths
        if not raw_dof_paths or len(raw_dof_paths[0]) != 11:
            raise RuntimeError("Isaac did not expose eleven runtime DOF paths")
        dof_paths = [str(path) for path in raw_dof_paths[0]]
        path_to_index = {path: index for index, path in enumerate(dof_paths)}
        expected_paths = {joint_prim for _, _, joint_prim in expected}
        if set(path_to_index) != expected_paths:
            raise RuntimeError("runtime DOF paths do not match the source-bound profile")
        runtime_mapping = [
            {"dof_index": index, "dof_name": names[index], "joint_prim": dof_paths[index]}
            for index in range(11)
        ]
        drives_before = _drive_snapshot(stage)
        task_gates = {
            "main_door_state_cycle": _command_cycle(
                articulation,
                world,
                np=np,
                index=path_to_index[f"{OVEN_SOURCE}/group_4/RevoluteJoint"],
                target=math.radians(90.0),
                target_band=(math.radians(75.0), math.radians(111.72676849365234)),
                reset_target=0.0,
                reset_band=(0.0, math.radians(3.0)),
                semantic="main_door",
            ),
            "temperature_dial_state_cycle": _command_cycle(
                articulation,
                world,
                np=np,
                index=path_to_index[f"{OVEN_SOURCE}/group_11/RevoluteJoint"],
                target=math.radians(60.0),
                target_band=(math.radians(50.0), math.radians(70.0)),
                reset_target=0.0,
                reset_band=(math.radians(-2.0), math.radians(2.0)),
                semantic="temperature_dial",
            ),
            "power_rocker_state_cycle": _command_cycle(
                articulation,
                world,
                np=np,
                index=path_to_index[f"{OVEN_SOURCE}/group_5/RevoluteJoint"],
                target=math.radians(9.0),
                target_band=(math.radians(7.0), math.radians(10.313240051269531)),
                reset_target=math.radians(-10.313240051269531),
                reset_band=(math.radians(-10.313240051269531), math.radians(-8.0)),
                semantic="power_rocker",
            ),
        }
        for _ in range(120):
            world.step(render=False)
        settled = np.asarray(articulation.get_joint_positions(), dtype=float)
        locked_records = []
        for group in LOCKED_GROUPS:
            joint_name = "PrismaticJoint" if group in {6, 7, 8, 9} else "RevoluteJoint"
            index = path_to_index[f"{OVEN_SOURCE}/group_{group}/{joint_name}"]
            value = float(settled[index])
            locked_records.append(
                {"group": group, "dof_index": index, "observed": value, "within_tolerance": abs(value) <= 1.0e-4}
            )
        task_gates["locked_joint_stability"] = {
            "status": "pass" if all(item["within_tolerance"] for item in locked_records) else "blocked",
            "method": "120-step reset-state observation",
            "tolerance": 1.0e-4,
            "locked_dofs": locked_records,
        }

        shelf = stage.GetPrimAtPath(f"{OVEN_SOURCE}/group_7")
        collision_prims = [
            str(prim.GetPath())
            for prim in Usd.PrimRange(shelf)
            if prim.HasAPI(UsdPhysics.CollisionAPI)
            and UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get() is not False
        ]
        bound = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render]
        ).ComputeWorldBound(shelf).ComputeAlignedRange()
        extent = [
            float(bound.GetMax()[axis] - bound.GetMin()[axis]) for axis in range(3)
        ]
        finite_extent = all(math.isfinite(value) and value > 0.0 for value in extent)
        task_gates["sample_shelf_support"] = {
            "status": "pass" if collision_prims and finite_extent else "blocked",
            "method": "composed locked shelf collider and finite-bound readback",
            "shelf_prim": f"{OVEN_SOURCE}/group_7",
            "profile_frame": "sample_shelf_target",
            "collision_prims": collision_prims,
            "world_aabb_extent_m": extent,
            "claim_boundary": "Shelf support geometry only; no sample-vessel placement or robot-policy claim.",
        }

        drives_after = _drive_snapshot(stage)
        drive_integrity = {
            "status": "pass" if drives_before == drives_after else "blocked",
            "before": drives_before,
            "after": drives_after,
        }
        asset_sha_after = _sha(asset)
        manifest_sha = _sha(args.manifest)
        source_sha = str(source["sha256"])
        inputs = {
            "device_profile": {
                "schema_version": PROFILE_SCHEMA,
                "profile_sha256": _sha(args.device_profile),
                "source_sha256": source_sha,
            },
            "integrity": {
                "status": "pass" if asset_sha_before == asset_sha_after else "blocked",
                "oven_manifest_sha256": manifest_sha,
                "oven_asset_usd_sha256_before": asset_sha_before,
                "oven_asset_usd_sha256_after": asset_sha_after,
            },
            "qualified_package": {
                "asset_path": "asset.usd",
                "asset_entry_prim": OVEN_ROOT,
                "runtime_profile": "isaac41",
                "prequalification_manifest_sha256": manifest_sha,
                "asset_usd_sha256_before": asset_sha_before,
                "asset_usd_sha256_after": asset_sha_after,
            },
        }
        status = (
            "pass"
            if all(task_gates[name]["status"] == "pass" for name in TASK_GATES)
            and drive_integrity["status"] == "pass"
            and inputs["integrity"]["status"] == "pass"
            else "blocked"
        )
        return {
            "schema_version": REPORT_SCHEMA,
            "status": status,
            "runtime": {
                "runtime_profile": "isaac41",
                "runtime_profile_gate": runtime_gate,
                "physics_dt_seconds": 0.01,
                "source_mutation": "none",
            },
            "inputs": inputs,
            "runtime_dof_mapping": runtime_mapping,
            "drive_integrity": drive_integrity,
            "task_gates": task_gates,
            "claim_boundary": (
                "This proves the declared state travel/readback, locked joints, and shelf "
                "support geometry. It does not claim robot contact, policy success, benchmark "
                "score, heating behavior, or real-world physical parity."
            ),
        }
    finally:
        # Evidence is written by the caller before the short-lived process exits.
        # Calling SimulationApp.close() is intentionally avoided on Isaac 4.1.
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--device-profile", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.package = args.package.resolve()
    args.manifest = args.manifest.resolve()
    args.device_profile = args.device_profile.resolve()
    args.out_dir = args.out_dir.resolve()
    try:
        report = _run(args)
    except Exception as exc:
        report = {
            "schema_version": REPORT_SCHEMA,
            "status": "blocked",
            "host_failure": f"{type(exc).__name__}: {exc}",
        }
    report_path = _write_report(args.out_dir, report)
    print(json.dumps({"status": report["status"], "report": str(report_path)}), flush=True)
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
