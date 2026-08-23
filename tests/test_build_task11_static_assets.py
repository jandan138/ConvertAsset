from __future__ import annotations

import ast
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts/build_task11_static_assets.py"


def test_task11_builder_keeps_source_boundaries_and_static_claims() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)
    assert "LidOpenStaticButton" in source
    assert "lid_open_button_joint" in source
    assert "stop_button_joint" in source
    assert '"causal_lid_transition": "pending"' in source
    assert '"observable_power_off_transition": "pending"' in source
    assert '"button_causes_lid_open": False' in source
    assert "PhysxSDFMeshCollisionAPI" in source
    assert "sdf_resolution" in source
    assert "particles_included" in source
