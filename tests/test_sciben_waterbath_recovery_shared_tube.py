import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('shared',Path(__file__).parents[1]/'scripts/sciben_waterbath_recovery_shared_tube.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_shared_collision_reduces_active_shapes_and_preserves_unrelated_filters():
 Usd=pytest.importorskip('pxr.Usd');from pxr import UsdPhysics,UsdGeom,Gf
 s=Usd.Stage.CreateInMemory();tube=s.DefinePrim('/World/obj_sample_tube','Xform');mass=UsdPhysics.MassAPI.Apply(tube);mass.CreateMassAttr(.0180089213);mass.CreateCenterOfMassAttr(Gf.Vec3f(0,0,.076103));before_mass=mass.GetMassAttr().Get();fine=s.DefinePrim('/World/obj_sample_tube/WaterbathCollision','Xform')
 for i in range(3745):UsdPhysics.CollisionAPI.Apply(s.DefinePrim(str(fine.GetPath())+'/c'+str(i),'Mesh'))
 proxy=[]
 for i in range(264):
  p=s.DefinePrim('/World/obj_sample_tube/RigidWallProxy/c'+str(i),'Mesh');UsdPhysics.CollisionAPI.Apply(p);proxy.append(p.GetPath())
 bath=s.DefinePrim('/World/obj_beaker/WaterbathCollision/c','Mesh');UsdPhysics.CollisionAPI.Apply(bath)
 for label in ['Sample','Bath']:
  p=s.DefinePrim('/World/WaterbathFluid/'+label+'System','Xform');UsdPhysics.FilteredPairsAPI.Apply(p).CreateFilteredPairsRel().SetTargets(proxy+['/World/unrelated'])
 data=m.author(s,'/World')
 assert not fine.IsActive() and data['retired_tube_fine_shapes']==3745
 assert sum(p.HasAPI(UsdPhysics.CollisionAPI) for p in Usd.PrimRange(tube))==264
 assert bath.IsActive() and mass.GetMassAttr().Get()==before_mass
 for label in ['Sample','Bath']:
  api=UsdPhysics.FilteredPairsAPI(s.GetPrimAtPath('/World/WaterbathFluid/'+label+'System'))
  assert [str(x) for x in api.GetFilteredPairsRel().GetTargets()]==['/World/unrelated']
 assert s.GetRootLayer().GetPrimAtPath('/World/obj_sample_tube/WaterbathCollision/c0') # retained source spec
