"""Unit tests for modular bimanual URDF assembly (ConvertAsset Layer 1)."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from convert_asset.robot_urdf import (
    DEFAULT_MODULAR_ROBOTS_ROOT,
    assemble_bimanual_urdf,
    builtin_starbucks_specs,
)


@pytest.mark.parametrize(
    "robot_id,expected_arm_dof,expected_ee_drivers,expected_ee_total",
    [
        ("bimanual_fr3_robotiq85", 7, 1, 6),
        ("bimanual_rizon4s_flexiv", 7, 1, 7),
        ("bimanual_fr3_wuji_hand", 7, 20, 20),
    ],
)
def test_assemble_builtin_starbucks_bimanual_urdfs(
    tmp_path: Path,
    robot_id: str,
    expected_arm_dof: int,
    expected_ee_drivers: int,
    expected_ee_total: int,
) -> None:
    if not DEFAULT_MODULAR_ROBOTS_ROOT.is_dir():
        pytest.skip(f"Modular robots root not present: {DEFAULT_MODULAR_ROBOTS_ROOT}")

    specs = builtin_starbucks_specs(DEFAULT_MODULAR_ROBOTS_ROOT)
    result = assemble_bimanual_urdf(specs[robot_id], tmp_path / robot_id)

    urdf_path = Path(result.urdf_path)
    meta_path = Path(result.meta_path)
    assert urdf_path.is_file()
    assert meta_path.is_file()

    root = ET.parse(urdf_path).getroot()
    assert root.tag == "robot"
    assert root.attrib["name"] == robot_id

    link_names = [el.attrib["name"] for el in root.findall("link")]
    joint_names = [el.attrib["name"] for el in root.findall("joint")]
    assert len(link_names) == len(set(link_names)), "Duplicate link names"
    assert len(joint_names) == len(set(joint_names)), "Duplicate joint names"
    assert "pedestal_base_link" in link_names
    assert "left_grasp_frame" in link_names
    assert "right_grasp_frame" in link_names

    # Every referenced mesh path must resolve to an existing file
    mesh_files = [m.attrib["filename"] for m in root.iter("mesh")]
    assert len(mesh_files) > 0
    for mf in mesh_files:
        assert Path(mf).is_file(), f"Missing resolved mesh file: {mf}"

    # Every mimic joint must reference an existing joint name in the assembled URDF
    joint_set = set(joint_names)
    for j in root.findall("joint"):
        mim = j.find("mimic")
        if mim is not None:
            assert mim.attrib["joint"] in joint_set

    for side in ("left", "right"):
        assert len(result.arm_joints[side]) == expected_arm_dof
        assert len(result.ee_driver_joints[side]) == expected_ee_drivers
        assert len(result.ee_joints[side]) == expected_ee_total
        assert result.grasp_frames[side] == f"{side}_grasp_frame"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["robot_id"] == robot_id
    assert len(meta["joint_limits"]) >= 2 * (expected_arm_dof + expected_ee_total)
