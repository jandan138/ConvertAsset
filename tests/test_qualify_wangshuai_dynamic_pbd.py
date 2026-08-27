from scripts.qualify_wangshuai_dynamic_pbd import classify_pbd_observation


def test_dynamic_pbd_passes_flow_and_moving_receiver() -> None:
    result = classify_pbd_observation(
        authored_count=1948,
        runtime_count=1948,
        captured_before_move=1948,
        captured_after_move=1910,
        tube_transport_distance=0.1,
        tube_transport_error=0.001,
        below_floor_count=0,
        nonfinite_count=0,
        hard_errors=[],
        kit_version="4.1.0",
    )
    assert result["overall_status"] == "pass"
    assert all(result["checks"].values())


def test_dynamic_pbd_blocks_wrong_runtime() -> None:
    result = classify_pbd_observation(
        authored_count=1948,
        runtime_count=1948,
        captured_before_move=1948,
        captured_after_move=1948,
        tube_transport_distance=0.1,
        tube_transport_error=0.0,
        below_floor_count=0,
        nonfinite_count=0,
        hard_errors=[],
        kit_version="4.5.0",
    )
    assert result["overall_status"] == "blocked"
    assert result["checks"]["isaac41"] is False


def test_dynamic_pbd_keeps_transport_as_a_separate_unqualified_claim() -> None:
    result = classify_pbd_observation(
        authored_count=1948,
        runtime_count=1948,
        captured_before_move=1948,
        captured_after_move=1750,
        tube_transport_distance=0.1,
        tube_transport_error=0.0,
        below_floor_count=0,
        nonfinite_count=0,
        hard_errors=[],
        kit_version="4.1.0",
    )
    assert result["overall_status"] == "pass"
    assert result["checks"]["moving_tube_retention"] is False
