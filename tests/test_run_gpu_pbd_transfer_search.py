from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_gpu_pbd_transfer_search.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("run_gpu_pbd_transfer_search", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selects_highest_target_then_lowest_spill() -> None:
    module = _module()
    runs = [
        {
            "candidate_id": "a",
            "pour": {"target": 300, "spill": 150},
            "overall_status": "pass",
        },
        {
            "candidate_id": "b",
            "pour": {"target": 320, "spill": 180},
            "overall_status": "pass",
        },
        {
            "candidate_id": "c",
            "pour": {"target": 320, "spill": 120},
            "overall_status": "pass",
        },
    ]

    assert module.select_candidate(runs)["candidate_id"] == "c"


def test_report_blocks_when_search_has_no_majority_transfer() -> None:
    module = _module()
    report = module.build_report(
        search_runs=[
            {
                "candidate_id": "a",
                "pour": {"target": 200, "spill": 348},
                "overall_status": "blocked",
            }
        ],
        cold_runs=[],
        selected=None,
    )

    assert report["overall_status"] == "blocked"
    assert report["promotion"]["allowed"] is False
    assert (
        report["blocked_reason"] == "bounded_search_found_no_50pct_transfer_candidate"
    )
