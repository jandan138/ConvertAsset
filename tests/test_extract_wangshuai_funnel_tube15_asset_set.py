from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.extract_wangshuai_funnel_tube15_asset_set import (
    ASSETS,
    build_asset_set,
)
from scripts.qualify_wangshuai_funnel_tube15_asset_set import classify_run
from scripts.promote_wangshuai_funnel_tube15_asset_set import promote


SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_wangshuai/lixinguan_funnel_liquid.usd"
)


def _mesh_hash(prim) -> str:
    from pxr import UsdGeom

    mesh = UsdGeom.Mesh(prim)
    digest = sha256()
    for attr in (
        mesh.GetPointsAttr(),
        mesh.GetFaceVertexCountsAttr(),
        mesh.GetFaceVertexIndicesAttr(),
    ):
        digest.update(repr(list(attr.Get())).encode())
    return digest.hexdigest()


@pytest.mark.skipif(not SOURCE.is_file(), reason="Wangshuai source scene unavailable")
def test_exact_split_preserves_mesh_and_physics_without_new_apis(tmp_path: Path) -> None:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    result = build_asset_set(SOURCE, tmp_path / "set")
    source = Usd.Stage.Open(str(SOURCE))
    for asset_id, spec in ASSETS.items():
        if asset_id == "small_v2_liquid_seed_1948":
            continue
        package = result["packages"][asset_id]
        stage = Usd.Stage.Open(str(package / "asset.usda"))
        root = stage.GetDefaultPrim()
        assert str(root.GetPath()) == spec["entry_prim"]
        assert UsdGeom.Xformable(root).GetLocalTransformation() == Gf.Matrix4d(1.0)
        assert root.HasAPI(UsdPhysics.RigidBodyAPI)
        source_root = source.GetPrimAtPath(spec["source_prim"])
        assert root.GetAttribute("physics:kinematicEnabled").Get() == source_root.GetAttribute(
            "physics:kinematicEnabled"
        ).Get()
        for relative in spec["mesh_paths"]:
            assert _mesh_hash(stage.GetPrimAtPath(str(root.GetPath()) + relative)) == _mesh_hash(
                source.GetPrimAtPath(spec["source_prim"] + relative)
            )
        manifest = json.loads((package / "evidence/manifest.json").read_text())
        assert manifest["overall_status"] == "candidate"
        assert manifest["claims"]["physics_parameters_unchanged"] is True
        assert manifest["claims"]["robot_policy_success"] is False
        assert manifest["forbidden_changes_detected"] == []


@pytest.mark.skipif(not SOURCE.is_file(), reason="Wangshuai source scene unavailable")
def test_liquid_overlay_preserves_exact_particle_arrays_and_internal_links(tmp_path: Path) -> None:
    from pxr import Usd

    result = build_asset_set(SOURCE, tmp_path / "set")
    package = result["packages"]["small_v2_liquid_seed_1948"]
    stage = Usd.Stage.Open(str(package / "asset.usda"))
    root = stage.GetDefaultPrim()
    particle_set = stage.GetPrimAtPath(str(root.GetPath()) + "/ParticleSet")
    system = stage.GetPrimAtPath(str(root.GetPath()) + "/ParticleSystem")
    sampler = stage.GetPrimAtPath(str(root.GetPath()) + "/Sampler")
    assert len(particle_set.GetAttribute("points").Get()) == 1948
    assert len(particle_set.GetAttribute("velocities").Get()) == 1948
    assert particle_set.GetRelationship("physxParticle:particleSystem").GetTargets() == [
        str(root.GetPath()) + "/ParticleSystem"
    ]
    assert sampler.GetRelationship("physxParticleSampling:particles").GetTargets() == [
        str(root.GetPath()) + "/ParticleSet"
    ]
    assert system.GetAttribute("maxVelocity").Get() == pytest.approx(0.1)
    assert system.GetAttribute("particleContactOffset").Get() == pytest.approx(0.002)
    assert system.GetAttribute("restOffset").Get() == pytest.approx(0.002)
    manifest = json.loads((package / "evidence/manifest.json").read_text())
    assert manifest["particle_count"] == 1948
    assert manifest["claims"]["physics_parameters_unchanged"] is True
    assert manifest["claims"]["contains_physics_scene"] is False


@pytest.mark.skipif(not SOURCE.is_file(), reason="Wangshuai source scene unavailable")
def test_material_dependencies_are_package_local_without_shader_parameter_changes(
    tmp_path: Path,
) -> None:
    from pxr import Usd, UsdShade

    result = build_asset_set(SOURCE, tmp_path / "set")
    for asset_id in (
        "tube15_threaded_liquid_ready",
        "tube15_threaded_closed_cap",
        "funnel_small_v2_liquid_ready",
    ):
        package = result["packages"][asset_id]
        stage = Usd.Stage.Open(str(package / "asset.usda"))
        source_assets = []
        for prim in stage.Traverse():
            if not prim.IsA(UsdShade.Shader):
                continue
            value = UsdShade.Shader(prim).GetSourceAsset("mdl")
            if value:
                source_assets.append(value.path)
        assert source_assets
        assert all(not Path(path).is_absolute() and ":/" not in path for path in source_assets)
        assert all((package / path).is_file() for path in source_assets)
    index = json.loads((tmp_path / "set/asset_set_manifest.json").read_text())
    assert index["source_sha256"] == sha256(SOURCE.read_bytes()).hexdigest()
    assert len(index["assets"]) == 4


def test_runtime_classifier_requires_particle_identity_capture_and_no_hard_errors() -> None:
    passed = classify_run(
        authored_particle_count=1948,
        runtime_particle_count=1948,
        captured_count=1900,
        below_floor_count=0,
        nonfinite_count=0,
        hard_errors=[],
    )
    assert passed["overall_status"] == "pass"
    assert passed["checks"]["tube_capture_ratio"] is True
    blocked = classify_run(
        authored_particle_count=1948,
        runtime_particle_count=1948,
        captured_count=1800,
        below_floor_count=0,
        nonfinite_count=0,
        hard_errors=[],
    )
    assert blocked["overall_status"] == "blocked"


@pytest.mark.skipif(not SOURCE.is_file(), reason="Wangshuai source scene unavailable")
def test_promotion_requires_source_and_three_hash_bound_recomposition_runs(
    tmp_path: Path,
) -> None:
    root = tmp_path / "set"
    build_asset_set(SOURCE, root)
    build_sha = sha256((root / "asset_set_manifest.json").read_bytes()).hexdigest()
    report = {
        "status": "pass",
        "source_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
        "asset_set_manifest_sha256": build_sha,
        "observations": {
            "authored_particle_count": 1948,
            "runtime_particle_count": 1948,
            "capture_ratio": 1.0,
            "below_floor_count": 0,
            "nonfinite_count": 0,
            "hard_errors": [],
        },
    }
    source = root / "evidence/source_baseline/report.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({**report, "mode": "source"}))
    for name in ("run_00", "run_01", "run_02"):
        path = root / f"evidence/recomposition/{name}/report.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({**report, "mode": "recomposed"}))
    receipt = promote(root)
    index = json.loads((root / "asset_set_manifest.json").read_text())
    assert receipt.is_file()
    assert index["status"] == "pass"
    assert index["claims"]["runtime_recomposition_qualified"] is True
    assert all(item["overall_status"] == "pass" for item in index["assets"])
