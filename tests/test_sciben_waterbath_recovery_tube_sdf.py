import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_tube_sdf import sdf_distances


def test_sdf_margin_is_dimensionless_diagonal_fraction_not_metres():
    r=sdf_distances([.02,.02,.15]);assert np.isclose(r['margin_world_m'],np.linalg.norm([.02,.02,.15])*.01);assert r['margin_world_m']>.0015;assert np.isclose(r['uniform_grid_spacing_m'],.15/512)
