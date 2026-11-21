import math
from collections import Counter

import pytest

from scripts.build_titration_tip_r4 import tip_mesh, inner_radius, lower_profile


def test_open_downward_taper_has_positive_wall_and_outward_faces():
    points,counts,indices,normals=tip_mesh()
    assert len(points)==384
    assert sum(counts)==len(indices)==len(normals)
    edges=Counter()
    cursor=0
    for count in counts:
        ids=indices[cursor:cursor+count]
        for a,b in zip(ids,ids[1:]+ids[:1]):
            edges[tuple(sorted((a,b)))]+=1
        a,b,c=[points[i] for i in ids[:3]]
        u=[b[i]-a[i] for i in range(3)]
        v=[c[i]-a[i] for i in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        assert sum(cross[i]*normals[cursor][i] for i in range(3))>0
        cursor+=count
    assert set(edges.values())=={2}
    assert all(math.hypot(x,y)>0 for x,y,z in points)
    assert min(z for x,y,z in points)==pytest.approx(-.03)
    assert max(z for x,y,z in points)==pytest.approx(.02)
    assert inner_radius(-.28)==pytest.approx(.0004)
    assert inner_radius(-.23)==pytest.approx(.00155)


def test_precharge_follows_lumen_and_keeps_outlet_clear():
    profile=lower_profile()
    assert profile[0][0]==pytest.approx(-.2798)
    assert profile[0][1]<.0004
    assert profile[-1]==(-.09,.005)
    for (za,ra),(zb,rb) in zip(profile,profile[1:]):
        for i in range(101):
            z=za+(zb-za)*i/100
            r=ra+(rb-ra)*i/100
            if z<=-.23:
                assert r<inner_radius(z)
                assert inner_radius(z)-r==pytest.approx(.00005)
