from scripts.promote_nonthreaded_tube15_neck_cap_fit import runs_pass


def test_promotion_requires_three_isaac41_runs() -> None:
    runs = [
        {"overall_status": "pass", "runtime": {"kit_version": "4.1.0"}}
        for _ in range(3)
    ]
    assert runs_pass(runs)
    assert not runs_pass(runs[:2])
    runs[0]["overall_status"] = "blocked"
    assert not runs_pass(runs)
