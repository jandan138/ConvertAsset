from __future__ import annotations

from scripts.probe_original_threaded_tube15_gravity_phase import classify_phase


def test_phase_pass_requires_closed_band_and_stability() -> None:
    result = classify_phase(
        relative_z_initial_m=1.104,
        relative_z_final_m=1.080,
        body_displacement_m=0.0002,
        maximum_radial_offset_m=0.001,
        maximum_cap_z_m=1.11,
        tail_relative_z_span_m=0.0002,
        hard_errors=[],
    )
    assert result["overall_status"] == "pass"


def test_phase_rejects_launch_or_no_descent() -> None:
    launched = classify_phase(
        relative_z_initial_m=1.104,
        relative_z_final_m=4.0,
        body_displacement_m=0.0,
        maximum_radial_offset_m=0.0,
        maximum_cap_z_m=4.0,
        tail_relative_z_span_m=1.0,
        hard_errors=[],
    )
    assert launched["overall_status"] == "blocked"
