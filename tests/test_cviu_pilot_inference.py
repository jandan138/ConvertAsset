import importlib.util
from pathlib import Path
import pytest
p=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/12_cviu_diagnostics/pilot_inference.py'
s=importlib.util.spec_from_file_location('pilot_inference',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
@pytest.mark.parametrize('text,expected', [('Point: 12, 30',[12.,30.]),('Point: -1, 1001',[-1.,1001.]),('The point is 12,30',None),('Point: 1,2\nPoint: 3,4',None),('Point: nan,20',None)])
def test_parse(text,expected):assert m.parse_point(text)==expected

def test_empty_pilot_rejected():
 with pytest.raises(ValueError,match='Incomplete paired'):m.validate_manifest({'records':[]})

def test_pair_task_mismatch_rejected(tmp_path):
 image=tmp_path/'image';image.write_bytes(b'image')
 mask=tmp_path/'mask';mask.write_bytes(b'mask')
 rows=[]
 for scene in range(3):
  for target in range(2):
   for view in range(2):
    for condition in ['original','converted']:
     rows.append(dict(pair_id=f'{scene}:{target}:{view}',scene_id=str(scene),target_prim=f'/target{target}',view_id=str(view),query='Point to the target.',condition=condition,visual_qa='PASS',image={'path':str(image),'sha256':m.sha(image)},mask={'path':str(mask),'sha256':m.sha(mask)}))
 assert len(m.validate_manifest({'records':rows}))==24
 rows[1]['query']='Point to a different target.'
 with pytest.raises(ValueError,match='Paired query mismatch'):m.validate_manifest({'records':rows})
