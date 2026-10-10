"""Beaker proxy must remain open and leave original public physical state intact."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('bath',Path(__file__).parents[1]/'scripts/sciben_waterbath_recovery_bath.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_body_and_rim_are_open_source_matched_cells():
    cells=m.bath_cells()
    assert len(cells)==96
    for name,xyz in cells:
        assert xyz.shape[1]==3 and np.isfinite(xyz).all()
        if not name.startswith('Floor'):
            direction=xyz[:,:2].mean(0);direction/=np.linalg.norm(direction)
            assert min(xyz[:,:2]@direction)>.0350
        if name.startswith('Rim'):
            r=np.linalg.norm(xyz[:,:2],axis=1)
            assert np.allclose(((r-.0389675)/.0022775)**2+((xyz[:,2]-.11349)/.0016)**2,1)
    assert min(x[:,2].min() for _,x in cells)==0
    assert max(x[:,2].max() for _,x in cells)==pytest.approx(.11509)

def test_author_preserves_visible_source_mass_and_spout():
    Usd=pytest.importorskip('pxr.Usd');from pxr import UsdPhysics,UsdGeom
    s=Usd.Stage.CreateInMemory();b=s.DefinePrim('/World/obj_beaker','Xform');mass=UsdPhysics.MassAPI.Apply(b);mass.CreateMassAttr(.18)
    for rel in [m.BODY,m.RIM,m.SPOUT]:
        mesh=UsdGeom.Mesh.Define(s,'/World/obj_beaker/'+rel);mesh.CreatePointsAttr([(0,0,0),(1,0,0),(0,1,0)]);UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    for label in ['Sample','Bath']:
        system=s.DefinePrim('/World/WaterbathFluid/'+label+'System','Xform')
        UsdPhysics.FilteredPairsAPI.Apply(system).CreateFilteredPairsRel().SetTargets(['/World/obj_sample_tube/RigidWallProxy/shape_'+str(i) for i in range(264)])
    before={rel:s.GetPrimAtPath('/World/obj_beaker/'+rel).GetAttribute('points').Get() for rel in [m.BODY,m.RIM,m.SPOUT]}
    info=m.author(s,'/World')
    assert info['rigid_proxy_count']==96 and mass.GetMassAttr().Get()==pytest.approx(.18)
    for rel,points in before.items():assert s.GetPrimAtPath('/World/obj_beaker/'+rel).GetAttribute('points').Get()==points
    assert UsdPhysics.CollisionAPI(s.GetPrimAtPath('/World/obj_beaker/'+m.SPOUT)).GetCollisionEnabledAttr().Get()
    for rel in [m.BODY,m.RIM]:assert not UsdPhysics.CollisionAPI(s.GetPrimAtPath('/World/obj_beaker/'+rel)).GetCollisionEnabledAttr().Get()
    for label in ['Sample','Bath']:assert len(UsdPhysics.FilteredPairsAPI(s.GetPrimAtPath('/World/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets())==360
