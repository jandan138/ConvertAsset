from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/package_scientific_workbench_beaker_sdf.py"


def test_sdf_beaker_package_is_metre_source_bound_and_web_standard():
    source = SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)
    assert "obj_beaker_sdf.usd" in source
    assert "PhysxSDFMeshCollisionAPI" in source
    assert "WebStandardClearBorosilicate" in source
    assert "SetStageMetersPerUnit(stage, 1.0)" in source
    assert "0.32" not in source
    assert "robot_policy_success" in source
