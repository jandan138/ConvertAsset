#!/usr/bin/env python3
"""Bake a closed, HCI-fit 15 mL red-cap tube facade and source-bound profiles.

The producer exception is explicit: radial k_d and height k_h are baked into
mesh points and child translates. The public entry prim stays identity-scale.
The cap is frozen at source frame 1 so the assembly is one closed rigid body.
This asset is not reusable for cap-tightening.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any, Callable


K_D = 0.53
K_H = 0.35
K_D_BAND = (0.50, 0.55)
K_H_BAND = (0.33, 0.37)
# Consumer-authorized "short" variant for the visual arm-plate cups: the cups
# are 17 mm deep blind holes (floor z 0.1281) and the closed-lid inner surface
# is z 0.1569, so the seated cap top must stay below ~0.155 m.
K_H_SHORT = 0.21
K_H_SHORT_BAND = (0.20, 0.22)
SOURCE_CAP_OD_MM = 20.84
SOURCE_ASSEMBLED_HEIGHT_MM = 119.7
SOURCE_BODY_RADIUS_M = 0.00834
SOURCE_BODY_HEIGHT_M = 0.101
SOURCE_BODY_Z_M = 0.0505
SOURCE_CAP_RADIUS_M = 0.01042
SOURCE_CAP_HEIGHT_M = 0.01874
SOURCE_CAP_Z_M = 0.11033
SOURCE_BODY_MASS_KG = 0.015
SOURCE_CAP_MASS_KG = 0.004
ENTRY_PRIM = "/World/CentrifugeTube15mlClosed"
ENTRY_NAME = "CentrifugeTube15mlClosed"
ASSET_ID = "scientific_workbench_centrifuge_tube_15ml_red_cap_closed_hci_fit"
PROFILE_ID = "scientific_workbench.centrifuge_tube_15ml_closed.hci_fit.r1"
ARCHIVE_SHA256 = "ab0e286972551f728f73d62054c5b46c00e9056c99e1d402eccb6819cad5f955"
FORBIDDEN_K0365_TUBE_SHA256 = (
    "7877f65af3d71bfdc51e6ec2a40fce7f7a199be8f70d3c19755ec3aa4650e794"
)
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}
DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "scientific_workbench_asset_library_20260810/实验室资产库/02_塑料耗材/"
    "15毫升离心管_红盖/centrifuge_tube_15ml_red_cap.usda"
)
VEC3_RE = re.compile(
    r"\(\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*"
    r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*"
    r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*\)"
)
TRANSLATE_RE = re.compile(
    r"((?:double|float)3\s+xformOp:translate\s*=\s*)"
    r"\(\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*"
    r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*,\s*"
    r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*\)"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    return _write(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
    )


def _fmt(value: float) -> str:
    if value == 0.0:
        return "0"
    text = f"{value:.12g}"
    if text.startswith("0.") or text.startswith("-0."):
        return text
    return text


def assert_hci_fit_scale(
    k_d: float,
    k_h: float,
    *,
    k_d_band: tuple[float, float] = K_D_BAND,
    k_h_band: tuple[float, float] = K_H_BAND,
) -> None:
    if not (k_d_band[0] <= k_d <= k_d_band[1]):
        raise ValueError(f"k_d {k_d} is outside {k_d_band}")
    if not (k_h_band[0] <= k_h <= k_h_band[1]):
        raise ValueError(f"k_h {k_h} is outside {k_h_band}")


def assert_not_forbidden_k0365_tube_hash(sha: str) -> None:
    if sha == FORBIDDEN_K0365_TUBE_SHA256:
        raise ValueError(
            "k=0.365 glass test-tube evidence is forbidden for this HCI-fit closed 15 mL request"
        )


def scaled_geometry(
    k_d: float = K_D,
    k_h: float = K_H,
    *,
    k_d_band: tuple[float, float] = K_D_BAND,
    k_h_band: tuple[float, float] = K_H_BAND,
) -> dict[str, Any]:
    assert_hci_fit_scale(k_d, k_h, k_d_band=k_d_band, k_h_band=k_h_band)
    volume_scale = k_d * k_d * k_h
    body_radius = SOURCE_BODY_RADIUS_M * k_d
    body_height = SOURCE_BODY_HEIGHT_M * k_h
    body_z = SOURCE_BODY_Z_M * k_h
    cap_radius = SOURCE_CAP_RADIUS_M * k_d
    cap_height = SOURCE_CAP_HEIGHT_M * k_h
    cap_z = SOURCE_CAP_Z_M * k_h
    body_mass = SOURCE_BODY_MASS_KG * volume_scale
    cap_mass = SOURCE_CAP_MASS_KG * volume_scale
    mass = body_mass + cap_mass
    com_z = (body_mass * body_z + cap_mass * cap_z) / mass

    def cylinder_inertia(mass_kg: float, radius: float, height: float, z: float) -> tuple[float, float]:
        ixx_cm = mass_kg * (3.0 * radius * radius + height * height) / 12.0
        izz = 0.5 * mass_kg * radius * radius
        dz = z - com_z
        return ixx_cm + mass_kg * dz * dz, izz

    body_ixx, body_izz = cylinder_inertia(body_mass, body_radius, body_height, body_z)
    cap_ixx, cap_izz = cylinder_inertia(cap_mass, cap_radius, cap_height, cap_z)
    cap_od_mm = SOURCE_CAP_OD_MM * k_d
    assembled_height_mm = SOURCE_ASSEMBLED_HEIGHT_MM * k_h
    hole_id_mm = (12.5, 13.3)
    return {
        "k_d": k_d,
        "k_h": k_h,
        "cap_od_mm": cap_od_mm,
        "assembled_height_mm": assembled_height_mm,
        "radial_clearance_in_hci_hole_mm": [
            (hole_id_mm[0] - cap_od_mm) / 2.0,
            (hole_id_mm[1] - cap_od_mm) / 2.0,
        ],
        "tube_radius_m": cap_radius,
        "tube_height_m": assembled_height_mm / 1000.0,
        "colliders": {
            "body": {
                "xyz": [0.0, 0.0, body_z],
                "radius": body_radius,
                "height": body_height,
            },
            "cap": {
                "xyz": [0.0, 0.0, cap_z],
                "radius": cap_radius,
                "height": cap_height,
            },
        },
        "mass_kg": mass,
        "com_z_m": com_z,
        "inertia_kg_m2": [body_ixx + cap_ixx, body_ixx + cap_ixx, body_izz + cap_izz],
        "grasp_z_m": body_z,
    }


def _matching_bracket(text: str, open_index: int, opener: str = "[", closer: str = "]") -> int:
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unbalanced {opener}{closer} starting at {open_index}")


def _strip_timesamples(text: str) -> str:
    marker = ".timeSamples = {"
    while marker in text:
        attr_end = text.index(marker)
        line_start = text.rfind("\n", 0, attr_end) + 1
        open_index = attr_end + len(marker) - 1
        close_index = _matching_bracket(text, open_index, "{", "}")
        end = close_index + 1
        if end < len(text) and text[end] == "\n":
            end += 1
        text = text[:line_start] + text[end:]
    return text


def _freeze_stage_timeline(text: str) -> str:
    text = re.sub(r"endTimeCode = \d+", "endTimeCode = 1", text, count=1)
    text = re.sub(r"startTimeCode = \d+", "startTimeCode = 1", text, count=1)
    return text


def _inject_frozen_cap_controller(text: str) -> str:
    marker = 'def Xform "Cap_Controller"'
    start = text.find(marker)
    if start < 0:
        return text
    brace = text.find("{", start)
    close = _matching_bracket(text, brace, "{", "}")
    inner = text[brace + 1 : close]
    if "xformOp:translate =" not in inner:
        inner = re.sub(
            r"\n[ \t]*uniform token\[\] xformOpOrder = \[[^\]]*\]",
            "",
            inner,
            count=1,
        )
        inner = (
            "\n            custom string userProperties:animation = "
            '"frozen_closed_frame_1"\n'
            "            custom string userProperties:blender:object_name = "
            '"Cap_Controller"\n'
            "            float3 xformOp:rotateXYZ = (0, 0, 0)\n"
            "            float3 xformOp:scale = (1, 1, 1)\n"
            "            double3 xformOp:translate = (0, 0, 0)\n"
            '            uniform token[] xformOpOrder = ["xformOp:translate", '
            '"xformOp:rotateXYZ", "xformOp:scale"]\n'
            + inner
        )
    return text[: brace + 1] + inner + text[close:]


def _scale_xyz(x: float, y: float, z: float, k_d: float, k_h: float) -> tuple[float, float, float]:
    return x * k_d, y * k_d, z * k_h


def _scale_normal(x: float, y: float, z: float, k_d: float, k_h: float) -> tuple[float, float, float]:
    nx, ny, nz = x / k_d, y / k_d, z / k_h
    norm = (nx * nx + ny * ny + nz * nz) ** 0.5
    if norm == 0.0:
        return 0.0, 0.0, 0.0
    return nx / norm, ny / norm, nz / norm


def _rewrite_vec3_block(block: str, mapper: Callable[[float, float, float], tuple[float, float, float]]) -> str:
    def replace(match: re.Match[str]) -> str:
        x, y, z = mapper(float(match.group(1)), float(match.group(2)), float(match.group(3)))
        return f"({_fmt(x)}, {_fmt(y)}, {_fmt(z)})"

    return VEC3_RE.sub(replace, block)


def _rewrite_named_vec3_arrays(
    text: str,
    prefixes: tuple[str, ...],
    mapper: Callable[[float, float, float], tuple[float, float, float]],
) -> str:
    for prefix in prefixes:
        cursor = 0
        pieces: list[str] = []
        while True:
            start = text.find(prefix, cursor)
            if start < 0:
                pieces.append(text[cursor:])
                break
            open_index = text.find("[", start + len(prefix))
            close_index = _matching_bracket(text, open_index, "[", "]")
            pieces.append(text[cursor:open_index])
            pieces.append(_rewrite_vec3_block(text[open_index : close_index + 1], mapper))
            cursor = close_index + 1
        text = "".join(pieces)
    return text


def bake_closed_usda(
    source_text: str,
    *,
    k_d: float = K_D,
    k_h: float = K_H,
    k_d_band: tuple[float, float] = K_D_BAND,
    k_h_band: tuple[float, float] = K_H_BAND,
) -> str:
    assert_hci_fit_scale(k_d, k_h, k_d_band=k_d_band, k_h_band=k_h_band)
    text = _strip_timesamples(source_text)
    text = _freeze_stage_timeline(text)
    text = _inject_frozen_cap_controller(text)
    text = _rewrite_named_vec3_arrays(
        text,
        ("point3f[] points = ", "float3[] extent = "),
        lambda x, y, z: _scale_xyz(x, y, z, k_d, k_h),
    )
    text = _rewrite_named_vec3_arrays(
        text,
        ("normal3f[] normals = ",),
        lambda x, y, z: _scale_normal(x, y, z, k_d, k_h),
    )

    def replace_translate(match: re.Match[str]) -> str:
        x, y, z = _scale_xyz(float(match.group(2)), float(match.group(3)), float(match.group(4)), k_d, k_h)
        return f"{match.group(1)}({_fmt(x)}, {_fmt(y)}, {_fmt(z)})"

    text = TRANSLATE_RE.sub(replace_translate, text)
    if "doc =" in text:
        text = re.sub(
            r'doc = "[^"]*"',
            'doc = "Closed rigid HCI-fit bake; cap frozen at frame 1; non-uniform scale baked into mesh points"',
            text,
            count=1,
        )
    return text


def _facade(baked: Path) -> str:
    return f'''#usda 1.0
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
    def Xform "{ENTRY_NAME}"
    {{
        def Xform "Visual"
        {{
            def Xform "Source" (
                prepend references = @{baked.resolve().as_posix()}@</root>
            ) {{}}
        }}
    }}
}}
'''


def _frame(z: float = 0.0) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [0.0, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _collider(name: str, *, xyz: list[float], radius: float, height: float) -> dict[str, Any]:
    return {
        "relative_path": f"__aan_collision_proxy/{name}",
        "mode": "author",
        "purpose": ["support", "gripper"],
        "geometry": {
            "type": "Cylinder",
            "axis": "Z",
            "radius": radius,
            "height": height,
            "translation_body_local_usd": xyz,
            "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
        },
    }


def _interaction(facade: Path, geometry: dict[str, Any]) -> dict[str, Any]:
    body = geometry["colliders"]["body"]
    cap = geometry["colliders"]["cap"]
    return {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": PROFILE_ID,
        "revision": "hci-fit-r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": ENTRY_PRIM,
        "rigid_root": {
            "motion_role": "dynamic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": [
            _collider("body", xyz=body["xyz"], radius=body["radius"], height=body["height"]),
            _collider("cap", xyz=cap["xyz"], radius=cap["radius"], height=cap["height"]),
        ],
        "required_named_frames": ["support", "grasp"],
        "named_frames": {
            "support": _frame(0.0),
            "grasp": _frame(geometry["grasp_z_m"]),
        },
        "open_top": {"required": False},
        "runtime_gates": {
            "root_motion": {"required": True, "min_translation_m": 0.01},
            "stable_support": {"required": True},
            "gripper_collision": {"required": True},
        },
        "claim_boundary": (
            "Closed rigid HCI-fit assembly after baked non-uniform scale. "
            "Not a cap-tightening asset and not a real 15 mL physical-parity claim."
        ),
    }


def _physics(facade: Path, geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": PROFILE_ID,
        "revision": "hci-fit-r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": (
                "Nominal geometry-based simulation values after k_d/k_h bake; "
                "not measured material parameters."
            ),
            "center_of_mass_convention": "asset_entry_prim_body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound bundle in a new profile revision.",
        },
        "scope_rules": [
            {
                "scope_path": ENTRY_PRIM,
                "body_rules": [
                    {
                        "relative_path": ".",
                        "motion_role": "dynamic",
                        "clear_density": True,
                        "mass_properties": {
                            "mode": "explicit",
                            "quality_tier": "provisional_geometry",
                            "mass_kg": geometry["mass_kg"],
                            "diagonal_inertia_kg_m2": geometry["inertia_kg_m2"],
                            "center_of_mass_body_local": [0.0, 0.0, geometry["com_z_m"]],
                            "principal_axes": [1.0, 0.0, 0.0, 0.0],
                        },
                    }
                ],
            }
        ],
    }


def build(
    *,
    source: Path,
    out: Path,
    k_d: float = K_D,
    k_h: float = K_H,
    k_d_band: tuple[float, float] = K_D_BAND,
    k_h_band: tuple[float, float] = K_H_BAND,
) -> dict[str, Path]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    source_before = _sha(source)
    geometry = scaled_geometry(k_d, k_h, k_d_band=k_d_band, k_h_band=k_h_band)
    baked_text = bake_closed_usda(
        source.read_text(encoding="utf-8"),
        k_d=k_d,
        k_h=k_h,
        k_d_band=k_d_band,
        k_h_band=k_h_band,
    )
    baked = _write(
        out / "input" / "baked" / "centrifuge_tube_15ml_red_cap_closed_hci_fit.usda",
        baked_text,
    )
    facade = _write(
        out / "input" / "facades" / "centrifuge_tube_15ml_closed_hci_fit" / "facade.usda",
        _facade(baked),
    )
    interaction = _write_json(
        out / "input" / "profiles" / "centrifuge_tube_15ml_closed_hci_fit.interaction.json",
        _interaction(facade, geometry),
    )
    physics = _write_json(
        out / "input" / "profiles" / "centrifuge_tube_15ml_closed_hci_fit.physics.json",
        _physics(facade, geometry),
    )
    source_after = _sha(source)
    if source_after != source_before:
        raise RuntimeError("raw 15 mL source USDA was modified")
    provenance = {
        "schema_version": "aan.hci_15ml_closed_insert_lid_provenance.v1",
        "asset_id": ASSET_ID,
        "request_id": "scientific_workbench_hci_15ml_closed_insert_lid_20260818",
        "archive_sha256": ARCHIVE_SHA256,
        "source": {
            "path": source.as_posix(),
            "sha256": source_before,
            "closed_pose": "frame_1",
            "unchanged": True,
        },
        "bake": {
            "k_d": k_d,
            "k_h": k_h,
            "root_scale": [1.0, 1.0, 1.0],
            "weld_cap_to_body": True,
            "method": "scale_mesh_points_child_translates_and_freeze_cap_controller",
        },
        "geometry": geometry,
        "forbidden_reuse": [
            "scientific_workbench_tighten_centrifuge_tube_cap",
            "scientific_workbench_test_tube_dynamic_uniform_scale_k0365",
            FORBIDDEN_K0365_TUBE_SHA256,
        ],
        "facade_sha256": _sha(facade),
        "baked_sha256": _sha(baked),
        "claim_boundary": (
            "Kinematic HCI insert-and-lid-close geometry only. "
            "Not Feishu Task 10/11, not robot policy, not real 15 mL parity."
        ),
    }
    manifest = _write_json(out / "input" / "source_manifest.json", provenance)
    return {
        "baked": baked,
        "facade": facade,
        "interaction": interaction,
        "physics": physics,
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--k-d", type=float, default=K_D)
    parser.add_argument("--k-h", type=float, default=K_H)
    parser.add_argument(
        "--short-cup-variant",
        action="store_true",
        help=(
            "Consumer-authorized short tube for the 17 mm visual arm-plate "
            "cups: pins k_h to the short band (default k_h %.3f)." % K_H_SHORT
        ),
    )
    args = parser.parse_args()
    k_h = K_H_SHORT if args.short_cup_variant else args.k_h
    k_h_band = K_H_SHORT_BAND if args.short_cup_variant else K_H_BAND
    result = build(
        source=args.source,
        out=args.out.resolve(),
        k_d=args.k_d,
        k_h=k_h,
        k_h_band=k_h_band,
    )
    print(json.dumps({key: value.as_posix() for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
