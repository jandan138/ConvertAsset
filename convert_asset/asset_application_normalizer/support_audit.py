"""Independent admission of producer-authored room support relations."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "room-support-relations-v1"
RELATION_KINDS = frozenset({"rests_on", "mounted_to", "stacked_on"})


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _blocked(reason: str) -> dict[str, Any]:
    return {
        "schema_version": "aan.generated_room_support_audit.v1",
        "overall_status": "blocked",
        "blocked_reasons": [reason],
        "source_usd": None,
        "source_sha256": None,
        "relations": [],
        "support_closure": {},
    }


def audit_support_relations(sidecar_path: str | Path) -> dict[str, Any]:
    """Validate sidecar provenance and recompute support from composed USD bounds.

    No producer geometry result is trusted. Bounds, path existence, margin, and
    vertical contact are calculated again from the exact source USD named by
    the hash-bound sidecar.
    """

    sidecar = Path(sidecar_path).resolve()
    if not sidecar.is_file():
        return _blocked(f"support relation sidecar is unavailable: {sidecar}")
    try:
        document = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _blocked(f"support relation sidecar is invalid JSON: {exc}")
    if document.get("schema_version") != SCHEMA_VERSION:
        return _blocked("support relation sidecar schema is unsupported")
    source_record = document.get("source_usd")
    if not isinstance(source_record, dict) or not isinstance(source_record.get("path"), str):
        return _blocked("support relation sidecar has no source USD path")
    source = (sidecar.parent / source_record["path"]).resolve()
    if not source.is_file():
        return _blocked(f"support relation source USD is unavailable: {source}")
    actual_hash = _file_sha256(source)
    if source_record.get("sha256") != actual_hash:
        return _blocked("support relation source USD SHA-256 does not match the sidecar")
    if document.get("review", {}).get("status") != "pass":
        return _blocked("producer engineering review is not passing")

    try:
        margin_m = float(document.get("margin_m"))
        vertical_tolerance_m = float(document.get("vertical_tolerance_m"))
    except (TypeError, ValueError):
        return _blocked("support relation tolerances are invalid")
    if margin_m < 0 or vertical_tolerance_m < 0:
        return _blocked("support relation tolerances must be non-negative")

    from pxr import Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(source))
    if stage is None:
        return _blocked(f"support relation source USD cannot be opened: {source}")
    meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage))
    margin = margin_m / meters_per_unit
    vertical_tolerance = vertical_tolerance_m / meters_per_unit
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    blocked_reasons: list[str] = []
    relation_reports: list[dict[str, Any]] = []
    support_closure: dict[str, list[str]] = {}
    relations = document.get("relations")
    if not isinstance(relations, list):
        return _blocked("support relation list is missing")

    for index, relation in enumerate(relations):
        if not isinstance(relation, dict):
            blocked_reasons.append(f"relation {index} is not a mapping")
            continue
        status = relation.get("audit_status")
        kind = relation.get("relation_kind")
        object_path = relation.get("object_prim")
        support_path = relation.get("support_prim")
        entry = {
            "object_prim": object_path,
            "support_prim": support_path,
            "relation_kind": kind,
            "producer_status": status,
            "independent_status": "blocked",
        }
        if kind not in RELATION_KINDS:
            blocked_reasons.append(f"relation {index} has unsupported relation kind")
            relation_reports.append(entry)
            continue
        if status == "removed":
            historical_name = relation.get("object_name")
            if object_path and stage.GetPrimAtPath(str(object_path)).IsValid():
                blocked_reasons.append(f"removed decoration still exists: {object_path}")
            else:
                entry["independent_status"] = "pass"
                entry["removed_object_name"] = historical_name
            relation_reports.append(entry)
            continue
        if status != "pass" or not isinstance(object_path, str) or not isinstance(support_path, str):
            blocked_reasons.append(f"relation {index} is unresolved")
            relation_reports.append(entry)
            continue
        object_prim = stage.GetPrimAtPath(object_path)
        support_prim = stage.GetPrimAtPath(support_path)
        if not object_prim.IsValid() or not support_prim.IsValid():
            blocked_reasons.append(f"relation prim is missing: {object_path} -> {support_path}")
            relation_reports.append(entry)
            continue
        object_range = bbox_cache.ComputeWorldBound(object_prim).ComputeAlignedRange()
        support_range = bbox_cache.ComputeWorldBound(support_prim).ComputeAlignedRange()
        object_min, object_max = object_range.GetMin(), object_range.GetMax()
        support_min, support_max = support_range.GetMin(), support_range.GetMax()
        if object_range.IsEmpty() or support_range.IsEmpty():
            blocked_reasons.append(f"relation has empty geometry bounds: {object_path}")
            relation_reports.append(entry)
            continue

        if kind in {"rests_on", "stacked_on"}:
            horizontal_pass = all(
                object_min[axis] >= support_min[axis] + margin - 1e-5
                and object_max[axis] <= support_max[axis] - margin + 1e-5
                for axis in (0, 1)
            )
            vertical_gap = abs(float(object_min[2] - support_max[2]))
            vertical_pass = vertical_gap <= vertical_tolerance + 1e-5
            entry.update(
                {
                    "horizontal_margin_pass": horizontal_pass,
                    "vertical_contact_pass": vertical_pass,
                    "vertical_gap_m": vertical_gap * meters_per_unit,
                }
            )
            if not horizontal_pass:
                blocked_reasons.append(f"object footprint is outside support margin: {object_path}")
            if not vertical_pass:
                blocked_reasons.append(f"object is outside vertical support tolerance: {object_path}")
            passed = horizontal_pass and vertical_pass
        else:
            overlaps = all(
                object_max[axis] >= support_min[axis] - 1e-5
                and object_min[axis] <= support_max[axis] + 1e-5
                for axis in range(3)
            )
            entry["mounted_geometry_overlap_pass"] = overlaps
            if not overlaps:
                blocked_reasons.append(f"mounted object does not overlap its support: {object_path}")
            passed = overlaps
        if passed:
            entry["independent_status"] = "pass"
            support_closure.setdefault(support_path, []).append(object_path)
        relation_reports.append(entry)

    return {
        "schema_version": "aan.generated_room_support_audit.v1",
        "overall_status": "pass" if not blocked_reasons else "blocked",
        "blocked_reasons": blocked_reasons,
        "source_usd": str(source),
        "source_sha256": actual_hash,
        "producer_sidecar": str(sidecar),
        "producer_review": dict(document.get("review", {})),
        "margin_m": margin_m,
        "vertical_tolerance_m": vertical_tolerance_m,
        "relations": relation_reports,
        "support_closure": {key: sorted(value) for key, value in sorted(support_closure.items())},
    }
