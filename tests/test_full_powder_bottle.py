"""R4 high tray: source invariants, exact interior mass and sealed convex pieces."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.spatial import ConvexHull


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def source():
    return load('model_full_powder_bottle')


@pytest.fixture(scope='module')
def baseline():
    return load('model_compact_powder_bottle').build_geometry()


@pytest.fixture(scope='module', params=[.083, .084, .085])
def model(request, source):
    return source.build_geometry(insert_top=request.param)


def volume(mesh):
    p = np.asarray(mesh['points'])
    return sum(np.dot(p[f[0]], np.cross(p[f[i]], p[f[i + 1]])) / 6
               for f in mesh['faces'] for i in range(1, len(f) - 1))


def inside(hull, points, tolerance=1e-10):
    return np.all(np.asarray(points) @ hull.equations[:, :3].T
                  + hull.equations[:, 3] <= tolerance, axis=-1)


def test_r3_shell_walls_base_profiles_and_schema_are_unchanged(model, baseline):
    for key in ['schema', 'inner_profile', 'outer_profile', 'root_scale',
                'meters_per_unit', 'up_axis', 'principal_axes_wxyz']:
        assert model[key] == baseline[key]
    assert model['visual_meshes'][0] == baseline['visual_meshes'][0]
    assert [p for p in model['colliders'] if not p['name'].startswith('Insert')] == [
        p for p in baseline['colliders'] if p['name'] != 'Insert']


def test_high_tray_dimensions_and_target_semantics(model):
    meta = model['metadata']
    top = meta['insert_top_m']
    assert .083 <= top <= .085
    assert meta['insert_thickness_m'] == .002
    assert meta['insert_wall_overlap_radius_m'] == .00015
    assert meta['suggested_powder_surface_m'] == pytest.approx(top + .011)
    assert meta['suggested_powder_depth_m'] == .011
    assert meta['target_headspace_m'] == pytest.approx(.1 - top - .011)
    assert 'no runtime or particle qualification' in meta['validation_scope']
    assert 'target' in meta['powder_surface_semantics']
    assert 'exact' in meta['mass_method']
    insert = model['visual_meshes'][1]
    points = np.asarray(insert['points'])
    assert points[:, 2].min() == pytest.approx(top - .002)
    assert points[:, 2].max() == pytest.approx(top)
    assert np.max(np.abs(points[:, :2])) < .026
    for part in model['colliders']:
        if part['name'].startswith('Insert'):
            z = np.asarray(part['points'])[:, 2]
            assert z.min() >= top - .002 - 1e-12
            assert z.max() <= top + 1e-12
    json.dumps(model, allow_nan=False)


def test_closed_outward_manifold_and_convex_collision(model):
    for mesh in model['visual_meshes'] + model['colliders']:
        edges = Counter((a, b) for f in mesh['faces']
                        for a, b in zip(f, f[1:] + f[:1]))
        assert all(n == 1 and edges[b, a] == 1 for (a, b), n in edges.items()), mesh['name']
        assert len(mesh['points']) - len(edges) // 2 + len(mesh['faces']) == 2
        assert volume(mesh) > 0, mesh['name']
    for part in model['colliders']:
        hull = ConvexHull(part['points'])
        assert volume(part) == pytest.approx(hull.volume, rel=1e-8), part['name']
        assert not inside(hull, [[0, 0, .03], [0, 0, .095], [0, 0, .099]]).any()


def test_tray_seals_to_actual_wall_hulls_across_all_angles(model):
    top = model['metadata']['insert_top_m']
    trays = [ConvexHull(p['points']) for p in model['colliders']
             if p['name'].startswith('Insert')]
    walls = [ConvexHull(p['points']) for p in model['colliders']
             if p['name'].startswith('Wall')]
    angles = np.arange(256) * 2 * np.pi / 256 + .0001
    directions = np.column_stack([np.cos(angles), np.sin(angles)])
    for z in np.linspace(top - .002, top, 9):
        entries = np.full(len(angles), np.inf)
        for hull in walls:
            den = directions @ hull.equations[:, :2].T
            num = -(hull.equations[:, 2] * z + hull.equations[:, 3])
            low = np.full_like(den, -np.inf)
            high = np.full_like(den, np.inf)
            np.divide(num, den, out=low, where=den < -1e-12)
            np.divide(num, den, out=high, where=den > 1e-12)
            entry, exit_ = low.max(axis=1), high.min(axis=1)
            valid = (entry <= exit_ + 1e-12) & (entry > 0)
            valid &= ~np.any((abs(den) <= 1e-12) & (num < -1e-12), axis=1)
            entries = np.minimum(entries, np.where(valid, entry, np.inf))
        assert np.isfinite(entries).all()
        # Probe continuously from the centre to 0.05 mm inside the wall.
        probes = np.array([[*(d * r), z] for d, entry in zip(directions, entries)
                           for r in np.linspace(0, entry + .00005, 17)])
        assert np.logical_or.reduce([inside(h, probes) for h in trays]).all()


def section_moments(shell, z):
    """Independent horizontal intersections of actual shell INNER triangles."""
    points = np.asarray(shell['points'])
    cuts = []
    for face in shell['faces']:
        if len(face) != 3:
            continue
        a, b, c = points[face]
        normal = np.cross(b - a, c - a)
        if np.dot(normal[:2], (a + b + c)[:2]) >= 0:
            continue
        for p, q in [(a, b), (b, c), (c, a)]:
            if min(p[2], q[2]) < z < max(p[2], q[2]):
                cuts.append((p + (q - p) * ((z - p[2]) / (q[2] - p[2])))[:2])
    xy = np.unique(np.round(cuts, 14), axis=0)
    xy = xy[np.argsort(np.arctan2(xy[:, 1], xy[:, 0]))]
    x, y = xy.T
    xx, yy = np.roll(x, -1), np.roll(y, -1)
    cross = x * yy - xx * y
    return np.array([cross.sum() / 2,
                     np.sum((x*x + x*xx + xx*xx) * cross) / 12,
                     np.sum((y*y + y*yy + yy*yy) * cross) / 12])


def test_mass_uses_exact_triangulated_interior_without_overlap(model, baseline):
    compact = load('model_compact_powder_bottle')
    shell = baseline['visual_meshes'][0]
    shell_v, shell_first, shell_second = compact._moments(shell)
    top = model['metadata']['insert_top_m']
    breaks = [p['z'] for p in baseline['inner_profile'] if top - .002 < p['z'] < top]

    def integrate(fn):
        return quad(fn, top - .002, top, points=breaks, epsabs=1e-16)[0]

    v = integrate(lambda z: section_moments(shell, z)[0])
    first_z = integrate(lambda z: z * section_moments(shell, z)[0])
    second = [integrate(lambda z: section_moments(shell, z)[k]) for k in [1, 2]]
    second.append(integrate(lambda z: z*z * section_moments(shell, z)[0]))
    total_v = shell_v + v
    com = (np.asarray(shell_first) + [0, 0, first_z]) / total_v
    second = np.asarray(shell_second) + second
    inertia = 950 * (second.sum() - second - total_v * (np.dot(com, com) - com*com))
    assert model['volume_m3'] == pytest.approx(total_v, rel=1e-9)
    assert model['mass_kg'] == pytest.approx(total_v * 950, rel=1e-9)
    assert model['center_of_mass_m'] == pytest.approx(com, abs=1e-12)
    assert model['diagonal_inertia_kg_m2'] == pytest.approx(inertia, rel=1e-9)
    assert volume(model['visual_meshes'][1]) > v  # Seam is visible, not counted twice.


def test_defaults_and_invalid_height(source):
    assert source.build_geometry()['metadata']['insert_top_m'] == .084
    for top in [.0829, .0851, float('nan'), float('inf')]:
        with pytest.raises(ValueError, match='insert_top'):
            source.build_geometry(insert_top=top)


def test_isolated_standard_library_import():
    code = (f"import runpy; m=runpy.run_path({str(SCRIPTS / 'model_full_powder_bottle.py')!r}); "
            "print(m['build_geometry']()['metadata']['insert_top_m'])")
    result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert float(result.stdout) == .084
