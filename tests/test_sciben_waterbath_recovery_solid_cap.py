import sys
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))

def test_solid_cap_does_not_fill_cavity_and_preserves_union():
    from sciben_silver_bad09_probe import tube_proxy_cells_v2
    from sciben_waterbath_recovery_solid_cap import repartition
    cells={n:v for n,v in tube_proxy_cells_v2() if n.startswith('Bottom_')}
    cap,upper,audit=repartition(cells)
    assert len(upper)==48 and audit['untouched_shapes']==96
    assert len(ConvexHull(cap).vertices)<=64
    assert cap[:,2].max()<audit['minimum_inner_z_m']
    assert abs(audit['relative_volume_delta'])<1e-6
    assert audit['old_lower_vertices_outside_new_cap_m']<2e-9
    assert audit['new_cap_boundary_outside_old_union_m']<2e-9
    for n,v in upper.items():assert v[:,2].min()>=audit['cut_z_m']-1e-12
