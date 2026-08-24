from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts/build_task11_r7_target_tube.py"
QUALIFY = ROOT / "scripts/qualify_task11_r7_target_tube.py"


def test_builder_keeps_body_insertion_material_and_splits_cap_grasp_material():
    source = BUILD.read_text(encoding="utf-8")
    ast.parse(source)
    assert "__aan_labspin_insert_material" in source
    assert "__aan_lift2_grasp_material" in source
    assert '"static_friction": 1.0' in source
    assert '"dynamic_friction": 0.9' in source
    assert '"friction_combine_mode": "max"' in source
    assert '"body": "insertion"' in source
    assert '"cap": "grasp"' in source
    assert '"grasp_contact_offset_m": 0.001' in source
    assert "cap_grasp_box" in source
    assert '"source_cap_cylinder_enabled": False' in source


def test_qualifier_requires_physical_close_lift_hold_without_tube_pose_writes():
    source = QUALIFY.read_text(encoding="utf-8")
    ast.parse(source)
    assert "kinematic_parallel_jaws" in source
    assert "lift_distance_m" in source
    assert "hold_tail_motion_m" in source
    assert "tube_transform_write_count" in source
    assert "tube.set_world_pose" not in source
