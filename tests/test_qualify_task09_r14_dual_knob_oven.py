from scripts.qualify_task09_r14_dual_knob_oven import (
    evaluate_door_report,
    evaluate_interactive_report,
)


def test_interactive_gate_requires_rotor_press_and_shared_state() -> None:
    report = {
        "status": "PASS",
        "passed": True,
        "sourceUsdUnchanged": True,
        "results": {
            "embeddedRuntimeGraph": {"passed": True},
            "rotorSetpointAndDisplay": {
                "passed": True,
                "setpointChangedByPhysicalRotation": True,
            },
            "knobPressStartsHeating": {"passed": True, "heatingStarted": True},
        },
    }
    assert evaluate_interactive_report(report)["status"] == "pass"
    report["results"]["knobPressStartsHeating"]["heatingStarted"] = False
    assert evaluate_interactive_report(report)["status"] == "blocked"


def test_door_gate_accepts_60_degree_stop_and_close() -> None:
    report = {
        "results": {
            "doorDynamicLimit": {
                "successfulForceCalls": 1110,
                "openingPeakDegrees": 59.98,
                "upperDwellPeakDegrees": 60.02,
                "closingFinalDegrees": 0.04,
                "bodyTranslationDriftMeters": 0.0,
            }
        }
    }
    assert evaluate_door_report(report)["status"] == "pass"
    report["results"]["doorDynamicLimit"]["openingPeakDegrees"] = 80.0
    assert evaluate_door_report(report)["status"] == "blocked"
