"""Tests for distillation_v08 M1 Blender 4.4.3 ART-001 Keck clip & calibrated thermometer unit."""

from __future__ import annotations

import json
from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parents[1] / "external_artifacts" / "distillation_v08_assets"


def test_v08_blender44_keck_clip_and_thermometer_assets() -> None:
    mp = ASSETS_DIR / "v08_assets_manifest.json"
    hp = ASSETS_DIR / "forge_manifest_and_critic_handoff.json"
    assert mp.is_file() and hp.is_file(), "Run scripts/build_m1_distillation_v08_assets.py first"

    m = json.loads(mp.read_text(encoding="utf-8"))
    h = json.loads(hp.read_text(encoding="utf-8"))

    assert tuple(int(x) for x in m["blender_version"].split(".")[:2]) >= (4, 4)
    assert Path(m["studio_sheet"]).is_file()

    keck = m["keck_clip_24_29_art001"]
    assert set(keck["links"].keys()) == {"ClipSpine", "LeftSpringJaw", "RightSpringJaw"}
    usda_p = Path(keck["simready_usd"]["usda_path"])
    assert usda_p.is_file()
    usda_txt = usda_p.read_text(encoding="utf-8")
    assert "PhysicsArticulationRootAPI" in usda_txt
    assert "LeftJawRevolute" in usda_txt and "RightJawRevolute" in usda_txt
    assert keck["simready_usd"]["collision_triangles"] <= keck["simready_usd"]["visual_triangles"]

    th = h["assets"]["thermometer_adapter_unit_v08"]
    assert abs(float(th["seated_bulb_top_world_z_m"]) - float(th["target_sidearm_bottom_lip_world_z_m"])) < 1e-4

