import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_bad11_analysis import estimate_alignment,ARM_DOF_INDICES,SOURCE_ARM_COLUMNS,pair_group


def test_alignment_estimates_this_case_not_415():
    rng=np.random.default_rng(7);commands=rng.normal(size=(1000,16));poses=[]
    for i in range(600,700):
        q=np.zeros(25);q[ARM_DOF_INDICES]=commands[i-423,SOURCE_ARM_COLUMNS];poses.append({'index':i,'joint_positions':q.tolist()})
    assert estimate_alignment(poses,commands)['best']['native_minus_source_index']==423


def test_cup_shape_pair_keeps_region_and_actual_cup_collider():
    row={'actors':['/World/_scene/obj_beaker','/World/_scene/obj_sample_tube'],'colliders':['/World/_scene/obj_beaker/Visual/HollowBody','/World/_scene/obj_sample_tube/RigidWallProxy/Wall_03_11']}
    assert pair_group(row)=='tube_bath | Wall_03 | Visual/HollowBody'
