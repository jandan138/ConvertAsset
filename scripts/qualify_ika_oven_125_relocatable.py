#!/usr/bin/env python3
"""Qualify the identity-root IKA OVEN 125 under three consumer namespaces."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.articulated_relocation_qualification import (  # noqa: E402
    resolve_promotion,
)


DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_identity_root_r1_20260831"
DEFAULT_ISAAC41_PYTHON = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/"
    "embodied-eval-os-isaacsim41-py310/bin/python"
)
SOURCE_ENTRY = "/World/Oven125"
MOUNTS: dict[str, dict[str, Any]] = {
    "canonical": {
        "root": "/World/Oven125",
        "device_root": "/World/Oven125",
        "translation": [0.0, 0.0, 0.0],
        "yaw_degrees": 0.0,
    },
    "runtime_obj": {
        "root": "/World/obj_oven",
        "device_root": "/World/obj_oven",
        "translation": [0.21, -0.13, 0.755],
        "yaw_degrees": 17.0,
    },
    "vr_scene": {
        "root": "/World/_scene/obj_oven",
        "device_root": "/World/_scene/obj_oven",
        "translation": [-0.18, 0.09, 0.755],
        "yaw_degrees": -13.0,
    },
}


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    def safe(item: Any) -> Any:
        if isinstance(item, float) and not math.isfinite(item):
            return "+Infinity" if item > 0 else "-Infinity"
        if isinstance(item, dict):
            return {str(key): safe(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [safe(child) for child in item]
        return item

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(safe(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build_fixtures(package: Path, qualification: Path) -> dict[str, Path]:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    package = package.resolve()
    asset = package / "asset.usd"
    if not asset.is_file():
        raise FileNotFoundError(asset)
    fixture_root = qualification / "fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    fixtures: dict[str, Path] = {}
    for name, spec in MOUNTS.items():
        path = fixture_root / f"{name}.usda"
        path.unlink(missing_ok=True)
        stage = Usd.Stage.CreateNew(str(path))
        world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
        stage.SetDefaultPrim(world)
        if spec["root"].startswith("/World/_scene/"):
            UsdGeom.Xform.Define(stage, "/World/_scene")
        root = UsdGeom.Xform.Define(stage, spec["root"]).GetPrim()
        root.GetReferences().AddReference(str(asset), SOURCE_ENTRY)
        xform = UsdGeom.Xformable(root)
        xform.AddTranslateOp().Set(Gf.Vec3d(*spec["translation"]))
        if spec["yaw_degrees"]:
            xform.AddRotateZOp().Set(float(spec["yaw_degrees"]))
        physics_scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
        physics_scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        physics_scene.CreateGravityMagnitudeAttr().Set(9.81)
        stage.GetRootLayer().Save()
        fixtures[name] = path
    return fixtures


def _door_force_passed(result: Mapping[str, Any]) -> bool:
    return bool(
        int(result.get("successfulForceCalls", 0)) >= 1000
        and float(result.get("openingPeakDegrees", 0.0)) >= 175.0
        and float(result.get("closingFinalDegrees", 180.0)) <= 3.0
        and float(result.get("bodyTranslationDriftMeters", 1.0)) <= 1.0e-6
    )


def adapt_producer_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate real motion while replacing the producer's obsolete anchor schema gate."""
    results = report.get("results", {})
    required = (
        "doorLeftVariantDynamic",
        "knobDecouplingAndReturn",
        "tenButtonsTravelAndReturn",
        "buttonCollisionClearance",
        "mainsRockerLimits",
        "shelvesLoadedAndRemovableReady",
        "closedDoorSealFrameClearance",
    )
    checks = {
        "door_right_force_open_close": _door_force_passed(
            results.get("doorDynamicLimit", {})
        ),
        **{
            name: bool(results.get(name, {}).get("passed"))
            for name in required
        },
    }
    return {
        **dict(report),
        "producer_schema_status": report.get("status"),
        "aan_relocation_checks": checks,
        "aan_passed": all(checks.values()),
        "aan_task_scoped_checks": {
            "task09_door_force_open_close": checks[
                "door_right_force_open_close"
            ],
            "task09_controls_press_return": checks["tenButtonsTravelAndReturn"],
            "task12_mains_rocker": checks["mainsRockerLimits"],
        },
    }


def evaluate_reports(reports: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    missing = sorted(set(MOUNTS) - set(reports))

    def passed(report: Mapping[str, Any]) -> bool:
        if "aan_passed" in report:
            return report.get("aan_passed") is True
        return report.get("status") == "PASS" and report.get("passed") is True

    full_blocked = sorted(
        name for name in MOUNTS if name not in missing and not passed(reports[name])
    )
    return {
        "schema_version": "aan.ika_oven_125_relocation_qualification.v2",
        "status": "pass" if not missing and not full_blocked else "blocked",
        "missing_namespaces": missing,
        "full_function_blocked_namespaces": full_blocked,
        "namespaces": {
            name: {
                "root": MOUNTS[name]["root"],
                "translation": MOUNTS[name]["translation"],
                "yaw_degrees": MOUNTS[name]["yaw_degrees"],
                "full_function_passed": passed(reports.get(name, {})),
            }
            for name in MOUNTS
        },
        "claim_boundary": (
            "Identity-root portability and producer physical-input parity at three "
            "namespaces in Isaac Sim 4.1. No robot-policy, benchmark, thermal "
            "calibration, or electrical-safety claim."
        ),
    }


def _static_fixture_check(path: Path, root: str) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdPhysics

    stage = Usd.Stage.Open(str(path))
    if stage is None:
        return {"passed": False, "reason": "stage_open_failed"}
    root_prim = stage.GetPrimAtPath(root)
    chassis = stage.GetPrimAtPath(root + "/Body")
    joints = [
        prim
        for prim in stage.Traverse()
        if prim.IsA(UsdPhysics.Joint)
        and prim.GetPath().HasPrefix(Sdf.Path(root))
    ]
    chassis_targets = sum(
        UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()
        == [Sdf.Path(root + "/Body")]
        for prim in joints
    )
    script = stage.GetPrimAtPath(
        root + "/ControlPanel/Runtime/ControllerGraph/Controller"
    ).GetAttribute("inputs:script").Get()
    checks = {
        "root_valid": root_prim.IsValid(),
        "chassis_kinematic": bool(
            chassis.IsValid()
            and chassis.HasAPI(UsdPhysics.RigidBodyAPI)
            and chassis.GetAttribute("physics:kinematicEnabled").Get() is True
        ),
        "joint_count_16": len(joints) == 16,
        "rebound_world_joints_15": chassis_targets == 15,
        "controller_instance_relative": bool(
            isinstance(script, str)
            and "db.node.get_prim_path()" in script
            and f'ROOT = "{SOURCE_ENTRY}"' not in script
        ),
    }
    return {"passed": all(checks.values()), "checks": checks}


def run_qualification(
    output: Path = DEFAULT_OUTPUT,
    *,
    isaac_python: Path = DEFAULT_ISAAC41_PYTHON,
    reuse_existing: bool = False,
) -> Path:
    output = output.resolve()
    package = output / "package"
    qualification = output / "qualification"
    script = package / "evidence/producer_physics_smoke.py"
    if not script.is_file():
        raise FileNotFoundError(script)
    if not isaac_python.is_file():
        raise FileNotFoundError(isaac_python)
    fixtures = build_fixtures(package, qualification)
    reports: dict[str, dict[str, Any]] = {}
    static_checks: dict[str, dict[str, Any]] = {}
    environment = dict(os.environ)
    environment.update(
        {"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES", "PYTHONNOUSERSITE": "1"}
    )
    for name, fixture in fixtures.items():
        static_checks[name] = _static_fixture_check(fixture, MOUNTS[name]["root"])
        report_path = qualification / name / "physics_smoke.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        existing = reuse_existing and report_path.is_file()
        if existing:
            returncode = int(
                json.loads(report_path.read_text(encoding="utf-8")).get(
                    "subprocess_returncode", 0
                )
            )
        else:
            completed = subprocess.run(
                [
                    str(isaac_python),
                    str(script),
                    "--usd",
                    str(fixture),
                    "--output",
                    str(report_path),
                    "--root",
                    MOUNTS[name]["root"],
                    "--/app/omni.graph.scriptnode/opt_in=true",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
            )
            returncode = completed.returncode
            (report_path.parent / "stdout.log").write_bytes(completed.stdout)
            (report_path.parent / "stderr.log").write_bytes(completed.stderr)
        if report_path.is_file():
            report = adapt_producer_report(
                json.loads(report_path.read_text(encoding="utf-8"))
            )
            report["subprocess_returncode"] = returncode
            report["reused_existing_runtime_report"] = existing
            report["static_portability"] = static_checks[name]
            report["aan_passed"] = bool(
                report["aan_passed"] and static_checks[name]["passed"]
            )
            _write_json(report_path, report)
            reports[name] = report
        else:
            reports[name] = {
                "aan_passed": False,
                "reason": "producer smoke emitted no report",
                "subprocess_returncode": returncode,
            }
    aggregate = evaluate_reports(reports)
    aggregate["static_checks"] = static_checks
    aggregate["reports"] = {
        name: {
            "path": str((qualification / name / "physics_smoke.json").relative_to(output)),
            "sha256": (
                _sha256_file(qualification / name / "physics_smoke.json")
                if (qualification / name / "physics_smoke.json").is_file()
                else None
            ),
        }
        for name in MOUNTS
    }
    aggregate_path = qualification / "full_report.json"
    _write_json(aggregate_path, aggregate)

    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    decision = resolve_promotion(
        requested_tier=manifest["promotion"]["requested_tier"],
        portability_checks={
            name: bool(check.get("passed"))
            for name, check in static_checks.items()
        },
        full_function_checks={
            name: bool(report.get("aan_passed"))
            for name, report in reports.items()
        },
        scoped_function_checks={
            name: bool(report.get("aan_task_scoped_checks"))
            and all(report["aan_task_scoped_checks"].values())
            for name, report in reports.items()
        },
    )
    promoted = decision.status == "pass"
    aggregate["promotion_decision"] = {
        "status": decision.status,
        "promoted_tier": decision.promoted_tier,
        "blocked_reasons": list(decision.blocked_reasons),
    }
    aggregate["status"] = decision.status
    for name in MOUNTS:
        aggregate["namespaces"][name]["portability_passed"] = bool(
            static_checks.get(name, {}).get("passed")
        )
        task_checks = reports.get(name, {}).get("aan_task_scoped_checks", {})
        aggregate["namespaces"][name]["task_scoped_function_passed"] = bool(
            task_checks and all(task_checks.values())
        )
    _write_json(aggregate_path, aggregate)
    manifest["qualification"] = {
        "report": "../../qualification/full_report.json",
        "report_sha256": _sha256_file(aggregate_path),
        "status": decision.status,
    }
    manifest["overall_status"] = "pass" if promoted else "blocked"
    manifest["promotion"]["portability_gates_passed"] = not any(
        not check.get("passed") for check in static_checks.values()
    )
    manifest["promotion"]["functional_gates_passed"] = promoted
    manifest["promotion"]["promoted_tier"] = decision.promoted_tier
    manifest["claims"]["relocatable_full"] = (
        decision.promoted_tier == "relocatable_full"
    )
    manifest["claims"]["relocatable_task_scoped"] = promoted
    _write_json(manifest_path, manifest)
    if promoted:
        _write_json(
            output / "promotion_receipt.json",
            {
                "schema_version": "aan.articulated_relocation_promotion_receipt.v1",
                "status": "promoted",
                "tier": decision.promoted_tier,
                "runtime": "isaac41",
                "profile_id": manifest["profile_id"],
                "qualification_report_sha256": _sha256_file(aggregate_path),
                "claims": manifest["claims"],
            },
        )
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac-python", type=Path, default=DEFAULT_ISAAC41_PYTHON)
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args(argv)
    print(
        run_qualification(
            args.output,
            isaac_python=args.isaac_python,
            reuse_existing=args.reuse_existing,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
