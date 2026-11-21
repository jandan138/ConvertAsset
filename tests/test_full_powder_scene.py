import numpy as np
from scipy.spatial import cKDTree

from scripts.build_full_powder_scene import preparation_positions, canonical_grains


def test_preparation_column_fits_throat_and_has_no_initial_overlap():
    points = np.array(preparation_positions(.084,10240,.0007,42))
    assert np.linalg.norm(points[:,:2],axis=1).max()<.024-.0007*1.182056-.00075
    assert points[:,2].min()>.084+.0007*1.182056
    assert points[:,2].max()>.100
    assert cKDTree(points).query(points,k=2)[0][:,1].min()>2*.0007*1.182056
    np.testing.assert_array_equal(points,preparation_positions(.084,10240,.0007,42))


def test_persisted_grains_follow_canonical_bottle_not_preparation_drift():
    angle = np.sqrt(.5)
    bottle = np.array([1.,2.,3.,0.,0.,angle,angle])
    points = np.array([[1.,2.01,3.095]])
    rotations = np.array([[angle,0.,0.,angle]])
    xyz,q = canonical_grains(points,rotations,bottle,[-.08,-.065,.756])
    np.testing.assert_allclose(xyz,[[-.07,-.065,.851]],atol=1e-12)
    np.testing.assert_allclose(q,[[1.,0.,0.,0.]],atol=1e-12)
