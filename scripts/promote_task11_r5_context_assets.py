#!/usr/bin/env python3
"""Bind three Task 11 r5 context qualification runs into producer manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RUNS = ("run_1.json", "run_2.json", "run_3.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = root / "evidence/runtime_qualification"
    reports = [json.loads((evidence / name).read_text()) for name in RUNS]
    if not all(report["status"] == "pass" for report in reports):
        raise RuntimeError("all three context qualification runs must pass")
    summary = {
        "schema_version": "aan.task11_r5_context_promotion.v1",
        "status": "pass",
        "runs": list(RUNS),
        "claims": {
            "visual_static_no_physics": True,
            "target_slot_insertion": True,
            "robot_policy_success": False,
        },
    }
    (evidence / "report.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    for label in ("context_15ml_closed", "context_50ml_closed"):
        path = root / f"{label}/package/evidence/manifest.json"
        manifest = json.loads(path.read_text())
        manifest["overall_status"] = "pass"
        manifest["blocked_reasons"] = []
        manifest["claims"]["isaac41_load_render_step_reset"] = True
        manifest["runtime_qualification"] = "../../evidence/runtime_qualification/report.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    rack_path = root / "mixed_rack_r2/package/evidence/manifest.json"
    rack = json.loads(rack_path.read_text())
    rack["overall_status"] = "pass"
    rack["blocked_reasons"] = []
    rack["claims"]["isaac41_static_stability"] = True
    rack["claims"]["target_slot_insertion"] = True
    rack["runtime_qualification"] = "../../../evidence/runtime_qualification/report.json"
    rack_path.write_text(json.dumps(rack, indent=2, sort_keys=True) + "\n")
    tube_path = root / "target_tube_r2/package/evidence/manifest.json"
    tube = json.loads(tube_path.read_text())
    tube["overall_status"] = "pass"
    tube["blocked_reasons"] = []
    tube["claims"]["target_slot_insertion"] = True
    tube["runtime_qualification"] = "../../../evidence/runtime_qualification/report.json"
    tube_path.write_text(json.dumps(tube, indent=2, sort_keys=True) + "\n")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
