import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal/extract_target_pool.py'
s=importlib.util.spec_from_file_location('formal_targets',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_order_independent_category_diversity():
 rows=[dict(scene_id='S',prim=f'/Root/{c}/{i}',category=c) for c in ['cup','chair','lamp','book','plate','bottle','sofa','shelf'] for i in range(2)]
 first,reserve=m.choose_targets(rows);second,_=m.choose_targets(list(reversed(rows)))
 assert first==second and len(first)==8 and len({r['category'] for r in first})==8
 assert not ({r['prim'] for r in first}&{r['prim'] for r in reserve})
def test_small_pool_not_inflated():
 rows=[dict(scene_id='S',prim='/A',category='cup')]
 assert m.choose_targets(rows)==(rows,[])
