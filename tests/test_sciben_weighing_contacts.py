"""Geometry audit stays separate from claims about SDK contacts."""
import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    'sciben_weighing_contacts', Path(__file__).parents[1] / 'scripts/sciben_weighing_contacts.py'
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_triangulate_preserves_quad_winding():
    assert MODULE.triangulate([4], [0, 1, 2, 3]).tolist() == [[0, 1, 2], [0, 2, 3]]


def test_vertical_hits_reject_outside_triangle():
    points = np.array([[0., 0., 2.], [1., 0., 2.], [0., 1., 2.]])
    faces = np.array([[0, 1, 2]])
    assert MODULE.vertical_hits(points, faces, [.2, .2]) == [2.]
    assert MODULE.vertical_hits(points, faces, [.9, .9]) == []


def test_vertical_hits_merge_shared_face_edge():
    points = np.array([[0., 0., 2.], [1., 0., 2.], [1., 1., 2.], [0., 1., 2.]])
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    assert MODULE.vertical_hits(points, faces, [.5, .5]) == [2.]


def test_topology_detects_open_triangle():
    result = MODULE.topology(np.array([[0, 1, 2]]))
    assert result['boundary_edges'] == 3
    assert not result['closed_two_manifold']


def test_topology_closed_tetrahedron():
    result = MODULE.topology(np.array([[0, 2, 1], [0, 1, 3], [1, 2, 3], [2, 0, 3]]))
    assert result['closed_two_manifold']
    assert result['inconsistently_oriented_edges'] == 0


def test_candidate_only_authors_missing_static_collisions(tmp_path):
    import pytest
    pytest.importorskip('pxr')
    from pxr import Usd, UsdGeom, UsdPhysics
    source = tmp_path / 'source.usda'
    stage = Usd.Stage.CreateNew(str(source))
    for path in MODULE.BACKGROUND_PATHS:
        UsdGeom.Xform.Define(stage, path)
        UsdGeom.Cube.Define(stage, path + '/Shape')
    stage.GetRootLayer().Save()
    out = tmp_path / 'candidate.usda'
    result = MODULE.author_background_candidate(source, out)
    assert result['shape_count'] == 5
    patch = Usd.Stage.Open(str(out))
    assert patch.GetRootLayer().subLayerPaths == []
    for path in MODULE.BACKGROUND_PATHS:
        prim = patch.GetPrimAtPath(path + '/Shape')
        assert prim.HasAPI(UsdPhysics.CollisionAPI)
        assert not prim.HasAPI(UsdPhysics.RigidBodyAPI)
        assert set(a.GetName() for a in prim.GetAttributes() if a.HasAuthoredValueOpinion()) == {'physics:collisionEnabled'}


def test_candidate_rejects_dynamic_background(tmp_path):
    import pytest
    pytest.importorskip('pxr')
    from pxr import Usd, UsdGeom, UsdPhysics
    source = tmp_path / 'source.usda'
    stage = Usd.Stage.CreateNew(str(source))
    prim = UsdGeom.Xform.Define(stage, MODULE.BACKGROUND_PATHS[0]).GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(prim)
    stage.GetRootLayer().Save()
    with pytest.raises(ValueError, match='Dynamic background'):
        MODULE.author_background_candidate(source, tmp_path / 'candidate.usda')


def test_candidate_accepts_explicit_context_roots(tmp_path):
    import pytest
    pytest.importorskip('pxr')
    from pxr import Usd, UsdGeom
    source = tmp_path / 'source.usda'
    stage = Usd.Stage.CreateNew(str(source))
    UsdGeom.Cube.Define(stage, '/World/context/Prop/Shape')
    stage.GetRootLayer().Save()
    result = MODULE.author_background_candidate(source, tmp_path / 'candidate.usda', ['/World/context/Prop'])
    assert result['paths'] == ['/World/context/Prop/Shape']


def test_candidate_rejects_rigid_ancestor(tmp_path):
    import pytest
    pytest.importorskip('pxr')
    from pxr import Usd, UsdGeom, UsdPhysics
    source = tmp_path / 'source.usda'
    stage = Usd.Stage.CreateNew(str(source))
    prim = UsdGeom.Xform.Define(stage, '/World/context').GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdGeom.Cube.Define(stage, '/World/context/Prop/Shape')
    stage.GetRootLayer().Save()
    with pytest.raises(ValueError, match='Dynamic background'):
        MODULE.author_background_candidate(source, tmp_path / 'candidate.usda', ['/World/context/Prop'])
