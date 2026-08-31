from scripts.qualify_task09_r13_oven_cart import evaluate_load_report


def test_100kg_load_gate_requires_height_stability_and_low_drift() -> None:
    passing = {
        "mass_kg": 100.0,
        "expected_rest_z_m": 0.805,
        "initial_xyz_m": [0.0, 0.0, 0.855],
        "mid_xyz_m": [0.0, 0.0, 0.8051],
        "final_xyz_m": [0.0002, -0.0001, 0.8051],
    }

    assert evaluate_load_report(passing)["status"] == "pass"
    passing["final_xyz_m"][2] = 0.72
    assert evaluate_load_report(passing)["status"] == "blocked"
