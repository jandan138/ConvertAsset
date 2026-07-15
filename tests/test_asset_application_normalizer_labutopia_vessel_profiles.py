"""Real-source admission tests for the LabUtopia pouring vessels."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.pipeline import normalize_asset


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/"
    "lab_001_localized_20260707/lab_001.usd"
)
SOURCE_SHA256 = "b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2"
RUNTIME_PYTHON = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/"
    "embodied-eval-os-isaacsim41-py310/bin/python"
)
ISAAC41_OMNIGLASS_SHA256 = (
    "d71555550deb30af245c0ec939c8647442df5709a2977549cad7f6ddcc8c1182"
)
SOURCE_OMNIGLASS_SHA256 = (
    "cd7c97781dc95f1694f9acc70c0b9ae327361a3b1c84abf917e55a9d672e627a"
)

VESSELS = (
    {
        "name": "conical_bottle03",
        "scope": "/World/conical_bottle03",
        "opening_y": 0.1965674179,
        "grasp_y": 0.16,
        "mass_kg": 0.25,
        "center_of_mass": [0.0, 0.075, 0.0],
        "inertia": [0.001874, 0.00214, 0.001874],
        "collider_strategy": "source_sdf",
    },
    {
        "name": "graduated_cylinder_03",
        "scope": "/World/graduated_cylinder_03",
        "opening_y": 0.2722941904,
        "grasp_y": 0.14,
        "mass_kg": 0.15,
        "center_of_mass": [0.0, 0.136, 0.0],
        "inertia": [0.001097, 0.000343, 0.001097],
        "collider_strategy": "open_top_compound_r3",
        "interaction_profile_filename": (
            "labutopia_lab001_graduated_cylinder_03_20260707.r3.interaction.json"
        ),
    },
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.skipif(
    os.environ.get("AAN_RUN_REAL_LABUTOPIA_VESSELS") != "1",
    reason="set AAN_RUN_REAL_LABUTOPIA_VESSELS=1 in the Isaac/PXR environment",
)
@pytest.mark.parametrize("spec", VESSELS, ids=lambda spec: spec["name"])
def test_real_labutopia_vessel_profiles_compile_static_packages(
    tmp_path: Path,
    spec: dict[str, object],
) -> None:
    assert SOURCE.is_file()
    assert _sha256(SOURCE) == SOURCE_SHA256
    assert RUNTIME_PYTHON.is_file()
    name = str(spec["name"])
    interaction_profile = (
        ROOT
        / "profiles"
        / "interaction"
        / str(
            spec.get(
                "interaction_profile_filename",
                f"labutopia_lab001_{name}_20260707.interaction.json",
            )
        )
    )
    physics_profile = (
        ROOT
        / "profiles"
        / "physics"
        / f"labutopia_lab001_{name}_20260707.provisional.json"
    )
    assert interaction_profile.is_file()
    assert physics_profile.is_file()

    interaction_payload = json.loads(interaction_profile.read_text(encoding="utf-8"))
    physics_payload = json.loads(physics_profile.read_text(encoding="utf-8"))
    assert interaction_payload["source_binding"]["sha256"] == SOURCE_SHA256
    assert interaction_payload["asset_entry_prim"] == spec["scope"]
    colliders = interaction_payload["colliders"]
    if spec["collider_strategy"] == "source_sdf":
        assert colliders == [
            {
                "relative_path": "mesh",
                "mode": "preserve",
                "purpose": ["gripper", "support", "containment"],
                "approximation": "sdf",
            }
        ]
    else:
        assert interaction_payload["revision"] == "r3"
        assert colliders[0] == {
            "relative_path": "mesh",
            "mode": "disable",
            "purpose": [],
        }
        authored = colliders[1:]
        assert len(authored) == 13
        assert authored[0]["relative_path"] == "__aan_collision_proxy/bottom"
        assert authored[0]["purpose"] == ["support", "containment"]
        assert authored[0]["geometry"] == {
            "type": "Cube",
            "size": 1.0,
            "translation_body_local_usd": [0.0, 0.003, 0.0],
            "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            "scale_body_local_usd": [0.1171587, 0.006, 0.1171587],
        }
        assert [item["relative_path"] for item in authored[1:]] == [
            f"__aan_collision_proxy/wall_{index:02d}" for index in range(12)
        ]
        assert all(
            item["mode"] == "author"
            and item["purpose"] == ["gripper", "containment"]
            and item["geometry"]["type"] == "Cube"
            and item["geometry"]["size"] == 1.0
            and item["geometry"]["scale_body_local_usd"]
            == [0.004, 0.2662941904, 0.0112]
            for item in authored[1:]
        )
        assert interaction_payload["grasp_cross_section"] == {
            "required": True,
            "frame": "grasp",
            "axis_body_local": [0.0, 1.0, 0.0],
            "sample_offsets_body_local_usd": [-0.01, 0.0, 0.01],
            "source_visual_mesh_relative_paths": ["mesh"],
            "closing_axis_body_local": [1.0, 0.0, 0.0],
            "expected_visual_width_m": 0.04701,
            "visual_width_tolerance_m": 0.001,
            "collision_visual_width_tolerance_m": 0.002,
            "max_gripper_opening_m": 0.088,
            "minimum_opening_clearance_m": 0.001,
            "claim_boundary": interaction_payload["grasp_cross_section"]["claim_boundary"],
        }
    assert interaction_payload["open_top"]["axis_body_local"] == [0.0, 1.0, 0.0]
    assert interaction_payload["named_frames"]["opening"][
        "translation_body_local_usd"
    ] == [0.0, spec["opening_y"], 0.0]
    assert interaction_payload["named_frames"]["grasp"][
        "translation_body_local_usd"
    ] == [0.0, spec["grasp_y"], 0.0]
    assert interaction_payload["named_frames"]["support"][
        "translation_body_local_usd"
    ] == [0.0, 0.0, 0.0]
    for frame in interaction_payload["named_frames"].values():
        assert frame["rotation_body_local_wxyz"] == [
            0.7071067811865476,
            -0.7071067811865475,
            0.0,
            0.0,
        ]
    mass_properties = physics_payload["scope_rules"][0]["body_rules"][0][
        "mass_properties"
    ]
    assert mass_properties["mass_kg"] == spec["mass_kg"]
    assert mass_properties["center_of_mass_body_local"] == spec["center_of_mass"]
    assert mass_properties["diagonal_inertia_kg_m2"] == spec["inertia"]

    out_dir = tmp_path / f"{name}_package"
    evidence_out = tmp_path / f"{name}_manifest.json"
    result = normalize_asset(
        NormalizeAssetRequest(
            source_usd=SOURCE,
            out_dir=out_dir,
            asset_id=f"LabUtopia_{name}",
            asset_class="rigid",
            asset_role="dynamic",
            source_runtime="isaac51",
            target_runtime="isaac41",
            target_benchmark="scenario-forge",
            task_id=f"ScenarioForge.{name}",
            required_prims=[str(spec["scope"])],
            asset_scope_prims=[str(spec["scope"])],
            gates=["static"],
            evidence_out=evidence_out,
            physics_profile=physics_profile,
            interaction_profile=interaction_profile,
            runtime_python=RUNTIME_PYTHON,
        )
    )

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    contract = manifest["interaction_contract"]
    extraction = manifest["dependency_closure"]["scope_extraction"]
    assert extraction["entry_reference_qualification"]["status"] == "pass"
    assert extraction["entry_reference_qualification"]["errors"] == []
    assert len(extraction["reference_scope_material_relocations"]) == 1
    relocation = extraction["reference_scope_material_relocations"][0]
    assert relocation["package_material_prim"].startswith(
        f"{spec['scope']}/__aan_materials/"
    )
    assert contract["status"] == "pass"
    assert contract["runtime_identity"]["active_rigid_body_prims"] == [spec["scope"]]
    contract_colliders = contract["collider_prims"]
    if spec["collider_strategy"] == "source_sdf":
        assert contract_colliders[0]["observed_approximation"] == "sdf"
    else:
        assert len(contract_colliders) == 14
        source_collider = next(
            item for item in contract_colliders if item["prim_path"].endswith("/mesh")
        )
        assert source_collider["mode"] == "disable"
        assert source_collider["collision_enabled"] is False
        assert all(
            item["collision_enabled"] is True
            and item["observed_approximation"] is None
            for item in contract_colliders
            if item is not source_collider
        )
    assert contract["open_top"]["status"] == "declared"
    assert contract["root_motion_gate"]["status"] == "not_run"
    assert manifest["physics_closure"]["profile_admission"]["status"] == "pass"
    assert (out_dir / "asset.usd").is_file()
    assert (out_dir / "interaction" / "profile.json").is_file()
    assert (out_dir / "physics" / "profile.json").is_file()
    assert _sha256(SOURCE) == SOURCE_SHA256

    if name == "graduated_cylinder_03":
        section = manifest["physics_closure"]["grasp_cross_section"]
        assert section["status"] == "pass"
        assert section["report_path"] == "interaction/grasp_cross_section.json"
        assert _sha256(out_dir / section["report_path"]) == section["report_sha256"]
        assert section["summary"] == {
            "support_colliders_intersect_grasp_band": [],
            "unsupported_active_collision_prims": [],
            "sample_count": 3,
            "sample_blocked_count": 0,
            "error_count": 0,
        }
        for sample in section["samples"]:
            assert sample["source_visual"]["max_in_plane_width_m"] == pytest.approx(
                0.04700993, abs=1.0e-6
            )
            assert sample["collision"]["closing_axis_width_m"] == pytest.approx(
                0.04701, abs=1.0e-6
            )
            assert sample["collision"]["max_in_plane_width_m"] < 0.049
            assert sample["checks"]["collision_within_max_gripper_opening"] is True
        assert next(
            gate
            for gate in manifest["stage_gates"]
            if gate["check_id"] == "AAN-05G-grasp-cross-section"
        )["status"] == "pass"

    Sdf = pytest.importorskip("pxr.Sdf")
    Usd = pytest.importorskip("pxr.Usd")
    UsdShade = pytest.importorskip("pxr.UsdShade")
    consumer = Usd.Stage.CreateInMemory()
    probe_path = Sdf.Path(f"/ReferenceProbe/{name}")
    probe = consumer.DefinePrim(probe_path, "Xform")
    assert probe.GetReferences().AddReference(
        str((out_dir / "asset.usd").resolve()),
        str(spec["scope"]),
    )
    mesh = consumer.GetPrimAtPath(probe_path.AppendChild("mesh"))
    material, _ = UsdShade.MaterialBindingAPI(mesh).ComputeBoundMaterial()
    assert material and material.GetPrim().IsValid()
    assert material.GetPath().HasPrefix(probe_path)

    if name == "graduated_cylinder_03":
        package_mdl = out_dir / "deps" / "mdl" / "OmniGlass.mdl"
        preserved_source_mdl = (
            out_dir / "deps" / "mdl_source" / "OmniGlass.mdl"
        )
        assert _sha256(package_mdl) == ISAAC41_OMNIGLASS_SHA256
        assert _sha256(preserved_source_mdl) == SOURCE_OMNIGLASS_SHA256
        assert relocation == {
            "source_material_prim": "/World/Looks/OmniGlass",
            "package_material_prim": (
                "/World/graduated_cylinder_03/__aan_materials/OmniGlass"
            ),
            "method": "Usd.NamespaceEditor.MovePrimAtPath",
        }
        material_record = manifest["material_closure"][0]
        assert material_record["source_material_prim"] == "/World/Looks/OmniGlass"
        assert material_record["package_material_prim"] == relocation[
            "package_material_prim"
        ]
        assert len(material_record["source_mdl_assets"]) == 1
        assert material_record["source_mdl_assets"][0][
            "package_sha256"
        ] == ISAAC41_OMNIGLASS_SHA256
        shaders = [
            prim
            for prim in Usd.PrimRange(material.GetPrim())
            if prim.GetTypeName() == "Shader"
        ]
        assert len(shaders) == 1
        source_asset = shaders[0].GetAttribute("info:mdl:sourceAsset").Get()
        assert source_asset
        assert Path(source_asset.resolvedPath).resolve() == package_mdl.resolve()
        assert _sha256(Path(source_asset.resolvedPath)) == ISAAC41_OMNIGLASS_SHA256


@pytest.mark.skipif(
    os.environ.get("AAN_RUN_REAL_LABUTOPIA_VESSELS") != "1",
    reason="set AAN_RUN_REAL_LABUTOPIA_VESSELS=1 in the Isaac/PXR environment",
)
def test_real_graduated_cylinder_r2_proxy_is_rejected_by_the_generic_grasp_section_gate(
    tmp_path: Path,
) -> None:
    """Exercise the real r2 profile geometry, not a synthetic wide-wall stand-in."""

    assert SOURCE.is_file()
    assert _sha256(SOURCE) == SOURCE_SHA256
    r2_profile = ROOT / "profiles" / "interaction" / (
        "labutopia_lab001_graduated_cylinder_03_20260707.interaction.json"
    )
    r3_profile = ROOT / "profiles" / "interaction" / (
        "labutopia_lab001_graduated_cylinder_03_20260707.r3.interaction.json"
    )
    physics_profile = ROOT / "profiles" / "physics" / (
        "labutopia_lab001_graduated_cylinder_03_20260707.provisional.json"
    )
    r2_payload = json.loads(r2_profile.read_text(encoding="utf-8"))
    r2_payload["revision"] = "r2-grasp-section-regression"
    r2_payload["grasp_cross_section"] = json.loads(
        r3_profile.read_text(encoding="utf-8")
    )["grasp_cross_section"]
    injected_profile = tmp_path / "r2-with-grasp-section.json"
    injected_profile.write_text(json.dumps(r2_payload, indent=2), encoding="utf-8")
    out_dir = tmp_path / "r2_package"
    manifest_path = tmp_path / "r2_manifest.json"

    result = normalize_asset(
        NormalizeAssetRequest(
            source_usd=SOURCE,
            out_dir=out_dir,
            asset_id="LabUtopia_graduated_cylinder_03_r2_regression",
            asset_class="rigid",
            asset_role="dynamic",
            source_runtime="isaac51",
            target_runtime="isaac41",
            target_benchmark="scenario-forge",
            task_id="ScenarioForge.graduated_cylinder_03.r2_regression",
            required_prims=["/World/graduated_cylinder_03"],
            asset_scope_prims=["/World/graduated_cylinder_03"],
            gates=["static"],
            evidence_out=manifest_path,
            physics_profile=physics_profile,
            interaction_profile=injected_profile,
            runtime_python=RUNTIME_PYTHON,
        )
    )

    assert result.return_code == 5
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    section = manifest["physics_closure"]["grasp_cross_section"]
    assert section["status"] == "blocked"
    assert section["summary"]["support_colliders_intersect_grasp_band"] == []
    for sample in section["samples"]:
        assert sample["source_visual"]["max_in_plane_width_m"] == pytest.approx(
            0.04700993, abs=1.0e-6
        )
        assert sample["collision"]["closing_axis_width_m"] == pytest.approx(
            0.115, abs=1.0e-6
        )
        assert sample["collision"]["max_in_plane_width_m"] > 0.118
        assert sample["checks"]["collision_matches_visual"] is False
        assert sample["checks"]["collision_within_max_gripper_opening"] is False
    assert next(
        gate
        for gate in manifest["stage_gates"]
        if gate["check_id"] == "AAN-05G-grasp-cross-section"
    )["status"] == "blocked"
    assert _sha256(SOURCE) == SOURCE_SHA256
