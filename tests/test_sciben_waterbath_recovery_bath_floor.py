import sys
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))

def test_floor_merge_preserves_128_segment_disk_and_height():
    from sciben_waterbath_recovery_bath import bath_cells
    from sciben_waterbath_recovery_bath_floor import merge_floor_cells
    old=[v for n,v in bath_cells() if n.startswith('Floor_')]
    new=merge_floor_cells(old)
    assert len(new)==8
    assert max(len(ConvexHull(v).vertices) for v in new)<=64
    assert np.isclose(sum(ConvexHull(v).volume for v in old),sum(ConvexHull(v).volume for v in new),rtol=1e-12,atol=1e-15)
    assert all(np.array_equal(np.unique(v[:,2]),[0,.003]) for v in new)
    old_arc=set(map(tuple,np.concatenate(old)))
    assert set(map(tuple,np.concatenate(new)))==old_arc
