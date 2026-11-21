import importlib.util,sys
from pathlib import Path
import pytest
DIRECTORY=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal'
sys.path.insert(0,str(DIRECTORY))
spec=importlib.util.spec_from_file_location('freeze_formal',DIRECTORY/'freeze_formal_inputs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def docs(n=30):return [(Path(f'{i}.json'),{'scene_id':str(i),'status':'qualified_scene_inputs'}) for i in range(n)]

def test_complete_frozen_order_preserved():
    expected=[str(i) for i in reversed(range(30))]
    assert [r['scene_id'] for _,r in m.require_cohort(expected,docs())]==expected

def test_partial_or_substituted_cohort_rejected():
    expected=[str(i) for i in range(30)]
    with pytest.raises(ValueError,match='missing 14'):m.require_cohort(expected,docs(16))
    changed=docs();changed[-1][1]['scene_id']='replacement_scene'
    with pytest.raises(ValueError,match='extra 1'):m.require_cohort(expected,changed)

def test_duplicate_and_unqualified_rejected():
    expected=[str(i) for i in range(30)]
    with pytest.raises(ValueError,match='Duplicate'):m.require_cohort(expected,docs()+docs(1))
    bad=docs();bad[0][1]['status']='pending'
    with pytest.raises(ValueError,match='Unqualified'):m.require_cohort(expected,bad)
