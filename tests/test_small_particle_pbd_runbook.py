from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "profiles/gpu_pbd/scientific_workbench_small_gpu_pbd_v2.json"
RUNBOOK = ROOT / "docs/operations/funnel-tube15-small-particle-pbd.md"


def test_runbook_tracks_the_canonical_small_v2_recipe() -> None:
    recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
    text = RUNBOOK.read_text(encoding="utf-8")

    assert recipe["recipe_id"] in text
    assert "0532f5f3ced74a1b7d6a8a20abfb9d457788a312285c71e5b0de4108754188fa" in text
    for value in (
        recipe["particle_system"]["max_velocity_m_s"],
        recipe["particle_system"]["particle_contact_offset_m"],
        recipe["particle_system"]["effective_rest_offset_m"],
        recipe["particle_set"]["spacing_m"],
        recipe["particle_set"]["width_m"],
        recipe["particle_set"]["mass_kg"],
        recipe["particle_set"]["maximum_count"],
    ):
        assert str(value) in text


def test_runbook_separates_liquid_and_container_collision_parameters() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "0.00035" in text
    assert "0.000175" in text
    assert "SDF resolution" in text
    assert "256" in text
    assert "512" in text
    assert "7 mm" in text
    assert "ParticleSystem" in text
    assert "ParticleSet" in text
    assert "robot-policy" in text
