#!/usr/bin/env python3
"""Promote LABSPIN X8 r5 only after rest-pose and behavior evidence pass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BEHAVIOR_CLAIMS = (
    "contact_press_qualified",
    "button_causes_lid_open",
    "lid_remains_open_after_release",
    "rotor_open_interlock",
    "shutdown_causes_power_off",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    rest_path = package / "evidence/rest_pose/report.json"
    behavior_path = package / "evidence/lid_behavior/report.json"
    rest = json.loads(rest_path.read_text())
    behavior = json.loads(behavior_path.read_text())
    passed = (
        rest.get("status") == "pass"
        and rest["claims"].get("static_rest_pose_assembled") is True
        and rest["claims"].get("first_step_pose_continuity") is True
        and behavior.get("status") == "pass"
        and all(behavior["claims"].get(name) is True for name in BEHAVIOR_CLAIMS)
    )
    if not passed:
        raise RuntimeError("r5 rest-pose or behavior qualification is incomplete")
    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["package_id"] = "labspin_x8_centrifuge_task11_r5_rest_pose_isaac41"
    manifest["overall_status"] = "pass"
    manifest["blocked_reasons"] = []
    manifest["claims"].update(rest["claims"])
    manifest["claims"].update(behavior["claims"])
    manifest["runtime_qualification"] = {
        "runtime": "isaac41",
        "rest_pose_report": "evidence/rest_pose/report.json",
        "behavior_report": "evidence/lid_behavior/report.json",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
