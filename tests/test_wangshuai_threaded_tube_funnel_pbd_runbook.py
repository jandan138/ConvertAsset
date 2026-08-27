from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs/operations/wangshuai-threaded-tube-funnel-pbd.md"
SMALL_V2 = ROOT / "profiles/gpu_pbd/scientific_workbench_small_gpu_pbd_v2.json"
OVERLAY_MANIFEST = (
    ROOT
    / "outputs/wangshuai_funnel_tube15_exact_asset_set_20260826"
    / "packages/small_v2_liquid_seed_1948/evidence/manifest.json"
)
OVERLAY_ASSET = (
    ROOT
    / "outputs/wangshuai_funnel_tube15_exact_asset_set_20260826"
    / "packages/small_v2_liquid_seed_1948/asset.usda"
)
FUNNEL_MANIFEST = (
    ROOT
    / "outputs/wangshuai_funnel_tube15_exact_asset_set_20260826"
    / "packages/funnel_small_v2_liquid_ready/evidence/manifest.json"
)
TUBE_MANIFEST = (
    ROOT
    / "outputs/wangshuai_funnel_tube15_exact_asset_set_20260826"
    / "packages/tube15_threaded_liquid_ready/evidence/manifest.json"
)


def test_runbook_tracks_the_exact_source_overlay_not_small_v2() -> None:
    overlay = json.loads(OVERLAY_MANIFEST.read_text(encoding="utf-8"))
    small_v2 = json.loads(SMALL_V2.read_text(encoding="utf-8"))
    text = RUNBOOK.read_text(encoding="utf-8")

    system = overlay["particle_system"]
    assert overlay["particle_count"] == 1948
    assert overlay["source"]["scene_sha256"] in text
    assert "scientific_workbench_small_gpu_pbd_v2" in text
    assert abs(float(system["maxVelocity"]) - 0.1) < 1e-8
    assert "0.1" in text
    assert "0.002" in text
    assert "1948" in text
    assert small_v2["particle_system"]["max_velocity_m_s"] == 0.2
    assert "不要把这套当成 small-v2" in text


def test_runbook_records_threaded_tube_and_funnel_collision_semantics() -> None:
    funnel = json.loads(FUNNEL_MANIFEST.read_text(encoding="utf-8"))
    tube = json.loads(TUBE_MANIFEST.read_text(encoding="utf-8"))
    text = RUNBOOK.read_text(encoding="utf-8")

    assert funnel["role"] == "liquid_conduit"
    assert tube["role"] == "liquid_ready_container"
    assert "kinematic" in text
    assert "sdf" in text.lower()
    assert "convexHull" in text
    assert "120" in text
    assert "GPU" in text
    assert "TGS" in text
    assert "PhysicsScene" in text
    assert "robot-policy" in text


def test_runbook_does_not_invent_particle_render_or_mass_parameters() -> None:
    from pxr import Usd

    stage = Usd.Stage.Open(str(OVERLAY_ASSET))
    root = stage.GetDefaultPrim().GetPath()
    system = stage.GetPrimAtPath(str(root) + "/ParticleSystem")
    particle_set = stage.GetPrimAtPath(str(root) + "/ParticleSet")
    text = RUNBOOK.read_text(encoding="utf-8")

    assert particle_set.GetAttribute("visibility").Get() == "invisible"
    assert len(set(float(value) for value in particle_set.GetAttribute("widths").Get())) == 1
    assert float(particle_set.GetAttribute("widths").Get()[0]) == 0.0023760003969073296
    assert particle_set.GetAttribute("physics:mass").HasAuthoredValueOpinion() is False
    assert not any("Isosurface" in attr.GetName() for attr in system.GetAttributes())
    assert not system.GetRelationship("material:binding").GetTargets()
    assert "没有显式作者 ParticleSystem isosurface" in text
    assert "不声明一套源文件中不存在的渲染配方" in text
