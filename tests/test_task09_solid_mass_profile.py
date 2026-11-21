"""Source-independent geometry and USD-profile regression checks."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    'task09_mass', Path(__file__).parents[1] / 'scripts/task09_solid_mass_profile.py'
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

POINTS = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])


def test_volume_is_not_bounding_box_and_translation_is_irrelevant():
    assert module.closed_mesh_volume(POINTS, FACES)['volume_m3'] == pytest.approx(1 / 6)
    world = POINTS * [2, 3, 4] + [1234, -5678, 90]
    assert module.closed_mesh_volume(world, FACES)['volume_m3'] == pytest.approx(4)


def test_open_or_inconsistently_wound_mesh_fails_closed():
    with pytest.raises(ValueError, match='manifold'):
        module.closed_mesh_volume(POINTS, FACES[:-1])
    wrong = FACES.copy()
    wrong[0] = wrong[0][::-1]
    with pytest.raises(ValueError, match='winding'):
        module.closed_mesh_volume(POINTS, wrong)


def test_global_reverse_winding_retains_volume():
    result = module.closed_mesh_volume(POINTS, FACES[:, ::-1])
    assert result['volume_m3'] == pytest.approx(1 / 6)
    assert result['signed_volume_m3'] < 0


def test_candidate_sequence_caps_each_body_and_has_original_baseline():
    candidates = module.mass_candidates([0.001, 0.003])
    assert [c['id'] for c in candidates] == ['reference_x1', 'reference_x2', 'reference_x5', 'reference_x10', 'original_10g']
    assert candidates[2]['masses_kg'] == pytest.approx([0.005, 0.01])
    assert candidates[-1]['masses_kg'] == [0.01, 0.01]


def test_usd_audit_uses_full_world_transform_and_mass_only_override(tmp_path):
    from pxr import Usd, UsdGeom, UsdPhysics, Gf
    source = tmp_path / 'source.usda'
    stage = Usd.Stage.CreateNew(str(source))
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    body = UsdGeom.Xform.Define(stage, '/World/obj_grain_01')
    body.AddScaleOp().Set(Gf.Vec3f(2, 3, 4))
    UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
    UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(0.01)
    mesh = UsdGeom.Mesh.Define(stage, '/World/obj_grain_01/CrystalMesh')
    mesh.CreatePointsAttr(POINTS.tolist())
    mesh.CreateFaceVertexCountsAttr([3] * 4)
    mesh.CreateFaceVertexIndicesAttr(FACES.flatten().tolist())
    stage.GetRootLayer().Save()
    result = module.audit_body(stage, '/World/obj_grain_01', 2160)
    assert result['volume_m3'] == pytest.approx(4e-6)
    assert result['reference_mass_kg'] == pytest.approx(0.00864)
    layer = tmp_path / 'override.usda'
    module.write_mass_layer(layer, [result], [0.001])
    overlay = Usd.Stage.Open(str(layer))
    assert overlay.GetRootLayer().subLayerPaths == []
    assert overlay.GetPrimAtPath('/World/obj_grain_01').GetAttribute('physics:mass').Get() == pytest.approx(0.001)
    text = layer.read_text()
    assert 'references' not in text and 'points' not in text and 'xformOp' not in text


def test_explicit_inertia_scales_with_mass(tmp_path):
    from pxr import Usd
    body = {
        'body_path': '/World/obj_grain_01', 'stage_kilograms_per_unit': 1.0,
        'original_mass_kg': 0.01, 'original_diagonal_inertia_stage_units': [1e-6, 2e-6, 3e-6],
    }
    target = tmp_path / 'inertia.usda'
    module.write_mass_layer(target, [body], [0.001])
    stage = Usd.Stage.Open(str(target))
    value = stage.GetPrimAtPath(body['body_path']).GetAttribute('physics:diagonalInertia').Get()
    assert list(value) == pytest.approx([1e-7, 2e-7, 3e-7])


def test_disconnected_shells_fail_instead_of_summing_overlaps():
    points = np.vstack([POINTS, POINTS + 0.2])
    faces = np.vstack([FACES, FACES + 4])
    with pytest.raises(ValueError, match='multiple closed shells'):
        module.closed_mesh_volume(points, faces)


def test_contact_profile_only_changes_enabled_grain_boat_colliders(tmp_path):
    from pxr import Usd, UsdGeom, UsdPhysics, Sdf
    contact_spec = importlib.util.spec_from_file_location(
        'task09_contact', Path(__file__).parents[1] / 'scripts/task09_solid_contact_profile.py'
    )
    contact = importlib.util.module_from_spec(contact_spec)
    contact_spec.loader.exec_module(contact)
    source = tmp_path / 'source.usda'
    stage = Usd.Stage.CreateNew(str(source))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    for i in range(1, 6):
        root = UsdGeom.Xform.Define(stage, f'/World/obj_grain_{i:02d}').GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(root)
        root.SetMetadata('apiSchemas', Sdf.TokenListOp.CreateExplicit(['PhysicsRigidBodyAPI', 'PhysxRigidBodyAPI']))
        mesh = UsdGeom.Mesh.Define(stage, f'/World/obj_grain_{i:02d}/CrystalMesh').GetPrim()
        UsdPhysics.CollisionAPI.Apply(mesh)
    boat = UsdGeom.Xform.Define(stage, '/World/obj_weighing_boat').GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(boat)
    for name in ['Cube', 'VisualDisabled']:
        prim = UsdGeom.Mesh.Define(stage, '/World/obj_weighing_boat/' + name).GetPrim()
        UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(name == 'Cube')
    other = UsdGeom.Mesh.Define(stage, '/World/table').GetPrim()
    UsdPhysics.CollisionAPI.Apply(other)
    stage.GetRootLayer().Save()
    before = source.read_bytes()
    result = contact.build_profiles(source, tmp_path / 'profiles')
    assert source.read_bytes() == before
    assert len(result['collider_paths']) == 6
    assert '/World/obj_weighing_boat/VisualDisabled' not in result['collider_paths']
    assert '/World/table' not in result['collider_paths']
    overlay = Usd.Stage.Open(str(tmp_path / 'profiles/contact_1mm.usda'))
    authored = {a.GetName() for p in overlay.TraverseAll() for a in p.GetAttributes()}
    assert authored == {'physxCollision:contactOffset', 'physxCollision:restOffset'}
    assert overlay.GetPrimAtPath('/World/obj_grain_01/CrystalMesh').GetAttribute('physxCollision:contactOffset').Get() == pytest.approx(0.001)
    assert overlay.GetPrimAtPath('/World/obj_grain_01/CrystalMesh').GetAttribute('physxCollision:restOffset').Get() == 0
    sleep = Usd.Stage.Open(str(tmp_path / 'profiles/grain_sleep.usda'))
    props = {a.GetName() for p in sleep.TraverseAll() for a in p.GetAttributes()}
    assert props == {'physxRigidBody:sleepThreshold', 'physxRigidBody:stabilizationThreshold'}
    assert sleep.GetPrimAtPath('/World/obj_grain_01').GetAttribute('physxRigidBody:sleepThreshold').Get() == pytest.approx(5e-4)
    assert not sleep.GetPrimAtPath('/World/obj_weighing_boat')


def test_solver_profile_binds_both_sources_and_only_authors_solver_counts(tmp_path):
    from pxr import Usd, UsdGeom, UsdPhysics
    spec = importlib.util.spec_from_file_location(
        'task09_contact_solver', Path(__file__).parents[1] / 'scripts/task09_solid_contact_profile.py'
    )
    contact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contact)
    source, balance = tmp_path / 'source.usda', tmp_path / 'balance.usda'
    stage = Usd.Stage.CreateNew(str(source))
    for path in [*[f'/World/obj_grain_{i:02d}' for i in range(1, 6)], '/World/obj_weighing_boat']:
        UsdPhysics.RigidBodyAPI.Apply(UsdGeom.Xform.Define(stage, path).GetPrim())
    stage.GetRootLayer().Save()
    other = Usd.Stage.CreateNew(str(balance))
    UsdPhysics.ArticulationRootAPI.Apply(UsdGeom.Xform.Define(other, '/World/obj_analytical_balance').GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(UsdGeom.Xform.Define(other, '/World/obj_analytical_balance/Instance/WeighingPan').GetPrim())
    other.GetRootLayer().Save()
    hashes = [contact.digest(source), contact.digest(balance)]
    report = contact.build_solver_profile(source, balance, tmp_path / 'solver')
    assert hashes == [contact.digest(source), contact.digest(balance)]
    assert len(report['source_bindings']) == 2
    assert len(report['targets']) == 8
    overlay = Usd.Stage.Open(str(tmp_path / 'solver/solver64_32.usda'))
    attrs = [a for p in overlay.TraverseAll() for a in p.GetAttributes()]
    assert len(attrs) == 16
    assert all(a.GetName().endswith(('solverPositionIterationCount', 'solverVelocityIterationCount')) for a in attrs)
    assert {a.Get() for a in attrs} == {64, 32}
    assert overlay.GetRootLayer().customLayerData['source_task14_sha256'] == hashes[1]
    assert not overlay.GetRootLayer().subLayerPaths
