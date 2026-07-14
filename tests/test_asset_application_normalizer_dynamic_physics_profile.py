"""TDD coverage for profile-owned dynamic physics admission."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import normalize_asset


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _source_usda(*, authored_mass: float = 0.0, second_body: bool = False) -> str:
    extra = """
        def Mesh \"Extra\" (
            prepend apiSchemas = [\"PhysicsRigidBodyAPI\", \"PhysicsCollisionAPI\", \"PhysicsMassAPI\"]
        )
        {
            bool physics:rigidBodyEnabled = 1
            bool physics:collisionEnabled = 1
            float physics:mass = 0
            float3 physics:diagonalInertia = (0, 0, 0)
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
            int[] faceVertexCounts = [3, 3, 3, 3]
            int[] faceVertexIndices = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
        }
    """ if second_body else ""
    return f"""#usda 1.0
(
    defaultPrim = \"World\"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = \"Z\"
    timeCodesPerSecond = 60
    framesPerSecond = 24
)
def Xform \"World\"
{{
    def Xform \"Asset\"
    {{
        def Mesh \"Body\" (
            prepend apiSchemas = [\"PhysicsRigidBodyAPI\", \"PhysicsCollisionAPI\", \"PhysicsMassAPI\"]
        )
        {{
            bool physics:rigidBodyEnabled = 1
            bool physics:collisionEnabled = 1
            float physics:mass = {authored_mass}
            float3 physics:diagonalInertia = (0, 0, 0)
            point3f physics:centerOfMass = (-inf, -inf, -inf)
            quatf physics:principalAxes = (0, 0, 0, 0)
            float physics:density = 0.001
            point3f[] points = [(0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 4)]
            int[] faceVertexCounts = [3, 3, 3, 3]
            int[] faceVertexIndices = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
        }}
        {extra}
    }}
}}
"""


def _request(source: Path, out_dir: Path, evidence_out: Path, profile: Path) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=source,
        out_dir=out_dir,
        asset_id="profiled-physics-fixture",
        asset_class="rigid",
        asset_role="dynamic",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="AAN.ProfiledPhysics",
        required_prims=["/World/Asset"],
        asset_scope_prims=["/World/Asset"],
        gates=["static"],
        evidence_out=evidence_out,
        physics_profile=profile,
    )


def _profile(
    source: Path,
    path: Path,
    *,
    mode: str = "explicit",
    body_rules: list[dict] | None = None,
    authored_mass_kg: float = 7.0,
) -> Path:
    mass_properties: dict[str, object] = {
        "mode": mode,
        "quality_tier": "provisional_geometry",
        "diagonal_inertia_kg_m2": [0.4, 0.5, 0.6],
        "center_of_mass_body_local": [0.5, 0.25, 0.75],
        "principal_axes": [1.0, 0.0, 0.0, 0.0],
    }
    if mode == "explicit":
        mass_properties["mass_kg"] = 2.5
    else:
        mass_properties["authored_mass_kg"] = authored_mass_kg
    payload = {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "tests.profiled-physics",
        "revision": "r1",
        "source_binding": {
            "sha256": _sha256(source),
            "stage_metrics": {
                "meters_per_unit": 1.0,
                "kilograms_per_unit": 1.0,
                "up_axis": "Z",
                "time_codes_per_second": 60.0,
                "frames_per_second": 24.0,
            },
        },
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": "Fixture values are explicit simulation candidates, not measurements.",
            "replacement_contract": "Replace the complete bundle in a new source-bound profile revision.",
        },
        "scope_rules": [
            {
                "scope_path": "/World/Asset",
                "body_rules": body_rules
                or [
                    {
                        "relative_path": "Body",
                        "motion_role": "dynamic",
                        "clear_density": True,
                        "mass_properties": mass_properties,
                    }
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_profiled_dynamic_package_preserves_source_physical_frame_and_authors_bundle(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(_request(source, out_dir, evidence_out, profile))

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["physics_closure"]["physical_frame"]["status"] == "pass"
    assert manifest["physics_closure"]["profile_admission"]["status"] == "pass"
    assert manifest["physics_closure"]["profile_admission"]["quality_tier"] == "provisional_geometry"
    assert manifest["visual_preservation_fingerprint"]["status"] == "pass"
    assert (
        "Measured, BOM, CAD, or real-world physical-parameter parity is verified."
        in manifest["claims_forbidden"]
    )

    Usd = pytest.importorskip("pxr.Usd")
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    UsdPhysics = pytest.importorskip("pxr.UsdPhysics")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    assert UsdGeom.GetStageMetersPerUnit(stage) == pytest.approx(1.0)
    assert UsdPhysics.GetStageKilogramsPerUnit(stage) == pytest.approx(1.0)
    assert UsdGeom.GetStageUpAxis(stage) == "Z"
    assert stage.GetTimeCodesPerSecond() == pytest.approx(60.0)
    body = stage.GetPrimAtPath("/World/Asset/Body")
    assert body.GetAttribute("physics:mass").Get() == pytest.approx(2.5)
    assert list(body.GetAttribute("physics:diagonalInertia").Get()) == pytest.approx([0.4, 0.5, 0.6])
    assert list(body.GetAttribute("physics:centerOfMass").Get()) == pytest.approx([0.5, 0.25, 0.75])
    assert body.GetAttribute("physics:density").Get() == pytest.approx(0.0)


def test_profile_authoring_uses_the_exact_bytes_that_were_admitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json")
    admitted_sha = _sha256(profile)

    from convert_asset.asset_application_normalizer import physics_authoring

    real_resolve = physics_authoring.load_and_resolve_profile

    def resolve_then_replace(*args, **kwargs):
        resolution = real_resolve(*args, **kwargs)
        replacement = json.loads(profile.read_text(encoding="utf-8"))
        replacement["scope_rules"][0]["body_rules"][0]["mass_properties"]["mass_kg"] = 9.0
        profile.write_text(json.dumps(replacement), encoding="utf-8")
        return resolution

    monkeypatch.setattr(physics_authoring, "load_and_resolve_profile", resolve_then_replace)
    out_dir = tmp_path / "package"
    result = normalize_asset(_request(source, out_dir, tmp_path / "manifest.json", profile))

    assert result.return_code == 0
    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    body = stage.GetPrimAtPath("/World/Asset/Body")
    assert body.GetAttribute("physics:mass").Get() == pytest.approx(2.5)
    assert _sha256(out_dir / "physics" / "profile.json") == admitted_sha


def test_profile_preserves_valid_authored_mass_as_the_inertia_mass_basis(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(authored_mass=7.0), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json", mode="preserve_authored_mass")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(_request(source, tmp_path / "package", evidence_out, profile))

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    record = manifest["physics_closure"]["mass_properties"][0]
    assert record["mass"]["value"] == pytest.approx(7.0)
    assert record["mass"]["value_source"] == "authored"
    assert record["inertia"]["value_source"] == "profile"
    assert record["inertia"]["mass_basis"]["source"] == "authored"
    assert record["inertia"]["mass_basis"]["value"] == pytest.approx(7.0)


def test_profile_rejects_a_mismatched_authored_mass_basis_for_inertia(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(authored_mass=7.0), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json", mode="preserve_authored_mass")
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["scope_rules"][0]["body_rules"][0]["mass_properties"]["authored_mass_kg"] = 2.5
    profile.write_text(json.dumps(payload), encoding="utf-8")

    result = normalize_asset(_request(source, tmp_path / "package", tmp_path / "manifest.json", profile))

    assert result.return_code == 5
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    admission = manifest["physics_closure"]["profile_admission"]
    assert admission["status"] == "blocked"
    assert "authored_mass_kg" in " ".join(admission["invalid_body_rules"][0]["errors"])


def test_measured_profile_requires_hashed_measurement_evidence(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json")
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["scope_rules"][0]["body_rules"][0]["mass_properties"]["quality_tier"] = "measured"
    payload["evidence"] = {
        "parameter_status": "measured",
        "claim_boundary": "Measured values require retained evidence.",
        "replacement_contract": "Publish a new complete profile revision.",
    }
    profile.write_text(json.dumps(payload), encoding="utf-8")

    result = normalize_asset(_request(source, tmp_path / "package", tmp_path / "manifest.json", profile))

    assert result.return_code == 5
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    admission = manifest["physics_closure"]["profile_admission"]
    assert admission["status"] == "blocked"
    assert "evidence.artifacts" in " ".join(admission["errors"])


def test_profile_source_hash_mismatch_blocks_dynamic_admission(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json")
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["source_binding"]["sha256"] = "0" * 64
    profile.write_text(json.dumps(payload), encoding="utf-8")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(_request(source, tmp_path / "package", evidence_out, profile))

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert "aan05_block_physics_profile" in {
        item["blocker_id"] for item in manifest["blocked_reasons"]
    }


def test_profile_requires_exact_coverage_for_every_active_rigid_body(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(second_body=True), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(_request(source, tmp_path / "package", evidence_out, profile))

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    admission = manifest["physics_closure"]["profile_admission"]
    assert admission["status"] == "blocked"
    assert admission["unmatched_rigid_bodies"] == ["/World/Asset/Extra"]


def test_runtime_warning_scope_binding_maps_reinstanced_asset_paths_without_prefix_leakage() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        build_physx_warning_diff,
        evaluate_physx_warning_scope,
        parse_physx_warning_events,
    )

    events = parse_physx_warning_events(
        "\n".join(
            [
                "[Warning] [omni.physx.plugin] The rigid body at /World/Room/DryingBox_03/handle/mesh has a negative mass.",
                "[Warning] [omni.physx.plugin] The rigid body at /World/Room/DryingBox_030/handle/mesh has a negative mass.",
            ]
        ),
        stream="stdout",
    )
    gate = evaluate_physx_warning_scope(
        events,
        ["/World/DryingBox_03"],
        runtime_scope_bindings=[
            {
                "package_scope": "/World/DryingBox_03",
                "runtime_scope": "/World/Room/DryingBox_03",
            }
        ],
    )

    assert gate["status"] == "blocked"
    assert gate["summary"]["scoped_event_count"] == 1
    assert gate["scoped_events"][0]["canonical_package_relative_prim"] == "scope_0/handle/mesh"
    assert gate["summary"]["out_of_scope_event_count"] == 1

    diff = build_physx_warning_diff(
        [],
        events[:1],
        baseline_scopes=["/World/Room/DryingBox_03"],
        candidate_scopes=["/World/DryingBox_03"],
        candidate_runtime_scope_bindings=[
            {
                "package_scope": "/World/DryingBox_03",
                "runtime_scope": "/World/Room/DryingBox_03",
            }
        ],
    )
    assert diff["status"] == "blocked"
    assert diff["rows"][0]["canonical_prim"] == "scope_0/handle/mesh"


def test_nonidentity_runtime_scope_binding_requires_instantiated_runtime_log(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    profile = _profile(source, tmp_path / "profile.json")
    request = replace(
        _request(source, tmp_path / "package", tmp_path / "manifest.json", profile),
        runtime_scope_bindings=[
            {
                "package_scope": "/World/Asset",
                "runtime_scope": "/World/Room/Asset",
            }
        ],
    )

    result = normalize_asset(request)

    assert result.return_code == 2
