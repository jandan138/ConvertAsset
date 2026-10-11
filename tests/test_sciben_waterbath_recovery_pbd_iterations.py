import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_pbd_iterations import author


def test_iteration_range_does_not_accept_substeps_or_unbounded_values():
    for value in [0,256,1.5]:
        with pytest.raises(ValueError):author(None,value)
