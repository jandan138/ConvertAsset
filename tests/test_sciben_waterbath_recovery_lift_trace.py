import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_lift_trace import particle_summary


def test_particle_trace_keeps_original_cavity_tolerance_and_indices():
    p=np.array([[0,0,.001],[0,0,-.0014],[.02,0,.04]]);v=np.zeros_like(p);r=particle_summary(p,v,[[.0011,.002],[.15,.008]],.001)
    assert r['bad_indices']==[1,2] and r['outside_count']==2 and r['lowest_index']==1
    assert abs(r['selected_particles'][0]['margin_m']+.0015)<1e-12
