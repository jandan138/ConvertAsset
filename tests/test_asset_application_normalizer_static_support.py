"""Contract tests for source-bound static support packages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import normalize_asset, validate_request


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_usda(*, with_collider: bool = True) -> str:
    schemas = ' (prepend apiSchemas = ["PhysicsCollisionAPI"])' if with_collider else ""
    collision = "bool physics:collisionEnabled = 1" if with_collider else ""
    return f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "World"
{{
    def Xform "Table"
    {{
        def Cube "Top"{schemas}
        {{
            double size = 1
            float3 xformOp:scale = (2, 1.2, 0.08)
            double3 xformOp:translate = (0, 0, 0.76)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            {collision}
        }}
    }}
}}
'''


def _profile(source: Path, path: Path, *, source_collider: str | None) -> Path:
    payload = {
        "schema_version": "aan.static_support_profile.v1",
        "profile_id": "tests.table.static-support",
        "revision": "r1",
        "source_binding": {"sha256": _sha256(source)},
        "asset_entry_prim": "/World/Table",
        "collider_policy": "prefer_source_then_proxy",
        "source_collider_prim": source_collider,
        "proxy": {
            "prim_path": "/World/Table/__aan_static_support_proxy",
            "center_xyz": [0.0, 0.0, 0.76],
            "size_xyz": [2.0, 1.2, 0.08],
        },
        "support_surface": {
            "top_z": 0.80,
            "x_range": [-1.0, 1.0],
            "y_range": [-0.6, 0.6],
            "edge_band_m": 0.05,
        },
        "physics_material": {
            "prim_path": "/World/Table/__aan_static_support_material",
            "static_friction": 0.5,
            "dynamic_friction": 0.5,
            "restitution": 0.0,
            "friction_combine_mode": "max",
            "restitution_combine_mode": "multiply",
            "calibration_status": "provisional_unmeasured",
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _request(source: Path, profile: Path | None, out_dir: Path) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=source,
        out_dir=out_dir,
        asset_id="support-table",
        asset_class="static_support",
        asset_role="static_support",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="AAN.StaticSupport",
        required_prims=["/World/Table"],
        asset_scope_prims=["/World/Table"],
        gates=["static"],
        evidence_out=out_dir / "evidence" / "manifest.json",
        static_support_profile=profile,
    )


def test_scenario_forge_static_support_requires_profile(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")

    result = validate_request(_request(source, None, tmp_path / "package"))

    assert result is not None
    assert result.overall_status == "invalid"


def test_static_support_preserves_qualified_source_collider_and_authors_material(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json", source_collider="/World/Table/Top")
    out_dir = tmp_path / "package"

    result = normalize_asset(_request(source, profile, out_dir))

    assert result.return_code == 0
    manifest = json.loads((out_dir / "evidence" / "manifest.json").read_text(encoding="utf-8"))
    contract = manifest["static_support_contract"]
    assert contract["status"] == "pass"
    assert manifest["dependency_closure"]["scope_extraction"]["status"] == "pass"
    assert manifest["dependency_closure"]["scope_dependency_filter"]["status"] == "applied"
    assert contract["collider_selection"] == "preserved_source"
    assert contract["colliders"] == [
        {
            "prim_path": "/World/Table/Top",
            "collision_enabled": True,
            "source": "qualified_source",
        }
    ]
    assert contract["physics_material"]["calibration_status"] == "provisional_unmeasured"
    assert (out_dir / "static_support" / "profile.json").is_file()

    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    top = stage.GetPrimAtPath("/World/Table/Top")
    assert "PhysicsCollisionAPI" in set(top.GetAppliedSchemas())
    assert top.GetAttribute("physics:collisionEnabled").Get() is True
    material = stage.GetPrimAtPath("/World/Table/__aan_static_support_material")
    assert material.IsValid()
    assert material.GetAttribute("physics:staticFriction").Get() == pytest.approx(0.5)
    assert material.GetAttribute("physxMaterial:frictionCombineMode").Get() == "max"


def test_static_support_falls_back_to_package_owned_proxy(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(with_collider=False), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json", source_collider=None)
    out_dir = tmp_path / "package"

    result = normalize_asset(_request(source, profile, out_dir))

    assert result.return_code == 0
    manifest = json.loads((out_dir / "evidence" / "manifest.json").read_text(encoding="utf-8"))
    contract = manifest["static_support_contract"]
    assert contract["collider_selection"] == "authored_proxy"
    assert contract["colliders"][0]["prim_path"] == "/World/Table/__aan_static_support_proxy"
    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    proxy = stage.GetPrimAtPath("/World/Table/__aan_static_support_proxy")
    assert proxy.GetTypeName() == "Cube"
    assert "PhysicsCollisionAPI" in set(proxy.GetAppliedSchemas())


def test_static_support_profile_is_source_bound(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json", source_collider="/World/Table/Top")
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["source_binding"]["sha256"] = "0" * 64
    profile.write_text(json.dumps(payload), encoding="utf-8")
    out_dir = tmp_path / "package"

    result = normalize_asset(_request(source, profile, out_dir))

    assert result.return_code == 5
    manifest = json.loads((out_dir / "evidence" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["static_support_contract"]["status"] == "blocked"
    assert any(
        item["blocker_id"] == "aan05_block_static_support_profile"
        for item in manifest["blocked_reasons"]
    )


def test_static_support_runtime_gate_requires_all_five_drops_and_side_impact() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        _evaluate_static_support_probe_samples,
    )

    samples = {
        name: {
            "initial_xyz_m": [0.0, 0.0, 0.95],
            "final_xyz_m": [0.0, 0.0, 0.82],
            "expected_rest_z_m": 0.82,
        }
        for name in (
            "center_drop",
            "north_edge_drop",
            "south_edge_drop",
            "east_edge_drop",
            "west_edge_drop",
        )
    }
    samples["side_impact"] = {
        "initial_xyz_m": [0.0, -0.72, 0.76],
        "final_xyz_m": [0.0, -0.59, 0.76],
        "maximum_allowed_inward_y_m": -0.55,
    }

    result = _evaluate_static_support_probe_samples(samples)

    assert result["status"] == "pass"
    assert result["probe_count"] == 6
    samples["east_edge_drop"]["final_xyz_m"][2] = 0.2
    assert _evaluate_static_support_probe_samples(samples)["status"] == "blocked"
