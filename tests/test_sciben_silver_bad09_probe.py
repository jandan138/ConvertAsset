"""Raw model actions must be replayed without trajectory or base reinterpretation."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('silver_probe',Path(__file__).parents[1]/'scripts/sciben_silver_bad09_probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_exact_targets_and_absolute_base():
    targets=np.arange(16,dtype=float)/100
    action,base=m.normalize_action({'arm_action':targets,'base_motion':[.1,-.2,.3]})
    np.testing.assert_allclose(action,targets)
    np.testing.assert_allclose(base,[.1,-.2,.3])

def test_invalid_action_fails_before_simulation():
    for value in [np.zeros(15),np.r_[np.zeros(15),np.nan]]:
        with pytest.raises(ValueError):m.normalize_action({'arm_action':value,'base_motion':[0,0,0]})

def test_baseline_absolute_yaw_uses_degrees():
    np.testing.assert_allclose(m.sdk_base_targets([.1,-.2,90]),[.1,-.2,np.pi/2])
    np.testing.assert_allclose(m.sdk_base_targets([.1,-.2,90],legacy_raw=True),[.1,-.2,90])

def test_contact_sampling_is_only_removed_call():
    source="state.repair_contacts=create_view()\n    contact=state.repair_contacts.get_contact_data(1/120)\n    count=bounded_contact_count(contact[4],config['contact_capacity'])\n    valid=read_particles()\n"
    result=m.skip_contact_sampling(source)
    assert 'create_view()' in result and 'read_particles()' in result
    assert 'get_contact_data(' not in result
    assert 'count=0' in result
    with pytest.raises(ValueError):m.skip_contact_sampling('different source')

def test_fluid_only_groups_preserve_rigid_and_particle_membership():
    Usd=pytest.importorskip('pxr.Usd'); from pxr import UsdPhysics
    stage=Usd.Stage.CreateInMemory();stage.DefinePrim('/World','Xform')
    for path in ['/World/obj_sample_tube/Visual/GlassShell','/World/obj_beaker/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh','/World/obj_sample_tube/WaterbathCollision/cell','/World/obj_beaker/WaterbathCollision/cell','/World/WaterbathFluid/Particles','/World/lift2/finger','/World/obj_test_tube_rack/body']:
        p=stage.DefinePrim(path,'Mesh');UsdPhysics.CollisionAPI.Apply(p)
    m.fluid_only_supplements(stage,'/World')
    groups='/World/Bad09FluidOnlyGroups'
    rigid=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(groups+'/RigidScene')).GetCollidersCollectionAPI().ComputeMembershipQuery()
    walls=UsdPhysics.CollisionGroup(stage.GetPrimAtPath(groups+'/Supplement')).GetCollidersCollectionAPI().ComputeMembershipQuery()
    for path in ['/World/lift2/finger','/World/obj_test_tube_rack/body','/World/obj_sample_tube/Visual/GlassShell']:
        assert rigid.IsPathIncluded(path) and not walls.IsPathIncluded(path)
    for path in ['/World/obj_sample_tube/WaterbathCollision/cell','/World/obj_beaker/WaterbathCollision/cell']:
        assert walls.IsPathIncluded(path) and not rigid.IsPathIncluded(path)
    assert not rigid.IsPathIncluded('/World/WaterbathFluid/Particles')
    assert not walls.IsPathIncluded('/World/WaterbathFluid/Particles')

def test_case_binding_uses_yaml_scene_and_matching_metadata(tmp_path):
    task='task_z4_silver_mirror_reaction';case='mixed_17'
    y=tmp_path/f'configs/tasks/scientific_experiments/{task}/test/mixed/{case}.yml';y.parent.mkdir(parents=True)
    y.write_text('evaluation_configs:\n- task_name: scientific_experiments/'+task+'/'+case+'\n  usd_name: scene_usds/scientific_experiments/'+task+'/unseen_scene_7/scene\n  warmup_steps: 300\n  physics_dt: 0.008333333333333333\n  rendering_dt: 0.008333333333333333\n')
    result=m.case_inputs(tmp_path,case)
    assert str(result['scene']).endswith('/unseen_scene_7/scene.usda')
    assert str(result['metadata']).endswith('/mixed_17/000/meta_info.pkl')
    with pytest.raises(ValueError):m.case_inputs(tmp_path,'../mixed_1')

def test_small_rigid_proxy_is_open_and_does_not_change_body_mass():
    cells=m.tube_proxy_cells()
    assert len(cells)==193
    assert max(v[:,2].max() for _,v in cells)==pytest.approx(.15)
    assert min(v[:,2].min() for _,v in cells)==pytest.approx(0)
    for name,v in cells:
        if name!='BottomCap':
            high=v[v[:,2]>.01,:2]
            if len(high):
                direction=high.mean(0);direction/=np.linalg.norm(direction)
                assert (high@direction).min()>.0079  # no slab crosses the open cavity
    Usd=pytest.importorskip('pxr.Usd');from pxr import UsdPhysics
    stage=Usd.Stage.CreateInMemory();body=stage.DefinePrim('/World/obj_sample_tube','Xform');UsdPhysics.MassAPI.Apply(body).CreateMassAttr(.01800892)
    glass=stage.DefinePrim('/World/obj_sample_tube/Visual/GlassShell','Mesh');UsdPhysics.CollisionAPI.Apply(glass)
    for label in ['Sample','Bath']:stage.DefinePrim('/World/WaterbathFluid/'+label+'System','Xform')
    m.author_tube_rigid_proxy(stage,'/World')
    assert UsdPhysics.MassAPI(body).GetMassAttr().Get()==pytest.approx(.01800892)
    assert not UsdPhysics.CollisionAPI(glass).GetCollisionEnabledAttr().Get()
    for label in ['Sample','Bath']:
        assert len(UsdPhysics.FilteredPairsAPI(stage.GetPrimAtPath('/World/WaterbathFluid/'+label+'System')).GetFilteredPairsRel().GetTargets())==193

def test_spherical_bottom_proxy_vertices_follow_both_source_surfaces():
    cells=m.tube_proxy_cells_v2();assert len(cells)==264
    for name,v in cells:
        if name.startswith('Bottom_'):
            radii=np.linalg.norm(v-[0,0,.009],axis=1)
            assert np.all(np.isclose(radii,.008)|np.isclose(radii,.009))
            assert v[:,2].min()>=-1e-12 and v[:,2].max()<=.009+1e-12

def test_measured_native_cadence_waits_only_during_passive_warmup():
    assert m.native_step_decision(10,11,True)
    assert m.native_step_decision(10,11,False)
    assert not m.native_step_decision(10,10,True)
    for before,after,warm in [(10,10,False),(10,12,False),(10,12,True),(10,9,True)]:
        with pytest.raises(RuntimeError):m.native_step_decision(before,after,warm)
