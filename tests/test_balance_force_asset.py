from scripts.build_balance_force_asset import repaired_mass, safe_member
import pytest


def test_mass_repair_uses_declared_instrument_mass_not_stability_hack():
    assert repaired_mass(1000000, 6.8) == 6.8
    with pytest.raises(ValueError):
        repaired_mass(1000000, None)


def test_archive_members_cannot_escape_extraction_root():
    assert safe_member('task_09_solid_weighing/SubUSDs/a.mdl')
    assert not safe_member('../escape')
    assert not safe_member('/absolute')
