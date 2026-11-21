import importlib.util
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal/prepare_views.py'
s=importlib.util.spec_from_file_location('formal_views',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_triangle_blocks_before_target_not_behind():
 tri=np.array([[[-1,-1,0],[1,-1,0],[0,1,0]]],dtype=float)
 assert m.intersects_triangles(np.array([0,0,-1.]),np.array([0,0,1.]),tri,1.)
 assert not m.intersects_triangles(np.array([0,0,-1.]),np.array([0,0,1.]),tri,.4)
 assert not m.intersects_triangles(np.array([2,2,-1.]),np.array([2,2,1.]),tri,1.)
def test_parallel_box_ray():
 assert m.aabb_entry(np.array([2.,0,0]),np.array([2.,0,1]),np.array([-1,-1,-1]),np.array([1,1,1])) is None
 assert m.aabb_entry(np.array([0.,0,-2]),np.array([0.,0,2]),np.array([-1,-1,-1]),np.array([1,1,1]))==.25
