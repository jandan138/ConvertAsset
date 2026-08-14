from __future__ import annotations

from scripts.audit_scientific_workbench_asset_library import CATALOG


def test_phase_2_role_candidate_contract_is_16_assets() -> None:
    phase_2 = [asset for asset in CATALOG if asset.phase == 2]

    assert len(phase_2) == 16
    assert sum(asset.role == "rigid_tool" for asset in phase_2) == 10
    assert sum(asset.role == "receptacle_support" for asset in phase_2) == 4
    assert sum(asset.role == "instrument_static" for asset in phase_2) == 2


def test_phase_1_role_candidate_contract_is_13_assets() -> None:
    phase_1 = [asset for asset in CATALOG if asset.phase == 1]

    assert len(phase_1) == 13
    assert sum(asset.role == "liquid_container" for asset in phase_1) == 12
    assert sum(asset.role == "liquid_conduit" for asset in phase_1) == 1
