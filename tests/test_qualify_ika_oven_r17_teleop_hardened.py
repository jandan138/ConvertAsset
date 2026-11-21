from __future__ import annotations

from scripts.qualify_ika_oven_r17_teleop_hardened import qualification_checks


def _pass() -> dict[str, object]:
    return {"status": "pass"}


def test_qualification_requires_three_cold_runs_per_knob_and_dual_runtime() -> None:
    checks = qualification_checks(
        isaac45_runs={
            f"{knob}_cold_{index}": _pass()
            for knob in ("primary", "auxiliary")
            for index in range(1, 4)
        },
        negative_control=_pass(),
        isaac41_interactive={"primary": _pass(), "auxiliary": _pass()},
        isaac41_articulation=_pass(),
        isaac41_door=_pass(),
    )
    assert all(checks.values())


def test_qualification_blocks_a_missing_or_failed_cold_run() -> None:
    runs = {
        f"{knob}_cold_{index}": _pass()
        for knob in ("primary", "auxiliary")
        for index in range(1, 4)
    }
    runs["auxiliary_cold_3"] = {"status": "blocked"}
    checks = qualification_checks(
        isaac45_runs=runs,
        negative_control=_pass(),
        isaac41_interactive={"primary": _pass(), "auxiliary": _pass()},
        isaac41_articulation=_pass(),
        isaac41_door=_pass(),
    )
    assert checks["isaac45_three_cold_runs_per_knob"] is False
