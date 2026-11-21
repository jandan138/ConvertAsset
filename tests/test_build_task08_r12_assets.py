from __future__ import annotations

import json
from pathlib import Path

import pytest
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

from scripts.build_task08_r12_assets import build_assets


def _mesh_signature(path: Path, prim_path: str) -> tuple[int, int, list[tuple[float, float, float]]]:
    stage = Usd.Stage.Open(str(path))
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(prim_path))
    points = mesh.GetPointsAttr().Get()
    return len(points), len(mesh.GetFaceVertexCountsAttr().Get()), [tuple(points[i]) for i in (0, len(points) // 2, len(points) - 1)]


def test_builder_bakes_scaled_sdf_rack_with_all_15ml_bottom_supports(tmp_path: Path) -> None:
    result = build_assets(tmp_path / "out")
    stage = Usd.Stage.Open(str(result["rack"] / "asset.usd"))
    root = stage.GetDefaultPrim()
    assert root.GetPath() == "/TubeRack15ml50ml_OriginalMesh"
    assert UsdGeom.Xformable(root).GetLocalTransformation().ExtractTranslation() == (0, 0, 0)
    mesh = stage.GetPrimAtPath(str(root.GetPath()) + "/Cube_015")
    assert mesh.GetAttribute("physics:approximation").Get() == "sdf"
    assert mesh.GetAttribute("physxSDFMeshCollision:sdfResolution").Get() == 256
    assert mesh.GetAttribute("physxSDFMeshCollision:sdfSubgridResolution").Get() == 6
    colliders = [prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.CollisionAPI)]
    assert not any(
        prim.IsA(UsdGeom.Mesh) and prim.GetAttribute("physics:approximation").Get() == "none"
        for prim in colliders
    )
    supports = [prim for prim in colliders if prim.GetName().startswith("slot_15ml_")]
    assert len(supports) == 18
    frame = stage.GetPrimAtPath(str(root.GetPath()) + "/__frames/slot_15ml_r00_c02_inserted_bottom")
    point = UsdGeom.XformCache().GetLocalToWorldTransform(frame).ExtractTranslation()
    assert tuple(point) == pytest.approx((-0.0143, -0.0061325, 0.0234))


def test_builder_changes_only_body_and_cap_visual_materials(tmp_path: Path) -> None:
    result = build_assets(tmp_path / "out")
    body_source = Path(result["sources"]["body"]) / "asset.usd"
    cap_source = Path(result["sources"]["cap"]) / "asset.usd"
    body = result["body"] / "asset.usd"
    cap = result["cap"] / "asset.usd"
    assert _mesh_signature(body_source, "/World/Tube15LongNeckThreadedBody/node_/mesh_") == _mesh_signature(
        body, "/World/Tube15LongNeckThreadedBody/node_/mesh_"
    )
    assert _mesh_signature(cap_source, "/World/Tube15LongNeckThreadedClosedCap/node_/mesh_") == _mesh_signature(
        cap, "/World/Tube15LongNeckThreadedClosedCap/node_/mesh_"
    )
    body_stage = Usd.Stage.Open(str(body))
    body_mesh = body_stage.GetPrimAtPath("/World/Tube15LongNeckThreadedBody/node_/mesh_")
    material, _ = UsdShade.MaterialBindingAPI(body_mesh).ComputeBoundMaterial()
    shader = UsdShade.Shader(body_stage.GetPrimAtPath(str(material.GetPath()) + "/Shader"))
    assert shader.GetSourceAsset("mdl").resolvedPath.endswith("OmniGlass.mdl")
    assert shader.GetInput("glass_ior").Get() == pytest.approx(1.47)
    assert shader.GetInput("thin_walled").Get() is False
    assert shader.GetInput("depth").Get() == pytest.approx(0.002)
    cap_stage = Usd.Stage.Open(str(cap))
    cap_mesh = cap_stage.GetPrimAtPath("/World/Tube15LongNeckThreadedClosedCap/node_/mesh_")
    cap_material, _ = UsdShade.MaterialBindingAPI(cap_mesh).ComputeBoundMaterial()
    cap_shader = UsdShade.Shader(cap_stage.GetPrimAtPath(str(cap_material.GetPath()) + "/Shader"))
    assert tuple(cap_shader.GetInput("diffuseColor").Get()) == pytest.approx(
        (0.56, 0.004, 0.008)
    )
    assert cap_shader.GetInput("roughness").Get() == pytest.approx(0.42)


def test_asset_set_keeps_thread_and_task_claims_false(tmp_path: Path) -> None:
    build_assets(tmp_path / "out")
    manifest = json.loads((tmp_path / "out/asset_set_manifest.json").read_text())
    assert manifest["status"] == "candidate_runtime_pending"
    assert manifest["claims"]["rack_scaled_sdf_ready"] is False
    assert manifest["claims"]["visual_material_variants_ready"] is False
    assert manifest["claims"]["thread_interaction_ready"] is False
    assert manifest["claims"]["task08_success"] is False
