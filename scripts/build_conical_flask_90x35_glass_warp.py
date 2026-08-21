#!/usr/bin/env python3
"""Bake LabUtopia conical-flask glass into a 90/35/150 mm identity-scale facade.

Radial scale varies with height (k_r(z)) and height is squashed by k_h. Both
are baked into mesh points. The public entry prim stays identity-scale.
The identity conical_bottle03 package is hash-locked and is not replaced.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import shutil
from pathlib import Path
from typing import Any, Iterable, Sequence


SOURCE_HEIGHT_MM = 196.5674179
SOURCE_BELLY_OD_MM = 113.3053223
SOURCE_INNER_MOUTH_MM = 49.19089655
Z_BELLY_M = 0.012295
Z_MOUTH_M = 0.195240
TARGET_BELLY_OD_MM = 90.0
TARGET_INNER_MOUTH_MM = 35.0
TARGET_HEIGHT_MM = 150.0
K_H = TARGET_HEIGHT_MM / SOURCE_HEIGHT_MM
K_R_BELLY = TARGET_BELLY_OD_MM / SOURCE_BELLY_OD_MM
K_R_MOUTH = TARGET_INNER_MOUTH_MM / SOURCE_INNER_MOUTH_MM
K_R_SLOPE = (K_R_MOUTH - K_R_BELLY) / (Z_MOUTH_M - Z_BELLY_M)

SOURCE_MASS_KG = 0.25
SOURCE_INERTIA_KG_M2 = (0.001874, 0.001874, 0.00214)
SOURCE_COM_Z_M = 0.075
SOURCE_OPENING_Z_M = 0.1965674179
SOURCE_GRASP_Z_M = 0.16

ENTRY_PRIM = "/World/ConicalFlask90x35Warp"
ENTRY_NAME = "ConicalFlask90x35Warp"
ASSET_ID = "scientific_workbench_conical_flask_90x35_glass_warp"
PROFILE_ID = "scientific_workbench.conical_flask_90x35_glass_warp.r1"
IDENTITY_FACADE_SHA256 = (
    "82115bd942c40214fdb2bacc6f4327111b452e67280bb3405b2451ddee6a83b9"
)
IDENTITY_PACKAGE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "scientific_workbench_task_assets_20260731/conical_bottle_identity"
)
IDENTITY_MESH_PRIM = "/World/conical_bottle03/Visual/Source/mesh"
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}
SLICE_BAND_M = 0.001


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


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
    return f"{value:.12g}"


def radial_scale(z: float) -> float:
    return K_R_BELLY + (z - Z_BELLY_M) * K_R_SLOPE


def warp_point(x: float, y: float, z: float) -> tuple[float, float, float]:
    scale = radial_scale(z)
    return scale * x, scale * y, K_H * z


def warp_points(
    points: Sequence[Sequence[float]],
) -> list[tuple[float, float, float]]:
    return [warp_point(float(x), float(y), float(z)) for x, y, z in points]


def warp_normal(
    nx: float,
    ny: float,
    nz: float,
    x: float,
    y: float,
    z: float,
) -> tuple[float, float, float]:
    kr = radial_scale(z)
    if kr == 0.0:
        return 0.0, 0.0, 0.0
    nxp = nx / kr
    nyp = ny / kr
    nzp = (
        -(K_R_SLOPE * x * nx) / (kr * K_H)
        - (K_R_SLOPE * y * ny) / (kr * K_H)
        + nz / K_H
    )
    norm = math.sqrt(nxp * nxp + nyp * nyp + nzp * nzp)
    if norm == 0.0:
        return 0.0, 0.0, 0.0
    return nxp / norm, nyp / norm, nzp / norm


def _radii(points: Sequence[Sequence[float]]) -> list[float]:
    return [math.hypot(float(x), float(y)) for x, y, _z in points]


def _slice(
    points: Sequence[Sequence[float]],
    z: float,
    band: float = SLICE_BAND_M,
) -> list[Sequence[float]]:
    selected = [point for point in points if abs(float(point[2]) - z) <= band]
    if selected:
        return selected
    nearest = min(points, key=lambda point: abs(float(point[2]) - z))
    nearest_z = float(nearest[2])
    return [point for point in points if abs(float(point[2]) - nearest_z) <= band]


def measure_flask_mm(
    points: Sequence[Sequence[float]],
    *,
    belly_z_m: float,
    mouth_z_m: float,
) -> dict[str, float]:
    zs = [float(point[2]) for point in points]
    zmin = min(zs)
    zmax = max(zs)
    belly = _slice(points, belly_z_m)
    mouth = _slice(points, mouth_z_m)
    return {
        "belly_od_mm": 2.0 * max(_radii(belly)) * 1000.0,
        "inner_mouth_mm": 2.0 * min(_radii(mouth)) * 1000.0,
        "height_mm": (zmax - zmin) * 1000.0,
        "opening_mm": zmax * 1000.0,
        "zmin_m": zmin,
        "zmax_m": zmax,
    }


def _mean_kr(points: Sequence[Sequence[float]]) -> float:
    scales = [radial_scale(float(z)) for _x, _y, z in points]
    return sum(scales) / len(scales)


def scaled_mass_bundle(source_points: Sequence[Sequence[float]]) -> dict[str, Any]:
    mean_kr = _mean_kr(source_points)
    volume_scale = mean_kr * mean_kr * K_H
    ixx, _iyy, izz = SOURCE_INERTIA_KG_M2
    i_radial = izz / 2.0
    i_z = ixx - i_radial
    ixx_new = volume_scale * (mean_kr * mean_kr * i_radial + K_H * K_H * i_z)
    izz_new = volume_scale * mean_kr * mean_kr * izz
    return {
        "mean_kr": mean_kr,
        "k_h": K_H,
        "volume_scale": volume_scale,
        "mass_kg": SOURCE_MASS_KG * volume_scale,
        "com_z_m": SOURCE_COM_Z_M * K_H,
        "inertia_kg_m2": [ixx_new, ixx_new, izz_new],
        "opening_z_m": SOURCE_OPENING_Z_M * K_H,
        "grasp_z_m": SOURCE_GRASP_Z_M * K_H,
    }


def load_composed_visual_mesh(facade: Path) -> dict[str, Any]:
    from pxr import Gf, Usd, UsdGeom

    stage = Usd.Stage.Open(str(facade))
    if stage is None:
        raise FileNotFoundError(facade)
    prim = stage.GetPrimAtPath(IDENTITY_MESH_PRIM)
    if not prim or not prim.IsValid():
        raise ValueError(f"missing composed mesh prim {IDENTITY_MESH_PRIM} in {facade}")
    mesh = UsdGeom.Mesh(prim)
    local_to_world = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    local_points = list(mesh.GetPointsAttr().Get() or [])
    points = []
    for point in local_points:
        world = local_to_world.Transform(Gf.Vec3d(point))
        points.append((float(world[0]), float(world[1]), float(world[2])))
    local_normals = list(mesh.GetNormalsAttr().Get() or [])
    indices = [int(index) for index in (mesh.GetFaceVertexIndicesAttr().Get() or [])]
    normals = []
    for index, normal in enumerate(local_normals):
        vertex = points[indices[index] if index < len(indices) else 0]
        world_n = local_to_world.TransformDir(Gf.Vec3d(normal))
        normals.append(
            (
                float(world_n[0]),
                float(world_n[1]),
                float(world_n[2]),
                vertex[0],
                vertex[1],
                vertex[2],
            )
        )
    st_attr = prim.GetAttribute("primvars:st")
    st1_attr = prim.GetAttribute("primvars:st_1")
    return {
        "points": points,
        "normals": normals,
        "face_vertex_counts": [int(v) for v in (mesh.GetFaceVertexCountsAttr().Get() or [])],
        "face_vertex_indices": indices,
        "st": [tuple(map(float, uv)) for uv in (st_attr.Get() or [])] if st_attr else [],
        "st_1": [tuple(map(float, uv)) for uv in (st1_attr.Get() or [])] if st1_attr else [],
        "normals_interpolation": mesh.GetNormalsInterpolation() or "faceVarying",
        "do_not_cast_shadows": True,
    }


def _format_vec3_array(prefix: str, values: Iterable[Sequence[float]], *, suffix: str = "") -> str:
    body = ", ".join(f"({_fmt(float(x))}, {_fmt(float(y))}, {_fmt(float(z))})" for x, y, z in values)
    return f"            {prefix} = [{body}]{suffix}\n"


def _format_vec2_array(name: str, values: Iterable[Sequence[float]]) -> str:
    body = ", ".join(f"({_fmt(float(u))}, {_fmt(float(v))})" for u, v in values)
    return (
        f"            texCoord2f[] {name} = [{body}] (\n"
        '                interpolation = "faceVarying"\n'
        "            )\n"
    )


def _format_int_array(name: str, values: Iterable[int]) -> str:
    body = ", ".join(str(int(value)) for value in values)
    return f"            int[] {name} = [{body}]\n"


def _baked_usda(mesh: dict[str, Any], warped_points: Sequence[Sequence[float]]) -> str:
    warped_normals = [
        warp_normal(nx, ny, nz, x, y, z) for nx, ny, nz, x, y, z in mesh["normals"]
    ]
    xs = [float(x) for x, _y, _z in warped_points]
    ys = [float(y) for _x, y, _z in warped_points]
    zs = [float(z) for _x, _y, z in warped_points]
    extent = ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))
    normals_block = (
        _format_vec3_array("normal3f[] normals", warped_normals).rstrip()
        + " (\n"
        f'                interpolation = "{mesh["normals_interpolation"]}"\n'
        "            )\n"
    )
    st_block = _format_vec2_array("primvars:st", mesh["st"]) if mesh["st"] else ""
    st1_block = _format_vec2_array("primvars:st_1", mesh["st_1"]) if mesh["st_1"] else ""
    return f'''#usda 1.0
(
    defaultPrim = "World"
    doc = "Axisymmetric k_r(z)/k_h glass warp; root scale identity; OmniSurface_Glass preserved"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "{ENTRY_NAME}"
    {{
        def Mesh "mesh" (
            prepend apiSchemas = ["MaterialBindingAPI", "PhysicsCollisionAPI", "PhysicsMeshCollisionAPI", "PhysxCollisionAPI", "PhysxSDFMeshCollisionAPI"]
        )
        {{
{_format_vec3_array("float3[] extent", extent).rstrip()}
{_format_int_array("faceVertexCounts", mesh["face_vertex_counts"]).rstrip()}
{_format_int_array("faceVertexIndices", mesh["face_vertex_indices"]).rstrip()}
            rel material:binding = </World/{ENTRY_NAME}/__aan_materials/OmniSurface_Glass> (
                bindMaterialAs = "weakerThanDescendants"
            )
{normals_block.rstrip()}
{_format_vec3_array("point3f[] points", warped_points).rstrip()}
            bool physics:collisionEnabled = 1
            uniform token physics:approximation = "sdf"
            bool primvars:doNotCastShadows = 1
{st_block.rstrip()}
{st1_block.rstrip()}
            uniform token subdivisionScheme = "none"
            float3 xformOp:scale = (1, 1, 1)
            double3 xformOp:translate = (0, 0, 0)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
        }}

        def Scope "__aan_materials"
        {{
            def Material "OmniSurface_Glass"
            {{
                token outputs:mdl:displacement.connect = </World/{ENTRY_NAME}/__aan_materials/OmniSurface_Glass/Shader.outputs:out>
                token outputs:mdl:surface.connect = </World/{ENTRY_NAME}/__aan_materials/OmniSurface_Glass/Shader.outputs:out>
                token outputs:mdl:volume.connect = </World/{ENTRY_NAME}/__aan_materials/OmniSurface_Glass/Shader.outputs:out>

                def Shader "Shader"
                {{
                    uniform token info:implementationSource = "sourceAsset"
                    uniform asset info:mdl:sourceAsset = @./mdl/OmniSurfacePresets.mdl@
                    uniform token info:mdl:sourceAsset:subIdentifier = "OmniSurface_Glass"
                    token outputs:out (
                        renderType = "material"
                    )
                }}
            }}
        }}
    }}
}}
'''


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
                prepend references = @{baked.resolve().as_posix()}@</World/{ENTRY_NAME}>
            )
            {{
            }}
        }}
    }}
}}
'''


def _frame(z: float = 0.0) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [0.0, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _interaction(facade: Path, geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "aan.object_interaction_profile.v1",
        "profile_id": PROFILE_ID,
        "revision": "r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": ENTRY_PRIM,
        "rigid_root": {
            "motion_role": "dynamic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": [
            {
                "relative_path": "Visual/Source/mesh",
                "mode": "preserve",
                "purpose": ["gripper", "support", "containment"],
                "approximation": "sdf",
            }
        ],
        "open_top": {
            "required": True,
            "axis_body_local": [0.0, 0.0, 1.0],
            "aperture_frame": "opening",
            "evidence": {
                "status": "declared",
                "method": "identity_sdf_preserved_after_axisymmetric_krz_kh_bake",
                "claim_boundary": (
                    "Cooked aperture remains a required Isaac 4.1 gate. "
                    "This is not a 250 mL, GPU-PBD, or pour-success claim."
                ),
            },
        },
        "named_frames": {
            "opening": _frame(geometry["opening_z_m"]),
            "grasp": _frame(geometry["grasp_z_m"]),
            "support": _frame(0.0),
        },
        "runtime_gates": {
            "root_motion": {"required": True, "min_translation_m": 0.05},
            "stable_support": {"required": True},
            "gripper_collision": {"required": True},
        },
        "claim_boundary": (
            "Proportion fit toward 90/35/150 mm after producer-side axisymmetric warp. "
            "Not a 250 mL volume, GPU-PBD cavity, or pour-success claim."
        ),
    }


def _physics(facade: Path, geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": PROFILE_ID,
        "revision": "r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": (
                "Identity r2 provisional mass bundle mapped by mean(k_r)^2 * k_h "
                "and the same affine z map. Not measured material parameters."
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


def build(*, source_package: Path, out: Path) -> dict[str, Any]:
    source_package = source_package.resolve()
    facade_src = source_package / "facade" / "facade.usda"
    if not facade_src.is_file():
        raise FileNotFoundError(facade_src)
    if _sha(facade_src) != IDENTITY_FACADE_SHA256:
        raise ValueError(f"identity facade hash drifted: {_sha(facade_src)}")
    before = _tree_hashes(source_package)
    mesh = load_composed_visual_mesh(facade_src)
    warped_points = warp_points(mesh["points"])
    geometry = scaled_mass_bundle(mesh["points"])
    geometry["measured_mm"] = measure_flask_mm(
        warped_points,
        belly_z_m=Z_BELLY_M * K_H,
        mouth_z_m=Z_MOUTH_M * K_H,
    )
    out = out.resolve()
    baked = _write(
        out / "input" / "baked" / "conical_flask_90x35_glass_warp.usda",
        _baked_usda(mesh, warped_points),
    )
    mdl_src = source_package / "package" / "deps" / "mdl"
    mdl_dst = baked.parent / "mdl"
    if mdl_dst.exists():
        shutil.rmtree(mdl_dst)
    shutil.copytree(mdl_src, mdl_dst)
    facade = _write(
        out / "input" / "facades" / "conical_flask_90x35_glass_warp" / "facade.usda",
        _facade(baked),
    )
    interaction = _write_json(
        out / "input" / "profiles" / "conical_flask_90x35_glass_warp.interaction.json",
        _interaction(facade, geometry),
    )
    physics = _write_json(
        out / "input" / "profiles" / "conical_flask_90x35_glass_warp.physics.json",
        _physics(facade, geometry),
    )
    after = _tree_hashes(source_package)
    if after != before:
        raise RuntimeError("identity conical_bottle03 package was modified")
    provenance = {
        "schema_version": "aan.conical_flask_90x35_glass_warp_provenance.v1",
        "asset_id": ASSET_ID,
        "request_id": "scientific_workbench_conical_flask_90x35_glass_warp_20260821",
        "source": {
            "package": source_package.as_posix(),
            "facade": facade_src.as_posix(),
            "facade_sha256": IDENTITY_FACADE_SHA256,
            "entry_prim": "/World/conical_bottle03",
            "unchanged": True,
        },
        "bake": {
            "k_h": K_H,
            "k_r_belly": K_R_BELLY,
            "k_r_mouth": K_R_MOUTH,
            "z_belly_m": Z_BELLY_M,
            "z_mouth_m": Z_MOUTH_M,
            "mean_kr": geometry["mean_kr"],
            "root_scale": [1.0, 1.0, 1.0],
            "method": "axisymmetric_krz_and_kh",
        },
        "geometry": geometry,
        "forbidden_reuse": [
            "scientific_workbench_conical_bottle03_dynamic",
            "runtime_nonuniform_xformOp_scale_on_identity_package",
        ],
        "facade_sha256": _sha(facade),
        "baked_sha256": _sha(baked),
        "claim_boundary": (
            "Proportion fit toward 90/35/150 mm only. "
            "Not a 250 mL volume, GPU-PBD, or pour-success claim."
        ),
    }
    manifest = _write_json(out / "input" / "source_manifest.json", provenance)
    return {
        "baked": baked,
        "facade": facade,
        "interaction": interaction,
        "physics": physics,
        "manifest": manifest,
        "warped_points": warped_points,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", type=Path, default=IDENTITY_PACKAGE)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(source_package=args.source_package, out=args.out.resolve())
    printable = {
        key: (value.as_posix() if isinstance(value, Path) else f"{len(value)} points")
        for key, value in result.items()
    }
    print(json.dumps(printable, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
