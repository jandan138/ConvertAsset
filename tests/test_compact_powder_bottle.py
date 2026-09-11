"""Independent geometry checks; neither Blender nor Isaac is required."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from scipy.spatial import ConvexHull


SOURCE = Path(__file__).resolve().parents[1] / 'scripts/model_compact_powder_bottle.py'


@pytest.fixture(scope='module')
def model():
    spec = importlib.util.spec_from_file_location('compact_bottle', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_geometry()


def volume(mesh):
    points = np.asarray(mesh['points'])
    return sum(np.dot(points[f[0]], np.cross(points[f[i]], points[f[i + 1]])) / 6
               for f in mesh['faces'] for i in range(1, len(f) - 1))


def assert_closed(mesh):
    edges = Counter((a, b) for face in mesh['faces']
                    for a, b in zip(face, face[1:] + face[:1]))
    assert all(count == 1 and edges[b, a] == 1 for (a, b), count in edges.items())
    assert volume(mesh) > 0


def hulls(model):
    return [(part, ConvexHull(part['points'])) for part in model['colliders']]


def inside(hull, points, tolerance=1e-10):
    return np.all(np.asarray(points) @ hull.equations[:, :3].T
                  + hull.equations[:, 3] <= tolerance, axis=-1)


def test_import_and_build_with_only_standard_library():
    code = ("import runpy,json; m=runpy.run_path(" + repr(str(SOURCE)) + "); "
            "g=m['build_geometry'](); print(len(g['colliders']))")
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert int(result.stdout) > 32


def test_si_dimensions_and_thin_rounded_open_lip(model):
    shell = next(m for m in model['visual_meshes'] if m['material'] == 'bottle')
    points = np.asarray(shell['points'])
    assert np.ptp(points, axis=0) == pytest.approx([.06, .06, .1])
    assert points[:, 2].min() == 0
    neck = points[(points[:, 2] >= .092) & (points[:, 2] <= .0992)]
    radii = np.linalg.norm(neck[:, :2], axis=1)
    assert radii.min() == pytest.approx(.024)
    assert radii.max() == pytest.approx(.027)
    # Crown is rounded back into the 3 mm maximum radial lip thickness.
    crown = points[np.isclose(points[:, 2], .1, atol=1e-10)]
    assert np.ptp(np.linalg.norm(crown[:, :2], axis=1)) < .001
    assert model['root_scale'] == [1, 1, 1]
    assert model['up_axis'] == 'Z' and model['meters_per_unit'] == 1


def test_insert_is_two_mm_plate_at_59_mm_with_empty_space_below(model):
    insert = next(m for m in model['visual_meshes'] if m['material'] == 'insert')
    z = np.asarray(insert['points'])[:, 2]
    assert z.min() == pytest.approx(.057)
    assert z.max() == pytest.approx(.059)
    assert .000005 < volume(insert) < .000007
    for _, hull in hulls(model):
        assert not inside(hull, [[0, 0, .03], [0, 0, .075], [0, 0, .099]]).any()
    insert_hull = next(h for p, h in hulls(model) if p['name'] == 'Insert')
    assert inside(insert_hull, [[0, 0, .058]])[0]


def test_every_visual_and_collision_piece_has_closed_outward_faces(model):
    for mesh in model['visual_meshes'] + model['colliders']:
        assert_closed(mesh)
    for part, hull in hulls(model):
        assert volume(part) == pytest.approx(hull.volume, rel=1e-8)
        assert 'rigidbody' not in part


def test_collision_preserves_open_cavity_and_thin_wall(model):
    walls = [(part, hull) for part, hull in hulls(model) if part['name'].startswith('Wall_')]
    assert model['metadata']['collider_segments'] == 32
    assert len(walls) % 32 == 0 and len(walls) <= 32 * 24
    for part, hull in walls:
        points = np.asarray(part['points'])
        z = points[:, 2].mean()
        assert not inside(hull, [[0, 0, z]])[0]
        if points[:, 2].min() >= .09:
            assert np.linalg.norm(points[:, :2], axis=1).min() >= .024 - 1e-10
            assert np.linalg.norm(points[:, :2], axis=1).max() <= .027 + 1e-10
    # Full circle, including segment midpoints, is usable right through the mouth.
    angles = np.linspace(0, 2 * np.pi, 257)
    probes = [[.023 * np.cos(t), .023 * np.sin(t), z]
              for z in [.091, .095, .098, .0995, .1] for t in angles]
    for _, hull in walls:
        assert not inside(hull, probes).any()


def test_collision_lod_budget_and_non_sliver_layers(model):
    assert len(model['colliders']) <= 258
    walls = [c for c in model['colliders'] if c['name'].startswith('Wall_')]
    assert len(walls) == 32 * 8
    heights = sorted({p[2] for c in walls for p in c['points']})
    assert heights == [.002, .004, .066, .070, .074, .082, .090, .0985, .100]
    for wall in walls:
        assert np.ptp(np.asarray(wall['points'])[:, 2]) >= .0015 - 1e-12
    assert model['metadata']['recommended_clearance_m'] <= .00075


def test_lod_preserves_r1_visuals_profiles_plates_and_mass_exactly(model):
    # Frozen from model_r1/geometry.json, independent of generated files being
    # available on the test host. Collision LOD must not reshape this payload.
    keys = ['visual_meshes', 'inner_profile', 'outer_profile', 'volume_m3',
            'mass_kg', 'center_of_mass_m', 'diagonal_inertia_kg_m2', 'principal_axes_wxyz']
    payload = {k: model[k] for k in keys}
    payload['plates'] = [c for c in model['colliders'] if c['name'] in ['Base', 'Insert']]
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == '959d44d812ef7ee9df976bd22140ba8d0f72436fa0a30afdb68d53828dc688f5'


def test_profile_clearance_and_real_powder_bed_are_collision_free(model):
    profile = model['inner_profile']
    clearance = model['metadata']['recommended_clearance_m']
    assert 0 < clearance <= .001
    assert all(a['z'] < b['z'] for a, b in zip(profile, profile[1:]))
    probes = []
    for a, b in zip(profile, profile[1:]):
        for t in np.linspace(0, 1, 7):
            z = a['z'] * (1 - t) + b['z'] * t
            if z <= .059 or z >= .1:
                continue
            radius = a['radius'] * (1 - t) + b['radius'] * t
            exponent = a['exponent'] * (1 - t) + b['exponent'] * t
            for angle in np.linspace(0, 2 * np.pi, 257):
                c, s = np.cos(angle), np.sin(angle)
                radial = radius / (abs(c)**exponent + abs(s)**exponent)**(1 / exponent)
                probes.append([(radial - clearance) * c, (radial - clearance) * s, z])
    probes = np.asarray(probes)
    for part, hull in hulls(model):
        z = np.asarray(part['points'])[:, 2]
        relevant = probes[(probes[:, 2] >= z.min()) & (probes[:, 2] <= z.max())]
        assert not inside(hull, relevant).any(), part['name']
    fill = model['metadata']['suggested_powder_surface_m']
    assert .010 <= fill - .059 <= .012
    assert fill < .075


def test_insert_collision_overlaps_wall_edges_without_hidden_plug(model):
    parts = dict((p['name'], p) for p in model['colliders'])
    insert = ConvexHull(parts['Insert']['points'])
    for part, wall in hulls(model):
        points = np.asarray(part['points'])
        if not part['name'].startswith('Wall_') or not points[:, 2].min() < .058 < points[:, 2].max():
            continue
        xy = points[np.argmin(np.linalg.norm(points[:, :2], axis=1)), :2]
        assert inside(insert, [[*xy, .058]])[0]


def collision_inset_audit(model):
    worst = 0.
    profile = model['inner_profile']
    ray_count = 0
    worst_at = None
    layer_worst = {}
    neck_outward = 0.
    outer = model['outer_profile']
    # Interpolate the ORIGINAL visual profile, never the coarser collision
    # profile: otherwise omitted shoulder heights silently evade the audit.
    for part, hull in hulls(model):
        if not part['name'].startswith('Wall_'):
            continue
        _, _, segment = part['name'].split('_')
        z0, z1 = np.min(np.asarray(part['points'])[:, 2]), np.max(np.asarray(part['points'])[:, 2])
        angles = (int(segment) + (np.arange(32) + .5) / 32) * 2 * np.pi / 32
        directions = np.column_stack([np.cos(angles), np.sin(angles)])
        denominator = directions @ hull.equations[:, :2].T
        heights = sorted(set(np.linspace(z0, z1, 65)) |
                         {p['z'] for p in profile + outer if z0 <= p['z'] <= z1})
        for z in heights:
            radius = np.interp(z, [p['z'] for p in profile], [p['radius'] for p in profile])
            exponent = np.interp(z, [p['z'] for p in profile], [p['exponent'] for p in profile])
            numerator = -(hull.equations[:, 2] * z + hull.equations[:, 3])
            lower = np.full(denominator.shape, -np.inf)
            np.divide(numerator, denominator, out=lower, where=denominator < -1e-12)
            entry = lower.max(axis=1)
            envelope = radius / np.sum(np.abs(directions)**exponent, axis=1)**(1 / exponent)
            inset = float(np.max(envelope - entry))
            layer_key = f'{z0:.4f}-{z1:.4f}'
            layer_worst[layer_key] = max(layer_worst.get(layer_key, 0.), inset)
            if inset > worst:
                worst, worst_at = inset, (part['name'], float(z))
            if z0 >= .09:
                upper = np.full(denominator.shape, np.inf)
                np.divide(numerator, denominator, out=upper, where=denominator > 1e-12)
                outer_radius = np.interp(z, [p['z'] for p in outer], [p['radius'] for p in outer])
                # The neck is circular, so the polar radius is its radius.
                neck_outward = max(neck_outward, float(np.max(upper.min(axis=1) - outer_radius)))
            ray_count += len(angles)
    return dict(maximum_inset_m=worst, ray_count=ray_count, worst_at=worst_at,
                per_layer_inset_m=layer_worst, neck_maximum_outward_deviation_m=neck_outward)


def test_measured_collision_inset_is_below_declared_clearance(model):
    audit = collision_inset_audit(model)
    print(json.dumps(audit, indent=2))
    assert audit['maximum_inset_m'] <= model['metadata']['recommended_clearance_m']
    assert audit['neck_maximum_outward_deviation_m'] <= .000565


def test_mass_properties_are_physical_and_json_serializable(model):
    assert .025 < model['mass_kg'] < .080
    assert model['mass_kg'] == pytest.approx(model['volume_m3'] * 950)
    assert model['center_of_mass_m'][:2] == pytest.approx([0, 0], abs=1e-10)
    assert .035 < model['center_of_mass_m'][2] < .065
    inertia = model['diagonal_inertia_kg_m2']
    assert all(0 < i < 1e-3 for i in inertia)
    assert inertia[0] == pytest.approx(inertia[1], rel=1e-9)
    assert max(inertia) < sum(inertia) - max(inertia)
    assert model['principal_axes_wxyz'] == [1, 0, 0, 0]
    json.dumps(model, allow_nan=False)
