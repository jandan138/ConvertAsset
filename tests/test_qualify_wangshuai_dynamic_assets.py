from scripts.qualify_wangshuai_dynamic_assets import classify_observation


def test_dynamic_rigid_observation_passes_for_finite_settled_transport() -> None:
    result = classify_observation(
        initial_z=0.12,
        minimum_z=0.019,
        final_speed=0.004,
        maximum_abs_coordinate=0.42,
        transport_distance=0.101,
        transport_error=0.0015,
        hard_errors=[],
    )
    assert result["overall_status"] == "pass"
    assert all(result["checks"].values())


def test_dynamic_rigid_observation_blocks_a_kinematic_asset() -> None:
    result = classify_observation(
        initial_z=0.12,
        minimum_z=0.1199,
        final_speed=0.0,
        maximum_abs_coordinate=0.12,
        transport_distance=0.1,
        transport_error=0.0,
        hard_errors=[],
    )
    assert result["overall_status"] == "blocked"
    assert result["checks"]["gravity_motion"] is False
