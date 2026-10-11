import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_shared_cap import replace_filter_targets


def test_remove_only_real_cap_keep_all_other_bottom_filters():
    targets=['cap']+['bottom'+str(i) for i in range(144)];result=replace_filter_targets(targets,'cap','floor');assert result==targets[1:];assert len(targets)==145


def test_reject_an_already_filtered_pbd_floor():
    with pytest.raises(ValueError):replace_filter_targets(['cap','floor']+list(map(str,range(143))),'cap','floor')
