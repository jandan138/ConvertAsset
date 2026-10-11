import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_trace_analysis import contact_stats,rack_region


def test_v1_negative_header_is_only_a_bound():
    rows=[dict(index=1,points=10,minimum_separation_m=-.001,colliders=[]),dict(index=1,points=20,minimum_separation_m=.001,colliders=[])]
    r=contact_stats(rows);assert r['negative_points_exact'] is None;assert r['negative_point_bounds']==[1,10];assert r['certain_nonnegative_points_from_minimum']==20;assert r['max_points_per_frame']==30


def test_v2_counts_zero_separation_as_nonnegative_and_groups_cap():
    row=dict(index=7,points=9,minimum_separation_m=-.0001,negative_points=2,nonnegative_points=7,colliders=['/World/_scene/obj_sample_tube/RigidSolidBottom/SolidCap','/World/_scene/obj_tube_rack/Cube_015']);r=contact_stats([row]);assert r['negative_points_exact']==2;assert r['max_negative_points_per_frame']==2;assert rack_region(row)=='Cube_015 | solid_cap'
