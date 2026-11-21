import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'gear_leadin', Path(__file__).parents[1] / 'scripts/build_ebench_gear_leadin.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_protected_hole_upper_teeth_and_zero_control():
    for point in ([0.02525, 0, 0.005], [0.02025, 0, 0.005],
                  [0.04125, 0, 0.009], [0.04125, 0, 0.015]):
        assert MODULE.relief_point(point, 0.002) == point
    assert MODULE.relief_point([0.04125, 0, 0.005], 0) == [0.04125, 0, 0.005]


def test_lower_tooth_relief_keeps_height_and_angular_direction():
    point = [0.02025, 0.021, 0.005]
    assert MODULE.relief_point(point, 0.002) == pytest.approx([0.02025, 0.019, 0.005])
    assert MODULE.relief_point([0.02025, 0.021, 0.007], 0.002) == pytest.approx(
        [0.02025, 0.020, 0.007])
    with pytest.raises(ValueError):
        MODULE.relief_point(point, 0.01)
