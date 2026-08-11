"""Source-bound facade that remaps complete source components into measured bounds.

This is intended for compound static assets such as worktables whose producer
hierarchy separates the load-bearing surface from the visual body.  Consumers
receive an identity entry prim; every component transform is contained below it.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


PROFILE_SCHEMA_VERSION = "aan.component_facade_profile.v1"


class ComponentFacadeProfileError(ValueError):
    """The measured component facade cannot be bound to its source."""


@dataclass(frozen=True)
class ComponentFacadeResult:
    facade_path: Path
    provenance_path: Path
    entry_prim_path: str


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ComponentFacadeProfileError(f"{field} must be an object")
    return value


def _vec3(value: object, field: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or not all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(float(item))
            for item in value
        )
    ):
        raise ComponentFacadeProfileError(f"{field} must contain three finite numbers")
    return [float(item) for item in value]


def _bounds(stage: Any, prim: Any) -> dict[str, list[float]]:
    from pxr import Usd, UsdGeom  # type: ignore

    value = (
        UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        )
        .ComputeWorldBound(prim)
        .ComputeAlignedRange()
    )
    lower = [float(item) for item in value.GetMin()]
    upper = [float(item) for item in value.GetMax()]
    size = [upper[index] - lower[index] for index in range(3)]
    if not all(math.isfinite(item) for item in [*lower, *upper]) or any(
        item <= 0 for item in size
    ):
        raise ComponentFacadeProfileError("component bounds are empty or non-finite")
    return {"min": lower, "max": upper, "size": size}


def build_component_facade(
    source_usd: Path,
    out_dir: Path,
    profile_path: Path,
) -> ComponentFacadeResult:
    from pxr import Gf, Sdf, Usd, UsdGeom  # type: ignore

    source_usd = source_usd.resolve()
    profile_path = profile_path.resolve()
    try:
        profile_bytes = profile_path.read_bytes()
        profile = _mapping(json.loads(profile_bytes), "profile")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComponentFacadeProfileError(f"cannot read component facade profile: {exc}") from exc
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ComponentFacadeProfileError(
            f"unsupported component facade profile: {profile.get('schema_version')!r}"
        )
    source = _mapping(profile.get("source"), "source")
    if source.get("sha256") != _sha256(source_usd):
        raise ComponentFacadeProfileError(
            "source SHA-256 does not match the component facade profile"
        )
    source_stage = Usd.Stage.Open(str(source_usd))
    if source_stage is None:
        raise ComponentFacadeProfileError(f"cannot open source USD: {source_usd}")
    observed_axis = str(UsdGeom.GetStageUpAxis(source_stage))
    observed_meters = float(UsdGeom.GetStageMetersPerUnit(source_stage))
    if source.get("expected_up_axis") != observed_axis:
        raise ComponentFacadeProfileError("source upAxis does not match the profile")
    if not math.isclose(
        float(source.get("expected_meters_per_unit", 0.0)),
        observed_meters,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ComponentFacadeProfileError("source metersPerUnit does not match the profile")

    entry = _mapping(profile.get("entry"), "entry")
    entry_path = str(entry.get("prim_path", ""))
    if not entry_path.startswith("/World/") or entry_path.count("/") != 2:
        raise ComponentFacadeProfileError("entry.prim_path must be a direct child of /World")
    if entry.get("require_identity") is not True:
        raise ComponentFacadeProfileError("entry.require_identity must be true")
    components = profile.get("components")
    if not isinstance(components, list) or not components:
        raise ComponentFacadeProfileError("components must be a non-empty list")

    out_dir.mkdir(parents=True, exist_ok=True)
    facade_path = out_dir / "facade.usda"
    if facade_path.exists():
        facade_path.unlink()
    stage = Usd.Stage.CreateNew(str(facade_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    entry_prim = UsdGeom.Xform.Define(stage, entry_path).GetPrim()
    material_scope_path = source.get("material_scope_prim_path")
    if material_scope_path is not None:
        material_scope_path = str(material_scope_path)
        if not source_stage.GetPrimAtPath(material_scope_path):
            raise ComponentFacadeProfileError(
                f"source material scope does not exist: {material_scope_path}"
            )
        material_mount = stage.OverridePrim(material_scope_path)
        material_mount.GetReferences().AddReference(str(source_usd), material_scope_path)
    provenance_components: list[dict[str, Any]] = []
    binding_retarget_count = 0
    seen_names: set[str] = set()
    for index, raw_component in enumerate(components):
        component = _mapping(raw_component, f"components[{index}]")
        name = str(component.get("name", ""))
        if not Sdf.Path.IsValidIdentifier(name) or name in seen_names:
            raise ComponentFacadeProfileError("component names must be unique USD identifiers")
        seen_names.add(name)
        source_path = str(component.get("source_prim_path", ""))
        source_prim = source_stage.GetPrimAtPath(source_path)
        if not source_prim:
            raise ComponentFacadeProfileError(f"source component does not exist: {source_path}")
        target = _mapping(component.get("target_bounds_m"), f"components[{index}].target_bounds_m")
        target_min = _vec3(target.get("min"), f"components[{index}].target_bounds_m.min")
        target_max = _vec3(target.get("max"), f"components[{index}].target_bounds_m.max")
        target_size = [target_max[axis] - target_min[axis] for axis in range(3)]
        if any(value <= 0 for value in target_size):
            raise ComponentFacadeProfileError("component target bounds must be increasing")

        component_path = f"{entry_path}/{name}"
        mounted = UsdGeom.Xform.Define(stage, component_path)
        source_mount = stage.OverridePrim(f"{component_path}/Source")
        source_mount.GetReferences().AddReference(str(source_usd), source_path)
        if material_scope_path is not None:
            for source_descendant in Usd.PrimRange(source_prim):
                binding = source_descendant.GetRelationship("material:binding")
                if not binding:
                    continue
                targets = [
                    target
                    for target in binding.GetTargets()
                    if target.pathString == material_scope_path
                    or target.pathString.startswith(material_scope_path + "/")
                ]
                if not targets:
                    continue
                suffix = source_descendant.GetPath().pathString[len(source_path) :]
                consumer = stage.OverridePrim(f"{component_path}/Source{suffix}")
                consumer.CreateRelationship("material:binding", custom=False).SetTargets(targets)
                binding_retarget_count += 1
        xform = UsdGeom.Xformable(mounted)
        translate_op = xform.AddTranslateOp()
        scale_op = xform.AddScaleOp()
        translate_op.Set(Gf.Vec3d(0.0, 0.0, 0.0))
        scale_op.Set(Gf.Vec3f(1.0, 1.0, 1.0))
        stage.GetRootLayer().Save()
        initial = _bounds(stage, mounted.GetPrim())
        scale = [target_size[axis] / initial["size"][axis] for axis in range(3)]
        scale_op.Set(Gf.Vec3f(*scale))
        stage.GetRootLayer().Save()
        scaled = _bounds(stage, mounted.GetPrim())
        translation = [target_min[axis] - scaled["min"][axis] for axis in range(3)]
        translate_op.Set(Gf.Vec3d(*translation))
        stage.GetRootLayer().Save()
        final = _bounds(stage, mounted.GetPrim())
        for axis in range(3):
            if not math.isclose(final["min"][axis], target_min[axis], abs_tol=1e-6) or not math.isclose(
                final["max"][axis], target_max[axis], abs_tol=1e-6
            ):
                raise ComponentFacadeProfileError(f"component target alignment failed: {name}")
        provenance_components.append(
            {
                "name": name,
                "source_prim_path": source_path,
                "source_bounds": initial,
                "target_bounds_m": final,
                "scale_xyz": scale,
                "translate_xyz": translation,
            }
        )

    stage.GetRootLayer().Save()
    if UsdGeom.Xformable(entry_prim).GetOrderedXformOps():
        raise ComponentFacadeProfileError("facade entry prim is not identity")
    final_bounds = _bounds(stage, entry_prim)
    provenance_path = out_dir / "facade_provenance.json"
    provenance_path.write_text(
        json.dumps(
            {
                "schema_version": "aan.component_facade_provenance.v1",
                "source": {
                    "path": str(source_usd),
                    "sha256": _sha256(source_usd),
                    "up_axis": observed_axis,
                    "meters_per_unit": observed_meters,
                },
                "profile": {
                    "path": str(profile_path),
                    "sha256": sha256(profile_bytes).hexdigest(),
                    "schema_version": PROFILE_SCHEMA_VERSION,
                },
                "entry": {"prim_path": entry_path, "identity_transform": True},
                "components": provenance_components,
                "material_scope_prim_path": material_scope_path,
                "material_binding_retarget_count": binding_retarget_count,
                "final_bounds_m": final_bounds,
                "geometry_claim": _mapping(profile.get("geometry_claim"), "geometry_claim"),
                "source_mutated": False,
                "facade": {"path": str(facade_path), "sha256": _sha256(facade_path)},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return ComponentFacadeResult(facade_path, provenance_path, entry_path)
