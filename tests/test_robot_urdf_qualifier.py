"""Unit tests for the SimReady Robot Qualification Gate (L1 Pinocchio checks)."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from convert_asset.robot_urdf import (
    DEFAULT_MODULAR_ROBOTS_ROOT,
    assemble_bimanual_urdf,
    builtin_starbucks_specs,
    run_kinematic_qualification,
)


@pytest.mark.parametrize(
    "robot_id",
    [
        "bimanual_fr3_robotiq85",
        "bimanual_rizon4s_flexiv",
        "bimanual_fr3_wuji_hand",
    ],
)
def test_builtin_starbucks_robots_pass_l1_kinematic_qualification(
    tmp_path: Path,
    robot_id: str,
) -> None:
    if not DEFAULT_MODULAR_ROBOTS_ROOT.is_dir():
        pytest.skip(f"Modular robots root not present: {DEFAULT_MODULAR_ROBOTS_ROOT}")
    specs = builtin_starbucks_specs(DEFAULT_MODULAR_ROBOTS_ROOT)
    res = assemble_bimanual_urdf(specs[robot_id], tmp_path / robot_id)
    rep = run_kinematic_qualification(res.meta_path)
    assert rep["passed"] is True, f"{robot_id} failed L1 qualification: {rep['failures']}"
    assert "left" in rep["arms"] and "right" in rep["arms"]


def test_qualifier_catches_90deg_rotated_robotiq_jaw_bug(tmp_path: Path) -> None:
    if not DEFAULT_MODULAR_ROBOTS_ROOT.is_dir():
        pytest.skip(f"Modular robots root not present: {DEFAULT_MODULAR_ROBOTS_ROOT}")
    spec = builtin_starbucks_specs(DEFAULT_MODULAR_ROBOTS_ROOT)["bimanual_fr3_robotiq85"]
    broken_arms = tuple(replace(a, grasp_frame_rpy=(0.0, 0.0, 0.0)) for a in spec.arms)
    broken_spec = replace(spec, arms=broken_arms)
    res = assemble_bimanual_urdf(broken_spec, tmp_path / "broken_robotiq_yaw")
    rep = run_kinematic_qualification(res.meta_path)
    assert rep["passed"] is False
    codes = {f["code"] for f in rep["failures"]}
    assert "GRASP_FRAME_CLOSING_AXIS_MISALIGNED" in codes


def test_qualifier_catches_45mm_short_flexiv_tcp_bug(tmp_path: Path) -> None:
    if not DEFAULT_MODULAR_ROBOTS_ROOT.is_dir():
        pytest.skip(f"Modular robots root not present: {DEFAULT_MODULAR_ROBOTS_ROOT}")
    spec = builtin_starbucks_specs(DEFAULT_MODULAR_ROBOTS_ROOT)["bimanual_rizon4s_flexiv"]
    broken_arms = tuple(replace(a, grasp_frame_xyz=(0.0, 0.0, 0.140)) for a in spec.arms)
    broken_spec = replace(spec, arms=broken_arms)
    res = assemble_bimanual_urdf(broken_spec, tmp_path / "broken_flexiv_tcp")
    rep = run_kinematic_qualification(res.meta_path)
    assert rep["passed"] is False
    codes = {f["code"] for f in rep["failures"]}
    assert "GRASP_FRAME_TCP_OFFSET_TOO_LARGE" in codes


def test_qualifier_catches_offcenter_wuji_palm_pocket_bug(tmp_path: Path) -> None:
    if not DEFAULT_MODULAR_ROBOTS_ROOT.is_dir():
        pytest.skip(f"Modular robots root not present: {DEFAULT_MODULAR_ROBOTS_ROOT}")
    spec = builtin_starbucks_specs(DEFAULT_MODULAR_ROBOTS_ROOT)["bimanual_fr3_wuji_hand"]
    broken_arms = tuple(replace(a, grasp_frame_xyz=(-0.012, 0.042, 0.118)) for a in spec.arms)
    broken_spec = replace(spec, arms=broken_arms)
    res = assemble_bimanual_urdf(broken_spec, tmp_path / "broken_wuji_palm")
    rep = run_kinematic_qualification(res.meta_path)
    assert rep["passed"] is False
    codes = {f["code"] for f in rep["failures"]}
    assert "DEXTEROUS_GRASP_FRAME_OFF_PALM_POCKET" in codes
