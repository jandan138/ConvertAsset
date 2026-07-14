"""Regression coverage for AAN physics admission and visual-static roles."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import normalize_asset


def _request(
    source: Path,
    out_dir: Path,
    evidence_out: Path,
    *,
    asset_class: str = "rigid",
    asset_role: str = "dynamic",
    target_benchmark: str = "ebench-lift2",
    scope: list[str] | None = None,
) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=source,
        out_dir=out_dir,
        asset_id="physics-admission-fixture",
        asset_class=asset_class,
        asset_role=asset_role,
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark=target_benchmark,
        task_id="AAN.PhysicsAdmission",
        required_prims=["/World/Asset"],
        asset_scope_prims=scope or ["/World/Asset"],
        gates=["static"],
        evidence_out=evidence_out,
    )


def _visual_static_usda() -> str:
    return """#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Xform "Asset" (
        prepend apiSchemas = ["PhysicsArticulationRootAPI", "PhysxArticulationAPI"]
    )
    {
        double3 xformOp:translate = (3, 4, 5)
        uniform token[] xformOpOrder = ["xformOp:translate"]
        def Mesh "Mesh" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsCollisionAPI", "PhysicsMassAPI", "PhysicsMeshCollisionAPI", "PhysxRigidBodyAPI"]
        )
        {
            rel material:binding = </Looks/Mat>
            bool physics:rigidBodyEnabled = 1
            bool physics:collisionEnabled = 1
            float physics:mass = 0
            float3 physics:diagonalInertia = (0, 0, 0)
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
            int[] faceVertexCounts = [3]
            int[] faceVertexIndices = [0, 1, 2]
        }
        def PhysicsFixedJoint "FixedJoint"
        {
            bool physics:jointEnabled = 1
        }
    }
}
def Scope "Looks"
{
    def Material "Mat"
    {
    }
}
"""


def _authored_mass_missing_inertia_usda() -> str:
    return """#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Mesh "Asset" (
        prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsCollisionAPI", "PhysicsMassAPI"]
    )
    {
        bool physics:rigidBodyEnabled = 1
        bool physics:collisionEnabled = 1
        float physics:mass = 7
        point3f[] points = [(0, 0, 0), (4, 0, 0), (0, 3, 0), (0, 0, 5)]
        int[] faceVertexCounts = [3, 3, 3, 3]
        int[] faceVertexIndices = [0, 1, 2, 0, 1, 3, 0, 2, 3, 1, 2, 3]
    }
}
"""


def _visual_static_scope_extraction_usda() -> str:
    return """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "World"
{
    double3 xformOp:translate = (10, 0, 0)
    uniform token[] xformOpOrder = ["xformOp:translate"]
    def Xform "Asset"
    {
        rel material:binding = </World/Looks/Keep>
        def Mesh "Mesh"
        {
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
            int[] faceVertexCounts = [3]
            int[] faceVertexIndices = [0, 1, 2]
        }
    }
    def Xform "Unrelated"
    {
        def Mesh "Mesh"
        {
            rel material:binding = </World/Looks/Drop>
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
            int[] faceVertexCounts = [3]
            int[] faceVertexIndices = [0, 1, 2]
        }
    }
    def Scope "Looks"
    {
        def Material "Keep" {}
        def Material "Drop" {}
    }
}
"""


def test_visual_static_separates_raw_physics_failure_from_output_admission(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_visual_static_usda(), encoding="utf-8")
    original_sha = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(
            source,
            out_dir,
            evidence_out,
            asset_class="articulated",
            asset_role="visual_static",
            target_benchmark="scenario-forge",
        )
    )

    assert result.return_code == 0
    assert __import__("hashlib").sha256(source.read_bytes()).hexdigest() == original_sha
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    package_manifest = out_dir / "evidence" / "manifest.json"
    assert package_manifest.is_file()
    assert json.loads(package_manifest.read_text(encoding="utf-8")) == manifest
    assert manifest["asset_role"] == "visual_static"
    assert manifest["entrypoints"] == {
        "root_usd": "asset.usd",
        "default_prim": "World",
        "asset_entry_prim": "/World/Asset",
        "asset_scope_prims": ["/World/Asset"],
        "consumer_profile": "scenario-forge",
        "task_config": None,
        "required_prims": None,
        "metric_evaluator": None,
    }
    assert manifest["source_integrity"]["unchanged"] is True
    assert manifest["source_physics_audit"]["status"] == "blocked"
    assert manifest["source_physics_audit"]["summary"]["invalid_rigid_body_count"] == 1
    assert manifest["output_role_admission"]["status"] == "pass"
    assert manifest["output_role_admission"]["summary"] == {
        "active_articulation_root_count": 0,
        "active_collision_count": 0,
        "active_joint_count": 0,
        "active_rigid_body_count": 0,
    }
    visual = manifest["visual_preservation_fingerprint"]
    assert visual["raw_source"]["signature"] == visual["package_before_role"]["signature"]
    assert visual["package_before_role"]["signature"] == visual["package_after_role"]["signature"]

    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    asset = stage.GetPrimAtPath("/World/Asset")
    mesh = stage.GetPrimAtPath("/World/Asset/Mesh")
    joint = stage.GetPrimAtPath("/World/Asset/FixedJoint")
    assert asset.GetAttribute("xformOp:translate").Get() == (3.0, 4.0, 5.0)
    assert mesh.GetRelationship("material:binding").GetTargets() == ["/Looks/Mat"]
    assert not any(
        token.startswith(("Physics", "Physx")) for token in asset.GetAppliedSchemas()
    )
    assert not any(
        token.startswith(("Physics", "Physx")) for token in mesh.GetAppliedSchemas()
    )
    assert not joint.IsActive()


def test_visual_static_extracts_declared_scope_and_bound_materials(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_visual_static_scope_extraction_usda(), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(
            source,
            out_dir,
            evidence_out,
            asset_class="auto",
            asset_role="visual_static",
            target_benchmark="scenario-forge",
        )
    )

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    extraction = manifest["static_usd_report"]["scope_extraction"]
    assert extraction["status"] == "pass"
    assert extraction["scope_prims"] == ["/World/Asset"]
    assert extraction["retained_material_prims"] == ["/World/Looks/Keep"]

    Usd = pytest.importorskip("pxr.Usd")
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    UsdShade = pytest.importorskip("pxr.UsdShade")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    assert stage.GetPrimAtPath("/World/Asset").IsValid()
    assert not stage.GetPrimAtPath("/World/Unrelated").IsValid()
    assert stage.GetPrimAtPath("/World/Looks/Keep").IsValid()
    assert not stage.GetPrimAtPath("/World/Looks/Drop").IsValid()
    mesh = stage.GetPrimAtPath("/World/Asset/Mesh")
    material, _ = UsdShade.MaterialBindingAPI(mesh).ComputeBoundMaterial()
    assert material.GetPath().pathString == "/World/Looks/Keep"
    world = stage.GetPrimAtPath("/World")
    transform = UsdGeom.Xformable(world).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    assert transform[3][0] == 10.0


def test_dynamic_role_derives_missing_inertia_from_authored_mass(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_authored_mass_missing_inertia_usda(), encoding="utf-8")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(_request(source, out_dir, evidence_out))

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    mass_record = manifest["physics_closure"]["mass_properties"][0]
    assert mass_record["mass"]["value"] == 7.0
    assert mass_record["mass"]["value_source"] == "authored"
    assert mass_record["inertia"]["value_source"] == "derived"
    assert mass_record["inertia"]["mass_basis"] == {
        "attribute": "/World/Asset.physics:mass",
        "source": "authored",
        "value": 7.0,
        "raw_value": 7.0,
    }
    assert mass_record["center_of_mass"]["value_source"] == "derived"
    assert mass_record["principal_axes"]["value_source"] == "derived"
    assert manifest["physics_closure"]["summary"]["invalid_rigid_body_count"] == 0


def test_dynamic_auto_class_blocks_incomplete_template_provenance(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
    def Mesh "Asset" (
        prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsCollisionAPI", "PhysicsMassAPI"]
    )
    {
        bool physics:rigidBodyEnabled = 1
        bool physics:collisionEnabled = 1
        float physics:mass = 2
        float3 physics:diagonalInertia = (1, 1, 1)
        point3f physics:centerOfMass = (0, 0, 0)
        quatf physics:principalAxes = (1, 0, 0, 0)
        point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        int[] faceVertexCounts = [3]
        int[] faceVertexIndices = [0, 1, 2]
    }
}
""",
        encoding="utf-8",
    )
    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(source))
    stage.GetPrimAtPath("/World/Asset").GetAttribute("physics:mass").SetCustomDataByKey(
        "aan:provenance", json.dumps({"value_source": "template"})
    )
    stage.GetRootLayer().Save()
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, out_dir, evidence_out, asset_class="auto")
    )

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    mass_record = manifest["physics_closure"]["mass_properties"][0]
    assert mass_record["status"] == "blocked"
    assert mass_record["mass"]["provenance_status"] == "invalid"
    assert manifest["physics_closure"]["summary"]["invalid_rigid_body_count"] == 1


def test_physx_warning_parser_blocks_only_boundary_safe_scoped_matches() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        evaluate_physx_warning_scope,
        parse_physx_warning_events,
    )

    text = "\n".join(
        [
            "[Warning] [omni.physx.plugin] The rigid body at /World/Room/DryingBox_03/handle/mesh has a possibly invalid inertia tensor and a negative mass, small sphere approximated inertia was used.",
            "[Warning] [omni.physx.plugin] The rigid body at /World/Room/DryingBox_030/handle/mesh has a negative mass.",
        ]
    )

    events = parse_physx_warning_events(text, stream="stdout")
    gate = evaluate_physx_warning_scope(events, ["/World/Room/DryingBox_03"])

    assert gate["status"] == "blocked"
    assert gate["summary"]["scoped_event_count"] == 1
    assert gate["summary"]["out_of_scope_event_count"] == 1
    assert gate["summary"]["by_category"] == {
        "invalid_inertia": 1,
        "negative_mass": 1,
        "small_sphere_approximated_inertia": 1,
    }


def test_physx_warning_scope_rejects_empty_or_overlapping_scope_mappings() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        evaluate_physx_warning_scope,
        parse_physx_warning_events,
    )

    events = parse_physx_warning_events(
        "rigid body at /World/A/Child/mesh has a negative mass", stream="stdout"
    )

    assert evaluate_physx_warning_scope(events, [])["status"] == "blocked"
    overlapping = evaluate_physx_warning_scope(events, ["/World/A", "/World/A/Child"])
    assert overlapping["status"] == "blocked"
    assert "disjoint" in overlapping["scope_validation"]["errors"][0]


def test_explicit_runtime_runner_strips_parent_kit_environment(tmp_path: Path) -> None:
    """A 4.1 Python must not inherit a 4.5 Kit bootstrap from its parent."""
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        runtime_subprocess_environment,
    )

    prefix = tmp_path / "isaac41"
    runner = prefix / "bin" / "python"
    runner.parent.mkdir(parents=True)
    runner.touch()
    cuda_dir = prefix / "lib" / "python3.10" / "site-packages" / "nvidia" / "cuda_runtime" / "lib"
    torch_dir = prefix / "lib" / "python3.10" / "site-packages" / "torch" / "lib"
    cuda_dir.mkdir(parents=True)
    torch_dir.mkdir(parents=True)

    environment, policy = runtime_subprocess_environment(
        runner,
        explicit_runner=True,
        parent_environment={
            "ISAAC_SIM_ROOT": "/isaac-sim",
            "CARB_APP_PATH": "/isaac-sim/kit",
            "EXP_PATH": "/isaac-sim/apps",
            "PYTHONPATH": "/isaac-sim/kit/python",
            "PYTHONHOME": "/isaac-sim/kit/python",
            "LD_LIBRARY_PATH": "/isaac-sim/kit/lib:/usr/lib",
        },
    )

    for key in ("ISAAC_SIM_ROOT", "CARB_APP_PATH", "EXP_PATH", "PYTHONPATH", "PYTHONHOME"):
        assert key not in environment
    assert "/isaac-sim" not in environment["LD_LIBRARY_PATH"]
    assert str(cuda_dir) in environment["LD_LIBRARY_PATH"]
    assert str(torch_dir) in environment["LD_LIBRARY_PATH"]
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["ACCEPT_EULA"] == "Y"
    assert policy["status"] == "pass"
    assert policy["isolated_explicit_runtime_environment"] is True


def test_runtime_shutdown_clears_world_instance_before_closing_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Kit teardown must release World callbacks before plugin unload."""
    from convert_asset.asset_application_normalizer import runtime_smoke

    calls: list[str] = []
    monkeypatch.setattr(
        runtime_smoke,
        "_write_report",
        lambda _path, _report: calls.append("write"),
    )

    class FakeWorld:
        def clear_instance(self) -> None:
            calls.append("clear_instance")

    class FakeApp:
        def close(self) -> None:
            calls.append("close")

    report = {"status": "pass"}
    runtime_smoke._close_simulation_app_with_report(
        FakeApp(),
        tmp_path / "report.json",
        report,
        world=FakeWorld(),
    )

    assert calls == ["write", "clear_instance", "write", "close"]
    assert report["shutdown_cleanup"] == {
        "status": "pass",
        "method": "world.clear_instance",
    }


def test_isolated_runtime_worker_exit_uses_os_cleanup_after_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pass report can avoid the known native Kit plugin-unload crash."""
    from convert_asset.asset_application_normalizer import runtime_smoke

    calls: list[str] = []

    class FakeWorld:
        def clear_instance(self) -> None:
            calls.append("clear_instance")

    report = {"status": "pass"}
    runtime_smoke._prepare_isolated_worker_exit(report, world=FakeWorld())

    assert calls == ["clear_instance"]
    assert report["shutdown_cleanup"]["status"] == "pass"
    assert report["process_exit"] == {
        "policy": "os_exit_after_evidence",
        "simulation_app_close": "not_called",
        "reason": "isolated_worker_avoids_isaac41_native_plugin_unload_crash",
    }


def test_runtime_worker_uses_declared_asset_scope_not_unrelated_required_prim(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Runtime cold-load/step/reset evidence must use the package role scope."""
    from convert_asset.asset_application_normalizer import runtime_smoke
    from convert_asset.asset_application_normalizer.package_layout import TargetPackageLayout

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir(parents=True)
    layout.root_usd.write_text("#usda 1.0\n", encoding="utf-8")
    request = NormalizeAssetRequest(
        source_usd=tmp_path / "source.usda",
        out_dir=layout.root,
        asset_id="scope-worker-fixture",
        asset_class="auto",
        asset_role="visual_static",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="AAN.RuntimeScope",
        required_prims=["/World/UnrelatedRequiredPrim"],
        asset_scope_prims=["/World/OwnedPackageScope"],
        runtime_python=Path(sys.executable),
    )
    captured: dict[str, list[str]] = {}

    def fake_run(argv, **_kwargs):
        captured["argv"] = list(argv)
        report_path = Path(argv[argv.index("--report-out") + 1])
        run_id = argv[argv.index("--run-id") + 1]
        root_usd_sha256 = argv[argv.index("--expected-root-usd-sha256") + 1]
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "run_id": run_id,
                    "root_usd_sha256": root_usd_sha256,
                    "expected_root_usd_sha256": root_usd_sha256,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runtime_smoke.subprocess, "run", fake_run)

    result = runtime_smoke.build_runtime_smoke(layout, request)

    argv = captured["argv"]
    prim_values = [argv[index + 1] for index, value in enumerate(argv) if value == "--required-prim"]
    scope_values = [argv[index + 1] for index, value in enumerate(argv) if value == "--asset-scope-prim"]
    assert prim_values == ["/World/UnrelatedRequiredPrim"]
    assert scope_values == ["/World/OwnedPackageScope"]
    assert argv[argv.index("--process-exit-policy") + 1] == "os-exit"
    assert argv[argv.index("--render-steps") + 1] == "4"
    assert result.overall_status == "pass"


def test_runtime_gate_rejects_a_stale_worker_report(tmp_path: Path) -> None:
    """An exit-zero executable cannot reuse evidence from a prior worker run."""
    from convert_asset.asset_application_normalizer import runtime_smoke
    from convert_asset.asset_application_normalizer.package_layout import TargetPackageLayout

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir(parents=True)
    layout.root_usd.write_text("#usda 1.0\n", encoding="utf-8")
    stale_report = layout.root / "evidence" / "runtime_smoke" / "report.json"
    stale_report.parent.mkdir(parents=True)
    stale_report.write_text('{"status": "pass"}\n', encoding="utf-8")
    request = NormalizeAssetRequest(
        source_usd=tmp_path / "source.usda",
        out_dir=layout.root,
        asset_id="stale-report-fixture",
        asset_class="auto",
        asset_role="visual_static",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="AAN.RuntimeStaleReport",
        required_prims=["/World/Asset"],
        asset_scope_prims=["/World/Asset"],
        runtime_python=Path("/bin/true"),
    )

    result = runtime_smoke.build_runtime_smoke(layout, request)

    assert result.overall_status == "blocked"
    assert result.return_code == 5
    assert result.runtime_evidence["cold_load"]["reason"] == (
        "runtime worker did not write a report JSON"
    )
    persisted = json.loads(stale_report.read_text(encoding="utf-8"))
    assert persisted["status"] == "blocked"
    assert persisted["cold_load"]["reason"] == "runtime worker did not write a report JSON"


def test_reset_gate_compares_pre_warmup_initial_state() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import _build_reset_gate

    initial = {"/World/Asset": [[0.0] * 4 for _ in range(4)]}
    post_warmup_pre_step = {"/World/Asset": [[2.0] * 4 for _ in range(4)]}
    reset = {"/World/Asset": [[0.0] * 4 for _ in range(4)]}

    gate = _build_reset_gate(initial, reset, pre_step=post_warmup_pre_step)

    assert gate["status"] == "pass"
    assert gate["max_abs_delta_from_initial"] == 0.0
    assert gate["max_abs_delta_from_pre_step"] == 2.0


def test_runtime_smoke_uses_authored_support_and_detects_sdf_gpu_requirement() -> None:
    from convert_asset.asset_application_normalizer.runtime_smoke import (
        _runtime_support_surface,
        _stage_requires_gpu_dynamics,
    )

    Gf = pytest.importorskip("pxr.Gf")
    Usd = pytest.importorskip("pxr.Usd")
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    UsdPhysics = pytest.importorskip("pxr.UsdPhysics")
    stage = Usd.Stage.CreateInMemory()
    asset = UsdGeom.Xform.Define(stage, "/World/Asset")
    asset.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 3.0))
    support = UsdGeom.Xform.Define(stage, "/World/Asset/__aan_frame_support")
    support.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.25))
    collider = UsdGeom.Mesh.Define(stage, "/World/Asset/collider")
    UsdPhysics.CollisionAPI.Apply(collider.GetPrim())
    UsdPhysics.MeshCollisionAPI.Apply(collider.GetPrim()).CreateApproximationAttr(
        "sdf"
    )

    surface = _runtime_support_surface(stage, ["/World/Asset"])

    assert surface == {
        "z_position_stage_units": pytest.approx(2.75),
        "method": "interaction_support_frame",
        "frame_paths": ["/World/Asset/__aan_frame_support"],
    }
    assert _stage_requires_gpu_dynamics(stage, ["/World/Asset"]) is True


def test_scoped_snapshot_rewrites_package_absolute_asset_paths(tmp_path: Path) -> None:
    from convert_asset.asset_application_normalizer.usd_closure import (
        rewrite_scoped_snapshot_asset_paths,
    )

    package = tmp_path / "package"
    scoped = package / "deps" / "usd" / "scoped_source.usda"
    mdl = package / "deps" / "mdl" / "keep.mdl"
    scoped.parent.mkdir(parents=True)
    mdl.parent.mkdir(parents=True)
    mdl.write_text("mdl 1.0;\n", encoding="utf-8")
    scoped.write_text(
        f'#usda 1.0\ndef Scope "Looks" {{ asset source = @{mdl}@ }}\n',
        encoding="utf-8",
    )

    report = rewrite_scoped_snapshot_asset_paths(package, scoped)

    assert report["status"] == "pass"
    assert report["rewrite_count"] == 1
    assert "@../mdl/keep.mdl@" in scoped.read_text(encoding="utf-8")
    assert str(package) not in scoped.read_text(encoding="utf-8")


@pytest.mark.skipif(
    os.environ.get("AAN_RUN_REAL_DRYINGBOX_FAMILY") != "1",
    reason="set AAN_RUN_REAL_DRYINGBOX_FAMILY=1 in the Isaac/PXR environment",
)
def test_real_dryingbox_family_raw_physics_audit() -> None:
    from convert_asset.asset_application_normalizer.physics_checks import audit_source_physics

    source = Path(
        "/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/"
        "lab_001_localized_20260707/lab_001.usd"
    )
    audit = audit_source_physics(
        source,
        [f"/World/DryingBox_{number:02d}" for number in range(1, 5)],
    )

    assert audit["source_sha256"] == "b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2"
    assert audit["status"] == "blocked"
    by_scope = {item["scope"]: item for item in audit["family_members"]}
    assert by_scope["/World/DryingBox_02"]["summary"]["invalid_rigid_body_count"] == 3
    assert by_scope["/World/DryingBox_03"]["summary"]["invalid_rigid_body_count"] == 3
    assert by_scope["/World/DryingBox_04"]["summary"]["invalid_rigid_body_count"] == 4
