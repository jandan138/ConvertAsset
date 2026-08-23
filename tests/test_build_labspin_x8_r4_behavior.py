from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts/build_labspin_x8_r4_behavior.py"
QUALIFY = ROOT / "scripts/qualify_labspin_x8_r4_behavior.py"


def test_r4_rebases_button_geometry_and_embeds_explicit_device_state():
    source = BUILD.read_text()
    ast.parse(source)
    assert "lid_open_button_link" in source
    assert "LID_BUTTON_CENTER" in source
    assert "set_dof_position_target" in source
    assert "closed" in source
    assert "opening" in source
    assert "open_hold" in source
    assert "closing" in source
    assert "locked" in source
    assert "power_state" in source
    assert "rotor_interlock_rad_s" in source


def test_r4_qualification_requires_contact_and_interlock_evidence():
    source = QUALIFY.read_text()
    ast.parse(source)
    assert '"contact_press_qualified"' in source
    assert '"rotor_open_interlock"' in source
    assert '"shutdown_causes_power_off"' in source
    assert "button_drive_target" not in source
    assert "RigidBodyAPI" in source
