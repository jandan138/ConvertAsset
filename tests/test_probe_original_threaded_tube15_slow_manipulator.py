from __future__ import annotations

from scripts.probe_original_threaded_tube15_slow_manipulator import (
    classify_against_baseline,
)


def test_slow_manipulator_requires_extra_descent_and_closed_hold() -> None:
    result = classify_against_baseline(
        baseline_descent_m=0.002,
        manipulated_descent_m=0.012,
        relative_z_final_m=1.074,
        maximum_radial_offset_m=0.002,
        body_displacement_m=0.0002,
        tail_span_m=0.0002,
        hard_errors=[],
    )
    assert result["overall_status"] == "pass"


def test_slow_manipulator_rejects_same_as_baseline() -> None:
    result = classify_against_baseline(
        baseline_descent_m=0.004,
        manipulated_descent_m=0.005,
        relative_z_final_m=1.074,
        maximum_radial_offset_m=0.001,
        body_displacement_m=0.0,
        tail_span_m=0.0,
        hard_errors=[],
    )
    assert result["overall_status"] == "blocked"
