"""Tests for Blender 4.4.3 ART-001 articulated mechanisms in distillation_v07."""

from __future__ import annotations

import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parents[1] / "external_artifacts" / "distillation_v07_assets"


def test_v07_blender44_articulated_mechanisms_and_agx_sheet() -> None:
    mp = OUT_DIR / "v07_mechanisms_manifest.json"
    hp = OUT_DIR / "forge_manifest_and_critic_handoff.json"
    assert mp.is_file() and hp.is_file(), "Run scripts/build_m1_distillation_v07_mechanisms.py first"
    m = json.loads(mp.read_text(encoding="utf-8"))
    h = json.loads(hp.read_text(encoding="utf-8"))
    assert tuple(int(x) for x in str(m["blender_version"]).split(".")[:2]) >= (4, 4)
    assert Path(m["studio_contact_sheet"]).is_file()
    assert h["hygiene_report"]["overall_passed"] is True
    assert h["hygiene_report"]["visual_collision_separated"] is True
    for mid in ("scissor_jack_blue_art001", "flask_clamp_2prong_art001", "condenser_clamp_3prong_art001"):
        assert len(m["mechanisms"][mid]) == 3
        uinfo = m["simready_art001_usd"][mid]
        usda_p = Path(uinfo["usda_path"])
        assert usda_p.is_file()
        txt = usda_p.read_text(encoding="utf-8")
        assert "PhysicsArticulationRootAPI" in txt
        assert 'scenarioForge:namedFrame = "grasp"' in txt
        assert uinfo["collision_triangles"] <= uinfo["visual_triangles"]
        for linfo in m["mechanisms"][mid].values():
            assert Path(linfo["npz_path"]).is_file()
            assert linfo["tris"] >= 100
