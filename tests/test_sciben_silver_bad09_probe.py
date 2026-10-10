"""Raw model actions must be replayed without trajectory or base reinterpretation."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('silver_probe',Path(__file__).parents[1]/'scripts/sciben_silver_bad09_probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_exact_targets_and_absolute_base():
    targets=np.arange(16,dtype=float)/100
    action,base=m.normalize_action({'arm_action':targets,'base_motion':[.1,-.2,.3]})
    np.testing.assert_allclose(action,targets)
    np.testing.assert_allclose(base,[.1,-.2,.3])

def test_invalid_action_fails_before_simulation():
    for value in [np.zeros(15),np.r_[np.zeros(15),np.nan]]:
        with pytest.raises(ValueError):m.normalize_action({'arm_action':value,'base_motion':[0,0,0]})

def test_baseline_absolute_yaw_uses_degrees():
    np.testing.assert_allclose(m.sdk_base_targets([.1,-.2,90]),[.1,-.2,np.pi/2])
    np.testing.assert_allclose(m.sdk_base_targets([.1,-.2,90],legacy_raw=True),[.1,-.2,90])
