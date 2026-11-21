from scripts.qualify_long_neck_threaded_tube15_packages import classify_asset_set


def test_geometry_can_pass_while_thread_interaction_stays_blocked() -> None:
    dynamic = {
        "body": [{"overall_status": "pass"}] * 3,
        "cap": [{"overall_status": "pass"}] * 3,
    }
    threads = [
        {"overall_status": "blocked"},
        {"overall_status": "blocked"},
    ]
    result = classify_asset_set(dynamic, threads)
    assert result["overall_status"] == "pass"
    assert result["claims"]["dynamic_geometry_ready"] is True
    assert result["claims"]["thread_interaction_ready"] is False
