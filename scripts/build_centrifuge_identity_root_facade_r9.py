#!/usr/bin/env python3
"""Build the r9 identity-root centrifuge facade with a stable benchtop support.

The r8 facade is retained as a weaker sublayer.  This producer-owned overlay
adds one thin, invisible collision cube to the existing base rigid body.  Its
footprint is the smallest union of the r8 housing footprint and a 10 mm band
around the mass-weighted center of mass.  Raw geometry, existing transforms,
joints, drives, and the complete mass/inertia bundle remain unchanged.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_R8_ROOT = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/outputs/centrifuge_identity_root_r8"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs/centrifuge_identity_root_r9"
ROOT = "/World/Centrifuge"
BASE_BODY = f"{ROOT}/group_0"
BASE_VISUAL_ROOT = f"{BASE_BODY}/body"
HOUSING_COLLIDER = f"{BASE_BODY}/__aan_collision_proxy/housing"
BENCHTOP_SUPPORT_COLLIDER = (
    f"{BASE_BODY}/__aan_collision_proxy/__aan_benchtop_support"
)
MINIMUM_COM_SUPPORT_MARGIN_M = 0.005
TARGET_COM_SUPPORT_MARGIN_M = 0.010
SUPPORT_PAD_HEIGHT_M = 0.008
IDENTITY_TOLERANCE = 1.0e-6


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to replace generated artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _vector(value: Any) -> list[float]:
    return [float(value[0]), float(value[1]), float(value[2])]


def _matrix(value: Any) -> list[list[float]]:
    return [
        [float(value[row][column]) for column in range(4)]
        for row in range(4)
    ]


def _rebind_physics_profile(
    value: dict[str, Any],
    *,
    source_sha256: str,
) -> dict[str, Any]:
    """Rebind source identity without changing any physical parameter."""
    rebound = deepcopy(value)
    source_binding = rebound.get("source_binding")
    if not isinstance(source_binding, dict):
        raise ValueError("physics profile source_binding must be an object")
    profile_id = rebound.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("physics profile profile_id must be a non-empty string")
    source_binding["sha256"] = source_sha256
    rebound["profile_id"] = f"{profile_id}.benchtop-r9"
    rebound["revision"] = "r2-benchtop-support"
    return rebound


def _support_margins(
    minimum: list[float],
    maximum: list[float],
    combined_com: list[float],
) -> dict[str, float]:
    """Return signed XY distances from the COM projection to support edges."""
    if not all(len(value) == 3 for value in (minimum, maximum, combined_com)):
        raise ValueError("support bounds and COM must have three components")
    return {
        "negative_x_m": float(combined_com[0] - minimum[0]),
        "positive_x_m": float(maximum[0] - combined_com[0]),
        "negative_y_m": float(combined_com[1] - minimum[1]),
        "positive_y_m": float(maximum[1] - combined_com[1]),
    }


def _plan_support_bounds(
    existing_minimum: list[float],
    existing_maximum: list[float],
    combined_com: list[float],
    *,
    support_plane_z_m: float,
) -> tuple[list[float], list[float]]:
    """Plan the minimal r9 support AABB with a 10 mm COM band."""
    if not all(
        len(value) == 3
        for value in (existing_minimum, existing_maximum, combined_com)
    ):
        raise ValueError("support inputs must have three components")
    if any(
        existing_minimum[index] >= existing_maximum[index]
        for index in range(3)
    ):
        raise ValueError("existing support bounds are empty or reversed")
    minimum = [
        min(
            float(existing_minimum[0]),
            float(combined_com[0]) - TARGET_COM_SUPPORT_MARGIN_M,
        ),
        min(
            float(existing_minimum[1]),
            float(combined_com[1]) - TARGET_COM_SUPPORT_MARGIN_M,
        ),
        float(support_plane_z_m),
    ]
    maximum = [
        max(
            float(existing_maximum[0]),
            float(combined_com[0]) + TARGET_COM_SUPPORT_MARGIN_M,
        ),
        max(
            float(existing_maximum[1]),
            float(combined_com[1]) + TARGET_COM_SUPPORT_MARGIN_M,
        ),
        float(support_plane_z_m) + SUPPORT_PAD_HEIGHT_M,
    ]
    margins = _support_margins(minimum, maximum, combined_com)
    if min(margins.values()) < MINIMUM_COM_SUPPORT_MARGIN_M:
        raise RuntimeError(
            "planned support does not retain the required COM projection margin"
        )
    return minimum, maximum


def _world_bounds(
    stage: Any,
    prim_path: str,
    *,
    usd: Any,
    usd_geom: Any,
) -> tuple[list[float], list[float]]:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise ValueError(f"missing prim for world-bound measurement: {prim_path}")
    cache = usd_geom.BBoxCache(
        usd.TimeCode.Default(),
        [usd_geom.Tokens.default_],
    )
    bound = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    minimum = _vector(bound.GetMin())
    maximum = _vector(bound.GetMax())
    if any(minimum[index] >= maximum[index] for index in range(3)):
        raise ValueError(f"empty world bound for {prim_path}")
    return minimum, maximum


def _near_plane_visual_footprint(
    stage: Any,
    *,
    support_plane_z_m: float,
    usd: Any,
    usd_geom: Any,
) -> tuple[list[float], list[float], list[dict[str, Any]]]:
    """Measure the composed world footprint of visual meshes touching the base."""
    visual_root = stage.GetPrimAtPath(BASE_VISUAL_ROOT)
    if not visual_root.IsValid():
        raise ValueError(f"missing base visual root: {BASE_VISUAL_ROOT}")
    records: list[dict[str, Any]] = []
    for prim in usd.PrimRange(visual_root):
        if prim.GetTypeName() != "Mesh":
            continue
        minimum, maximum = _world_bounds(
            stage,
            str(prim.GetPath()),
            usd=usd,
            usd_geom=usd_geom,
        )
        if minimum[2] <= support_plane_z_m + 0.002:
            records.append(
                {
                    "prim_path": str(prim.GetPath()),
                    "world_bounds_m": {"min": minimum, "max": maximum},
                }
            )
    if len(records) < 3:
        raise ValueError(
            "expected at least three composed visual contact meshes at the base"
        )
    minimum = [
        min(record["world_bounds_m"]["min"][axis] for record in records)
        for axis in range(3)
    ]
    maximum = [
        max(record["world_bounds_m"]["max"][axis] for record in records)
        for axis in range(3)
    ]
    return minimum, maximum, records


def _mass_rules(
    physics_profile: Mapping[str, Any],
) -> list[tuple[str, float, list[float]]]:
    rules = physics_profile.get("scope_rules")
    if not isinstance(rules, list) or len(rules) != 1:
        raise ValueError("physics profile must contain one centrifuge scope rule")
    scope_rule = rules[0]
    if (
        not isinstance(scope_rule, dict)
        or scope_rule.get("scope_path") != ROOT
        or not isinstance(scope_rule.get("body_rules"), list)
    ):
        raise ValueError("physics profile does not bind the centrifuge scope")
    result: list[tuple[str, float, list[float]]] = []
    for index, body_rule in enumerate(scope_rule["body_rules"]):
        if not isinstance(body_rule, dict):
            raise ValueError(f"physics body rule {index} must be an object")
        relative_path = body_rule.get("relative_path")
        properties = body_rule.get("mass_properties")
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or not isinstance(properties, dict)
        ):
            raise ValueError(f"physics body rule {index} is incomplete")
        mass = properties.get("mass_kg")
        center = properties.get("center_of_mass_body_local")
        if (
            isinstance(mass, bool)
            or not isinstance(mass, (int, float))
            or float(mass) <= 0.0
            or not isinstance(center, list)
            or len(center) != 3
            or any(
                isinstance(component, bool)
                or not isinstance(component, (int, float))
                for component in center
            )
        ):
            raise ValueError(f"physics body rule {index} has invalid mass properties")
        result.append(
            (
                f"{ROOT}/{relative_path}",
                float(mass),
                [float(component) for component in center],
            )
        )
    if not result:
        raise ValueError("physics profile has no mass-bearing bodies")
    return result


def _combined_com_world(
    stage: Any,
    physics_profile: Mapping[str, Any],
    *,
    usd: Any,
    usd_geom: Any,
    gf: Any,
) -> tuple[list[float], list[dict[str, Any]]]:
    cache = usd_geom.XformCache(usd.TimeCode.Default())
    total_mass = 0.0
    weighted = gf.Vec3d(0.0)
    records: list[dict[str, Any]] = []
    for prim_path, mass, center_local in _mass_rules(physics_profile):
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            raise ValueError(f"mass profile body is missing from facade: {prim_path}")
        center_world = cache.GetLocalToWorldTransform(prim).Transform(
            gf.Vec3d(*center_local)
        )
        total_mass += mass
        weighted += center_world * mass
        records.append(
            {
                "body_prim": prim_path,
                "mass_kg": mass,
                "center_of_mass_body_local_m": center_local,
                "center_of_mass_world_m": _vector(center_world),
            }
        )
    if total_mass <= 0.0:
        raise ValueError("combined centrifuge mass must be positive")
    return _vector(weighted / total_mass), records


def _world_aligned_cube_parent_local_ops(
    parent_world: Any,
    *,
    world_minimum: list[float],
    world_maximum: list[float],
    gf: Any,
) -> tuple[list[float], list[float]]:
    """Map an axis-aligned world cube to a signed-axis-permutation parent."""
    dimensions = [
        float(world_maximum[index] - world_minimum[index])
        for index in range(3)
    ]
    if any(value <= 0.0 for value in dimensions):
        raise ValueError("world cube bounds are empty or reversed")
    center = gf.Vec3d(
        *[
            (float(world_minimum[index]) + float(world_maximum[index])) / 2.0
            for index in range(3)
        ]
    )
    translation = parent_world.GetInverse().Transform(center)
    local_scale = [0.0, 0.0, 0.0]
    used_world_axes: set[int] = set()
    for local_axis in range(3):
        basis = [0.0, 0.0, 0.0]
        basis[local_axis] = 1.0
        transformed = parent_world.TransformDir(gf.Vec3d(*basis))
        components = [abs(float(transformed[index])) for index in range(3)]
        length = sum(component * component for component in components) ** 0.5
        if length <= 1.0e-12:
            raise ValueError("support parent transform contains a zero axis")
        world_axis = max(range(3), key=components.__getitem__)
        alignment = components[world_axis] / length
        if alignment < 1.0 - 1.0e-6 or world_axis in used_world_axes:
            raise ValueError(
                "support parent must be a signed world-axis permutation"
            )
        used_world_axes.add(world_axis)
        # The authored Cube uses size=1, so scale is the full local dimension.
        local_scale[local_axis] = dimensions[world_axis] / length
    return _vector(translation), local_scale


def _xform_snapshot(stage: Any, *, usd: Any, usd_geom: Any) -> dict[str, Any]:
    cache = usd_geom.XformCache(usd.TimeCode.Default())
    return {
        str(prim.GetPath()): _matrix(cache.GetLocalToWorldTransform(prim))
        for prim in stage.Traverse()
        if prim.IsA(usd_geom.Xformable)
    }


def _drive_snapshot(stage: Any) -> dict[str, Any]:
    return {
        str(attribute.GetPath()): attribute.Get()
        for prim in stage.Traverse()
        for attribute in prim.GetAttributes()
        if attribute.GetName().startswith("drive:")
        and attribute.HasAuthoredValueOpinion()
    }


def _maximum_matrix_error(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> float:
    if not set(before).issubset(after):
        raise RuntimeError("generated facade removed existing xformable prims")
    return max(
        (
            abs(
                float(before[path][row][column])
                - float(after[path][row][column])
            )
            for path in before
            for row in range(4)
            for column in range(4)
        ),
        default=0.0,
    )


def _verify_identity_root(stage: Any, *, usd: Any, usd_geom: Any) -> None:
    prim = stage.GetPrimAtPath(ROOT)
    if not prim.IsValid():
        raise ValueError(f"facade is missing entry prim {ROOT}")
    matrix = usd_geom.XformCache(
        usd.TimeCode.Default()
    ).GetLocalToWorldTransform(prim)
    for row in range(4):
        for column in range(4):
            expected = 1.0 if row == column else 0.0
            if abs(float(matrix[row][column]) - expected) > IDENTITY_TOLERANCE:
                raise ValueError(
                    f"{ROOT} is not identity at [{row}][{column}]"
                )


def _build(args: argparse.Namespace) -> dict[str, Any]:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    r8_facade = args.r8_facade.resolve()
    r8_provenance_path = args.r8_provenance.resolve()
    r8_physics_path = args.r8_physics.resolve()
    out_root = args.out_root.resolve()
    output_facade = out_root / "facade" / "facade.usda"
    output_provenance = out_root / "facade" / "facade_provenance.json"
    output_support_measurement = (
        out_root / "facade" / "benchtop_support_measurement.json"
    )
    output_physics = out_root / "centrifuge.physics.json"
    for path in (
        output_facade,
        output_provenance,
        output_support_measurement,
        output_physics,
    ):
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"refusing to replace generated artifact: {path}")

    r8_provenance = _json_object(r8_provenance_path)
    r8_facade_sha = _sha256_file(r8_facade)
    if r8_provenance.get("facade_sha256") != r8_facade_sha:
        raise ValueError("r8 facade provenance SHA-256 does not match the facade")
    r8_physics = _json_object(r8_physics_path)
    source_binding = r8_physics.get("source_binding")
    if (
        not isinstance(source_binding, dict)
        or source_binding.get("sha256") != r8_facade_sha
    ):
        raise ValueError("r8 physics profile is not bound to the r8 facade")

    r8_stage = Usd.Stage.Open(str(r8_facade))
    if r8_stage is None:
        raise RuntimeError(f"could not open r8 facade: {r8_facade}")
    _verify_identity_root(r8_stage, usd=Usd, usd_geom=UsdGeom)
    xforms_before = _xform_snapshot(r8_stage, usd=Usd, usd_geom=UsdGeom)
    drives_before = _drive_snapshot(r8_stage)
    housing_minimum, housing_maximum = _world_bounds(
        r8_stage,
        HOUSING_COLLIDER,
        usd=Usd,
        usd_geom=UsdGeom,
    )
    scope_minimum, _ = _world_bounds(
        r8_stage,
        ROOT,
        usd=Usd,
        usd_geom=UsdGeom,
    )
    support_plane_z = float(scope_minimum[2])
    if abs(support_plane_z) <= 1.0e-4:
        support_plane_z = 0.0
    combined_com, mass_records = _combined_com_world(
        r8_stage,
        r8_physics,
        usd=Usd,
        usd_geom=UsdGeom,
        gf=Gf,
    )
    contact_minimum, contact_maximum, contact_meshes = (
        _near_plane_visual_footprint(
            r8_stage,
            support_plane_z_m=support_plane_z,
            usd=Usd,
            usd_geom=UsdGeom,
        )
    )
    support_minimum, support_maximum = _plan_support_bounds(
        contact_minimum,
        contact_maximum,
        combined_com,
        support_plane_z_m=support_plane_z,
    )
    base_body = r8_stage.GetPrimAtPath(BASE_BODY)
    if not base_body.IsValid():
        raise ValueError(f"r8 facade is missing base body {BASE_BODY}")
    parent_world = UsdGeom.XformCache(
        Usd.TimeCode.Default()
    ).GetLocalToWorldTransform(base_body)
    local_translation, local_scale = _world_aligned_cube_parent_local_ops(
        parent_world,
        world_minimum=support_minimum,
        world_maximum=support_maximum,
        gf=Gf,
    )

    output_facade.parent.mkdir(parents=True, exist_ok=True)
    layer = Sdf.Layer.CreateNew(str(output_facade))
    layer.subLayerPaths.append(os.path.relpath(r8_facade, output_facade.parent))
    stage = Usd.Stage.Open(layer.identifier)
    if stage is None:
        raise RuntimeError(f"could not create r9 facade: {output_facade}")
    stage.SetEditTarget(layer)
    stage.SetDefaultPrim(stage.OverridePrim("/World"))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.GetStageUpAxis(r8_stage))
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.GetStageMetersPerUnit(r8_stage))
    stage.SetTimeCodesPerSecond(r8_stage.GetTimeCodesPerSecond())
    stage.SetFramesPerSecond(r8_stage.GetFramesPerSecond())

    support = UsdGeom.Cube.Define(stage, BENCHTOP_SUPPORT_COLLIDER)
    support.GetSizeAttr().Set(1.0)
    support.GetVisibilityAttr().Set(UsdGeom.Tokens.invisible)
    xformable = UsdGeom.Xformable(support.GetPrim())
    xformable.ClearXformOpOrder()
    xformable.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble).Set(
        Gf.Vec3d(*local_translation)
    )
    xformable.AddScaleOp(UsdGeom.XformOp.PrecisionDouble).Set(
        Gf.Vec3d(*local_scale)
    )
    collision = UsdPhysics.CollisionAPI.Apply(support.GetPrim())
    collision.GetCollisionEnabledAttr().Set(True)
    stage.GetRootLayer().Save()

    verify_stage = Usd.Stage.Open(str(output_facade))
    if verify_stage is None:
        raise RuntimeError(f"could not reopen r9 facade: {output_facade}")
    _verify_identity_root(verify_stage, usd=Usd, usd_geom=UsdGeom)
    actual_minimum, actual_maximum = _world_bounds(
        verify_stage,
        BENCHTOP_SUPPORT_COLLIDER,
        usd=Usd,
        usd_geom=UsdGeom,
    )
    bound_error = max(
        abs(actual - expected)
        for actual_values, expected_values in (
            (actual_minimum, support_minimum),
            (actual_maximum, support_maximum),
        )
        for actual, expected in zip(actual_values, expected_values)
    )
    if bound_error > 1.0e-6:
        raise RuntimeError(
            f"r9 benchtop support world-bound error is {bound_error} m"
        )
    margins = _support_margins(
        actual_minimum,
        actual_maximum,
        combined_com,
    )
    if min(margins.values()) < MINIMUM_COM_SUPPORT_MARGIN_M:
        raise RuntimeError("r9 support does not contain the COM projection")
    xform_error = _maximum_matrix_error(
        xforms_before,
        _xform_snapshot(verify_stage, usd=Usd, usd_geom=UsdGeom),
    )
    if xform_error > 1.0e-9:
        raise RuntimeError(
            f"r9 changed an existing world transform by {xform_error}"
        )
    if _drive_snapshot(verify_stage) != drives_before:
        raise RuntimeError("r9 changed an existing joint drive attribute")

    facade_sha = _sha256_file(output_facade)
    rebound_physics = _rebind_physics_profile(
        r8_physics,
        source_sha256=facade_sha,
    )
    if rebound_physics.get("scope_rules") != r8_physics.get("scope_rules"):
        raise RuntimeError("r9 physics rebind changed mass or inertia rules")
    _write_json(output_physics, rebound_physics)

    measurement = {
        "schema_version": "aan.benchtop_support_measurement.v1",
        "status": "pass",
        "support_collider_prim": BENCHTOP_SUPPORT_COLLIDER,
        "support_collider_type": "UsdGeomCube",
        "cube_size": 1.0,
        "visibility": "invisible",
        "world_bounds_m": {
            "min": actual_minimum,
            "max": actual_maximum,
        },
        "parent_local_ops": {
            "translation_m": local_translation,
            "scale_full_dimensions": local_scale,
        },
        "combined_center_of_mass_world_m": combined_com,
        "combined_mass_records": mass_records,
        "com_projection_margins": margins,
        "minimum_required_margin_m": MINIMUM_COM_SUPPORT_MARGIN_M,
        "target_extension_margin_m": TARGET_COM_SUPPORT_MARGIN_M,
        "existing_housing_world_bounds_m": {
            "min": housing_minimum,
            "max": housing_maximum,
        },
        "composed_visual_contact_footprint_m": {
            "min": contact_minimum,
            "max": contact_maximum,
            "mesh_count": len(contact_meshes),
            "meshes": contact_meshes,
        },
        "protected_state_verification": {
            "entry_identity": "pass",
            "maximum_existing_world_transform_error": xform_error,
            "joint_drive_attributes": "unchanged",
            "physics_scope_rules": "unchanged",
        },
        "claim_boundary": (
            "This is a producer-side benchtop support collider repair. It does "
            "not change visual geometry, existing world transforms, joint "
            "drives, mass, center of mass, inertia, or raw source USD."
        ),
    }
    _write_json(output_support_measurement, measurement)
    provenance = deepcopy(r8_provenance)
    provenance.update(
        {
            "facade_revision": "identity_root_benchtop_support_r9",
            "facade_sha256": facade_sha,
            "predecessor_facade": {
                "path": str(r8_facade),
                "sha256": r8_facade_sha,
            },
            "benchtop_support": measurement,
        }
    )
    _write_json(output_provenance, provenance)
    return {
        "status": "pass",
        "facade": str(output_facade),
        "facade_sha256": facade_sha,
        "facade_provenance": str(output_provenance),
        "benchtop_support_measurement": str(output_support_measurement),
        "physics_profile": str(output_physics),
        "minimum_com_support_margin_m": min(margins.values()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the identity-root r9 centrifuge facade with a measured "
            "benchtop support collider."
        )
    )
    parser.add_argument(
        "--r8-facade",
        type=Path,
        default=DEFAULT_R8_ROOT / "facade" / "facade.usda",
    )
    parser.add_argument(
        "--r8-provenance",
        type=Path,
        default=DEFAULT_R8_ROOT / "facade" / "facade_provenance.json",
    )
    parser.add_argument(
        "--r8-physics",
        type=Path,
        default=DEFAULT_R8_ROOT / "centrifuge.physics.json",
    )
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = _build(args)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": f"{type(exc).__name__}: {exc}",
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
