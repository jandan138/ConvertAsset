from scripts.qualify_task09_r13_materialized_oven import evaluate_producer_report


def test_task09_scope_requires_graph_rotation_and_physical_start() -> None:
    report = {
        "status": "PASS",
        "passed": True,
        "results": {
            "embeddedRuntimeGraph": {"passed": True},
            "rotorSetpointAndDisplay": {
                "passed": True,
                "setpointChangedByPhysicalRotation": True,
            },
            "knobPressStartsHeating": {
                "passed": True,
                "heatingStarted": True,
            },
        },
    }

    assert evaluate_producer_report(report)["status"] == "pass"
    report["results"]["knobPressStartsHeating"]["heatingStarted"] = False
    assert evaluate_producer_report(report)["status"] == "blocked"
