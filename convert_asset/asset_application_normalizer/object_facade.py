"""Source-bound canonical facade for one uniformly scaled task object.

The immutable producer USD is referenced below an identity entry prim.  Axis
conversion, uniform scale, and support-plane alignment live only on the facade
visual child, so consumers never need asset-specific scale or pose patches.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


PROFILE_SCHEMA_VERSION = "aan.object_facade_profile.v1"


class ObjectFacadeProfileError(ValueError):
    """The object facade profile cannot be bound to the immutable source."""


@dataclass(frozen=True)
class ObjectFacadeResult:
    facade_path: Path
    provenance_path: Path
    entry_prim_path: str


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObjectFacadeProfileError(f"{field} must be an object")
    return value


def _vector(value: object, length: int, field: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != length
        or not all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and math.isfinite(float(item))
            for item in value
        )
    ):
        raise ObjectFacadeProfileError(f"{field} must contain {length} finite numbers")
    return [float(item) for item in value]


def _read_profile(profile_path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw_bytes = profile_path.read_bytes()
        value = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ObjectFacadeProfileError(
            f"cannot read object facade profile: {exc}"
        ) from exc
    profile = _mapping(value, "profile")
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ObjectFacadeProfileError(
            f"unsupported object facade profile: {profile.get('schema_version')!r}"
        )
    return profile, sha256(raw_bytes).hexdigest()


def _stage_bounds(stage: Any, prim: Any) -> dict[str, list[float]]:
    from pxr import Usd, UsdGeom  # type: ignore

    bounds = (
        UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
        )
        .ComputeWorldBound(prim)
        .ComputeAlignedRange()
    )
    lower = [float(value) for value in bounds.GetMin()]
    upper = [float(value) for value in bounds.GetMax()]
    if not all(math.isfinite(value) for value in [*lower, *upper]):
        raise ObjectFacadeProfileError("object bounds are empty or non-finite")
    return {
        "min": lower,
        "max": upper,
        "size": [upper[index] - lower[index] for index in range(3)],
    }


def build_object_facade(
    source_usd: Path,
    out_dir: Path,
    profile_path: Path,
) -> ObjectFacadeResult:
    from pxr import Gf, Sdf, Usd, UsdGeom  # type: ignore

    source_usd = source_usd.resolve()
    profile_path = profile_path.resolve()
    if not source_usd.is_file():
        raise ObjectFacadeProfileError(f"source USD does not exist: {source_usd}")
    profile, profile_sha = _read_profile(profile_path)
    source = _mapping(profile.get("source"), "source")
    source_sha = _sha256(source_usd)
    if source.get("sha256") != source_sha:
        raise ObjectFacadeProfileError(
            "source SHA-256 does not match the object facade profile"
        )

    source_stage = Usd.Stage.Open(str(source_usd))
    if source_stage is None:
        raise ObjectFacadeProfileError(f"cannot open source USD: {source_usd}")
    source_prim_path = str(source.get("prim_path", ""))
    source_prim = source_stage.GetPrimAtPath(source_prim_path)
    if not source_prim:
        raise ObjectFacadeProfileError(
            f"source prim does not exist: {source_prim_path}"
        )
    expected_axis = str(source.get("expected_up_axis", ""))
    observed_axis = str(UsdGeom.GetStageUpAxis(source_stage))
    if expected_axis != observed_axis:
        raise ObjectFacadeProfileError(
            f"source upAxis mismatch: expected {expected_axis}, got {observed_axis}"
        )
    expected_meters = float(source.get("expected_meters_per_unit", 0.0))
    observed_meters = float(UsdGeom.GetStageMetersPerUnit(source_stage))
    if not math.isclose(expected_meters, observed_meters, rel_tol=0.0, abs_tol=1e-12):
        raise ObjectFacadeProfileError(
            "source metersPerUnit does not match the object facade profile"
        )
    source_bounds = _stage_bounds(source_stage, source_prim)

    entry = _mapping(profile.get("entry"), "entry")
    entry_path = str(entry.get("prim_path", ""))
    if not entry_path.startswith("/World/") or entry_path.count("/") != 2:
        raise ObjectFacadeProfileError(
            "entry.prim_path must be a direct child of /World"
        )
    if entry.get("require_identity") is not True:
        raise ObjectFacadeProfileError("entry.require_identity must be true")
    visual_name = str(entry.get("visual_child_name", ""))
    if (
        not visual_name
        or "/" in visual_name
        or not Sdf.Path.IsValidIdentifier(visual_name)
    ):
        raise ObjectFacadeProfileError(
            "entry.visual_child_name must be a USD identifier"
        )

    normalization = _mapping(profile.get("normalization"), "normalization")
    rotation = _vector(
        normalization.get("rotation_wxyz"), 4, "normalization.rotation_wxyz"
    )
    norm = math.sqrt(sum(component * component for component in rotation))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ObjectFacadeProfileError(
            "normalization.rotation_wxyz must be unit length"
        )
    scale = float(normalization.get("uniform_scale", 0.0))
    if not math.isfinite(scale) or scale <= 0:
        raise ObjectFacadeProfileError("normalization.uniform_scale must be positive")
    support_z = float(normalization.get("support_plane_z_m", 0.0))
    if not math.isfinite(support_z):
        raise ObjectFacadeProfileError("normalization.support_plane_z_m must be finite")
    if normalization.get("target_up_axis") != "Z":
        raise ObjectFacadeProfileError("normalization.target_up_axis must be Z")
    if not math.isclose(
        float(normalization.get("target_meters_per_unit", 0.0)),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ObjectFacadeProfileError(
            "normalization.target_meters_per_unit must be 1.0"
        )

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
    visual_path = f"{entry_path}/{visual_name}"
    visual = UsdGeom.Xform.Define(stage, visual_path)
    source_reference_path = f"{visual_path}/Source"
    source_reference = UsdGeom.Xform.Define(stage, source_reference_path)
    source_reference.GetPrim().GetReferences().AddReference(
        str(source_usd), source_prim_path
    )
    xform = UsdGeom.Xformable(visual)
    translate_op = xform.AddTranslateOp()
    orient_op = xform.AddOrientOp(UsdGeom.XformOp.PrecisionDouble)
    scale_op = xform.AddScaleOp()
    translate_op.Set(Gf.Vec3d(0.0, 0.0, 0.0))
    orient_op.Set(
        Gf.Quatd(rotation[0], Gf.Vec3d(rotation[1], rotation[2], rotation[3]))
    )
    scale_op.Set(Gf.Vec3d(scale, scale, scale))
    stage.GetRootLayer().Save()

    normalized_bounds = _stage_bounds(stage, entry_prim)
    center_x = (normalized_bounds["min"][0] + normalized_bounds["max"][0]) / 2.0
    center_y = (normalized_bounds["min"][1] + normalized_bounds["max"][1]) / 2.0
    translate_op.Set(
        Gf.Vec3d(
            -center_x,
            -center_y,
            support_z - normalized_bounds["min"][2],
        )
    )
    stage.GetRootLayer().Save()
    final_bounds = _stage_bounds(stage, entry_prim)
    if not math.isclose(final_bounds["min"][2], support_z, abs_tol=1e-6):
        raise ObjectFacadeProfileError("facade support-plane alignment failed")
    if UsdGeom.Xformable(entry_prim).GetOrderedXformOps():
        raise ObjectFacadeProfileError("facade entry prim is not identity")

    provenance_path = out_dir / "facade_provenance.json"
    provenance = {
        "schema_version": "aan.object_facade_provenance.v1",
        "source": {
            "path": str(source_usd),
            "sha256": source_sha,
            "prim_path": source_prim_path,
            "up_axis": observed_axis,
            "meters_per_unit": observed_meters,
            "bounds": source_bounds,
            **(
                {"archive_sha256": source["archive_sha256"]}
                if isinstance(source.get("archive_sha256"), str)
                else {}
            ),
        },
        "profile": {
            "path": str(profile_path),
            "sha256": profile_sha,
            "schema_version": PROFILE_SCHEMA_VERSION,
        },
        "entry": {
            "prim_path": entry_path,
            "visual_prim_path": visual_path,
            "source_reference_prim_path": source_reference_path,
            "identity_transform": True,
        },
        "normalization": {
            "rotation_wxyz": rotation,
            "uniform_scale": scale,
            "support_plane_z_m": support_z,
            "centered_on_entry_xy": True,
            "target_up_axis": "Z",
            "target_meters_per_unit": 1.0,
            "bounds_m": final_bounds,
        },
        "geometry_claim": _mapping(profile.get("geometry_claim"), "geometry_claim"),
        "facade": {
            "path": str(facade_path),
            "sha256": _sha256(facade_path),
        },
        "source_mutated": False,
    }
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return ObjectFacadeResult(
        facade_path=facade_path,
        provenance_path=provenance_path,
        entry_prim_path=entry_path,
    )
