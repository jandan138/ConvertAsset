#!/usr/bin/env python3
"""Build a source-bound GPU-PBD vessel candidate from a measured recipe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from convert_asset.asset_application_normalizer.container_topology import (
    UnifiedCylindricalVesselSpec,
)
from scripts.build_partitioned_gpu_pbd_container_package import (
    build_partitioned_package,
)
from scripts.build_unified_pbd_container_package import (
    build_unified_pbd_container_package,
)


SCHEMA = "aan.source_bound_cylindrical_container_recipe.v1"


def _load_recipe(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA:
        raise ValueError(f"recipe schema_version must be {SCHEMA}")
    required = {
        "profile_id",
        "vessel_root",
        "replaced_prim_paths",
        "glass_material_path",
        "geometry",
        "partition",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError("recipe is missing: " + ", ".join(missing))
    return payload


def build_source_bound_container(
    *, source_package: Path, recipe_path: Path, output: Path
) -> dict[str, Any]:
    recipe = _load_recipe(recipe_path.resolve())
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite build: {output}")
    geometry = dict(recipe["geometry"])
    spec = UnifiedCylindricalVesselSpec(**geometry)
    vessel_root = str(recipe["vessel_root"])
    profile_id = str(recipe["profile_id"])
    unified = output / "unified"
    candidate = output / "candidate"
    build_unified_pbd_container_package(
        source_package=source_package,
        output=unified,
        vessel_root=vessel_root,
        replaced_prim_paths=tuple(recipe["replaced_prim_paths"]),
        glass_material_path=str(recipe["glass_material_path"]),
        spec=spec,
        profile_id=f"{profile_id}.unified",
        cooking_recipe="liquid_0812_promotable",
    )
    partition = dict(recipe["partition"])
    unified_mesh_prim = (
        f"{vessel_root}/Visual/Source/PBD_Unified_Vessel/PBD_Unified_Vessel_Mesh"
    )
    build_partitioned_package(
        unified_package=unified,
        output=candidate,
        vessel_root=vessel_root,
        unified_mesh_prim=unified_mesh_prim,
        spec=spec,
        profile_id=profile_id,
        contact_offset_m=float(partition.get("contact_offset_m", 0.001)),
        rest_offset_m=float(partition.get("rest_offset_m", 0.0)),
        voxel_resolution=int(partition.get("voxel_resolution", 10000)),
        piece_approximation=str(
            partition.get("piece_approximation", "convexDecomposition")
        ),
        collision_render_mode=str(partition.get("collision_render_mode", "guide")),
        support_bottom_z_m=float(partition.get("support_bottom_z_m", spec.bottom_z)),
        wall_segments=int(partition.get("wall_segments", 31)),
        wall_vertical_segments=int(partition.get("wall_vertical_segments", 1)),
        bottom_segments=int(partition.get("bottom_segments", 1)),
        bottom_arc_subdivisions=int(partition.get("bottom_arc_subdivisions", 32)),
        reuse_rotated_wall_geometry=bool(
            partition.get("reuse_rotated_wall_geometry", True)
        ),
        support_bottom_source_prims=tuple(
            str(value) for value in recipe.get("support_bottom_source_prims", [])
        ),
    )
    result = {
        "schema_version": "aan.source_bound_gpu_pbd_container_build.v1",
        "status": "candidate",
        "recipe": str(recipe_path.resolve()),
        "source_package": str(source_package.resolve()),
        "unified_package": str(unified),
        "candidate_package": str(candidate),
    }
    evidence = output / "build_result.json"
    evidence.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build_source_bound_container(
                source_package=args.source_package,
                recipe_path=args.recipe,
                output=args.out,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
