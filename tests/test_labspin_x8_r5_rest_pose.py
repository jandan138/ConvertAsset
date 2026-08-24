from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts/build_labspin_x8_r5_rest_pose.py"
QUALIFY = ROOT / "scripts/qualify_labspin_x8_r5_rest_pose.py"
PROMOTE = ROOT / "scripts/promote_labspin_x8_r5_rest_pose.py"


def test_r5_builder_authors_joint_satisfied_closed_rest_pose():
    source = BUILD.read_text(encoding="utf-8")
    ast.parse(source)
    for name in (
        "lid_link",
        "rotor_link",
        "encoder_link",
        "start_button_link",
        "stop_button_link",
        "lid_open_button_link",
    ):
        assert name in source
    assert "GetLocalPos0Attr" in source and "GetLocalPos1Attr" in source
    assert "GetLocalRot0Attr" in source and "GetLocalRot1Attr" in source
    assert "base_fixed_joint" in source
    assert "UsdPhysics.FixedJoint" not in source
    assert "OnPhysicsStep" not in source


def test_r5_qualifier_requires_preview_and_first_step_continuity():
    source = QUALIFY.read_text(encoding="utf-8")
    ast.parse(source)
    assert "static_rest_pose_assembled" in source
    assert "first_step_pose_continuity" in source
    assert "maximum_first_step_jump_m" in source
    assert "0.001" in source


def test_r5_promotion_requires_rest_pose_and_existing_behavior_gates():
    source = PROMOTE.read_text(encoding="utf-8")
    ast.parse(source)
    assert "rest_pose/report.json" in source
    assert "lid_behavior/report.json" in source
    assert "button_causes_lid_open" in source
    assert "rotor_open_interlock" in source
    assert "shutdown_causes_power_off" in source
    assert "labspin_x8_centrifuge_task11_r5_rest_pose_isaac41" in source
