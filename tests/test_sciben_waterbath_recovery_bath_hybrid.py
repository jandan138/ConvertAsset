import importlib.util,sys
from pathlib import Path
from pxr import Usd,UsdPhysics

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))

def test_filter_union_preserves_bottom_and_keeps_straight_shared():
    from sciben_waterbath_recovery_bath_hybrid import filter_audit
    s=Usd.Stage.CreateInMemory();root='/World/_scene'
    bottom=[root+'/obj_sample_tube/RigidWallProxy/Bottom_'+str(i) for i in range(144)]
    bath=[root+'/obj_beaker/RigidBathProxy/Wall_'+str(i) for i in range(96)]
    for label in ['Sample','Bath']:
        p=s.DefinePrim(root+'/WaterbathFluid/'+label+'System')
        UsdPhysics.FilteredPairsAPI.Apply(p).CreateFilteredPairsRel().SetTargets(bottom+bath)
    assert filter_audit(s,root)['Sample']['total']==240
    p=s.GetPrimAtPath(root+'/WaterbathFluid/SampleSystem')
    UsdPhysics.FilteredPairsAPI(p).CreateFilteredPairsRel().SetTargets(bottom+bath+[root+'/obj_sample_tube/RigidWallProxy/Wall_00'])
    import pytest
    with pytest.raises(ValueError):filter_audit(s,root)
