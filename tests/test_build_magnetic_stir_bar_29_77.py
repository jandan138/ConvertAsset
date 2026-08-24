from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts/build_magnetic_stir_bar_29_77.py"
QUALIFY = ROOT / "scripts/qualify_magnetic_stir_bar_29_77.py"


def test_builder_is_source_bound_and_uses_reviewed_dimensions():
    source = BUILD.read_text(encoding="utf-8")
    ast.parse(source)
    assert "magnetic_stir_bar_01_29_77mm.usda" in source
    assert "LENGTH_M = 0.02977" in source
    assert "DIAMETER_M = 0.00871" in source
    assert '"Cylinder"' in source
    assert "source_sha256" in source
    assert "raw_source_unchanged" in source


def test_qualifier_keeps_robot_and_task_claims_false():
    source = QUALIFY.read_text(encoding="utf-8")
    ast.parse(source)
    assert '"stable_support"' in source
    assert '"root_motion"' in source
    assert '"robot_grasp_success": False' in source
    assert '"task_success": False' in source
