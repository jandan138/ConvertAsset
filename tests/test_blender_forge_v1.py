"""Tests for the Unified Blender 4.4+ -> OpenUSD SimReady Asset Forge."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from convert_asset.blender_forge.contracts import (
    MIN_BLENDER_VERSION,
    BlenderVersionError,
    resolve_blender44_bin,
)


PILOT_OUT_ROOT = Path(
    r"I:\cpfs\shared\simulation\zhuzihou\dev\ConvertAsset\external_artifacts\blender_forge_pilots_20261121"
)


def test_resolve_blender44_finds_443_and_rejects_legacy_36() -> None:
    info = resolve_blender44_bin()
    assert info.version >= MIN_BLENDER_VERSION
    legacy = Path(r"G:\my_program\blender\blender.exe")
    if legacy.is_file():
        with pytest.raises(BlenderVersionError):
            resolve_blender44_bin(legacy)


def test_forged_pilots_pass_hygiene_and_emit_simready_deliverables() -> None:
    inc_handoff = PILOT_OUT_ROOT / "precision_benchtop_incubator_01" / "forge_manifest_and_critic_handoff.json"
    cro_handoff = PILOT_OUT_ROOT / "blender_croissant_artisan_01" / "forge_manifest_and_critic_handoff.json"
    if not (inc_handoff.is_file() and cro_handoff.is_file()):
        pytest.skip("Run convert_asset.blender_forge.runner --pilot all first")

    inc = json.loads(inc_handoff.read_text(encoding="utf-8"))
    assert inc["hygiene_report"]["overall_passed"] is True
    assert inc["hygiene_report"]["dimension_gate_passed"] is True
    assert inc["hygiene_report"]["manifold_gate_passed"] is True
    assert inc["hygiene_report"]["uv_present"] is True
    assert inc["hygiene_report"]["visual_collision_separated"] is True
    usda_path = Path(inc["deliverables"]["simready_usda"])
    assert usda_path.is_file()
    usda_text = usda_path.read_text(encoding="utf-8")
    assert "PhysicsArticulationRootAPI" in usda_text
    assert 'def Xform "grasp"' in usda_text
    assert Path(inc["deliverables"]["studio_contact_sheet"]).is_file()

    cro = json.loads(cro_handoff.read_text(encoding="utf-8"))
    assert cro["hygiene_report"]["overall_passed"] is True
    assert cro["hygiene_report"]["dimension_gate_passed"] is True
    assert cro["hygiene_report"]["manifold_gate_passed"] is True
    assert Path(cro["deliverables"]["deformable_bundle_v02_manifest"]).is_file()
    assert len(cro["deliverables"]["deformable_bundle_v02_engines"]) == 4
    assert Path(cro["deliverables"]["studio_contact_sheet"]).is_file()

