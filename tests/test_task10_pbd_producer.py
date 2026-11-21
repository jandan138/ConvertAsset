"""Task10 geometry, accounting and GPU PBD USD contract checks."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('task10_producer', Path(__file__).parents[1] / 'scripts/task10_pbd_producer.py')
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


def test_profile_volume_and_sampler_stay_inside_taper():
    profile = [[0, .005], [.02, .003]]
    expected = np.pi * .02 * (.005**2 + .005*.003 + .003**2) / 3
    assert producer.profile_volume(profile) == pytest.approx(expected)
    points = np.asarray(producer.sample_profile(profile, .001, .0004))
    assert len(points) > 0
    assert np.all(np.linalg.norm(points[:, :2], axis=1) <= np.interp(points[:, 2], *np.asarray(profile).T) - .0004 + 1e-10)
    assert points[:, 2].min() > 0 and points[:, 2].max() < .02


def test_annular_partition_has_real_open_cavity():
    vertices, counts, indices = producer.annular_wedge(.01, .011, .009, .01, 0, .02, 0, .2)
    assert len(vertices) == 8 and len(counts) == 6 and len(indices) == 24
    assert min(np.linalg.norm(np.asarray(vertices)[:, :2], axis=1)) >= .009 - 1e-9


def test_particles_use_total_mass_and_isosurface_material_per_system():
    from pxr import Usd, UsdShade
    stage = Usd.Stage.CreateInMemory()
    material = UsdShade.Material.Define(stage, '/Liquid')
    producer.author_particles(stage, 'Falling', [[0, 0, 1], [0, 0, 1.0015]], material.GetPath())
    pts = stage.GetPrimAtPath('/World/Task10Fluid/FallingParticles')
    assert pts.GetAttribute('physics:mass').Get() == pytest.approx(2*producer.PARTICLE_MASS_KG)
    assert pts.GetAttribute('physxParticle:fluid').Get() is True
    assert not pts.GetAttribute('physxParticle:simulationPoints').HasAuthoredValueOpinion()
    system = stage.GetPrimAtPath('/World/Task10Fluid/FallingSystem')
    assert system.GetAttribute('physxParticleIsosurface:isosurfaceEnabled').Get() is True
    assert system.GetRelationship('material:binding').GetTargets() == [material.GetPath()]
    assert system.GetRelationship('simulationOwner').GetTargets() == []


def test_empty_falling_set_does_not_have_fake_liquid_points():
    from pxr import Usd, UsdShade
    stage = Usd.Stage.CreateInMemory()
    mat = UsdShade.Material.Define(stage, '/Liquid')
    producer.author_particles(stage, 'Falling', [], mat.GetPath())
    prim = stage.GetPrimAtPath('/World/Task10Fluid/FallingParticles')
    assert len(prim.GetAttribute('points').Get()) == 0
    assert prim.GetAttribute('physics:mass').Get() == 0


def test_passive_precharge_uses_its_own_finer_mass_and_width():
    from pxr import Usd, UsdShade
    stage = Usd.Stage.CreateInMemory()
    material = UsdShade.Material.Define(stage, '/Liquid')
    producer.author_particles(stage, 'DeadPrecharge', [[0, 0, 1]], material.GetPath())
    prim = stage.GetPrimAtPath('/World/Task10Fluid/DeadPrechargeParticles')
    assert prim.GetAttribute('physics:mass').Get() == pytest.approx(producer.DEAD_SPACING**3*1000)
    assert list(prim.GetAttribute('widths').Get()) == pytest.approx([producer.DEAD_SPACING])
    system = stage.GetPrimAtPath('/World/Task10Fluid/DeadPrechargeSystem')
    assert system.GetAttribute('particleContactOffset').Get() == pytest.approx(.00018)
    assert system.GetAttribute('enableCCD').Get() is True
    assert system.GetAttribute('physxParticleSmoothing:particleSmoothingEnabled').Get() is False


def test_closed_shell_is_watertight_with_open_fluid_cavity():
    from collections import defaultdict
    points, counts, indices = producer.closed_shell([[0, .01], [.02, .01]], .003, .002, 32)
    edges = defaultdict(list)
    triangles = []
    cursor = 0
    for count in counts:
        face = indices[cursor:cursor+count]
        cursor += count
        for u, v in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((u, v)))].append((u, v))
        triangles.extend((face[0], face[i], face[i+1]) for i in range(1, count-1))
    assert all(len(pair) == 2 and pair[0] == pair[1][::-1] for pair in edges.values())
    p = np.asarray(points)
    volume = sum(np.dot(p[a], np.cross(p[b], p[c])) for a,b,c in triangles)/6
    polygon_factor = 32/2*np.sin(2*np.pi/32)
    assert volume == pytest.approx(polygon_factor*(.013**2*.022-.01**2*.02))


def test_settled_reframing_preserves_all_particles_and_velocity_vectors():
    actual = np.eye(4)
    actual[:3, :3] = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
    actual[3, :3] = [10, 20, 30]
    original = np.eye(4)
    original[3, :3] = [2, 3, 4]
    local = np.array([[1., 0, 0], [0, 2., 0]])
    local_vel = np.array([[.01, .02, .03], [-.04, .05, .06]])
    points = local @ actual[:3, :3] + actual[3, :3]
    velocities = local_vel @ actual[:3, :3]
    transformed, rotated = producer.reframe_settled(points, velocities, actual, original)
    assert transformed == pytest.approx(local + original[3, :3])
    assert rotated == pytest.approx(local_vel)
    assert len(transformed) == len(points)
    assert np.linalg.norm(rotated, axis=1) == pytest.approx(np.linalg.norm(velocities, axis=1))


def test_settled_reframing_rejects_count_mismatch():
    with pytest.raises(ValueError, match='shape'):
        producer.reframe_settled([[0, 0, 0]], [], np.eye(4), np.eye(4))


def test_settled_state_signature_ignores_particle_motion_but_binds_collision_recipe():
    from pxr import Usd, UsdShade, Gf
    stage = Usd.Stage.CreateInMemory()
    material = UsdShade.Material.Define(stage, '/Liquid')
    producer.author_particles(stage, 'Source', [[0, 0, 1]], material.GetPath())
    signature = producer.physics_digest(stage.GetRootLayer(), 'immutable-source-hash')
    points = stage.GetPrimAtPath('/World/Task10Fluid/SourceParticles')
    points.GetAttribute('points').Set([Gf.Vec3f(.001, 0, 1.01)])
    points.GetAttribute('velocities').Set([Gf.Vec3f(.01, 0, -.02)])
    assert producer.physics_digest(stage.GetRootLayer(), 'immutable-source-hash') == signature
    system = stage.GetPrimAtPath('/World/Task10Fluid/SourceSystem')
    system.GetAttribute('restOffset').Set(.0012)
    assert producer.physics_digest(stage.GetRootLayer(), 'immutable-source-hash') != signature
