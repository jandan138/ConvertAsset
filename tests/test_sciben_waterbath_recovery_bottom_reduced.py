import sys
from pathlib import Path
from pxr import Usd,UsdPhysics
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))

def test_reduced_bottom_keeps_filter_targets_and_registers_group():
    from sciben_waterbath_recovery_bottom_reduced import author
    s=Usd.Stage.CreateInMemory();root='/World';old=root+'/obj_sample_tube/PBDBottomProxy'
    for i in range(353):UsdPhysics.CollisionAPI.Apply(s.DefinePrim(old+'/Cell'+str(i),'Mesh'))
    for label in ['Sample','Bath']:
        p=s.DefinePrim(root+'/WaterbathFluid/'+label+'System');UsdPhysics.FilteredPairsAPI.Apply(p).CreateFilteredPairsRel().SetTargets(['/World/original'])
    for name in ['Supplement','RigidScene']:UsdPhysics.CollisionGroup.Define(s,root+'/Bad09FluidOnlyGroups/'+name)
    profile=[[.0011,.0013],[.003,.0055],[.009,.008]]
    result=author(s,root,profile)
    assert not s.GetPrimAtPath(old).IsActive()
    assert result['new_shapes']==33
    for label in ['Sample','Bath']:
        assert list(map(str,UsdPhysics.FilteredPairsAPI(s.GetPrimAtPath(root+'/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets()))==['/World/original']
    group=UsdPhysics.CollisionGroup(s.GetPrimAtPath(root+'/Bad09FluidOnlyGroups/Supplement'))
    assert group.GetCollidersCollectionAPI().ComputeMembershipQuery().IsPathIncluded(root+'/obj_sample_tube/PBDBottomReduced/Floor')
