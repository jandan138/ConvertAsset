from __future__ import annotations

from scripts.qualify_threaded_tube15_contact import classify_thread_result


def test_true_thread_gate_requires_rotation_dependent_axial_motion() -> None:
    result = classify_thread_result(
        control_descent_m=0.0002,
        forward_descent_m=0.0031,
        reverse_rise_m=0.0028,
        maximum_radial_offset_m=0.0002,
        maximum_tilt_deg=2.0,
        hard_errors=[],
    )
    assert result["overall_status"] == "pass"


def test_true_thread_gate_rejects_gravity_only_drop() -> None:
    result = classify_thread_result(
        control_descent_m=0.003,
        forward_descent_m=0.0032,
        reverse_rise_m=0.0,
        maximum_radial_offset_m=0.0001,
        maximum_tilt_deg=1.0,
        hard_errors=[],
    )
    assert result["overall_status"] == "blocked"
