#!/usr/bin/env python3
"""Build and statically screen simple Task 02 graduated-cylinder collision routes."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping


SOURCE = "/World/Transfer/Source"
BODY = SOURCE + "/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002"
RIM = SOURCE + "/Visual/Source/Thickened_Rim/Torus_002"
BOTTOM = SOURCE + "/Visual/Source/Closed_Inner_Bottom/Cylinder_006"
HEX_BASE = SOURCE + "/Visual/Source/Hex_Base/Cylinder_004"
CONNECTOR = SOURCE + "/Visual/Source/Base_Connector/Cylinder_005"
SPOUT = SOURCE + "/Visual/Source/Pour_Spout/Pour_Spout_Mesh_002"
UNIFIED = SOURCE + "/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"
LEGACY = SOURCE + "/__aan_collision_proxy"

ROUTES: dict[str, dict[str, Any]] = {
    "visual_components_sdf": {
        "cavity_radius_m": 0.019185,
        "cavity_floor_z_m": 0.016,
        "cavity_rim_z_m": 0.27659,
    },
    "visual_mesh_direct_convex": {
        "cavity_radius_m": 0.019185,
        "cavity_floor_z_m": 0.016,
        "cavity_rim_z_m": 0.27659,
    },
    "qualified_unified_proxy_control": {
        "cavity_radius_m": 0.0165,
        "cavity_floor_z_m": 0.016,
        "cavity_rim_z_m": 0.27824,
    },
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _apply_mesh_collision(stage: Any, path: str, approximation: str) -> None:
    from pxr import Sdf, UsdPhysics

    prim = stage.OverridePrim(path)
    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True).Set(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(approximation)
    if approximation == "convexDecomposition":
        for name, type_name, value in (
            ("physxCollision:contactOffset", Sdf.ValueTypeNames.Float, 0.005),
            ("physxCollision:restOffset", Sdf.ValueTypeNames.Float, 0.003),
            (
                "physxConvexDecompositionCollision:errorPercentage",
                Sdf.ValueTypeNames.Float,
                0.1,
            ),
            (
                "physxConvexDecompositionCollision:minThickness",
                Sdf.ValueTypeNames.Float,
                0.001,
            ),
            (
                "physxConvexDecompositionCollision:shrinkWrap",
                Sdf.ValueTypeNames.Bool,
                True,
            ),
            (
                "physxConvexDecompositionCollision:voxelResolution",
                Sdf.ValueTypeNames.Int,
                500_000,
            ),
        ):
            prim.CreateAttribute(name, type_name).Set(value)


def author_variant_overlay(*, scene: Path, output: Path, route: str) -> dict[str, Any]:
    from pxr import Sdf, Usd

    if route not in ROUTES:
        raise ValueError(f"unsupported collision route: {route}")
    source = Usd.Stage.Open(str(scene.resolve()))
    if source is None:
        raise ValueError(f"cannot open fixture scene: {scene}")
    for path in (BODY, RIM, BOTTOM, HEX_BASE, CONNECTOR, SPOUT, UNIFIED):
        if not source.GetPrimAtPath(path).IsValid():
            raise ValueError(f"fixture is missing required prim: {path}")
    layer = Sdf.Layer.CreateNew(str(output))
    stage = Usd.Stage.Open(layer)
    if route != "qualified_unified_proxy_control":
        stage.OverridePrim(UNIFIED).SetActive(False)
        stage.OverridePrim(LEGACY).SetActive(False)
        if route == "visual_components_sdf":
            _apply_mesh_collision(stage, BODY, "sdf")
        else:
            _apply_mesh_collision(stage, BODY, "convexDecomposition")
        _apply_mesh_collision(stage, RIM, "sdf")
        for path in (BOTTOM, HEX_BASE, CONNECTOR, SPOUT):
            _apply_mesh_collision(stage, path, "convexHull")
    stage.GetRootLayer().Save()
    return {
        "schema_version": "aan.task02_collision_route_overlay.v1",
        "route": route,
        "source_fixture": str(scene.resolve()),
        "changed_collision_paths": (
            []
            if route == "qualified_unified_proxy_control"
            else [BODY, RIM, BOTTOM, HEX_BASE, CONNECTOR, SPOUT]
        ),
        "unified_proxy_disabled": route != "qualified_unified_proxy_control",
    }


def _topology(stage: Any, path: str) -> dict[str, Any]:
    from pxr import UsdGeom

    prim = stage.GetPrimAtPath(path)
    mesh = UsdGeom.Mesh(prim)
    counts = [int(value) for value in (mesh.GetFaceVertexCountsAttr().Get() or [])]
    indices = [int(value) for value in (mesh.GetFaceVertexIndicesAttr().Get() or [])]
    edges: Counter[tuple[int, int]] = Counter()
    cursor = 0
    for count in counts:
        face = indices[cursor : cursor + count]
        cursor += count
        for index, start in enumerate(face):
            edges[tuple(sorted((start, face[(index + 1) % len(face)])))] += 1
    return {
        "prim_path": path,
        "point_count": len(mesh.GetPointsAttr().Get() or []),
        "face_count": len(counts),
        "boundary_edge_count": sum(value == 1 for value in edges.values()),
        "non_manifold_edge_count": sum(value > 2 for value in edges.values()),
    }


def evaluate_static_runs(runs: list[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if len(runs) != 3:
        blockers.append("required_three_cold_runs")
    for index, run in enumerate(runs, start=1):
        if int(run.get("particle_count", -1)) != 580:
            blockers.append(f"run_{index}:particle_count_not_580")
        if int(run.get("outside_source_count", 10**9)) > 2:
            blockers.append(f"run_{index}:outside_source_above_2")
        if int(run.get("below_source_floor_count", 10**9)) != 0:
            blockers.append(f"run_{index}:below_source_floor")
        if run.get("hard_runtime_errors", []) != []:
            blockers.append(f"run_{index}:hard_runtime_errors")
    return {
        "overall_status": "pass" if not blockers else "blocked",
        "blocked_reasons": blockers,
        "run_count": len(runs),
        "maximum_outside_source_count": max(
            (int(run.get("outside_source_count", 10**9)) for run in runs), default=None
        ),
        "maximum_below_source_floor_count": max(
            (int(run.get("below_source_floor_count", 10**9)) for run in runs), default=None
        ),
        "settled_fill_ratio_range": (
            [
                min(float(run["settled_fill_ratio"]) for run in runs),
                max(float(run["settled_fill_ratio"]) for run in runs),
            ]
            if runs
            else None
        ),
    }


def _runtime_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "LD_LIBRARY_PATH",
        "CARB_APP_PATH",
        "EXP_PATH",
        "ISAAC_PATH",
        "ISAAC_SIM_ROOT",
    ):
        environment.pop(name, None)
    environment["ACCEPT_EULA"] = "Y"
    environment.setdefault("PRIVACY_CONSENT", "Y")
    return environment


def build_and_screen(
    *, fixture_root: Path, output: Path, isaac_python: Path, worker: Path
) -> dict[str, Any]:
    from pxr import Sdf, Usd

    fixture_root = fixture_root.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    summaries = []
    for route, route_spec in ROUTES.items():
        root = output / route
        shutil.copytree(fixture_root, root)
        overlay = root / "collision_route_overlay.usda"
        base_scene = root / "qualification.usda"
        overlay_evidence = author_variant_overlay(
            scene=base_scene, output=overlay, route=route
        )
        scene = root / "scene.usda"
        layer = Sdf.Layer.CreateNew(str(scene))
        layer.defaultPrim = "World"
        layer.subLayerPaths = [overlay.name, base_scene.name]
        layer.Save()
        fixture = json.loads((root / "transfer_fixture_profile.json").read_text())
        fixture["source"]["cavity"].update(
            {
                "radius_m": route_spec["cavity_radius_m"],
                "floor_z_m": route_spec["cavity_floor_z_m"],
                "rim_z_m": route_spec["cavity_rim_z_m"],
                "radial_profile": {
                    "bottom_radius_m": route_spec["cavity_radius_m"],
                    "top_radius_m": route_spec["cavity_radius_m"],
                },
            }
        )
        _write_json(root / "transfer_fixture_profile.json", fixture)
        pose = {
            "xyz_m": [
                float(fixture["source"]["initial_xyz_m"][0]),
                float(fixture["source"]["initial_xyz_m"][1]),
                0.0,
            ],
            "wxyz": [1.0, 0.0, 0.0, 0.0],
        }
        pose_path = root / "static_pose.json"
        _write_json(pose_path, pose)
        runs = []
        for index in range(1, 4):
            destination = root / "evidence" / f"static_run_{index}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            completed = subprocess.run(
                [
                    str(isaac_python),
                    str(worker),
                    "--scene",
                    str(scene),
                    "--mode",
                    "pre-settle",
                    "--support-plane-z-m",
                    "0",
                    "--pose",
                    str(pose_path),
                    "--run-index",
                    str(index),
                    "--out",
                    str(destination),
                ],
                check=False,
                env=_runtime_environment(),
            )
            if destination.is_file():
                run = json.loads(destination.read_text())
                run["worker_process_exit_code"] = completed.returncode
                runs.append(run)
                if (
                    int(run.get("particle_count", -1)) != 580
                    or int(run.get("outside_source_count", 10**9)) > 2
                    or int(run.get("below_source_floor_count", 10**9)) != 0
                    or run.get("hard_runtime_errors", []) != []
                ):
                    break
                continue
            if completed.returncode:
                runs.append(
                    {
                        "particle_count": -1,
                        "outside_source_count": 10**9,
                        "below_source_floor_count": 10**9,
                        "settled_fill_ratio": -1.0,
                        "hard_runtime_errors": [
                            f"worker_exit_code_{completed.returncode}"
                        ],
                    }
                )
                break
            raise RuntimeError("worker returned without an observation artifact")
        stage = Usd.Stage.Open(str(scene))
        topology_path = UNIFIED if route == "qualified_unified_proxy_control" else BODY
        evaluation = evaluate_static_runs(runs)
        summary = {
            "route": route,
            "overlay": overlay_evidence,
            "cavity": fixture["source"]["cavity"],
            "topology": _topology(stage, topology_path),
            "static_validation": evaluation,
            "dynamic_eligible": evaluation["overall_status"] == "pass",
        }
        _write_json(root / "evidence/static_summary.json", summary)
        summaries.append(summary)
    report = {
        "schema_version": "aan.task02_collision_route_ab_report.v1",
        "fixture": str(fixture_root),
        "particle_count": 580,
        "routes": summaries,
        "claim_boundary": (
            "Collision-route screening only; no robot, pour, benchmark, or replacement claim."
        ),
    }
    _write_json(output / "static_ab_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--isaac-python", required=True, type=Path)
    parser.add_argument(
        "--worker",
        type=Path,
        default=Path(__file__).with_name("observe_gpu_pbd_dynamic_loaded_start.py"),
    )
    args = parser.parse_args()
    report = build_and_screen(
        fixture_root=args.fixture_root,
        output=args.out,
        isaac_python=args.isaac_python.resolve(),
        worker=args.worker.resolve(),
    )
    print(args.out.resolve())
    return 0 if any(
        item["route"] == "qualified_unified_proxy_control"
        and item["static_validation"]["overall_status"] == "pass"
        for item in report["routes"]
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
