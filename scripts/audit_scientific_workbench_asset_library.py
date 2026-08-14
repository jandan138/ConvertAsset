#!/usr/bin/env python3
"""Audit the 29 single assets in the scientific workbench source archive."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from convert_asset.asset_application_normalizer.container_topology import (
    ContainerTopologyError,
    analyze_mesh_topology,
    close_annular_wall_rim,
)


ARCHIVE_SHA256 = "ab0e286972551f728f73d62054c5b46c00e9056c99e1d402eccb6819cad5f955"


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    source: str
    role: str
    phase: int
    primary_mesh_suffix: str | None = None


def _spec(
    asset_id: str,
    source: str,
    role: str,
    phase: int,
    suffix: str | None = None,
) -> AssetSpec:
    return AssetSpec(asset_id, source, role, phase, suffix)


CATALOG: tuple[AssetSpec, ...] = (
    _spec(
        "graduated_cylinder_100ml",
        "01_玻璃器皿/100毫升量筒/graduated_cylinder_100ml.usda",
        "liquid_container",
        1,
        "/Hollow_Body/Hollow_Body_Mesh",
    ),
    _spec(
        "glass_test_tube_150mm",
        "01_玻璃器皿/150毫米玻璃试管/glass_test_tube_150mm.usda",
        "liquid_container",
        1,
        "/Test_Tube_Hollow_Glass/Test_Tube_Hollow_Glass_Mesh",
    ),
    _spec(
        "glass_test_tube_200mm",
        "01_玻璃器皿/200毫米玻璃试管/glass_test_tube_200mm.usda",
        "liquid_container",
        1,
        "/Test_Tube_Hollow_Glass/Test_Tube_Hollow_Glass_Mesh",
    ),
    _spec(
        "round_bottom_flask_250ml",
        "01_玻璃器皿/250毫升圆底烧瓶/round_bottom_flask_250ml.usda",
        "liquid_container",
        1,
        "/Round_Bottom_Flask_Hollow_Body/Round_Bottom_Flask_Hollow_Body_Mesh",
    ),
    _spec(
        "flat_bottom_flask_250ml_29_42",
        "01_玻璃器皿/250毫升平底烧瓶_29_42磨口/flat_bottom_flask_250ml_29_42.usda",
        "liquid_container",
        1,
        "/Flat_Bottom_Flask_Hollow_Body/Flat_Bottom_Flask_Hollow_Body_Mesh",
    ),
    _spec(
        "graduated_cylinder_250ml",
        "01_玻璃器皿/250毫升量筒/graduated_cylinder_250ml.usda",
        "liquid_container",
        1,
        "/Hollow_Body/Hollow_Body_Mesh_002",
    ),
    _spec(
        "beaker_325ml",
        "01_玻璃器皿/325毫升烧杯/beaker_325ml.usda",
        "liquid_container",
        1,
        "/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh",
    ),
    _spec(
        "petri_dish_base",
        "01_玻璃器皿/培养皿底/petri_dish_base.usda",
        "liquid_container",
        1,
        "/Petri_Dish_Open_Base/Petri_Dish_Open_Base_Mesh",
    ),
    _spec(
        "glass_funnel_24_40",
        "01_玻璃器皿/玻璃漏斗_24_40/glass_funnel_24_40.usda",
        "liquid_conduit",
        1,
        "/Glass_Funnel_Hollow_Body/Glass_Funnel_Hollow_Body_Mesh",
    ),
    _spec(
        "centrifuge_tube_15ml_red_cap",
        "02_塑料耗材/15毫升离心管_红盖/centrifuge_tube_15ml_red_cap.usda",
        "liquid_container",
        1,
        "/Tube_Body_Hollow/Tube_Body_Hollow_Mesh",
    ),
    _spec(
        "centrifuge_tube_15ml_opaque_blue_cap",
        "02_塑料耗材/15毫升离心管_蓝盖深色不透明/centrifuge_tube_15ml_opaque_blue_cap.usda",
        "liquid_container",
        1,
        "/Tube_Body_Hollow/Tube_Body_Hollow_Mesh",
    ),
    _spec(
        "centrifuge_tube_50ml_orange_cap",
        "02_塑料耗材/50毫升离心管_橙盖/centrifuge_tube_50ml_orange_cap.usda",
        "liquid_container",
        1,
        "/Tube_Body_Hollow/Tube_Body_Hollow_Mesh",
    ),
    _spec(
        "centrifuge_tube_50ml_red_cap",
        "02_塑料耗材/50毫升离心管_红盖/centrifuge_tube_50ml_red_cap.usda",
        "liquid_container",
        1,
        "/Tube_Body_Hollow/Tube_Body_Hollow_Mesh",
    ),
    _spec(
        "glass_stirring_rod_300mm",
        "01_玻璃器皿/300毫米玻璃搅拌棒/glass_stirring_rod_300mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "cork_flask_support",
        "03_支架与托具/软木烧瓶托/cork_flask_support.usda",
        "receptacle_support",
        2,
    ),
    _spec(
        "acrylic_spoon_rack",
        "03_支架与托具/透明亚克力勺子架/acrylic_spoon_rack.usda",
        "receptacle_support",
        2,
    ),
    _spec(
        "test_tube_rack_aluminum",
        "03_支架与托具/铝制试管架/test_tube_rack_aluminum.usda",
        "receptacle_support",
        2,
    ),
    _spec(
        "magnetic_stir_bar_01",
        "04_磁力搅拌/磁力搅拌子_01_29.77毫米/magnetic_stir_bar_01_29_77mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_02",
        "04_磁力搅拌/磁力搅拌子_02_24.85毫米/magnetic_stir_bar_02_24_85mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_03",
        "04_磁力搅拌/磁力搅拌子_03_14.90毫米/magnetic_stir_bar_03_14_90mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_04",
        "04_磁力搅拌/磁力搅拌子_04_6.03毫米/magnetic_stir_bar_04_6_03mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_05",
        "04_磁力搅拌/磁力搅拌子_05_34.62毫米/magnetic_stir_bar_05_34_62mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_06",
        "04_磁力搅拌/磁力搅拌子_06_29.98毫米/magnetic_stir_bar_06_29_98mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_07",
        "04_磁力搅拌/磁力搅拌子_07_19.78毫米/magnetic_stir_bar_07_19_78mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_08",
        "04_磁力搅拌/磁力搅拌子_08_10.03毫米/magnetic_stir_bar_08_10_03mm.usda",
        "rigid_tool",
        2,
    ),
    _spec(
        "magnetic_stir_bar_storage_case",
        "04_磁力搅拌/磁力搅拌子收纳盒/magnetic_stir_bar_storage_case.usda",
        "receptacle_support",
        2,
    ),
    _spec(
        "analytical_balance_lichen",
        "05_实验仪器/LICHEN电子分析天平_程序化版本/analytical_balance_lichen.usda",
        "instrument_static",
        2,
    ),
    _spec(
        "analytical_balance_textured_measured",
        "05_实验仪器/电子分析天平_贴图实测修订版/analytical_balance_textured_measured.usda",
        "instrument_static",
        2,
    ),
    _spec(
        "stainless_micro_spatula_250mm",
        "06_金属工具/不锈钢微量药勺_250毫米标称/stainless_micro_spatula_250mm.usda",
        "rigid_tool",
        2,
    ),
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _select_primary(meshes: list[dict[str, Any]], suffix: str | None) -> dict[str, Any]:
    if suffix:
        matches = [mesh for mesh in meshes if mesh["prim_path"].endswith(suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"expected one primary mesh ending in {suffix!r}")
        return matches[0]
    return max(meshes, key=lambda mesh: (mesh["face_count"], mesh["point_count"]))


def _raw_edge_counts(counts: Any, indices: Any) -> tuple[int, int]:
    edges: Counter[tuple[int, int]] = Counter()
    offset = 0
    for count in counts:
        face = [int(value) for value in indices[offset : offset + int(count)]]
        offset += int(count)
        for left, right in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((left, right)))] += 1
    return (
        sum(value == 1 for value in edges.values()),
        sum(value > 2 for value in edges.values()),
    )


def _audit_asset(spec: AssetSpec, source_root: Path) -> dict[str, Any]:
    from pxr import Usd, UsdGeom

    source = source_root / spec.source
    stage = Usd.Stage.Open(str(source))
    if stage is None:
        raise RuntimeError(f"could not open {source}")
    meshes: list[dict[str, Any]] = []
    mesh_values: dict[str, tuple[Any, Any, Any]] = {}
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        mesh = UsdGeom.Mesh(prim)
        points = mesh.GetPointsAttr().Get() or []
        counts = mesh.GetFaceVertexCountsAttr().Get() or []
        indices = mesh.GetFaceVertexIndicesAttr().Get() or []
        try:
            topology = analyze_mesh_topology(counts, indices)
        except ContainerTopologyError as error:
            boundary_edges, non_manifold_edges = _raw_edge_counts(counts, indices)
            topology_values = {
                "boundary_edge_count": boundary_edges,
                "boundary_loop_count": None,
                "non_manifold_edge_count": non_manifold_edges,
                "topology_error": str(error),
            }
        else:
            topology_values = {
                "boundary_edge_count": topology.boundary_edge_count,
                "boundary_loop_count": topology.boundary_loop_count,
                "non_manifold_edge_count": topology.non_manifold_edge_count,
                "topology_error": None,
            }
        path = str(prim.GetPath())
        meshes.append(
            {
                "prim_path": path,
                "point_count": len(points),
                "face_count": len(counts),
                **topology_values,
            }
        )
        mesh_values[path] = (points, counts, indices)
    if not meshes:
        raise RuntimeError(f"source has no meshes: {source}")
    primary = _select_primary(meshes, spec.primary_mesh_suffix)
    repair = {"applicable": False, "recipe": None}
    if spec.role in {"liquid_container", "liquid_conduit"}:
        if primary["topology_error"]:
            status = "blocked_primary_mesh_topology_ambiguous"
            repair["reason"] = primary["topology_error"]
        elif primary["non_manifold_edge_count"]:
            status = "blocked_primary_mesh_non_manifold"
        elif primary["boundary_edge_count"] == 0:
            status = "topology_pass_runtime_pending"
        else:
            points, counts, indices = mesh_values[primary["prim_path"]]
            try:
                result = close_annular_wall_rim(points, counts, indices)
            except ContainerTopologyError as error:
                status = "blocked_no_conservative_topology_repair"
                repair["reason"] = str(error)
            else:
                status = "repair_required"
                repair = {
                    "applicable": True,
                    "recipe": "close_coplanar_concentric_dual_rim_loops.v1",
                    "added_face_count": result.added_face_count,
                }
    else:
        status = "topology_audit_complete_runtime_pending"
    return {
        **asdict(spec),
        "source_sha256": _sha(source),
        "status": status,
        "primary_mesh": primary,
        "repair": repair,
        "mesh_count": len(meshes),
        "meshes_with_boundary_edges": sum(
            mesh["boundary_edge_count"] > 0 for mesh in meshes
        ),
        "meshes_with_non_manifold_edges": sum(
            mesh["non_manifold_edge_count"] > 0 for mesh in meshes
        ),
        "claim_boundary": "Topology and role classification only; no collision cooking, dynamics, interaction, robot, policy, or benchmark claim.",
    }


def audit(*, source_root: Path, archive: Path, out: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    archive = archive.resolve()
    if _sha(archive) != ARCHIVE_SHA256:
        raise ValueError("archive SHA-256 does not match the reviewed source archive")
    assets = [_audit_asset(spec, source_root) for spec in CATALOG]
    report = {
        "schema_version": "aan.scientific_workbench_role_topology_audit.v1",
        "archive": {"path": str(archive), "sha256": ARCHIVE_SHA256},
        "source_root": str(source_root),
        "catalog_contract": {"single_asset_count": 29, "combo_scenes_excluded": 6},
        "summary": {
            "asset_count": len(assets),
            "phase_1_count": sum(asset["phase"] == 1 for asset in assets),
            "phase_2_count": sum(asset["phase"] == 2 for asset in assets),
            "repair_required": [
                asset["asset_id"]
                for asset in assets
                if asset["status"] == "repair_required"
            ],
            "blocked": [
                asset["asset_id"]
                for asset in assets
                if asset["status"].startswith("blocked_")
            ],
        },
        "assets": assets,
        "overall_status": "audit_complete",
        "claim_boundary": "The report is an admission inventory, not a promoted package manifest or runtime qualification report.",
    }
    out.mkdir(parents=True, exist_ok=False)
    target = out / "role_topology_audit.json"
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = audit(source_root=args.source_root, archive=args.archive, out=args.out)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
