from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest
import yaml

from convert_asset.workspace.zone_batch import build_zone_profiles


ROOM_USDA = """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "World"
{
    def Mesh "Floor"
    {
        point3f[] points = [(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)]
        int[] faceVertexCounts = [4]
        int[] faceVertexIndices = [0, 1, 2, 3]
    }
    def Xform "Zone__North_Workbench"
    {
        def Mesh "Bench"
        {
            point3f[] points = [
                (-1, 3, 0), (1, 3, 0), (1, 4, 0), (-1, 4, 0),
                (-1, 3, 1), (1, 3, 1), (1, 4, 1), (-1, 4, 1)
            ]
            int[] faceVertexCounts = [4, 4]
            int[] faceVertexIndices = [0, 1, 2, 3, 4, 5, 6, 7]
        }
    }
}
"""


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_zone_batch_writes_replace_and_open_floor_profiles(tmp_path: Path) -> None:
    pytest.importorskip("pxr.Usd")
    source = tmp_path / "facade.usda"
    source.write_text(ROOM_USDA, encoding="utf-8")
    request = tmp_path / "zones.json"
    request.write_text(
        json.dumps(
            {
                "schema_version": "aan.workspace_zone_request.v1",
                "background_asset_id": (
                    "scientific_environment_code_room_example4_v1"
                ),
                "source_usd": str(source),
                "source_sha256": _sha(source),
                "scope": "/World",
                "units_per_meter": 1.0,
                "floor_z": 0.0,
                "package_manifest": "../package/evidence/manifest.json",
                "facade_provenance": "../facade/facade_provenance.json",
                "shell_prefixes": ["/World/Floor"],
                "zones": {
                    "center_open_floor": {
                        "workspace_mode": "open_floor",
                        "assembly_roots": [],
                        "anchor_prim": "/World/Floor",
                        "anchor_xyz": [0.0, 0.0, 0.772761],
                        "yaw_deg": 0.0,
                    },
                    "north_workbench_replace": {
                        "workspace_mode": "replace_assembly",
                        "assembly_roots": ["/World/Zone__North_Workbench"],
                        "anchor_prim": (
                            "/World/Zone__North_Workbench/Bench"
                        ),
                        "anchor_xyz": [0.0, 3.5, 1.0],
                        "yaw_deg": 0.0,
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = build_zone_profiles(
        request,
        tmp_path / "profiles",
        git_commit="a" * 40,
        revision="generated-room-zone-profile-r1",
    )

    assert result.profiled_count == 2
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert set(manifest["zones"]) == {
        "center_open_floor",
        "north_workbench_replace",
    }
    assert manifest["source"]["package_manifest"] == (
        "../package/evidence/manifest.json"
    )
    assert manifest["source"]["facade_provenance"] == (
        "../facade/facade_provenance.json"
    )
    open_profile = yaml.safe_load(
        (
            result.manifest_path.parent
            / manifest["zones"]["center_open_floor"]["profile"]
        ).read_text(encoding="utf-8")
    )
    assert open_profile["workspace"]["mode"] == "open_floor"
    assert open_profile["assembly"]["replaceable_assembly_roots"] == []
    assert open_profile["inactivation"]["inactive_prim_root_paths"] == []
    north_profile = yaml.safe_load(
        (
            result.manifest_path.parent
            / manifest["zones"]["north_workbench_replace"]["profile"]
        ).read_text(encoding="utf-8")
    )
    assert north_profile["workspace"]["mode"] == "replace_assembly"
    assert north_profile["yaw"]["rotation_convention"] == (
        "usd_z_up_right_handed_ccw"
    )


def test_zone_batch_can_audit_facade_while_binding_raw_source(
    tmp_path: Path,
) -> None:
    pytest.importorskip("pxr.Usd")
    source = tmp_path / "facade.usda"
    source.write_text(ROOM_USDA, encoding="utf-8")
    request = tmp_path / "zones.json"
    request.write_text(
        json.dumps(
            {
                "schema_version": "aan.workspace_zone_request.v1",
                "background_asset_id": (
                    "scientific_environment_code_room_example4_v1"
                ),
                "source_usd": str(source),
                "source_sha256": "b" * 64,
                "geometry_source_sha256": _sha(source),
                "scope": "/World",
                "units_per_meter": 1.0,
                "floor_z": 0.0,
                "shell_prefixes": ["/World/Floor"],
                "zones": {
                    "center_open_floor": {
                        "workspace_mode": "open_floor",
                        "assembly_roots": [],
                        "anchor_prim": "/World/Floor",
                        "anchor_xyz": [0.0, 0.0, 0.772761],
                        "yaw_deg": 0.0,
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = build_zone_profiles(
        request,
        tmp_path / "profiles",
        git_commit="a" * 40,
        revision="generated-room-zone-profile-r1",
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source"]["source_usd_sha256"] == "b" * 64
