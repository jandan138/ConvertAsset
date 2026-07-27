"""Tests for convert_asset.workspace.profiles."""

from __future__ import annotations

import yaml

from convert_asset.workspace.profiles import (
    CoordinateMapping,
    ProducerInfo,
    WorkspaceProfile,
    ZoneManifest,
    ZoneProfile,
    write_yaml,
)


def _mapping() -> CoordinateMapping:
    return CoordinateMapping(units_per_meter=19.146, derivation="test derivation")


def test_workspace_profile_schema_roundtrip(tmp_path) -> None:
    profile = WorkspaceProfile(
        candidate_id="lab_test",
        source_usd="/abs/lab_test.usd",
        source_sha256="abc123",
        scope="/World",
        producer=ProducerInfo(git_commit="deadbeef", revision="2026-07-27-test-1"),
        coordinate_mapping=_mapping(),
        assembly_roots=["/World/group_000"],
        anchor_prim="/World/group_000",
        anchor_xyz=(-18.96, 4.23, 18.194),
        clearance_aabb={"min": [-42.41, -22.1, 1.74], "max": [4.49, 30.56, 60.32]},
        optional_inactives=["/World/decal"],
        coverage_note="zero non-shell intruders",
        evidence_image="evidence/lab_test_workspace.png",
    )
    out = tmp_path / "profile.yaml"
    write_yaml(profile.to_document(), out)
    doc = yaml.safe_load(out.read_text(encoding="utf-8"))

    assert doc["schema_version"] == "scenario-forge-convertasset-workspace-integration-profile/v0.1"
    cm = doc["coordinate_mapping"]
    assert cm["frame"] == "source_composed"
    assert cm["source_composed_units_per_meter"] == 19.146
    assert cm["source_composed_meters_per_unit"] == 1 / 19.146
    assert "source_composed" in doc["unit_clarification"]
    assert doc["assembly"]["replaceable_assembly_roots"] == ["/World/group_000"]
    assert doc["inactivation"]["optional_inactive_prim_paths"] == ["/World/decal"]


def test_zone_profile_and_manifest_schema(tmp_path) -> None:
    zone = ZoneProfile(
        zone_id="north_pair",
        background_asset_id="scientific_environment_x",
        source_sha256="abc123",
        producer=ProducerInfo(git_commit="deadbeef", revision="r1"),
        coordinate_mapping=_mapping(),
        assembly_roots=["/World/Root/A", "/World/Root/B"],
        anchor_prim="/World/Root/A",
        anchor_xyz=(0.0, 1.0, 0.9),
        clearance_aabb={"min": [-1.0, -1.0, 0.0], "max": [1.0, 3.0, 2.2]},
        yaw_deg=90.0,
        yaw_note="x-axis row",
        coverage_note="clean",
    )
    out = tmp_path / "zone.yaml"
    write_yaml(zone.to_document(), out)
    doc = yaml.safe_load(out.read_text(encoding="utf-8"))

    assert doc["schema_version"] == "scenario-forge-convertasset-workspace-zone-profile/v0.2"
    assert doc["yaw"]["reviewed_yaw_deg"] == 90.0
    assert doc["status"] == "profiled"

    manifest = ZoneManifest(
        background_asset_id="scientific_environment_x",
        source_sha256="abc123",
        producer=ProducerInfo(git_commit="deadbeef", revision="r1"),
        zones={
            "north_pair": {"status": "profiled", "profile": "zone.yaml"},
            "south_spot": {"status": "not_applicable", "reason": "aisle too narrow"},
        },
    )
    mout = tmp_path / "manifest.json"
    manifest.write(mout)
    import json

    data = json.loads(mout.read_text(encoding="utf-8"))
    assert data["schema_version"] == "scenario-forge-convertasset-workspace-zone-profile-manifest/v0.2"
    assert data["zones"]["south_spot"]["status"] == "not_applicable"


def test_not_applicable_zone_document(tmp_path) -> None:
    zone = ZoneProfile(
        zone_id="bad_spot",
        background_asset_id="scientific_environment_x",
        source_sha256="abc123",
        producer=ProducerInfo(git_commit="deadbeef", revision="r1"),
        coordinate_mapping=_mapping(),
    )
    doc = zone.to_not_applicable_document("measured reason here")
    assert doc["status"] == "not_applicable"
    assert doc["not_applicable_reason"] == "measured reason here"
