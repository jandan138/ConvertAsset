#!/usr/bin/env python3
"""Build Task 02 r8.2 from a closed-wall cylinder and source beaker package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

from convert_asset.asset_application_normalizer.interactive_fluid_scene import (
    load_interactive_fluid_scene_profile,
)
from scripts import build_task02_r8_fluid_component as base


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(
    *, cylinder_package: Path, beaker_package: Path, out: Path
) -> dict[str, Path]:
    cylinder_package = Path(cylinder_package).resolve()
    beaker_package = Path(beaker_package).resolve()
    topology_source = cylinder_package / "evidence/container_topology.json"
    if not topology_source.is_file():
        raise FileNotFoundError("closed-wall cylinder package lacks topology evidence")
    result = base.build(
        cylinder_package=cylinder_package,
        beaker_package=beaker_package,
        out=out,
    )
    topology_target = out / "evidence/source_container_topology.json"
    shutil.copy2(topology_source, topology_target)

    profile_path = result["profile"]
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile.update(
        {
            "schema_version": "aan.interactive_fluid_scene_profile.v3",
            "profile_id": "scientific_workbench.task02.cylinder_to_beaker.fluid.r8_2",
            "revision": "r8.2",
        }
    )
    collision = profile["container_collision"]
    collision["strategy"] = "visual_mesh_closed_wall_convex_decomposition"
    collision["source_visual_mesh"] = (
        "/World/FluidWorkcell/SourceContainer/Visual/Source/Hollow_Body/"
        "Hollow_Body_Mesh_002"
    )
    collision["topology_evidence"] = "evidence/source_container_topology.json"
    for mesh in collision["meshes"]:
        mesh["render_visible"] = True
    profile["qualification"] = {
        "static_hold_seconds": 8.0,
        "minimum_source_retention_ratio": 0.95,
        "maximum_below_support_count": 0,
        "minimum_final_target_ratio": 0.8,
        "maximum_tabletop_spill_ratio": 0.05,
        "required_cold_runs": 3,
        "oracle": {
            "pivot_inside_target_rim_m": 0.025,
            "pivot_above_target_rim_m": 0.06,
            "tilt_axis": "local_y",
            "tilt_degrees": -110.0,
            "tilt_seconds": 3.0,
            "hold_seconds": 3.0,
            "settle_seconds": 2.0,
        },
        "performance": {
            "width": 960,
            "height": 540,
            "minimum_rtx_fps": 40.0,
            "required_repeats": 3,
            "gpu": "NVIDIA GeForce RTX 4090",
        },
    }
    profile["claim_boundary"] = {
        "physics_package_candidate": True,
        "liquid_metric_active": False,
        "robot_grasp_success": False,
        "policy_success": False,
        "benchmark_success": False,
    }
    _write_json(profile_path, profile)
    load_interactive_fluid_scene_profile(profile_path)

    manifest_path = result["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "package_id": "scientific_workbench_task02_fluid_component_r82",
            "producer_revision": "2026-08-14-task02-r82-closed-wall-candidate",
            "overall_status": "candidate_pending_runtime",
            "blocked_reasons": ["runtime_qualification_not_run"],
            "claims": profile["claim_boundary"],
        }
    )
    manifest["profile"] = {
        "path": profile_path.name,
        "sha256": _sha(profile_path),
    }
    manifest["source_container_topology"] = {
        "path": topology_target.relative_to(out).as_posix(),
        "sha256": _sha(topology_target),
    }
    _write_json(manifest_path, manifest)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cylinder-package", required=True, type=Path)
    parser.add_argument("--beaker-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = build(
        cylinder_package=args.cylinder_package,
        beaker_package=args.beaker_package,
        out=args.out,
    )
    print(json.dumps({key: str(path) for key, path in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
