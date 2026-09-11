"""Powder objects must behave like ordinary task roots, not nested rigid grains."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest


def builder():
    path = Path(__file__).resolve().parents[1]/'scripts/build_task09_powder_bottle.py'
    spec = importlib.util.spec_from_file_location('task09_powder_builder',path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_shallow_fill_stays_inside_cavity_with_clearance():
    mod = builder()
    positions = np.asarray(mod.powder_centers(2048,42))
    assert positions.shape == (2048,3)
    assert np.max(np.linalg.norm(positions[:,:2],axis=1))+.0006 < .027
    assert positions[:,2].min()-.0006 >= mod.FALSE_FLOOR
    assert positions[:,2].max()+.0006 < .14
    # Nearest neighbour clearance, without allocating a huge pairwise matrix.
    from scipy.spatial import cKDTree
    assert cKDTree(positions).query(positions,k=2)[0][:,1].min() >= .00124
    assert np.array_equal(positions,mod.powder_centers(2048,42))
    with pytest.raises(ValueError):
        mod.powder_centers(1000000,42)


def test_grain_promotes_mass_to_xform_without_duplicate_body():
    from pxr import Usd,UsdGeom,UsdPhysics,Gf
    mod = builder()
    src = Usd.Stage.CreateInMemory()
    mesh = UsdGeom.Mesh.Define(src,'/World/Powder/g_00000')
    mesh.CreatePointsAttr([Gf.Vec3f(1,0,0),Gf.Vec3f(0,1,0),Gf.Vec3f(0,0,1),Gf.Vec3f(0)])
    mesh.AddTranslateOp().Set(Gf.Vec3d(1,2,3))
    mesh.AddOrientOp().Set(Gf.Quatf(1))
    mesh.AddScaleOp().Set(Gf.Vec3f(.0005))
    UsdPhysics.RigidBodyAPI.Apply(mesh.GetPrim())
    UsdPhysics.MassAPI.Apply(mesh.GetPrim()).CreateMassAttr(.000001)
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    dst = Usd.Stage.CreateInMemory()
    mod.add_grain(dst,src.GetRootLayer(),'/World/obj_powder_00000',(0,0,1),Gf.Quatf(1))
    root = dst.GetPrimAtPath('/World/obj_powder_00000')
    child = dst.GetPrimAtPath('/World/obj_powder_00000/Mesh')
    assert root.IsA(UsdGeom.Xform) and root.HasAPI(UsdPhysics.RigidBodyAPI)
    assert root.GetAttribute('physics:mass').Get() == pytest.approx(.000001)
    assert not child.HasAPI(UsdPhysics.RigidBodyAPI)
    assert not child.HasAPI(UsdPhysics.MassAPI)
    assert not child.GetAttribute('physics:mass')
    assert child.HasAPI(UsdPhysics.CollisionAPI)
    assert child.GetAttribute('xformOp:scale').Get() == Gf.Vec3f(.0005)
    assert not child.GetAttribute('xformOp:translate')


def test_collision_winding_repair_preserves_geometry_and_makes_volume_positive():
    mod = builder()
    points = [(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]
    inward = [0,1,2,0,3,1,0,2,3,1,3,2]
    original = inward.copy()
    fixed,volume = mod.outward_winding(points,inward)
    assert inward == original
    assert volume == pytest.approx(1/6)
    assert mod.signed_volume(points,fixed) == pytest.approx(1/6)
    assert [set(fixed[i:i+3]) for i in range(0,12,3)] == [set(inward[i:i+3]) for i in range(0,12,3)]
