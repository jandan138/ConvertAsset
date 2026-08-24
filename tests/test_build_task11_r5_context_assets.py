from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts/build_task11_r5_context_assets.py"
QUALIFY = ROOT / "scripts/qualify_task11_r5_context_assets.py"
PROMOTE = ROOT / "scripts/promote_task11_r5_context_assets.py"


def test_builder_authors_visual_static_closed_tubes_and_target_support():
    source = BUILD.read_text(encoding="utf-8")
    ast.parse(source)
    assert "ContextTube15mlClosed" in source
    assert "ContextTube50mlClosed" in source
    assert "visual_static_context" in source
    assert "slot_15ml_r00_c02_inserted_bottom" in source
    assert "target_slot_bottom_support" in source
    assert "target_tube_r2" in source
    assert "RigidBodyAPI" not in source


def test_qualifier_and_promoter_require_three_target_slot_runs():
    qualify = QUALIFY.read_text(encoding="utf-8")
    promote = PROMOTE.read_text(encoding="utf-8")
    ast.parse(qualify)
    ast.parse(promote)
    assert "target_slot_insertion" in qualify
    assert "visual_static_no_physics" in qualify
    assert "run_1.json" in promote and "run_3.json" in promote
    assert "robot_policy_success" in promote
