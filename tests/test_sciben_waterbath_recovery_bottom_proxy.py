import importlib.util,math
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('bottom',Path(__file__).parents[1]/'scripts/sciben_waterbath_recovery_bottom_proxy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_bottom_reduction_preserves_ends_and_bounded_profile_error():
 z=np.linspace(.0011,.009,81);r=np.sqrt(.008**2-(z-.009)**2);source=np.column_stack((z,r)).tolist()+[[.149,.008],[.15,.009]]
 old,reduced=m.bottom_profile(source,.00005)
 assert reduced[0]==old[0] and reduced[-1]==old[-1]
 assert reduced[-1]==[.009,.008]
 err=np.abs(np.interp(np.array(old)[:,0],np.array(reduced)[:,0],np.array(reduced)[:,1])-np.array(old)[:,1])
 assert err.max()<=.00005 and len(reduced)<len(old)

def test_builder_overrides_strong_source_root_filters_and_preserves_groups(tmp_path):
 from pxr import Usd,UsdPhysics
 import json
 src=tmp_path/'source';src.mkdir();s=Usd.Stage.CreateNew(str(src/'scene.usda'));s.DefinePrim('/World','Xform');s.DefinePrim('/World/obj_sample_tube','Xform')
 for i in range(3745):UsdPhysics.CollisionAPI.Apply(s.DefinePrim('/World/obj_sample_tube/WaterbathCollision/c'+str(i),'Mesh'))
 targets=[]
 for i in range(264):
  path='/World/obj_sample_tube/RigidWallProxy/'+('Bottom_' if i<144 else 'Wall_')+str(i);UsdPhysics.CollisionAPI.Apply(s.DefinePrim(path,'Mesh'));targets.append(path)
 s.DefinePrim('/World/obj_beaker','Xform')
 for label in ['Sample','Bath']:
  p=s.DefinePrim('/World/WaterbathFluid/'+label+'System','Xform');UsdPhysics.FilteredPairsAPI.Apply(p).CreateFilteredPairsRel().SetTargets(targets)
 g='/World/Bad09FluidOnlyGroups';supp=UsdPhysics.CollisionGroup.Define(s,g+'/Supplement');rigid=UsdPhysics.CollisionGroup.Define(s,g+'/RigidScene');supp.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(['/World/obj_sample_tube/WaterbathCollision','/World/obj_beaker/WaterbathCollision']);rigid.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(['/World']);rigid.GetCollidersCollectionAPI().CreateExcludesRel().SetTargets(['/World/obj_sample_tube/WaterbathCollision','/World/obj_beaker/WaterbathCollision','/World/WaterbathFluid']);supp.CreateFilteredGroupsRel().SetTargets([supp.GetPath(),rigid.GetPath()]);rigid.CreateFilteredGroupsRel().SetTargets([supp.GetPath()]);s.GetRootLayer().Save()
 z=np.linspace(.0011,.009,81);profile=np.column_stack((z,np.sqrt(.008**2-(z-.009)**2))).tolist()+[[.149,.008],[.15,.009]];(src/'manifest.json').write_text(json.dumps({'liquids':{'Sample':{'cavity_profile_m':profile}}}));(src/'probe.usda').write_text('#usda 1.0\n')
 out=tmp_path/'built';result=m.build(src/'scene.usda',out);final=Usd.Stage.Open(str(out/'scene.usda'))
 for label in ['Sample','Bath']:
  path='/World/WaterbathFluid/'+label+'System'
  assert len(UsdPhysics.FilteredPairsAPI(s.GetPrimAtPath(path)).GetFilteredPairsRel().GetTargets())==264
  pairs=UsdPhysics.FilteredPairsAPI(final.GetPrimAtPath(path)).GetFilteredPairsRel().GetTargets()
  assert len(pairs)==144 and all('/Bottom_' in str(p) for p in pairs)
 assert not final.GetPrimAtPath('/World/obj_sample_tube/WaterbathCollision').IsActive()
 sq=UsdPhysics.CollisionGroup(final.GetPrimAtPath(g+'/Supplement')).GetCollidersCollectionAPI().ComputeMembershipQuery();rq=UsdPhysics.CollisionGroup(final.GetPrimAtPath(g+'/RigidScene')).GetCollidersCollectionAPI().ComputeMembershipQuery()
 for p in Usd.PrimRange(final.GetPrimAtPath('/World/obj_sample_tube/PBDBottomProxy')):
  if p.HasAPI(UsdPhysics.CollisionAPI):assert sq.IsPathIncluded(p.GetPath()) and not rq.IsPathIncluded(p.GetPath())
 assert result['change']['tube_total_active_shapes']<1000
