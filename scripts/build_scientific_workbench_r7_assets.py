#!/usr/bin/env python3
"""Build source-bound facades and profiles for Scenario Forge r7 tasks 2/7/8."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


REQUIRED_SOURCE_KEYS = (
    "graduated_cylinder_250ml",
    "beaker_325ml",
    "glass_stirring_rod_300mm",
    "centrifuge_tube_15ml_red_cap",
    "glass_test_tube_150mm",
    "test_tube_rack_aluminum",
)
ARCHIVE_SHA256 = "ab0e286972551f728f73d62054c5b46c00e9056c99e1d402eccb6819cad5f955"
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}
MEDIUM_SOCKET_X = (-0.08303, -0.049818, -0.016606, 0.016606, 0.049818, 0.08303)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    return _write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _facade(source: Path, entry: str, source_prim: str = "/root") -> str:
    return f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "{entry}"
    {{
        def Xform "Visual"
        {{
            def Xform "Source" (
                prepend references = @{source.resolve().as_posix()}@<{source_prim}>
            ) {{}}
        }}
    }}
}}
'''


def _closed_tube_facade(source: Path) -> str:
    # Referencing the full source scope preserves its material namespace. The
    # facade authors no timeline and Scenario Forge consumes this context at
    # the source's closed default state; it never treats the animation as a
    # threaded-joint claim.
    return _facade(source, "CentrifugeTube15mlClosed")


def _open_tube_body_facade(source: Path) -> str:
    # The source root contains an animated cap controller. Referencing that
    # whole scope makes bounds depend on timeline samples and can explode the
    # runtime qualification search. The body prim is static; its glass look is
    # deliberately rebound by the visual profile below.
    return _facade(
        source,
        "CentrifugeTube15mlBody",
        "/root/centrifuge_tube_15ml_red_cap_ROOT/Tube_Body_Hollow",
    )


def _frame(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [x, y, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _collider(name: str, kind: str, *, xyz: list[float], scale: list[float] | None = None,
              radius: float | None = None, height: float | None = None,
              purpose: list[str] | None = None) -> dict[str, Any]:
    geometry: dict[str, Any] = {
        "type": kind,
        "translation_body_local_usd": xyz,
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }
    if kind == "Cube":
        geometry.update({"size": 1.0, "scale_body_local_usd": scale})
    else:
        geometry.update({"axis": "Z", "radius": radius, "height": height})
    return {
        "relative_path": f"__aan_collision_proxy/{name}",
        "mode": "author",
        "purpose": purpose or ["support", "gripper"],
        "geometry": geometry,
    }


def _interaction(source: Path, profile_id: str, entry: str, colliders: list[dict[str, Any]],
                 frames: dict[str, Any], *, role: str = "dynamic", open_top: bool = False) -> dict[str, Any]:
    return {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": profile_id,
        "revision": "r7",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": entry,
        "rigid_root": {"motion_role": role, "disable_descendant_rigid_bodies": True, "remove_descendant_mass_api": True},
        "colliders": colliders,
        "required_named_frames": list(frames),
        "named_frames": frames,
        "open_top": ({
            "required": True,
            "axis_body_local": [0.0, 0.0, 1.0],
            "aperture_frame": "opening",
            "evidence": {
                "status": "declared",
                "method": "producer_dimensions_and_source_geometry",
                "claim_boundary": "Opening geometry is source-bound; contained liquid volume is not qualified.",
            },
        } if open_top else {"required": False}),
        "runtime_gates": {
            "root_motion": {"required": role == "dynamic", "min_translation_m": 0.01},
            "stable_support": {"required": role == "dynamic"},
            "gripper_collision": {"required": role == "dynamic"},
        },
    }


def _context(source: Path, profile_id: str, entry: str, colliders: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "aan.dynamic_context_profile.v1",
        "profile_id": profile_id,
        "revision": "r7",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": entry,
        "rigid_root": {"motion_role": "dynamic", "disable_descendant_rigid_bodies": True, "remove_descendant_mass_api": True},
        "colliders": colliders,
        "required_named_frames": ["support"],
        "named_frames": {"support": _frame()},
        "open_top": {"required": False},
        "runtime_gates": {
            "root_motion": {"required": False, "min_translation_m": 0.01},
            "stable_support": {"required": True},
            "gripper_collision": {"required": False},
        },
    }


def _physics(source: Path, profile_id: str, entry: str, *, mass: float, inertia: list[float],
             com_z: float, role: str = "dynamic") -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": profile_id,
        "revision": "r7",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": "Nominal geometry-based simulation values; not measured material parameters.",
            "center_of_mass_convention": "asset_entry_prim_body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound bundle in a new profile revision.",
        },
        "scope_rules": [{
            "scope_path": entry,
            "body_rules": [{
                "relative_path": ".",
                "motion_role": role,
                "clear_density": True,
                "mass_properties": {
                    "mode": "explicit",
                    "quality_tier": "provisional_geometry",
                    "mass_kg": mass,
                    "diagonal_inertia_kg_m2": inertia,
                    "center_of_mass_body_local": [0.0, 0.0, com_z],
                    "principal_axes": [1.0, 0.0, 0.0, 0.0],
                },
            }],
        }],
    }


def _vessel_colliders(radius: float, height: float, base_radius: float) -> list[dict[str, Any]]:
    wall = 0.003
    return [
        _collider("bottom", "Cylinder", xyz=[0.0, 0.0, 0.002], radius=base_radius, height=0.004, purpose=["support", "containment"]),
        _collider("wall_pos_x", "Cube", xyz=[radius, 0.0, height / 2], scale=[wall, radius * 2, height], purpose=["gripper", "containment"]),
        _collider("wall_neg_x", "Cube", xyz=[-radius, 0.0, height / 2], scale=[wall, radius * 2, height], purpose=["gripper", "containment"]),
        _collider("wall_pos_y", "Cube", xyz=[0.0, radius, height / 2], scale=[radius * 2, wall, height], purpose=["gripper", "containment"]),
        _collider("wall_neg_y", "Cube", xyz=[0.0, -radius, height / 2], scale=[radius * 2, wall, height], purpose=["gripper", "containment"]),
    ]


def _rack_interaction(source: Path) -> dict[str, Any]:
    frames = {"support": _frame()}
    for index, x in enumerate(MEDIUM_SOCKET_X, 1):
        frames[f"medium_socket_{index:02d}_aperture"] = _frame(x, 0.0, 0.06651)
        frames[f"medium_socket_{index:02d}_inserted_bottom"] = _frame(x, 0.0, 0.0012)
    # Compatibility aliases allow the existing source-bound insertion worker
    # to qualify the central selected socket without inventing a second frame.
    frames["socket_0_aperture"] = frames["medium_socket_03_aperture"]
    frames["socket_0_inserted_bottom"] = frames["medium_socket_03_inserted_bottom"]
    colliders = [
        _collider("base", "Cube", xyz=[0.0, 0.0, 0.0012], scale=[0.20116, 0.10558, 0.0024], purpose=["support"]),
        _collider("left_end", "Cube", xyz=[-0.09958, 0.0, 0.033255], scale=[0.002, 0.10558, 0.06651], purpose=["containment"]),
        _collider("right_end", "Cube", xyz=[0.09958, 0.0, 0.033255], scale=[0.002, 0.10558, 0.06651], purpose=["containment"]),
        _collider("rear_rail", "Cube", xyz=[0.0, 0.05079, 0.040], scale=[0.20116, 0.004, 0.052], purpose=["containment"]),
        _collider("front_rail", "Cube", xyz=[0.0, -0.05079, 0.040], scale=[0.20116, 0.004, 0.052], purpose=["containment"]),
    ]
    socket_inner = 0.0191
    socket_wall = 0.001
    wall_offset = socket_inner / 2 + socket_wall / 2
    for index, socket_x in enumerate(MEDIUM_SOCKET_X, 1):
        prefix = f"medium_socket_{index:02d}"
        colliders.extend([
            _collider(f"{prefix}_bottom", "Cube", xyz=[socket_x, 0.0, 0.0012], scale=[socket_inner, socket_inner, 0.0024], purpose=["support", "containment"]),
            _collider(f"{prefix}_wall_pos_x", "Cube", xyz=[socket_x + wall_offset, 0.0, 0.033855], scale=[socket_wall, socket_inner, 0.06531], purpose=["containment"]),
            _collider(f"{prefix}_wall_neg_x", "Cube", xyz=[socket_x - wall_offset, 0.0, 0.033855], scale=[socket_wall, socket_inner, 0.06531], purpose=["containment"]),
            _collider(f"{prefix}_wall_pos_y", "Cube", xyz=[socket_x, wall_offset, 0.033855], scale=[socket_inner, socket_wall, 0.06531], purpose=["containment"]),
            _collider(f"{prefix}_wall_neg_y", "Cube", xyz=[socket_x, -wall_offset, 0.033855], scale=[socket_inner, socket_wall, 0.06531], purpose=["containment"]),
        ])
    # Compatibility aliases retain the already-qualified central-socket
    # protocol while all six named sockets now have equivalent source-scale
    # collision support.
    socket_x = MEDIUM_SOCKET_X[2]
    colliders.extend([
        _collider("socket_0_bottom", "Cube", xyz=[socket_x, 0.0, 0.0012], scale=[socket_inner, socket_inner, 0.0024], purpose=["support", "containment"]),
        _collider("socket_0_wall_pos_x", "Cube", xyz=[socket_x + wall_offset, 0.0, 0.033855], scale=[socket_wall, socket_inner, 0.06531], purpose=["containment"]),
        _collider("socket_0_wall_neg_x", "Cube", xyz=[socket_x - wall_offset, 0.0, 0.033855], scale=[socket_wall, socket_inner, 0.06531], purpose=["containment"]),
        _collider("socket_0_wall_pos_y", "Cube", xyz=[socket_x, wall_offset, 0.033855], scale=[socket_inner, socket_wall, 0.06531], purpose=["containment"]),
        _collider("socket_0_wall_neg_y", "Cube", xyz=[socket_x, -wall_offset, 0.033855], scale=[socket_inner, socket_wall, 0.06531], purpose=["containment"]),
    ])
    return _interaction(source, "scientific_workbench.test_tube_rack_aluminum_k100.r7", "/World/TubeRack", colliders, frames, role="kinematic")


def build(*, sources: dict[str, Path], out: Path) -> dict[str, Path]:
    missing = set(REQUIRED_SOURCE_KEYS) - set(sources)
    if missing:
        raise ValueError(f"missing r7 sources: {sorted(missing)}")
    sources = {key: Path(value).resolve() for key, value in sources.items()}
    for key, path in sources.items():
        if not path.is_file():
            raise FileNotFoundError(f"{key}: {path}")

    facade_specs = {
        "graduated_cylinder_250ml": ("GraduatedCylinder250ml", _facade(sources["graduated_cylinder_250ml"], "GraduatedCylinder250ml")),
        "beaker_325ml": ("Beaker325ml", _facade(sources["beaker_325ml"], "Beaker325ml")),
        "glass_stirring_rod_300mm": ("GlassStirringRod", _facade(sources["glass_stirring_rod_300mm"], "GlassStirringRod")),
        "centrifuge_tube_15ml_body": ("CentrifugeTube15mlBody", _open_tube_body_facade(sources["centrifuge_tube_15ml_red_cap"])),
        "centrifuge_tube_15ml_cap": ("CentrifugeTube15mlCap", _facade(sources["centrifuge_tube_15ml_red_cap"], "CentrifugeTube15mlCap", "/root/centrifuge_tube_15ml_red_cap_ROOT/Cap_Controller/Cap_Removable")),
        "centrifuge_tube_15ml_closed": ("CentrifugeTube15mlClosed", _closed_tube_facade(sources["centrifuge_tube_15ml_red_cap"])),
        "glass_test_tube_150mm": ("GlassTestTube150mm", _facade(sources["glass_test_tube_150mm"], "GlassTestTube150mm")),
        "test_tube_rack_aluminum": ("TubeRack", _facade(sources["test_tube_rack_aluminum"], "TubeRack")),
    }
    facades: dict[str, Path] = {}
    for key, (_, text) in facade_specs.items():
        facades[key] = _write(out / "facades" / key / "facade.usda", text)

    profiles = out / "profiles"
    results: dict[str, Path] = {}
    def emit(key: str, kind: str, payload: dict[str, Any]) -> None:
        results[f"{key}_{kind}"] = _write_json(profiles / f"{key}.{kind}.json", payload)

    cylinder = facades["graduated_cylinder_250ml"]
    emit("graduated_cylinder_250ml", "interaction", _interaction(cylinder, "scientific_workbench.graduated_cylinder_250ml.r7", "/World/GraduatedCylinder250ml", _vessel_colliders(0.02099, 0.27824, 0.035785), {"support": _frame(), "grasp": _frame(z=0.135), "opening": _frame(z=0.27824), "interior_center": _frame(z=0.135)}, open_top=True))
    emit("graduated_cylinder_250ml", "physics", _physics(cylinder, "scientific_workbench.graduated_cylinder_250ml.r7", "/World/GraduatedCylinder250ml", mass=0.20, inertia=[0.00132, 0.00132, 0.00010], com_z=0.125))

    beaker = facades["beaker_325ml"]
    emit("beaker_325ml", "interaction", _interaction(beaker, "scientific_workbench.beaker_325ml.r7", "/World/Beaker325ml", _vessel_colliders(0.041245, 0.11509, 0.03727), {"support": _frame(), "grasp": _frame(z=0.065), "opening": _frame(z=0.11509), "interior_center": _frame(z=0.055)}, open_top=True))
    emit("beaker_325ml", "physics", _physics(beaker, "scientific_workbench.beaker_325ml.r7", "/World/Beaker325ml", mass=0.18, inertia=[0.00025, 0.00025, 0.00016], com_z=0.052))

    rod = facades["glass_stirring_rod_300mm"]
    emit("glass_stirring_rod_300mm", "interaction", _interaction(rod, "scientific_workbench.glass_stirring_rod_300mm.r7", "/World/GlassStirringRod", [_collider("rod", "Cylinder", xyz=[0.0, 0.0, 0.15], radius=0.003615, height=0.3)], {"support": _frame(), "grasp": _frame(z=0.225), "working_tip": _frame(z=0.008)}))
    emit("glass_stirring_rod_300mm", "physics", _physics(rod, "scientific_workbench.glass_stirring_rod_300mm.r7", "/World/GlassStirringRod", mass=0.031, inertia=[0.000233, 0.000233, 0.00000021], com_z=0.15))

    body = facades["centrifuge_tube_15ml_body"]
    emit("centrifuge_tube_15ml_body", "interaction", _interaction(body, "scientific_workbench.centrifuge_tube_15ml_body.r7", "/World/CentrifugeTube15mlBody", [_collider("body", "Cylinder", xyz=[0.0, 0.0, 0.0505], radius=0.00861, height=0.101)], {"support": _frame(), "grasp": _frame(z=0.065), "closure_seat": _frame(z=0.10096), "opening": _frame(z=0.101)}))
    emit("centrifuge_tube_15ml_body", "physics", _physics(body, "scientific_workbench.centrifuge_tube_15ml_body.r7", "/World/CentrifugeTube15mlBody", mass=0.015, inertia=[0.000013, 0.000013, 0.00000052], com_z=0.052))
    cap = facades["centrifuge_tube_15ml_cap"]
    emit("centrifuge_tube_15ml_cap", "interaction", _interaction(cap, "scientific_workbench.centrifuge_tube_15ml_cap.r7", "/World/CentrifugeTube15mlCap", [_collider("cap", "Cylinder", xyz=[0.0, 0.0, 0.00937], radius=0.01042, height=0.01874)], {"support": _frame(), "grasp": _frame(z=0.00937), "closure_mate": _frame()}))
    emit("centrifuge_tube_15ml_cap", "physics", _physics(cap, "scientific_workbench.centrifuge_tube_15ml_cap.r7", "/World/CentrifugeTube15mlCap", mass=0.004, inertia=[0.00000016, 0.00000016, 0.00000022], com_z=0.00937))

    emit("centrifuge_tube_15ml_body", "visual", {
        "schema_version": "aan.visual_material_profile.v1",
        "profile_id": "scientific_workbench.centrifuge_tube_15ml_body.transparent.r7",
        "revision": "r7",
        "source_binding": {"sha256": _sha(body)},
        "override": {
            "kind": "mdl_glass",
            "source_mdl": "/isaac-sim/kit/mdl/core/Base/OmniGlass.mdl",
            "source_sub_identifier": "OmniGlass",
            "material_name": "TransparentTube",
            "binding_targets": ["/World/CentrifugeTube15mlBody/Visual/Source/Tube_Body_Hollow_Mesh"],
            "claim_boundary": "Representative transparent polymer appearance only; geometry and physics are unchanged.",
        },
    })
    emit("centrifuge_tube_15ml_cap", "visual", {
        "schema_version": "aan.visual_material_profile.v1",
        "profile_id": "scientific_workbench.centrifuge_tube_15ml_cap.red.r7",
        "revision": "r7",
        "source_binding": {"sha256": _sha(cap)},
        "override": {
            "kind": "usd_preview_surface",
            "material_name": "RedPolypropylene",
            "binding_targets": ["/World/CentrifugeTube15mlCap/Visual/Source/Cap_Shell_Mesh"],
            "diffuse_color": [0.65, 0.02, 0.02],
            "opacity": 1.0,
            "roughness": 0.35,
            "metallic": 0.0,
            "claim_boundary": "Representative red polymer appearance only; geometry and physics are unchanged.",
        },
    })

    tube_collider = [_collider("tube", "Cylinder", xyz=[0.0, 0.0, 0.075], radius=0.008905, height=0.15)]
    glass_tube = facades["glass_test_tube_150mm"]
    emit("glass_test_tube_150mm", "interaction", _interaction(glass_tube, "scientific_workbench.glass_test_tube_150mm.r7", "/World/GlassTestTube150mm", tube_collider, {"support": _frame(), "grasp": _frame(z=0.10), "opening": _frame(z=0.15)}))
    emit("glass_test_tube_150mm", "physics", _physics(glass_tube, "scientific_workbench.glass_test_tube_150mm.r7", "/World/GlassTestTube150mm", mass=0.022, inertia=[0.000041, 0.000041, 0.00000087], com_z=0.075))
    closed = facades["centrifuge_tube_15ml_closed"]
    emit("centrifuge_tube_15ml_closed", "context", _context(closed, "scientific_workbench.centrifuge_tube_15ml_closed.r7", "/World/CentrifugeTube15mlClosed", [
        _collider("body", "Cylinder", xyz=[0.0, 0.0, 0.0505], radius=0.00834, height=0.101),
        _collider("cap", "Cylinder", xyz=[0.0, 0.0, 0.11033], radius=0.01042, height=0.01874),
    ]))
    emit("centrifuge_tube_15ml_closed", "physics", _physics(closed, "scientific_workbench.centrifuge_tube_15ml_closed.r7", "/World/CentrifugeTube15mlClosed", mass=0.019, inertia=[0.000024, 0.000024, 0.0000010], com_z=0.055))

    rack = facades["test_tube_rack_aluminum"]
    emit("test_tube_rack_aluminum", "interaction", _rack_interaction(rack))
    emit("test_tube_rack_aluminum", "physics", _physics(rack, "scientific_workbench.test_tube_rack_aluminum_k100.r7", "/World/TubeRack", mass=0.85, inertia=[0.0017, 0.0049, 0.0056], com_z=0.033, role="kinematic"))

    manifest = {
        "schema_version": "aan.scientific_workbench_r7_asset_inputs.v1",
        "archive_sha256": ARCHIVE_SHA256,
        "sources": {key: {"path": path.as_posix(), "sha256": _sha(path)} for key, path in sources.items()},
        "facades": {key: path.as_posix() for key, path in facades.items()},
        "profiles": {key: path.as_posix() for key, path in results.items()},
        "rack_layout": {
            "scale": 1.0,
            "medium_socket_count": 6,
            "selected_medium_socket_indices": [1, 3, 6],
            "medium_socket_x_m": list(MEDIUM_SOCKET_X),
            "claim_boundary": "Named frames are source-composed coordinates; runtime three-tube fit is a separate qualification gate.",
        },
    }
    results.update(facades)
    results["manifest"] = _write_json(out / "source_manifest.json", manifest)
    return results


def _default_sources(root: Path) -> dict[str, Path]:
    return {
        "graduated_cylinder_250ml": root / "01_玻璃器皿/250毫升量筒/graduated_cylinder_250ml.usda",
        "beaker_325ml": root / "01_玻璃器皿/325毫升烧杯/beaker_325ml.usda",
        "glass_stirring_rod_300mm": root / "01_玻璃器皿/300毫米玻璃搅拌棒/glass_stirring_rod_300mm.usda",
        "centrifuge_tube_15ml_red_cap": root / "02_塑料耗材/15毫升离心管_红盖/centrifuge_tube_15ml_red_cap.usda",
        "glass_test_tube_150mm": root / "01_玻璃器皿/150毫米玻璃试管/glass_test_tube_150mm.usda",
        "test_tube_rack_aluminum": root / "03_支架与托具/铝制试管架/test_tube_rack_aluminum.usda",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(sources=_default_sources(args.library_root), out=args.out.resolve())
    print(json.dumps({key: value.as_posix() for key, value in result.items()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
