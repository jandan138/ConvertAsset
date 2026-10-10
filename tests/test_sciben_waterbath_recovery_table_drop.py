import importlib.util,json
from pathlib import Path
import numpy as np

def test_native_json_preserves_numpy_false_and_numeric_values():
    path=Path(__file__).parents[1]/"scripts/sciben_waterbath_recovery_table_drop.py"
    spec=importlib.util.spec_from_file_location("drop_fixture",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data={"gate":np.bool_(False),"count":np.int64(480),"depth":np.float64(-.003)}
    assert json.loads(json.dumps(data,default=module.json_scalar))=={"gate":False,"count":480,"depth":-.003}
