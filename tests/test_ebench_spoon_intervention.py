import pytest

from scripts.build_ebench_spoon_intervention import build_native_overlay, deform_point, handle_weight


def test_bowl_and_length_are_preserved():
    for z in [0.1, 0.3, 0.5]:
        assert deform_point([0.12, 0.04, z], 2.0) == [0.12, 0.04, z]
    for z in [-0.5, -0.1, 0, 0.1, 0.5]:
        assert deform_point([0.02, 0.01, z], 2.0)[2] == z


def test_handle_scale_and_same_process_control():
    assert deform_point([0.02, 0.01, -0.4], 2.0) == [0.04, 0.02, -0.4]
    assert deform_point([0.02, 0.01, -0.4], 1.0) == [0.02, 0.01, -0.4]
    assert handle_weight(0.0) == 0.5
    with pytest.raises(ValueError):
        deform_point([0, 0, 0], 4.0)


def test_native_overlay_restores_pose_without_double_scaling(tmp_path):
    pytest.importorskip("pxr")
    from pxr import Usd, UsdGeom, UsdShade

    original_path, prepared_path = tmp_path / "source.usda", tmp_path / "prepared.usda"
    original = Usd.Stage.CreateNew(str(original_path))
    old = UsdGeom.Xform.Define(original, "/root/obj_spoon")
    old.AddTranslateOp().Set((1, 2, 3))
    old.AddScaleOp().Set((0.2, 0.2, 0.2))
    original.GetRootLayer().Save()
    prepared = Usd.Stage.CreateNew(str(prepared_path))
    body = UsdGeom.Xform.Define(prepared, "/World/Spoon")
    body.AddScaleOp().Set((0.2, 0.2, 0.2))
    mesh = UsdGeom.Mesh.Define(prepared, "/World/Spoon/mesh")
    mesh.GetPointsAttr().Set([(0, 0, 0), (1, 0, 0), (0, 1, 0)])
    material = UsdShade.Material.Define(prepared, "/World/Spoon/Looks/material")
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    prepared.GetRootLayer().Save()
    output = tmp_path / "overlay.usda"
    build_native_overlay(original_path, "/root/obj_spoon", prepared_path, output)
    result = Usd.Stage.Open(str(output))
    new = UsdGeom.Xformable(result.GetPrimAtPath("/root/obj_spoon"))
    assert new.GetLocalTransformation() == old.GetLocalTransformation()
    bound, _ = UsdShade.MaterialBindingAPI(result.GetPrimAtPath("/root/obj_spoon/mesh")).ComputeBoundMaterial()
    assert str(bound.GetPath()) == "/root/obj_spoon/Looks/material"
