# -*- coding: utf-8 -*-
"""Manifest records for scene target capture."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from convert_asset.camera.bounds import Bounds3D
from convert_asset.camera.poses import CameraPoseSpec
from convert_asset.capture.targets import TargetSpec


@dataclass(frozen=True)
class CaptureRecord:
    scene_usd_path: str
    target: TargetSpec
    bounds: Bounds3D | None
    pose: CameraPoseSpec | None
    output_path: str
    status: str
    error: str | None = None


def target_record_to_dict(target: TargetSpec, bounds: Bounds3D | None = None) -> dict:
    data = target.to_dict()
    if bounds is not None:
        data["bbox"] = {
            "min": list(bounds.min),
            "max": list(bounds.max),
            "center": list(bounds.center),
            "size": list(bounds.size),
            "diagonal": bounds.diagonal,
        }
    return data


def capture_record_to_dict(record: CaptureRecord) -> dict:
    data = {
        "scene_usd_path": record.scene_usd_path,
        "target_path": record.target.prim_path,
        "target_id": record.target.target_id,
        "name": record.target.name,
        "category": record.target.category,
        "level": record.target.level,
        "mesh_count": record.target.mesh_count,
        "type_name": record.target.type_name,
        "output_path": record.output_path,
        "status": record.status,
        "error": record.error,
    }
    if record.bounds is not None:
        data["bbox"] = {
            "min": list(record.bounds.min),
            "max": list(record.bounds.max),
            "center": list(record.bounds.center),
            "size": list(record.bounds.size),
            "diagonal": record.bounds.diagonal,
        }
    if record.pose is not None:
        data["camera"] = {
            "view_index": record.pose.view_index,
            "azimuth_deg": record.pose.azimuth_deg,
            "elevation_deg": record.pose.elevation_deg,
            "distance": record.pose.distance,
            "position": list(record.pose.position),
            "target": list(record.pose.target),
        }
    return data


def write_targets_json(path: str | Path, targets: list[TargetSpec], bounds_by_target: dict[str, Bounds3D] | None = None) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bounds_by_target = bounds_by_target or {}
    payload = [
        target_record_to_dict(target, bounds_by_target.get(target.target_id))
        for target in targets
    ]
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_capture_record(path: str | Path, record: CaptureRecord) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(capture_record_to_dict(record), sort_keys=True))
        handle.write("\n")

