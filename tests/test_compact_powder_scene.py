import importlib.util
from pathlib import Path

import numpy as np
import pytest


def module():
    path = Path(__file__).resolve().parents[1]/'scripts/build_compact_powder_scene.py'
    spec = importlib.util.spec_from_file_location('compact_scene',path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PROFILE = [dict(z=.002,radius=.0282,exponent=5.),dict(z=.066,radius=.0282,exponent=5.),
           dict(z=.09,radius=.024,exponent=2.),dict(z=.1,radius=.0249,exponent=2.)]


def test_deep_fill_uses_profile_and_bounded_clearance():
    from scipy.spatial import cKDTree
    mod = module()
    xyz = np.asarray(mod.fill_positions(PROFILE,.059,12288,.0007,42))
    assert xyz.shape == (12288,3)
    assert xyz[:,2].min()>.0598
    assert xyz[:,2].max()<.095
    assert cKDTree(xyz).query(xyz,k=2)[0][:,1].min()>.0017
    for point in xyz[::31]:
        assert mod.in_profile(point,PROFILE,margin=.00155)
    assert np.array_equal(xyz,mod.fill_positions(PROFILE,.059,12288,.0007,42))
    with pytest.raises(ValueError):
        mod.fill_positions(PROFILE,.059,1000000,.0007,42)


def test_geometry_mass_and_inertia_scale_consistently():
    mod = module()
    mass, inertia = mod.grain_properties(.0007)
    base_mass, base_inertia = mod.grain_properties(.0005)
    assert mass == pytest.approx(base_mass*1.4**3)
    assert inertia == pytest.approx(base_inertia*1.4**5)
    with pytest.raises(ValueError):
        mod.grain_properties(0.)
