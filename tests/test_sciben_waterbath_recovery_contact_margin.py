import sys
from pathlib import Path
from pxr import Usd,Sdf,UsdPhysics
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))

def test_only_table_margin_and_body_ccd_flags_change():
    from sciben_waterbath_recovery_contact_margin import author
    s=Usd.Stage.CreateInMemory();root='/World';p=s.DefinePrim(root+'/table/Mesh','Mesh');UsdPhysics.CollisionAPI.Apply(p)
    for obj in ['obj_sample_tube','obj_beaker']:
        b=s.DefinePrim(root+'/'+obj);b.CreateAttribute('physxRigidBody:enableCCD',Sdf.ValueTypeNames.Bool).Set(True);b.CreateAttribute('physxRigidBody:enableSpeculativeCCD',Sdf.ValueTypeNames.Bool).Set(True)
        shape=s.DefinePrim(root+'/'+obj+'/PBD','Mesh');shape.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.0014)
    r=author(s,root)
    assert abs(p.GetAttribute('physxCollision:contactOffset').Get()-.009)<1e-9
    assert not p.GetAttribute('physxCollision:restOffset').HasAuthoredValueOpinion()
    for obj in ['obj_sample_tube','obj_beaker']:
        b=s.GetPrimAtPath(root+'/'+obj);assert b.GetAttribute('physxRigidBody:enableCCD').Get() is False;assert b.GetAttribute('physxRigidBody:enableSpeculativeCCD').Get() is False
        assert abs(s.GetPrimAtPath(root+'/'+obj+'/PBD').GetAttribute('physxCollision:contactOffset').Get()-.0014)<1e-9
