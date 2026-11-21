from scripts.qualify_task08_r12_assets import classify


def test_classification_promotes_assets_but_not_thread_task() -> None:
    reports = {
        "rack": [{"overall_status": "pass"}] * 3,
        "body": [{"overall_status": "pass"}] * 3,
        "cap": [{"overall_status": "pass"}] * 3,
    }
    result = classify(reports)
    assert result["status"] == "pass"
    assert result["claims"]["rack_scaled_sdf_ready"] is True
    assert result["claims"]["visual_material_variants_ready"] is True
    assert result["claims"]["thread_interaction_ready"] is False
    assert result["claims"]["task08_success"] is False
