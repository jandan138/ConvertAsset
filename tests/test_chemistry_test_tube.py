"""Engineering tube: true open lumen, oriented glass solid and source-bound USD."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def model():
    return load('model_chemistry_test_tube').build_geometry()


def winding(mesh, point):
    triangles = np.asarray(mesh['points'])[mesh['faces']] - point
    a, b, c = triangles.transpose(1, 0, 2)
    la, lb, lc = np.linalg.norm(triangles, axis=2).T
    numerator = np.einsum('ij,ij->i', a, np.cross(b, c))
    denominator = (la*lb*lc + np.einsum('ij,ij->i', a, b)*lc
                   + np.einsum('ij,ij->i', b, c)*la
                   + np.einsum('ij,ij->i', c, a)*lb)
    return np.arctan2(numerator, denominator).sum() / (2*np.pi)


def test_dimensions_spherical_floors_and_dense_cavity(model):
    p = np.asarray(model['mesh']['points'])
    assert p[:, 2].min() == pytest.approx(0, abs=1e-12)
    assert p[:, 2].max() == pytest.approx(.150)
    assert np.linalg.norm(p[:, :2], axis=1).max() == pytest.approx(.010)
    for key, radius in [('outer_profile_m', .009), ('cavity_profile_m', .008)]:
        profile = np.asarray(model[key])
        sphere = profile[profile[:, 0] <= .009]
        assert (sphere[:, 0] - .009)**2 + sphere[:, 1]**2 == pytest.approx(radius**2)
        cylinder = profile[(profile[:, 0] >= .009) & (profile[:, 0] <= .147)]
        assert cylinder[:, 1] == pytest.approx(radius)
    cavity = np.asarray(model['cavity_profile_m'])
    assert cavity[0] == pytest.approx([.001, 0])
    assert cavity[-1] == pytest.approx([.150, .009])
    assert np.all(np.diff(cavity[:, 0]) > 0)
    assert np.diff(cavity[cavity[:, 0] <= .050, 0]).max() <= .00201
    assert model['parameter_status'] == 'engineering_geometry'


def test_closed_consistently_outward_and_open_lumen(model):
    mesh = model['mesh']
    edges = Counter((a, b) for f in mesh['faces'] for a, b in zip(f, f[1:] + f[:1]))
    assert all(n == 1 and edges[b, a] == 1 for (a, b), n in edges.items())
    assert len(mesh['points']) - len(edges)//2 + len(mesh['faces']) == 2
    for point in [[0, 0, .0005], [.0085, 0, .08]]:
        assert winding(mesh, point) == pytest.approx(1, abs=1e-8)
    for z in [.0011, .003, .009, .03, .05, .10, .149, .1501]:
        assert winding(mesh, [0, 0, z]) == pytest.approx(0, abs=1e-8)
    # Every straight inner/outer triangle normal must point out of GLASS.
    a, b, c = np.asarray(mesh['points'])[mesh['faces']].transpose(1, 0, 2)
    centers = (a+b+c)/3
    normals = np.cross(b-a, c-a)
    body = (centers[:, 2] > .01) & (centers[:, 2] < .14)
    radial = np.linalg.norm(centers[:, :2], axis=1)
    dots = np.einsum('ij,ij->i', normals[:, :2], centers[:, :2])
    assert np.all(dots[body & (radial > .0085)] > 0)
    assert np.all(dots[body & (radial < .0085)] < 0)


def test_mass_independent_tetrahedral_integral(model):
    a, b, c = np.asarray(model['mesh']['points'])[model['mesh']['faces']].transpose(1, 0, 2)
    dv = np.einsum('ij,ij->i', a, np.cross(b, c))/6
    total = a+b+c
    volume = dv.sum()
    com = (dv[:, None]*total/4).sum(axis=0)/volume
    second = (dv[:, None]*(total**2+a*a+b*b+c*c)/20).sum(axis=0)
    inertia = 2230*(second.sum()-second-volume*(np.dot(com, com)-com*com))
    assert model['volume_m3'] == pytest.approx(volume, rel=1e-10)
    assert model['mass_kg'] == pytest.approx(volume*2230, rel=1e-10)
    assert model['center_of_mass_m'] == pytest.approx(com, abs=1e-12)
    assert model['diagonal_inertia_kg_m2'] == pytest.approx(inertia, rel=1e-10)
    assert .016 < model['mass_kg'] < .019
    assert np.all(inertia > 0)
    assert inertia[0] == pytest.approx(inertia[1], rel=1e-10)


def test_usd_exact_mesh_physics_material_and_audit(model, tmp_path):
    from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade
    producer = load('build_chemistry_test_tube')
    producer.write_asset(model, tmp_path)
    stage = Usd.Stage.Open(str(tmp_path / 'asset.usd'))
    root = stage.GetPrimAtPath('/World/TestTube')
    assert stage.GetDefaultPrim().GetPath() == '/World'
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1
    assert UsdGeom.GetStageUpAxis(stage) == 'Z'
    assert UsdGeom.XformCache().GetLocalToWorldTransform(root) == Gf.Matrix4d(1)
    assert [str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)] == ['/World/TestTube']
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath('/World/TestTube/Visual/GlassShell'))
    assert np.asarray(mesh.GetPointsAttr().Get()) == pytest.approx(np.asarray(model['mesh']['points']), abs=1e-8)
    assert list(mesh.GetFaceVertexIndicesAttr().Get()) == [i for f in model['mesh']['faces'] for i in f]
    assert mesh.GetPrim().GetAttribute('physics:approximation').Get() == 'sdf'
    assert mesh.GetPrim().GetAttribute('physxSDFMeshCollision:sdfResolution').Get() == 512
    assert mesh.GetPrim().GetAttribute('physxCollision:contactOffset').Get() == pytest.approx(.00025)
    assert mesh.GetPrim().GetAttribute('physxCollision:restOffset').Get() == 0
    assert UsdShade.MaterialBindingAPI(mesh).ComputeBoundMaterial()[0]
    shader = UsdShade.Shader(stage.GetPrimAtPath('/World/TestTube/Looks/TransparentTube/Shader'))
    assert shader.GetInput('glass_color').Get() == Gf.Vec3f(1)
    assert shader.GetInput('glass_ior').Get() == pytest.approx(1.47)
    assert shader.GetInput('frosting_roughness').Get() == pytest.approx(.02)
    assert shader.GetInput('enable_opacity').Get() is False
    assert shader.GetInput('thin_walled').Get() is False
    report = producer.audit_asset(tmp_path, model)
    assert report['status'] == 'pass'
    assert report['asset_sha256'] == producer.file_sha(tmp_path / 'asset.usd')
    # Fail closed after changing the authored collision or physical contract.
    mesh.GetPrim().GetAttribute('physics:approximation').Set('convexHull')
    stage.GetRootLayer().Save()
    with pytest.raises(ValueError, match='sdf'):
        producer.audit_asset(tmp_path, model)


def test_package_rejects_unverified_blender_source(tmp_path):
    producer = load('build_chemistry_test_tube')
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'geometry.json').write_text(json.dumps({}))
    with pytest.raises((ValueError, FileNotFoundError)):
        producer.build(source, tmp_path / 'package')
    assert not (tmp_path / 'package/asset.usd').exists()


def test_plain_python_imports_without_sdk():
    for name in ('model_chemistry_test_tube', 'build_chemistry_test_tube'):
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c',
                                 f'import runpy; runpy.run_path({str(SCRIPTS / (name+".py"))!r})'],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_actual_package_contract_and_stale_evidence_rejection(tmp_path):
    package = SCRIPTS.parent/'outputs/chemistry_test_tube_18x150_r1_20260912/package'
    if not package.is_dir():
        pytest.skip('Actual Blender delivery not yet generated')
    producer = load('build_chemistry_test_tube')
    manifest = json.loads((package/'evidence/manifest.json').read_text())
    assert manifest['package_id'] == 'chemistry_test_tube_18x150_r1'
    assert manifest['overall_status'] in {'runtime_pending', 'pass'}
    if manifest['overall_status'] == 'pass':
        assert manifest['claims']['runtime_qualified'] is True
        assert manifest['qualification_scope'] == 'Isaac Sim 4.5 Fehling r7 rack and bath prescribed fixtures'
        assert len(set(manifest['runtime_qualification']['process_ids'])) == 3
        for name, expected in manifest['runtime_evidence_sha256'].items():
            assert producer.file_sha(package/name) == expected
    else:
        assert manifest['claims']['runtime_qualified'] is False
    assert manifest['static_validation']['status'] == 'pass'
    assert manifest['entrypoints'] == dict(root_usd='asset.usd', default_prim='World',
                                         asset_entry_prim='/World/TestTube')
    assert producer.audit_package(package)['status'] == 'pass'
    copied = tmp_path/'copied'
    shutil.copytree(package, copied)
    manifest['asset_sha256'] = '0'*64
    (copied/'evidence/manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='manifest asset hash'):
        producer.audit_package(copied)
    manifest['asset_sha256'] = producer.file_sha(copied/'asset.usd')
    (copied/'evidence/manifest.json').write_text(json.dumps(manifest))
    with (copied/'deps/mdl/OmniGlass_Opacity.mdl').open('a') as stream:
        stream.write('\n// changed dependency\n')
    with pytest.raises(ValueError, match='MDL dependency hash'):
        producer.audit_package(copied)
