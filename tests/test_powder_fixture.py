"""Physical authoring checks for the powder producer's bounded fixture."""
import importlib.util
import math
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build_powder_fixture.py'


def module():
    spec = importlib.util.spec_from_file_location('powder_fixture', SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_mass_is_geometric_not_display_tuned():
    mod = module()
    assert mod.grain_mass_kg(.0003, 1500) == pytest.approx(1.696460032938488e-7)
    assert mod.grain_mass_kg(.0006, 1500) == pytest.approx(8*mod.grain_mass_kg(.0003, 1500))
    for radius, density in [(0, 1500), (-1,1500), (.001, math.nan)]:
        with pytest.raises(ValueError):
            mod.grain_mass_kg(radius, density)


def test_initial_fill_has_clearance_and_stable_ids():
    mod = module()
    points = mod.fill_positions(200, .0004, .00003, 42)
    import numpy as np
    p = np.array(points)
    delta = p[:, None] - p[None, :]
    distance = np.linalg.norm(delta, axis=2)
    np.fill_diagonal(distance, np.inf)
    assert distance.min() >= .00086
    assert np.max(abs(p[:,0])) + .0004 < .015
    assert np.max(abs(p[:,1])) + .0004 < .012
    assert np.array_equal(p, mod.fill_positions(200,.0004,.00003,42))
    assert not np.array_equal(p, mod.fill_positions(200,.0004,.00003,43))
    with pytest.raises(ValueError):
        mod.fill_positions(1000000,.001,.00003,42)
