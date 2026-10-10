"""Independent geometry and physical declaration guards."""
import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('waterbath_geometry', Path(__file__).parents[1]/'scripts/sciben_waterbath_geometry.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def test_volume_frustum_and_exact_mass():
    import math
    assert mod.profile_volume([[0, .01],[.1,.01]]) == pytest.approx(math.pi*.00001)
    assert mod.particle_mass(.008, 1234) * 1234 == pytest.approx(.008)

def test_invalid_profiles_fail_before_authoring():
    for profile in [[], [[0,1]], [[1,1],[0,1]], [[0,-1],[1,1]]]:
        with pytest.raises(ValueError): mod.validate_profile(profile)

def test_particle_centers_and_world_movement_are_distinct():
    import numpy as np
    profile=[[0,.01],[.03,.01]]
    xyz=mod.seed_profile(profile,.002,.001)
    assert len(xyz)>0
    assert mod.outside_count(xyz,profile,.00001)==0
    assert mod.outside_count(np.asarray(xyz)+[.1,0,0],profile,.00001)==len(xyz)

def test_mass_rejects_empty_or_nonpositive():
    for mass,count in [(0,1),(-1,1),(1,0)]:
        with pytest.raises(ValueError):mod.particle_mass(mass,count)

def test_profile_frustum_not_cylinder_shortcut():
    import math
    assert mod.profile_volume([[0,.01],[.1,.02]]) == pytest.approx(math.pi*.1*(.0001+.0002+.0004)/3)

def test_tiny_rim_cells_coalesce_without_open_gaps():
    profile=[[0,.001],[.00002,.002],[.0002,.003],[.00025,.004],[.001,.005]]
    result=mod.collision_profile(profile)
    assert result[0]==profile[0] and result[-1]==profile[-1]
    assert all(b[0]-a[0]>=.0001 for a,b in zip(result,result[1:]))

def test_fluid_only_group_keeps_particle_helpers_out_of_rigid_group():
    from pxr import Usd,Sdf
    s=Usd.Stage.CreateInMemory();p=s.DefinePrim('/World/obj_sample_tube/Visual/GlassShell','Mesh');p.CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True)
    result=mod.separate_tube_contacts(s)
    rigid=s.GetPrimAtPath(result['rigid_group'])
    assert Sdf.Path('/World/WaterbathFluid') in rigid.GetRelationship('collection:colliders:excludes').GetTargets()
    assert p.GetAttribute('physics:collisionEnabled').Get()
    assert s.GetPrimAtPath(result['supplemental_group']).GetRelationship('physics:filteredGroups').GetTargets()==[rigid.GetPath()]
