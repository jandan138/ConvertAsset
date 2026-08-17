#!/usr/bin/env python3
"""Build source-bound facade and profiles for the acrylic seven-hole rack."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


ENTRY_PRIM = "/World/AcrylicSpoonRack"
SOCKET_X = tuple((index - 3) * 0.0256 for index in range(7))
UPPER_BOTTOM_Z = 0.13205
UPPER_TOP_Z = 0.13672
LOWER_TOP_Z = 0.01743
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _json(path: Path, payload: dict[str, Any]) -> Path:
    return _write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _frame(x: float, z: float) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [x, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _cube(name: str, xyz: list[float], scale: list[float], purpose: list[str]) -> dict[str, Any]:
    return {
        "relative_path": f"__aan_collision_proxy/{name}",
        "mode": "author",
        "purpose": purpose,
        "geometry": {
            "type": "Cube",
            "size": 1.0,
            "translation_body_local_usd": xyz,
            "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            "scale_body_local_usd": scale,
        },
    }


def _upper_shelf_colliders() -> list[dict[str, Any]]:
    thickness = UPPER_TOP_Z - UPPER_BOTTOM_Z
    z = (UPPER_TOP_Z + UPPER_BOTTOM_Z) / 2.0
    colliders = [
        _cube("upper_front_rail", [0.0, -0.011, z], [0.19, 0.008, thickness], ["containment"]),
        _cube("upper_rear_rail", [0.0, 0.011, z], [0.19, 0.008, thickness], ["containment"]),
    ]
    edges = [-0.095, *[x - 0.007 for x in SOCKET_X], *[x + 0.007 for x in SOCKET_X], 0.095]
    edges.sort()
    solid_segments = [(edges[index], edges[index + 1]) for index in range(0, len(edges) - 1, 2)]
    for index, (left, right) in enumerate(solid_segments):
        label = (
            "upper_gap_04_left" if index == 3 else
            "upper_gap_04_right" if index == 4 else
            f"upper_segment_{index + 1:02d}"
        )
        colliders.append(
            _cube(label, [(left + right) / 2.0, 0.0, z], [right - left, 0.014, thickness], ["containment"])
        )
    # These aliases cover material that is already represented by the shelf
    # strips.  Their stable ABI lets the generic insertion qualifier select
    # the central aperture without inventing a rack-specific worker.
    colliders.extend(
        [
            _cube("socket_0_wall_pos_x", [0.0075, 0.0, z], [0.001, 0.014, thickness], ["containment"]),
            _cube("socket_0_wall_neg_x", [-0.0075, 0.0, z], [0.001, 0.014, thickness], ["containment"]),
            _cube("socket_0_wall_pos_y", [0.0, 0.0075, z], [0.014, 0.001, thickness], ["containment"]),
            _cube("socket_0_wall_neg_y", [0.0, -0.0075, z], [0.014, 0.001, thickness], ["containment"]),
        ]
    )
    return colliders


def build(*, source: Path, out: Path) -> dict[str, Path]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    out = out.resolve()
    facade = _write(
        out / "facade.usda",
        f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    timeCodesPerSecond = 24
    framesPerSecond = 24
)

def Xform "World"
{{
    def Xform "AcrylicSpoonRack"
    {{
        def Xform "Visual" (
            prepend references = @{source.as_posix()}@</root>
        ) {{}}
    }}
}}
''',
    )
    frames = {"support": _frame(0.0, 0.0)}
    for index, x in enumerate(SOCKET_X, 1):
        frames[f"middle_socket_{index:02d}_aperture"] = _frame(x, UPPER_TOP_Z)
        # The qualified rod's authoritative support frame is its lower tip,
        # so the inserted frame belongs on the lower shelf top (no radius add).
        frames[f"middle_socket_{index:02d}_inserted_bottom"] = _frame(x, LOWER_TOP_Z)
    frames["socket_0_aperture"] = dict(frames["middle_socket_04_aperture"])
    frames["socket_0_inserted_bottom"] = dict(frames["middle_socket_04_inserted_bottom"])
    colliders = [
        _cube("base", [0.0, 0.0, 0.0035], [0.2, 0.11, 0.007], ["support"]),
        _cube("lower_shelf", [0.0, 0.0, 0.015095], [0.19, 0.03, 0.00467], ["support", "containment"]),
        _cube("socket_0_bottom", [0.0, 0.0, 0.015095], [0.014, 0.014, 0.00467], ["support", "containment"]),
        _cube("left_side", [-0.102335, 0.0, 0.10], [0.00467, 0.11, 0.19], ["containment"]),
        _cube("right_side", [0.102335, 0.0, 0.10], [0.00467, 0.11, 0.19], ["containment"]),
        *_upper_shelf_colliders(),
    ]
    interaction_payload = {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": "scientific_workbench.acrylic_spoon_rack.r1",
        "revision": "r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": ENTRY_PRIM,
        "rigid_root": {
            "motion_role": "kinematic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": colliders,
        "required_named_frames": ["support", "socket_0_aperture", "socket_0_inserted_bottom"],
        "named_frames": frames,
        "open_top": {"required": False},
        "runtime_gates": {
            "root_motion": {"required": False, "min_translation_m": 0.01},
            # This rack is an authored kinematic fixture.  Dynamic settling is
            # therefore not an applicable admission claim; insertion/contact
            # is qualified separately against the packaged colliders.
            "stable_support": {"required": False},
            "gripper_collision": {"required": False},
        },
    }
    interaction = _json(out / "interaction_profile.json", interaction_payload)
    physics_payload = {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "scientific_workbench.acrylic_spoon_rack.provisional.r1",
        "revision": "r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": "Geometry and nominal acrylic density only; not measured material parameters.",
            "center_of_mass_convention": "asset_entry_prim_body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound profile bundle in a new revision.",
        },
        "scope_rules": [{
            "scope_path": ENTRY_PRIM,
            "body_rules": [{
                "relative_path": ".",
                "motion_role": "kinematic",
                "clear_density": True,
                "mass_properties": {
                    "mode": "explicit",
                    "quality_tier": "provisional_geometry",
                    "mass_kg": 0.35,
                    "diagonal_inertia_kg_m2": [0.00225, 0.00318, 0.00164],
                    "center_of_mass_body_local": [0.0, 0.0, 0.08],
                    "principal_axes": [1.0, 0.0, 0.0, 0.0],
                },
            }],
        }],
    }
    physics = _json(out / "physics_profile.json", physics_payload)
    provenance = _json(out / "provenance.json", {
        "schema_version": "aan.acrylic_spoon_rack_source_bound_build.v1",
        "source_usd": str(source),
        "source_sha256": _sha(source),
        "source_modified": False,
        "facade_sha256": _sha(facade),
        "central_socket": "middle_socket_04",
        "hole_diameter_m": 0.014,
        "rod_diameter_m": 0.00723,
        "claim_boundary": "Profile construction only; runtime insertion is qualified separately.",
    })
    return {"facade": facade, "interaction": interaction, "physics": physics, "provenance": provenance}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({key: str(value) for key, value in build(source=args.source, out=args.out).items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
