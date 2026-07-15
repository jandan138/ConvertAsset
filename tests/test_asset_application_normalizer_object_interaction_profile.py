"""TDD coverage for package-owned object interaction normalization."""

from __future__ import annotations

from dataclasses import replace
import argparse
import hashlib
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.model import NormalizeAssetRequest
from convert_asset.asset_application_normalizer.cli import (
    add_normalize_asset_parser,
    request_from_args,
)
from convert_asset.asset_application_normalizer.pipeline import normalize_asset


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_usda() -> str:
    return """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    timeCodesPerSecond = 60
    framesPerSecond = 24
)
def Xform "World"
{
    def Xform "Asset"
    {
        def Mesh "Body" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsCollisionAPI", "PhysicsMassAPI"]
        )
        {
            bool physics:rigidBodyEnabled = 1
            bool physics:collisionEnabled = 1
            float physics:mass = 0
            float3 physics:diagonalInertia = (0, 0, 0)
            point3f physics:centerOfMass = (-inf, -inf, -inf)
            quatf physics:principalAxes = (0, 0, 0, 0)
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
            int[] faceVertexCounts = [3, 3, 3, 3]
            int[] faceVertexIndices = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
        }
        def Mesh "Shell"
        {
            point3f[] points = [(0, 0, 0), (2, 0, 0), (0, 2, 0), (0, 0, 2)]
            int[] faceVertexCounts = [3, 3, 3, 3]
            int[] faceVertexIndices = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
        }
    }
}
"""


def _source_usda_with_external_materials(
    *,
    reserved_material_scope: bool = False,
    external_shader_connection: bool = False,
    duplicate_material_leaf: bool = False,
) -> str:
    reserved_scope = (
        '        def Scope "__aan_materials" {}\n'
        if reserved_material_scope
        else ""
    )
    all_material_shader = (
        """
            token outputs:surface.connect = </World/SharedShader.outputs:surface>
"""
        if external_shader_connection
        else """
            token outputs:surface.connect = </World/Looks/GlassAll/Shader.outputs:surface>
            def Shader "Shader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.2, 0.4, 0.8)
                token outputs:surface
            }
"""
    )
    external_shader = (
        """
    def Shader "SharedShader"
    {
        uniform token info:id = "UsdPreviewSurface"
        color3f inputs:diffuseColor = (0.2, 0.4, 0.8)
        token outputs:surface
    }
"""
        if external_shader_connection
        else ""
    )
    source = (
        """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    timeCodesPerSecond = 60
    framesPerSecond = 24
)
def Xform "World"
{
    def Xform "Asset"
    {
%s        def Mesh "Body" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsCollisionAPI", "PhysicsMassAPI", "MaterialBindingAPI"]
        )
        {
            rel material:binding = </World/Looks/GlassAll>
            rel material:binding:preview = </World/Looks/GlassPreview>
            bool physics:rigidBodyEnabled = 1
            bool physics:collisionEnabled = 1
            float physics:mass = 0
            float3 physics:diagonalInertia = (0, 0, 0)
            point3f physics:centerOfMass = (-inf, -inf, -inf)
            quatf physics:principalAxes = (0, 0, 0, 0)
            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
            int[] faceVertexCounts = [3, 3, 3, 3]
            int[] faceVertexIndices = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
            def GeomSubset "PaintedFaces" (
                prepend apiSchemas = ["MaterialBindingAPI"]
            )
            {
                uniform token elementType = "face"
                uniform token familyName = "materialBind"
                int[] indices = [0]
                rel material:binding = </World/Looks/GlassSubset>
            }
        }
        def Mesh "Shell"
        {
            point3f[] points = [(0, 0, 0), (2, 0, 0), (0, 2, 0), (0, 0, 2)]
            int[] faceVertexCounts = [3, 3, 3, 3]
            int[] faceVertexIndices = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]
        }
    }
    def Scope "Looks"
    {
        def Material "GlassAll"
        {%s        }
        def Material "GlassPreview"
        {
            token outputs:surface.connect = </World/Looks/GlassPreview/Shader.outputs:surface>
            def Shader "Shader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.3, 0.5, 0.9)
                token outputs:surface
            }
        }
        def Material "GlassSubset"
        {
            token outputs:surface.connect = </World/Looks/GlassSubset/Shader.outputs:surface>
            def Shader "Shader"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.8, 0.4, 0.2)
                token outputs:surface
            }
        }
    }
%s}
"""
        % (reserved_scope, all_material_shader, external_shader)
    )
    if duplicate_material_leaf:
        source = source.replace(
            '        def Mesh "Shell"\n        {\n',
            '        def Mesh "Shell" (\n'
            '            prepend apiSchemas = ["MaterialBindingAPI"]\n'
            '        )\n'
            '        {\n'
            '            rel material:binding = </World/OtherLooks/GlassAll>\n',
        )
        world_close = source.rfind("\n}\n")
        source = (
            source[:world_close]
            + """
    def Scope "OtherLooks"
    {
        def Material "GlassAll"
        {
            token outputs:surface.connect = </World/OtherLooks/GlassAll/Shader.outputs:surface>
            def Shader "Shader"
            {
                uniform token info:id = "UsdPreviewSurface"
                token outputs:surface
            }
        }
    }
"""
            + source[world_close:]
        )
    return source


def _interaction_profile(source: Path, path: Path) -> Path:
    payload = {
        "schema_version": "aan.object_interaction_profile.v1",
        "profile_id": "tests.object-interaction",
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
        "asset_entry_prim": "/World/Asset",
        "rigid_root": {
            "motion_role": "dynamic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": [
            {
                "relative_path": "Body",
                "mode": "preserve",
                "purpose": ["gripper", "support"],
                "approximation": "sdf",
            },
            {
                "relative_path": "Shell",
                "mode": "author",
                "purpose": ["gripper"],
            },
        ],
        "open_top": {
            "required": True,
            "axis_body_local": [0.0, 0.0, 1.0],
            "aperture_frame": "opening",
            "evidence": {
                "status": "declared",
                "method": "profile_geometry_intent",
                "claim_boundary": "Static authoring does not prove an open runtime collision aperture.",
            },
        },
        "named_frames": {
            "opening": {
                "translation_body_local_usd": [0.0, 0.0, 1.0],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
            "grasp": {
                "translation_body_local_usd": [0.0, 0.0, 0.5],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
            "support": {
                "translation_body_local_usd": [0.0, 0.0, 0.0],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
        },
        "runtime_gates": {
            "root_motion": {"required": True, "min_translation_m": 0.05},
            "stable_support": {"required": True},
            "gripper_collision": {"required": True},
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _physics_profile(source: Path, path: Path) -> Path:
    payload = {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "tests.root-mass",
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
            "claim_boundary": "Fixture mass is not a measurement.",
            "replacement_contract": "Replace the complete source-bound bundle in a new revision.",
        },
        "scope_rules": [
            {
                "scope_path": "/World/Asset",
                "body_rules": [
                    {
                        "relative_path": ".",
                        "motion_role": "dynamic",
                        "clear_density": True,
                        "mass_properties": {
                            "mode": "explicit",
                            "quality_tier": "provisional_geometry",
                            "mass_kg": 1.5,
                            "diagonal_inertia_kg_m2": [0.2, 0.3, 0.4],
                            "center_of_mass_body_local": [0.0, 0.0, 0.4],
                            "principal_axes": [1.0, 0.0, 0.0, 0.0],
                        },
                    }
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _request(
    source: Path,
    out_dir: Path,
    evidence_out: Path,
    physics_profile: Path,
    interaction_profile: Path,
) -> NormalizeAssetRequest:
    return NormalizeAssetRequest(
        source_usd=source,
        out_dir=out_dir,
        asset_id="interaction-fixture",
        asset_class="rigid",
        asset_role="dynamic",
        source_runtime="isaac51",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="AAN.ObjectInteraction",
        required_prims=["/World/Asset"],
        asset_scope_prims=["/World/Asset"],
        gates=["static"],
        evidence_out=evidence_out,
        physics_profile=physics_profile,
        interaction_profile=interaction_profile,
    )


def test_interaction_profile_runs_before_mass_profile_and_compiles_runtime_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    physics = _physics_profile(source, tmp_path / "physics.json")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, out_dir, evidence_out, physics, interaction)
    )

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    contract = manifest["interaction_contract"]
    assert contract["schema_version"] == "aan.interaction_contract.v1"
    assert contract["status"] == "pass"
    assert contract["asset_entry_prim"] == "/World/Asset"
    assert contract["runtime_identity"] == {
        "rigid_root_prim": "/World/Asset",
        "exactly_one_active_rigid_body": True,
        "active_rigid_body_prims": ["/World/Asset"],
    }
    assert contract["disabled_source_rigid_bodies"] == [
        {
            "prim_path": "/World/Asset/Body",
            "rigid_body_api_removed": True,
            "rigid_body_disabled": True,
            "mass_api_removed": True,
        }
    ]
    assert [item["prim_path"] for item in contract["collider_prims"]] == [
        "/World/Asset/Body",
        "/World/Asset/Shell",
    ]
    assert contract["collider_prims"][0]["requested_approximation"] == "sdf"
    assert contract["collider_prims"][0]["observed_approximation"] == "sdf"
    assert contract["open_top"]["status"] == "declared"
    assert set(contract["named_frames"]) == {"opening", "grasp", "support"}
    assert all(frame["authoritative"] for frame in contract["named_frames"].values())
    assert contract["root_motion_gate"]["status"] == "not_run"
    assert contract["stable_support_gate"]["status"] == "not_run"
    assert contract["gripper_collision_gate"]["status"] == "not_run"
    closure = contract["closure"]
    assert closure["status"] == "pass"
    assert len(closure["contract_payload_sha256"]) == 64
    assert len(closure["runtime_tree_sha256"]) == 64
    artifact_paths = [item["path"] for item in closure["artifacts"]]
    assert artifact_paths == sorted(artifact_paths)
    assert {
        "asset.usd",
        "deps/usd/scoped_source.usda",
        "interaction/profile.json",
        "overlays/interaction.usda",
        "overlays/physics_profile.usda",
        "physics/profile.json",
    }.issubset(artifact_paths)
    for artifact in closure["artifacts"]:
        assert artifact["sha256"] == _sha256(out_dir / artifact["path"])
    encoded_artifacts = json.dumps(
        closure["artifacts"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    assert (
        closure["runtime_tree_sha256"] == hashlib.sha256(encoded_artifacts).hexdigest()
    )

    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    root = stage.GetPrimAtPath("/World/Asset")
    body = stage.GetPrimAtPath("/World/Asset/Body")
    shell = stage.GetPrimAtPath("/World/Asset/Shell")
    assert "PhysicsRigidBodyAPI" in root.GetAppliedSchemas()
    assert "PhysicsMassAPI" in root.GetAppliedSchemas()
    assert root.GetAttribute("physics:mass").Get() == pytest.approx(1.5)
    assert "PhysicsRigidBodyAPI" not in body.GetAppliedSchemas()
    assert "PhysicsMassAPI" not in body.GetAppliedSchemas()
    assert "PhysicsCollisionAPI" in body.GetAppliedSchemas()
    assert "PhysicsCollisionAPI" in shell.GetAppliedSchemas()
    assert stage.GetPrimAtPath("/World/Asset/__aan_frame_opening").IsValid()
    assert _sha256(out_dir / "interaction" / "profile.json") == _sha256(interaction)

    root_text = (out_dir / "asset.usd").read_text(encoding="utf-8")
    assert root_text.index("overlays/physics_profile.usda") < root_text.index(
        "overlays/interaction.usda"
    )
    assert root_text.index("overlays/interaction.usda") < root_text.index(
        "deps/usd/scoped_source.usda"
    )


def test_interaction_entry_reference_closes_material_purposes_and_geom_subset(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda_with_external_materials(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    physics = _physics_profile(source, tmp_path / "physics.json")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, out_dir, evidence_out, physics, interaction)
    )

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    extraction = manifest["dependency_closure"]["scope_extraction"]
    assert extraction["entry_reference_qualification"]["status"] == "pass"
    assert extraction["reference_scope_material_relocations"] == [
        {
            "source_material_prim": "/World/Looks/GlassAll",
            "package_material_prim": "/World/Asset/__aan_materials/GlassAll",
            "method": "Usd.NamespaceEditor.MovePrimAtPath",
        },
        {
            "source_material_prim": "/World/Looks/GlassPreview",
            "package_material_prim": "/World/Asset/__aan_materials/GlassPreview",
            "method": "Usd.NamespaceEditor.MovePrimAtPath",
        },
        {
            "source_material_prim": "/World/Looks/GlassSubset",
            "package_material_prim": "/World/Asset/__aan_materials/GlassSubset",
            "method": "Usd.NamespaceEditor.MovePrimAtPath",
        },
    ]
    assert manifest["visual_preservation_fingerprint"]["status"] == "pass"

    Sdf = pytest.importorskip("pxr.Sdf")
    Usd = pytest.importorskip("pxr.Usd")
    UsdShade = pytest.importorskip("pxr.UsdShade")
    consumer = Usd.Stage.CreateInMemory()
    probe_path = Sdf.Path("/Arbitrary/Deep/Probe")
    probe = consumer.DefinePrim(probe_path, "Xform")
    assert probe.GetReferences().AddReference(
        str((out_dir / "asset.usd").resolve()),
        "/World/Asset",
    )

    body = consumer.GetPrimAtPath(probe_path.AppendChild("Body"))
    subset = consumer.GetPrimAtPath(
        probe_path.AppendPath("Body/PaintedFaces")
    )
    all_material, _ = UsdShade.MaterialBindingAPI(body).ComputeBoundMaterial()
    preview_material, _ = UsdShade.MaterialBindingAPI(body).ComputeBoundMaterial(
        materialPurpose=UsdShade.Tokens.preview
    )
    subset_material, _ = UsdShade.MaterialBindingAPI(subset).ComputeBoundMaterial()
    assert all_material.GetPath() == probe_path.AppendPath(
        "__aan_materials/GlassAll"
    )
    assert preview_material.GetPath() == probe_path.AppendPath(
        "__aan_materials/GlassPreview"
    )
    assert subset_material.GetPath() == probe_path.AppendPath(
        "__aan_materials/GlassSubset"
    )
    assert body.GetRelationship("material:binding").GetTargets() == [
        probe_path.AppendPath("__aan_materials/GlassAll")
    ]
    assert body.GetRelationship("material:binding:preview").GetTargets() == [
        probe_path.AppendPath("__aan_materials/GlassPreview")
    ]
    assert subset.GetRelationship("material:binding").GetTargets() == [
        probe_path.AppendPath("__aan_materials/GlassSubset")
    ]
    for material in (all_material, preview_material, subset_material):
        connected = UsdShade.Material(material).GetSurfaceOutput().GetConnectedSource()
        assert connected
        assert connected[0].GetPath().HasPrefix(probe_path)

    active_rigid = [
        prim.GetPath()
        for prim in consumer.Traverse()
        if "PhysicsRigidBodyAPI" in set(str(item) for item in prim.GetAppliedSchemas())
        and prim.GetAttribute("physics:rigidBodyEnabled").Get() is not False
    ]
    assert active_rigid == [probe_path]


@pytest.mark.parametrize(
    ("source_kwargs", "reason_fragment"),
    [
        ({"reserved_material_scope": True}, "__aan_materials"),
        ({"external_shader_connection": True}, "connection"),
        ({"duplicate_material_leaf": True}, "collision"),
    ],
)
def test_interaction_reference_material_closure_fails_closed(
    tmp_path: Path,
    source_kwargs: dict[str, bool],
    reason_fragment: str,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(
        _source_usda_with_external_materials(**source_kwargs),
        encoding="utf-8",
    )
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    physics = _physics_profile(source, tmp_path / "physics.json")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(
            source,
            tmp_path / "package",
            evidence_out,
            physics,
            interaction,
        )
    )

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    extraction = manifest["dependency_closure"]["scope_extraction"]
    assert extraction["status"] == "blocked"
    assert reason_fragment in str(extraction["reason"])


def test_interaction_profile_authors_compound_proxy_and_disables_source_mesh(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    payload = json.loads(interaction.read_text(encoding="utf-8"))
    payload["colliders"] = [
        {
            "relative_path": "Body",
            "mode": "disable",
            "purpose": [],
        },
        {
            "relative_path": "__aan_collision_proxy/bottom",
            "mode": "author",
            "purpose": ["support", "containment"],
            "geometry": {
                "type": "Cube",
                "size": 1.0,
                "translation_body_local_usd": [0.5, 0.01, 0.5],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "scale_body_local_usd": [1.0, 0.02, 1.0],
            },
        },
        {
            "relative_path": "__aan_collision_proxy/wall_00",
            "mode": "author",
            "purpose": ["gripper", "containment"],
            "geometry": {
                "type": "Cube",
                "size": 1.0,
                "translation_body_local_usd": [0.99, 0.5, 0.5],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "scale_body_local_usd": [0.02, 1.0, 0.3],
            },
        },
    ]
    interaction.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    physics = _physics_profile(source, tmp_path / "physics.json")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, out_dir, evidence_out, physics, interaction)
    )

    assert result.return_code == 0
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    colliders = {
        item["prim_path"]: item
        for item in manifest["interaction_contract"]["collider_prims"]
    }
    assert colliders["/World/Asset/Body"]["mode"] == "disable"
    assert colliders["/World/Asset/Body"]["collision_enabled"] is False
    assert colliders["/World/Asset/__aan_collision_proxy/bottom"][
        "collision_enabled"
    ] is True

    Usd = pytest.importorskip("pxr.Usd")
    stage = Usd.Stage.Open(str(out_dir / "asset.usd"))
    body = stage.GetPrimAtPath("/World/Asset/Body")
    bottom = stage.GetPrimAtPath("/World/Asset/__aan_collision_proxy/bottom")
    wall = stage.GetPrimAtPath("/World/Asset/__aan_collision_proxy/wall_00")
    assert body.GetAttribute("physics:collisionEnabled").Get() is False
    assert bottom.GetTypeName() == "Cube"
    assert wall.GetTypeName() == "Cube"
    assert bottom.GetAttribute("visibility").Get() == "invisible"
    assert wall.GetAttribute("visibility").Get() == "invisible"
    assert bottom.GetAttribute("size").Get() == pytest.approx(1.0)
    assert "PhysicsCollisionAPI" in bottom.GetAppliedSchemas()
    assert "PhysicsCollisionAPI" in wall.GetAppliedSchemas()


def test_interaction_profile_rebuilds_owned_overlays_idempotently(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    physics = _physics_profile(source, tmp_path / "physics.json")
    out_dir = tmp_path / "package"
    evidence_out = tmp_path / "manifest.json"
    request = _request(source, out_dir, evidence_out, physics, interaction)

    first = normalize_asset(request)
    first_manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    stale_runtime_artifact = out_dir / "deps" / "mdl" / "stale_helper.mdl"
    stale_runtime_artifact.parent.mkdir(parents=True, exist_ok=True)
    stale_runtime_artifact.write_text("mdl 1.7;\n", encoding="utf-8")
    second = normalize_asset(request)
    second_manifest = json.loads(evidence_out.read_text(encoding="utf-8"))

    assert first.return_code == 0
    assert second.return_code == 0
    assert first_manifest["interaction_contract"]["closure"] == second_manifest[
        "interaction_contract"
    ]["closure"]
    assert not stale_runtime_artifact.exists()


def test_interaction_profile_blocks_when_required_named_frame_is_missing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    payload = json.loads(interaction.read_text(encoding="utf-8"))
    del payload["named_frames"]["support"]
    interaction.write_text(json.dumps(payload), encoding="utf-8")
    physics = _physics_profile(source, tmp_path / "physics.json")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, tmp_path / "package", evidence_out, physics, interaction)
    )

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    assert manifest["interaction_contract"]["status"] == "blocked"
    assert "named_frames" in " ".join(
        manifest["interaction_contract"]["profile_admission"]["errors"]
    )
    assert manifest["physics_closure"]["status"] == "not_run"


def test_interaction_profile_rejects_misaligned_grasp_cross_section_declaration(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    payload = json.loads(interaction.read_text(encoding="utf-8"))
    payload["grasp_cross_section"] = {
        "required": True,
        "frame": "grasp",
        "axis_body_local": [0.0, 0.0, 1.0],
        "sample_offsets_body_local_usd": [-0.01, 0.0, 0.01],
        "source_visual_mesh_relative_paths": ["Body"],
        "closing_axis_body_local": [0.0, 0.0, 1.0],
        "expected_visual_width_m": 0.05,
        "visual_width_tolerance_m": 0.001,
        "collision_visual_width_tolerance_m": 0.002,
        "max_gripper_opening_m": 0.08,
        "minimum_opening_clearance_m": 0.001,
        "claim_boundary": "Fixture declaration must not bypass vector validation.",
    }
    interaction.write_text(json.dumps(payload), encoding="utf-8")
    physics = _physics_profile(source, tmp_path / "physics.json")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, tmp_path / "package", evidence_out, physics, interaction)
    )

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    errors = manifest["interaction_contract"]["profile_admission"]["errors"]
    assert any("closing_axis_body_local must be perpendicular" in error for error in errors)


def test_interaction_profile_is_source_bound_and_dynamic_only(tmp_path: Path) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    physics = _physics_profile(source, tmp_path / "physics.json")
    payload = json.loads(interaction.read_text(encoding="utf-8"))
    payload["source_binding"]["sha256"] = "0" * 64
    interaction.write_text(json.dumps(payload), encoding="utf-8")

    mismatched = normalize_asset(
        _request(
            source,
            tmp_path / "package-mismatch",
            tmp_path / "mismatch.json",
            physics,
            interaction,
        )
    )
    assert mismatched.return_code == 5

    visual_static = replace(
        _request(
            source,
            tmp_path / "package-static",
            tmp_path / "static.json",
            physics,
            interaction,
        ),
        asset_role="visual_static",
        physics_profile=None,
    )
    invalid = normalize_asset(visual_static)
    assert invalid.return_code == 2


def test_interaction_profile_requires_exact_source_collider_coverage(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.usda"
    source.write_text(_source_usda(), encoding="utf-8")
    interaction = _interaction_profile(source, tmp_path / "interaction.json")
    payload = json.loads(interaction.read_text(encoding="utf-8"))
    payload["colliders"] = [payload["colliders"][1]]
    interaction.write_text(json.dumps(payload), encoding="utf-8")
    physics = _physics_profile(source, tmp_path / "physics.json")
    evidence_out = tmp_path / "manifest.json"

    result = normalize_asset(
        _request(source, tmp_path / "package", evidence_out, physics, interaction)
    )

    assert result.return_code == 5
    manifest = json.loads(evidence_out.read_text(encoding="utf-8"))
    errors = manifest["interaction_contract"]["profile_admission"]["errors"]
    assert any("cover every active source collision prim" in error for error in errors)


def test_cli_projects_interaction_profile_path_into_request(tmp_path: Path) -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_normalize_asset_parser(subparsers)
    source = tmp_path / "source.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    interaction = tmp_path / "interaction.json"
    interaction.write_text("{}\n", encoding="utf-8")
    args = parser.parse_args(
        [
            "normalize-asset",
            str(source),
            "--out",
            str(tmp_path / "package"),
            "--asset-id",
            "fixture",
            "--source-runtime",
            "isaac51",
            "--target-runtime",
            "isaac41",
            "--target-benchmark",
            "scenario-forge",
            "--task-id",
            "fixture.task",
            "--required-prim",
            "/World/Asset",
            "--interaction-profile",
            str(interaction),
        ]
    )

    request = request_from_args(args)

    assert request.interaction_profile == interaction
