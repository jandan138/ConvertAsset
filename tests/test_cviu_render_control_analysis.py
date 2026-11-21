import importlib.util
import json
import sys
from pathlib import Path
import pytest

DIRECTORY = Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal'
sys.path.insert(0, str(DIRECTORY))
spec = importlib.util.spec_from_file_location('render_controls_analysis', DIRECTORY/'analyze_render_controls.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(hit, point):
    return {'hit': hit, 'valid_point': point is not None,
            'point_normalized': point, 'raw_response': str(point)}


def test_canceling_render_gains_losses_remain_visible():
    a, b = row(True, [100, 100]), row(False, [200, 100])
    result = m.summarize([m.compare(a, b), m.compare(b, a)])
    assert result['gain'] == result['loss'] == 1
    assert result['hit_flip'] == 2
    assert result['mean_point_displacement_px'] == pytest.approx(102.4)


def test_invalid_points_do_not_silently_enter_displacement_denominator():
    a, b = row(False, None), row(True, [100, 100])
    result = m.summarize([m.compare(a, b), m.compare(b, b)])
    assert result['n'] == 2
    assert result['validity_flip'] == 1
    assert result['valid_pair_count_for_displacement'] == 1
    assert result['mean_point_displacement_px'] == 0


def test_runtime_failed_run_rejected_before_scoring(tmp_path):
    (tmp_path/'completion.json').write_text(json.dumps({'mode': 'render_control',
        'records': 96, 'runtime_errors': 1, 'status': 'incomplete_runtime_errors'}))
    with pytest.raises(ValueError, match='incomplete'):
        m.load_verified_run(tmp_path, tmp_path/'missing.json', [None]*96,
                            '8b', 'render_control', 'unused')
