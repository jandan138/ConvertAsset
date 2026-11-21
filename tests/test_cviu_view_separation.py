import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('view_checks', Path(__file__).resolve().parents[1] / 'paper/shared/evidence/experiments/13_cviu_formal/check_view_selections.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_wrapped_angles():
    assert m.separation(350, 20) == 30
    assert m.separation(350, 10) == 20


def test_back_vector_and_up_axis():
    camera = {'xformOp:transform': '((1,0,0,0),(0,1,0,0),(0,1,0,0),(100,200,300,1))'}
    assert m.camera_azimuth(camera, 'Z') == 90
    with pytest.raises(ValueError, match='Vertical'):
        m.camera_azimuth(camera, 'Y')
