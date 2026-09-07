import pytest


def test_open_tube_source_removes_cap_without_sealing_mouth():
    pytest.importorskip('pxr')
    from scripts.build_fehlings_open_tube import mass_ratio
    assert mass_ratio(3.0, 1.0, 0.019) == pytest.approx(0.01425)
