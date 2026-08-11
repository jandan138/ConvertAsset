from __future__ import annotations

import json
from pathlib import Path

from scripts.build_scientific_workbench_closure_assets import build_closure_assets


def test_closure_asset_build_keeps_measured_stopper_and_pair_geometry(tmp_path: Path) -> None:
    source = tmp_path / "stopper.usda"
    source.write_text(
        '#usda 1.0\n(defaultPrim = "root" metersPerUnit = 1 upAxis = "Z")\n'
        'def Xform "root" {}\n',
        encoding="utf-8",
    )
    rack = tmp_path / "rack.usda"
    rack.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    result = build_closure_assets(stopper_source=source, rack_source=rack, out=tmp_path / "out")

    fit = json.loads(result["fit_report"].read_text(encoding="utf-8"))
    assert fit["status"] == "pass"
    assert fit["measurements_mm"]["rack_aperture_diameter"] == 28.33
    assert fit["measurements_mm"]["stopper_joint_max_diameter"] == 25.3
    assert fit["measurements_mm"]["stopper_handle_width"] == 30.0
    assert fit["gates"]["joint_passes_aperture"]["status"] == "pass"
    assert fit["gates"]["handle_is_retained"]["status"] == "pass"

    stopper_profile = json.loads(result["stopper_interaction"].read_text(encoding="utf-8"))
    assert stopper_profile["asset_entry_prim"] == "/World/GroundGlassStopper2942"
    assert stopper_profile["named_frames"]["joint_tip"]["translation_body_local_usd"] == [
        0.0,
        0.0,
        0.0,
    ]

    flask_profile = json.loads(result["flask_interaction"].read_text(encoding="utf-8"))
    assert flask_profile["named_frames"]["closure_seat"]["translation_body_local_usd"] == [
        0.0,
        0.0,
        0.12814,
    ]
    assert "29/42" in result["flask_source"].read_text(encoding="utf-8")
