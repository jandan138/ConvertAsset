#!/usr/bin/env python3
"""Promote LABSPIN X8 r6 after collision, rest-pose, and behavior gates pass."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


PACKAGE_ID = "labspin_x8_centrifuge_task11_r6_visual_fitted_lid_collision_isaac41"
REQUIRED_BEHAVIOR_CLAIMS = (
    "contact_press_qualified",
    "button_causes_lid_open",
    "lid_remains_open_after_release",
    "rotor_open_interlock",
    "shutdown_causes_power_off",
)


def _read(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def promote(package: Path) -> Path:
    package = package.resolve()
    asset = package / "asset.usd"
    asset_sha = sha256(asset.read_bytes()).hexdigest()
    audit = _read(package / "evidence/collision_fit/report.json")
    rest = _read(package / "evidence/rest_pose/report.json")
    behavior = _read(package / "evidence/lid_behavior/report.json")
    render = _read(package / "evidence/collision_fit/render_report.json")
    static = _read(package / "evidence/task11_static_manifest.json")
    if audit.get("overall_status") != "pass" or audit.get("asset_usd_sha256") != asset_sha:
        raise RuntimeError("collision-fit evidence does not bind the current asset")
    if (
        rest.get("status") != "pass"
        or rest.get("asset_usd_sha256") != asset_sha
        or rest.get("claims", {}).get("static_rest_pose_assembled") is not True
        or rest.get("claims", {}).get("first_step_pose_continuity") is not True
    ):
        raise RuntimeError("rest-pose evidence does not bind and pass the current asset")
    if behavior.get("status") != "pass" or not all(
        behavior.get("claims", {}).get(name) is True
        for name in REQUIRED_BEHAVIOR_CLAIMS
    ):
        raise RuntimeError("device behavior evidence is incomplete")
    if static.get("asset_usd_sha256") != asset_sha:
        raise RuntimeError("behavior qualification does not bind the current asset")
    if (
        render.get("asset_usd_sha256") != asset_sha
        or render.get("visual_review") != "pass"
        or {item.get("state") for item in render.get("images", [])}
        != {"closed", "open"}
    ):
        raise RuntimeError("closed/open collision overlay evidence is incomplete")

    manifest_path = package / "evidence/manifest.json"
    manifest = _read(manifest_path)
    manifest["package_id"] = PACKAGE_ID
    manifest["overall_status"] = "pass"
    manifest["blocked_reasons"] = []
    manifest.setdefault("claims", {}).update(behavior["claims"])
    manifest["claims"].update(rest["claims"])
    manifest["claims"]["visual_fitted_lid_collision"] = True
    manifest["claims"]["robot_policy_success"] = False
    manifest["claims"]["task11_success"] = False
    manifest["runtime_qualification"] = {
        "runtime": "isaac41",
        "collision_fit": "evidence/collision_fit/report.json",
        "rest_pose": "evidence/rest_pose/report.json",
        "device_behavior": "evidence/lid_behavior/report.json",
        "collision_overlay": "evidence/collision_fit/render_report.json",
        "asset_usd_sha256": asset_sha,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    receipt = {
        "schema_version": "aan.labspin_x8_r6_promotion.v1",
        "status": "pass",
        "package_id": PACKAGE_ID,
        "asset_usd_sha256": asset_sha,
        "evidence": manifest["runtime_qualification"],
        "claim_boundary": (
            "Visual-fitted lid collision and robot-free device mechanics only; "
            "robot policy, canonical Task 11, and benchmark success remain false."
        ),
    }
    receipt_path = package / "evidence/promotion.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    print(promote(args.package))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
