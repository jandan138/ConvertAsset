import importlib.util
from pathlib import Path
import pytest
p=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/12_cviu_diagnostics/analyze_pilot.py'
s=importlib.util.spec_from_file_location('pilot_analysis',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def rows():
 return [dict(pair_id=p,condition=c,repeat=i,status='ok',hit=(p=='a')==(c=='original'),scene_id='scene',image={'path':'fixture'}) for p in ['a','b'] for c in ['original','converted'] for i in range(3)]
def test_equal_means_hide_turnover():
 r=m.summarize(rows())
 assert all(x['original_hits']==x['converted_hits']==1 and x['flips']==2 for x in r['by_repeat'])
 assert r['within_condition']['original']['rate']==0
 assert all(x['original_hit_rate']==.5 and x['converted_hit_rate']==.5 and x['flip_rate']==1 for x in r['by_repeat'])
 assert r['by_repeat'][0]['original_valid_point_rate'] is None

def test_repeat_noise_and_missing():
 data=rows();data[0]['hit']=False
 assert m.summarize(data)['within_condition']['original']['rate']==pytest.approx(1/3)
 with pytest.raises(ValueError,match='Incomplete'):m.summarize(data[:-1])

def test_runtime_errors_not_misses():
 data=rows();data[0].update(status='runtime_error',hit=None)
 with pytest.raises(ValueError,match='runtime'):m.summarize(data)
