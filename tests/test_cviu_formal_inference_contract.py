"""Reject cohort drift and unqualified inputs without discarding visibility loss."""
import copy
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('formal_inference', Path(__file__).resolve().parents[1] / 'paper/shared/evidence/experiments/13_cviu_formal/formal_inference.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def manifest():
    rows = []
    for scene in range(30):
        for target in range(8):
            for view in range(2):
                for condition in ['original', 'converted']:
                    rows.append({'scene_id': str(scene), 'target_prim': str(target), 'view_id': str(view),
                                 'pair_id': f'{scene}:{target}:{view}', 'condition': condition,
                                 'query': 'Point to the object.', 'technical_qa': 'PASS', 'original_qualification': 'PASS'})
    return {'status': 'frozen_formal_inputs', 'records': rows}


def test_full_cohort_and_pair_contract():
    data = manifest()
    assert len(m.validate_structure(data, map(str, range(30)))) == 960
    bad = copy.deepcopy(data)
    bad['records'][-1] = bad['records'][0]
    with pytest.raises(ValueError, match='Duplicate'):
        m.validate_structure(bad, map(str, range(30)))
    bad = copy.deepcopy(data)
    bad['records'][0]['query'] = 'different query'
    with pytest.raises(ValueError, match='Paired identity'):
        m.validate_structure(bad, map(str, range(30)))
    with pytest.raises(ValueError, match='cohort mismatch'):
        m.validate_structure(data, map(str, range(1, 31)))


def test_no_silent_small_or_unqualified_dataset():
    data = manifest()
    data['records'].pop()
    with pytest.raises(ValueError, match='960'):
        m.validate_structure(data, map(str, range(30)))
    data = manifest()
    data['records'][0]['technical_qa'] = 'pending'
    with pytest.raises(ValueError, match='Unqualified'):
        m.validate_structure(data, map(str, range(30)))


def test_empty_converted_mask_retained_but_empty_original_rejected(tmp_path):
    import numpy as np
    from PIL import Image
    image = tmp_path / 'image.png'
    mask = tmp_path / 'mask.npy'
    Image.new('RGB', (1024, 768), 'gray').save(image)
    np.save(mask, np.zeros((768, 1024), dtype=bool))
    row = {'condition': 'converted', 'image': {'path': str(image), 'sha256': m.sha(image)},
           'mask': {'path': str(mask), 'sha256': m.sha(mask)}}
    m.validate_files([row])
    row['condition'] = 'original'
    with pytest.raises(ValueError, match='visible target'):
        m.validate_files([row])


def control_fixture():
    primary=manifest()['records']
    for row in primary:
        key=row['pair_id']+row['condition']
        row['image']={'path':'primary/'+key,'sha256':key}
        row['capture_receipt']='primary/'+key+'.json'
    controls=copy.deepcopy([r for r in primary if r['scene_id'] in ['0','1','2']])
    for row in controls:
        row['render_repeat_of_image_sha256']=row['image']['sha256']
        row['image']['path']=row['image']['path'].replace('primary/','control/')
        row['capture_receipt']=row['capture_receipt'].replace('primary/','control/')
    return primary,{'status':'frozen_render_control_inputs','records':controls}


def test_controls_bound_to_full_primary_cohort_and_independent_capture():
    primary,control=control_fixture()
    assert len(m.validate_control_structure(control,primary,['0','1','2']))==96
    with pytest.raises(ValueError,match='Complete primary'):
        m.validate_control_structure(control,primary[:96],['0','1','2'])
    control['records'][0]['image']['path']=primary[0]['image']['path']
    with pytest.raises(ValueError,match='independent capture'):
        m.validate_control_structure(control,primary,['0','1','2'])


def test_controls_reject_identity_drift_and_wrong_primary_binding():
    primary,control=control_fixture()
    bad=copy.deepcopy(control);bad['records'][0]['query']='different query'
    with pytest.raises(ValueError,match='identity mismatch'):
        m.validate_control_structure(bad,primary,['0','1','2'])
    bad=copy.deepcopy(control);bad['records'][0]['render_repeat_of_image_sha256']='wrong'
    with pytest.raises(ValueError,match='linked to primary'):
        m.validate_control_structure(bad,primary,['0','1','2'])
