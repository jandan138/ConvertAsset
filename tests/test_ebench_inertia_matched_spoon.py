import pytest

from scripts.build_ebench_inertia_matched_spoon import build


def test_matches_inertia_without_replacing_target_mesh(tmp_path):
    pytest.importorskip("pxr")
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    sources = []
    for name, width in (("control", 1), ("wide", 2)):
        path = tmp_path / f"{name}.usda"
        stage = Usd.Stage.CreateNew(str(path))
        root = UsdGeom.Xform.Define(stage, "/root")
        stage.SetDefaultPrim(root.GetPrim())
        body = UsdGeom.Xform.Define(stage, "/root/obj_spoon")
        mass = UsdPhysics.MassAPI.Apply(body.GetPrim())
        mass.CreateMassAttr(0.1)
        mass.CreateCenterOfMassAttr(Gf.Vec3f(width, 0, 0))
        mass.CreateDiagonalInertiaAttr(Gf.Vec3f(width, width, width))
        mass.CreatePrincipalAxesAttr(Gf.Quatf(1))
        mesh = UsdGeom.Mesh.Define(stage, "/root/obj_spoon/mesh")
        mesh.CreatePointsAttr([(0, 0, 0), (width, 0, 0), (0, 1, 0)])
        stage.GetRootLayer().Save()
        sources.append(path)
    output = tmp_path / "matched.usda"
    report = build(*sources, output)
    stage = Usd.Stage.Open(str(output))
    assert stage.GetPrimAtPath("/root/obj_spoon/mesh").GetAttribute("points").Get()[1][0] == 2
    assert stage.GetPrimAtPath("/root/obj_spoon").GetAttribute("physics:centerOfMass").Get()[0] == 1
    assert len(report["changed_attributes"]) == 2
    assert report["physics_qualified"] is False
    for field, unchanged in (("physics:centerOfMass", "physics:diagonalInertia"),
                             ("physics:diagonalInertia", "physics:centerOfMass")):
        target = tmp_path / (field.split(":")[-1] + ".usda")
        partial = build(*sources, target, properties=[field])
        # Keep the stage alive while checking its prim.
        partial_stage = Usd.Stage.Open(str(target))
        checked = partial_stage.GetPrimAtPath("/root/obj_spoon")
        assert checked.GetAttribute(field).Get()[0] == 1
        assert checked.GetAttribute(unchanged).Get()[0] == 2
        assert partial["changed_attributes"] == ["/root/obj_spoon." + field]
    with pytest.raises(FileExistsError):
        build(*sources, output)
