"""Batch source-bound workspace-zone profiling for one complete room."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

import yaml

from .audit import ClearanceSpec, audit_clearance
from .profiles import (
    CoordinateMapping,
    ProducerInfo,
    ZoneManifest,
    ZoneProfile,
    write_yaml,
)


REQUEST_SCHEMA = "aan.workspace_zone_request.v1"
_ZONE_ID = re.compile(r"^[a-z0-9](?:[a-z0-9_]*[a-z0-9])?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ZoneBatchResult:
    manifest_path: Path
    profiled_count: int
    not_applicable_count: int


def build_zone_profiles(
    request_path: str | Path,
    out_dir: str | Path,
    *,
    git_commit: str,
    revision: str,
) -> ZoneBatchResult:
    """Audit every requested zone and write v0.2 profiles plus one manifest."""

    request_file = Path(request_path).resolve()
    request = _load_request(request_file)
    if request.get("schema_version") != REQUEST_SCHEMA:
        raise ValueError("workspace zone request schema is unsupported")
    source_usd = Path(_string(request, "source_usd")).resolve()
    if not source_usd.is_file():
        raise ValueError(f"workspace zone source USD is unavailable: {source_usd}")
    profile_source_sha256 = _sha256_value(request, "source_sha256")
    geometry_source_sha256 = (
        _sha256_value(request, "geometry_source_sha256")
        if "geometry_source_sha256" in request
        else profile_source_sha256
    )
    if _file_sha256(source_usd) != geometry_source_sha256:
        raise ValueError("workspace zone source USD SHA-256 does not match request")
    background_asset_id = _string(request, "background_asset_id")
    scope = _prim_path(_string(request, "scope"))
    units_per_meter = _positive_number(request.get("units_per_meter"), "units_per_meter")
    floor_z = _finite_number(request.get("floor_z", 0.0), "floor_z")
    clearance_footprint_m = _positive_number2(
        request.get("clearance_footprint_m", [2.345, 2.645]),
        "clearance_footprint_m",
    )
    shell_prefixes = tuple(
        _prim_path(value)
        for value in _string_list(request.get("shell_prefixes", []), "shell_prefixes")
    )
    package_manifest = str(request.get("package_manifest", ""))
    facade_provenance = str(request.get("facade_provenance", ""))
    support_closure: dict[str, list[str]] | None = None
    if request.get("support_audit_report"):
        support_report_path = Path(str(request["support_audit_report"]))
        if not support_report_path.is_absolute():
            support_report_path = (request_file.parent / support_report_path).resolve()
        support_report = _load_request(support_report_path)
        if support_report.get("overall_status") != "pass":
            raise ValueError("workspace zone support audit report is not passing")
        if support_report.get("source_sha256") != profile_source_sha256:
            raise ValueError("workspace zone support audit source SHA-256 does not match request")
        raw_closure = _mapping(support_report.get("support_closure"), "support_closure")
        support_closure = {
            _prim_path_allow_room(str(key)): [
                _prim_path_allow_room(value)
                for value in _string_list(values, f"support_closure.{key}")
            ]
            for key, values in raw_closure.items()
        }
    raw_zones = _mapping(request.get("zones"), "zones")
    if not raw_zones:
        raise ValueError("workspace zone request must contain at least one zone")

    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(source_usd))
    if stage is None:
        raise ValueError(f"cannot open workspace zone source stage: {source_usd}")
    if not stage.GetPrimAtPath(scope):
        raise ValueError(f"workspace zone scope is absent: {scope}")

    output = Path(out_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    producer = ProducerInfo(git_commit=git_commit, revision=revision)
    coordinate_mapping = CoordinateMapping(
        units_per_meter=units_per_meter,
        derivation=str(
            request.get(
                "mapping_derivation",
                "source USD declares metric units; no inferred scale",
            )
        ),
    )
    manifest_zones: dict[str, dict[str, str]] = {}
    profiled_count = 0
    not_applicable_count = 0

    for zone_id, raw_zone in sorted(raw_zones.items()):
        if not isinstance(zone_id, str) or _ZONE_ID.fullmatch(zone_id) is None:
            raise ValueError(f"workspace zone id is invalid: {zone_id}")
        zone = _mapping(raw_zone, f"zones.{zone_id}")
        workspace_mode = str(zone.get("workspace_mode", "replace_assembly"))
        if workspace_mode not in {"replace_assembly", "open_floor"}:
            raise ValueError(f"workspace mode is unsupported: {workspace_mode}")
        assembly_roots = [
            _prim_path(value)
            for value in _string_list(
                zone.get("assembly_roots", []),
                f"zones.{zone_id}.assembly_roots",
            )
        ]
        if workspace_mode == "replace_assembly" and not assembly_roots:
            raise ValueError(
                f"replace_assembly zone requires at least one root: {zone_id}"
            )
        if workspace_mode == "open_floor" and assembly_roots:
            raise ValueError(f"open_floor zone must not replace assemblies: {zone_id}")
        for prim_path in assembly_roots:
            if not stage.GetPrimAtPath(prim_path):
                raise ValueError(
                    f"workspace zone assembly root is absent: {prim_path}"
                )
        anchor_prim = _prim_path(_string(zone, "anchor_prim"))
        if not stage.GetPrimAtPath(anchor_prim):
            raise ValueError(f"workspace zone anchor prim is absent: {anchor_prim}")
        anchor_xyz = _number3(zone.get("anchor_xyz"), f"zones.{zone_id}.anchor_xyz")
        yaw_deg = _finite_number(zone.get("yaw_deg", 0.0), f"zones.{zone_id}.yaw_deg")
        if abs(yaw_deg) > 360.0:
            raise ValueError(f"workspace zone yaw is out of range: {zone_id}")
        optional_inactives = [
            _prim_path(value)
            for value in _string_list(
                zone.get("optional_inactive_paths", []),
                f"zones.{zone_id}.optional_inactive_paths",
            )
        ]
        report = audit_clearance(
            stage,
            ClearanceSpec(
                assembly_roots=assembly_roots,
                anchor_xyz=anchor_xyz,
                table_footprint_m=_rotated_aabb_footprint(
                    yaw_deg,
                    clearance_footprint_m,
                ),
                units_per_meter=units_per_meter,
                floor_z=floor_z,
            ),
            is_room_shell=lambda prim: any(
                prim.GetPath().pathString == prefix
                or prim.GetPath().pathString.startswith(prefix.rstrip("/") + "/")
                for prefix in shell_prefixes
            ),
        )
        blockers = [
            item
            for item in report.intruders
            if not _covered_by_inactive_root(item.prim_path, optional_inactives)
        ]
        profile = ZoneProfile(
            zone_id=zone_id,
            background_asset_id=background_asset_id,
            source_sha256=profile_source_sha256,
            producer=producer,
            coordinate_mapping=coordinate_mapping,
            workspace_mode=workspace_mode,
            assembly_roots=assembly_roots,
            anchor_prim=anchor_prim,
            anchor_xyz=anchor_xyz,
            clearance_aabb=report.clearance_aabb_m,
            optional_inactives=optional_inactives,
            yaw_deg=yaw_deg,
            yaw_note=str(zone.get("yaw_note", "reviewed in source-composed frame")),
            coverage_note=(
                f"room shell intersections: {report.room_shell_intersections}; "
                f"optional inactives: {optional_inactives}"
            ),
            anchor_frame_note=str(
                zone.get("anchor_frame_note", "source-composed metric coordinates")
            ),
            package_manifest=package_manifest,
            facade_provenance=facade_provenance,
            evidence_image=str(zone.get("evidence_image", "")),
            evidence_camera_position=_optional_number3(
                zone.get("evidence_camera_position"),
                f"zones.{zone_id}.evidence_camera_position",
            ),
            evidence_camera_target=_optional_number3(
                zone.get("evidence_camera_target"),
                f"zones.{zone_id}.evidence_camera_target",
            ),
            room_survey=_room_survey_override(zone, stage, zone_id),
            support_closure=support_closure,
        )
        profile_name = (
            f"{background_asset_id}__{zone_id}_workspace_zone.yaml"
        )
        profile_path = output / profile_name
        if blockers:
            reason = (
                "clearance intersects non-inactivated source geometry: "
                + ", ".join(item.prim_path for item in blockers[:20])
            )
            if len(blockers) > 20:
                reason += f" (+{len(blockers) - 20} more)"
            write_yaml(profile.to_not_applicable_document(reason), profile_path)
            manifest_zones[zone_id] = {
                "status": "not_applicable",
                "profile": profile_name,
                "reason": reason,
            }
            not_applicable_count += 1
        else:
            write_yaml(profile.to_document(), profile_path)
            manifest_zones[zone_id] = {
                "status": "profiled",
                "profile": profile_name,
            }
            profiled_count += 1

    manifest = ZoneManifest(
        background_asset_id=background_asset_id,
        source_sha256=profile_source_sha256,
        producer=producer,
        zones=manifest_zones,
        package_manifest=package_manifest,
        facade_provenance=facade_provenance,
    )
    manifest_path = output / "workspace_zone_profiles_manifest.json"
    manifest.write(manifest_path)
    return ZoneBatchResult(
        manifest_path=manifest_path,
        profiled_count=profiled_count,
        not_applicable_count=not_applicable_count,
    )


def _room_survey_override(
    zone: Mapping[str, Any], stage: Any, zone_id: str
) -> dict[str, Any] | None:
    raw = zone.get("room_survey")
    if raw is None:
        return None
    survey = _mapping(raw, f"zones.{zone_id}.room_survey")
    allowed_views = {
        "room_topdown",
        "room_corner_a",
        "room_corner_b",
        "room_entrance_eye_level",
    }
    views: dict[str, Any] = {}
    for view_name, raw_view in survey.items():
        if view_name not in allowed_views:
            raise ValueError(f"room survey view is unsupported: {view_name}")
        view = _mapping(raw_view, f"zones.{zone_id}.room_survey.{view_name}")
        position = _number3(
            view.get("position_xyz"),
            f"zones.{zone_id}.room_survey.{view_name}.position_xyz",
        )
        target = _number3(
            view.get("target_xyz"),
            f"zones.{zone_id}.room_survey.{view_name}.target_xyz",
        )
        hidden_paths = [
            _prim_path(value)
            for value in _string_list(
                view.get("temporary_hidden_prim_paths", []),
                f"zones.{zone_id}.room_survey.{view_name}.temporary_hidden_prim_paths",
            )
        ]
        if hidden_paths and view_name not in {"room_corner_a", "room_corner_b"}:
            raise ValueError("only room corner survey views may hide wall roots")
        for prim_path in hidden_paths:
            prim = stage.GetPrimAtPath(prim_path)
            if (
                not prim
                or str(prim.GetTypeName()) != "Xform"
                or not prim.GetName().lower().startswith("wall_")
            ):
                raise ValueError(
                    f"room survey hidden path is not a complete wall Xform root: {prim_path}"
                )
        views[view_name] = {
            "position_xyz": [float(value) for value in position],
            "target_xyz": [float(value) for value in target],
            "temporary_hidden_prim_paths": hidden_paths,
        }
    if not views:
        raise ValueError(f"zones.{zone_id}.room_survey must contain at least one view")
    return {
        "frame_convention": "usd_z_up_right_handed_ccw",
        "views": views,
    }


def _load_request(path: Path) -> dict[str, object]:
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"workspace zone request is invalid: {path}") from exc
    return dict(_mapping(raw, "request"))


def _rotated_aabb_footprint(
    yaw_deg: float,
    footprint_m: tuple[float, float],
) -> tuple[float, float]:
    width, depth = footprint_m
    angle = math.radians(yaw_deg)
    return (
        abs(math.cos(angle)) * width + abs(math.sin(angle)) * depth,
        abs(math.sin(angle)) * width + abs(math.cos(angle)) * depth,
    )


def _covered_by_inactive_root(prim_path: str, roots: list[str]) -> bool:
    """Return whether a reported leaf belongs to a declared assembly root."""

    return any(
        prim_path == root or prim_path.startswith(f"{root}/")
        for root in roots
    )


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return value


def _string(value: Mapping[str, object], key: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{key} must be a non-empty string")
    return raw


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return list(value)


def _sha256_value(value: Mapping[str, object], key: str) -> str:
    raw = _string(value, key)
    if _SHA256.fullmatch(raw) is None:
        raise ValueError(f"{key} must be a lowercase SHA-256")
    return raw


def _prim_path(value: str) -> str:
    if value != "/World" and not value.startswith("/World/"):
        raise ValueError(f"prim path must be inside /World: {value}")
    return value


def _prim_path_allow_room(value: str) -> str:
    if value != "/Room" and not value.startswith("/Room/"):
        raise ValueError(f"support closure prim path must be inside /Room: {value}")
    return value


def _finite_number(value: object, field: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{field} must be finite")
    return float(value)


def _positive_number(value: object, field: str) -> float:
    result = _finite_number(value, field)
    if result <= 0:
        raise ValueError(f"{field} must be positive")
    return result


def _positive_number2(value: object, field: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{field} must contain two positive numbers")
    return (
        _positive_number(value[0], field),
        _positive_number(value[1], field),
    )


def _number3(value: object, field: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{field} must contain three numbers")
    return tuple(_finite_number(item, field) for item in value)  # type: ignore[return-value]


def _optional_number3(
    value: object,
    field: str,
) -> tuple[float, float, float] | None:
    return None if value is None else _number3(value, field)
