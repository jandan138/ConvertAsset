"""Workspace/zone profile schema writers (v0.1 integration profile, v0.2 zone profile).

Schema-conformant writers keep every profile self-describing: source hash,
producer revision/git commit, exact coordinate mapping, and the
not_applicable contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

V01_SCHEMA = "scenario-forge-convertasset-workspace-integration-profile/v0.1"
V02_ZONE_SCHEMA = "scenario-forge-convertasset-workspace-zone-profile/v0.2"
V02_MANIFEST_SCHEMA = "scenario-forge-convertasset-workspace-zone-profile-manifest/v0.2"

UNIT_CLARIFICATION = (
    "anchor_xyz and clearance_aabb values in this profile are source_composed coordinates, "
    "not necessarily metres; multiply by source_composed_meters_per_unit for metres. The "
    "legacy *_m field names are kept for schema compatibility and will be renamed to *_su "
    "in a future schema version."
)


@dataclass(frozen=True)
class CoordinateMapping:
    units_per_meter: float
    derivation: str

    def to_document(self) -> dict:
        return {
            "frame": "source_composed",
            "source_composed_meters_per_unit": 1.0 / self.units_per_meter,
            "source_composed_units_per_meter": self.units_per_meter,
            "derivation": self.derivation,
        }


@dataclass(frozen=True)
class ProducerInfo:
    git_commit: str
    revision: str
    note: str = (
        "Source-bound analysis only: no source USD/MDL/mesh was modified for this "
        "profile, and no collider, rigid body, mass/inertia, or PhysX suppression was added."
    )

    def to_document(self) -> dict:
        return {"repo": "ConvertAsset", "git_commit": self.git_commit, "revision": self.revision, "note": self.note}


@dataclass(frozen=True)
class WorkspaceProfile:
    candidate_id: str
    source_usd: str
    source_sha256: str
    scope: str
    producer: ProducerInfo
    coordinate_mapping: CoordinateMapping
    assembly_roots: list[str]
    anchor_prim: str
    anchor_xyz: tuple[float, float, float]
    clearance_aabb: dict[str, list[float]]
    optional_inactives: list[str] = field(default_factory=list)
    coverage_note: str = ""
    anchor_frame_note: str = ""
    clearance_note: str = ""
    evidence_image: str = ""
    evidence_note: str = ""
    status: str = "profiled"

    def to_document(self) -> dict:
        return {
            "schema_version": V01_SCHEMA,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "source": {
                "source_usd": self.source_usd,
                "source_sha256": self.source_sha256,
                "scope": self.scope,
            },
            "producer": self.producer.to_document(),
            "coordinate_mapping": self.coordinate_mapping.to_document(),
            "unit_clarification": UNIT_CLARIFICATION,
            "assembly": {
                "replaceable_assembly_roots": self.assembly_roots,
                "anchor_prim": self.anchor_prim,
                "anchor_xyz_m": [float(v) for v in self.anchor_xyz],
                "anchor_frame_note": self.anchor_frame_note,
            },
            "inactivation": {
                "inactive_prim_root_paths": self.assembly_roots,
                "optional_inactive_prim_paths": self.optional_inactives,
                "coverage_note": self.coverage_note,
            },
            "workspace": {
                "clearance_aabb_m": self.clearance_aabb,
                "clearance_note": self.clearance_note,
            },
            "evidence": {"image": self.evidence_image, "image_note": self.evidence_note},
        }


@dataclass(frozen=True)
class ZoneProfile:
    zone_id: str
    background_asset_id: str
    source_sha256: str
    producer: ProducerInfo
    coordinate_mapping: CoordinateMapping
    assembly_roots: list[str] = field(default_factory=list)
    anchor_prim: str = ""
    anchor_xyz: tuple[float, float, float] | None = None
    clearance_aabb: dict[str, list[float]] | None = None
    optional_inactives: list[str] = field(default_factory=list)
    yaw_deg: float | None = None
    yaw_note: str = ""
    coverage_note: str = ""
    anchor_frame_note: str = ""
    package_manifest: str = ""
    evidence_image: str = ""

    def to_document(self) -> dict:
        return {
            "schema_version": V02_ZONE_SCHEMA,
            "zone_id": self.zone_id,
            "status": "profiled",
            "background_asset_id": self.background_asset_id,
            "source": {
                "source_usd_sha256": self.source_sha256,
                "consumer_facade_scope": "/World",
                **({"package_manifest": self.package_manifest} if self.package_manifest else {}),
            },
            "producer": self.producer.to_document(),
            "coordinate_mapping": self.coordinate_mapping.to_document(),
            "assembly": {
                "replaceable_assembly_roots": self.assembly_roots,
                "anchor_prim": self.anchor_prim,
                "anchor_xyz_m": [float(v) for v in (self.anchor_xyz or (0.0, 0.0, 0.0))],
                "anchor_frame_note": self.anchor_frame_note,
            },
            "inactivation": {
                "inactive_prim_root_paths": self.assembly_roots,
                "optional_inactive_prim_paths": self.optional_inactives,
                "coverage_note": self.coverage_note,
            },
            "workspace": {"clearance_aabb_m": self.clearance_aabb},
            "yaw": {"reviewed_yaw_deg": self.yaw_deg, "note": self.yaw_note},
            "evidence": {"image": self.evidence_image},
        }

    def to_not_applicable_document(self, reason: str) -> dict:
        return {
            "schema_version": V02_ZONE_SCHEMA,
            "zone_id": self.zone_id,
            "status": "not_applicable",
            "background_asset_id": self.background_asset_id,
            "source": {"source_usd_sha256": self.source_sha256, "consumer_facade_scope": "/World"},
            "producer": self.producer.to_document(),
            "not_applicable_reason": reason,
        }


@dataclass(frozen=True)
class ZoneManifest:
    background_asset_id: str
    source_sha256: str
    producer: ProducerInfo
    zones: dict[str, dict]
    claim_boundary: str = (
        "Zone profiles are source-bound analysis only; each keeps the complete room USD. "
        "They do not claim task success, background interaction physics, or liquid transfer."
    )

    def to_document(self) -> dict:
        return {
            "schema_version": V02_MANIFEST_SCHEMA,
            "background_asset_id": self.background_asset_id,
            "source": {
                "source_usd_sha256": self.source_sha256,
                "consumer_facade_scope": "/World",
            },
            "producer": self.producer.to_document(),
            "zones": self.zones,
            "claim_boundary": self.claim_boundary,
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_document(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def write_yaml(document: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
