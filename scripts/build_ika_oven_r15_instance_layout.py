#!/usr/bin/env python3
"""Build Task 09 r15 with the complete oven subtree under `/Instance`."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.articulated_instance_layout import (  # noqa: E402
    audit_instance_layout,
    move_asset_contents_under_instance,
)


DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_task09_r14_dual_knob_20260831"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r15_instance_layout_20260901"
ASSET_ROOT = "/World/obj_oven"


@dataclass(frozen=True)
class OvenR15Result:
    output: Path
    package: Path
    asset_usd: Path
    manifest: Path


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    source: Path = DEFAULT_SOURCE,
) -> OvenR15Result:
    from pxr import Usd

    output = output.resolve()
    source = source.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    receipt = source / "promotion_receipt.json"
    if json.loads(receipt.read_text()).get("status") != "promoted":
        raise ValueError("r14 source package is not promoted")
    package = output / "package"
    package.mkdir(parents=True)
    shutil.copytree(source / "package", package / "deps/r14")
    provenance = output / "provenance/r14"
    provenance.mkdir(parents=True)
    shutil.copy2(receipt, provenance / "promotion_receipt.json")
    asset = package / "asset.usd"
    source_stage = Usd.Stage.Open(str(source / "package/asset.usd"))
    source_stage.Flatten(False).Export(str(asset))
    stage = Usd.Stage.Open(str(asset))
    instance = move_asset_contents_under_instance(
        stage, ASSET_ROOT, instance_type="scope"
    )
    stage.GetRootLayer().Save()
    audit = audit_instance_layout(stage, ASSET_ROOT)
    if audit["status"] != "pass":
        raise RuntimeError(f"r15 Instance audit blocked: {audit}")
    _write_json(package / "evidence/instance_layout_audit.json", audit)
    manifest = {
        "schema_version": "aan.ika_oven_125_task09_r15_instance_layout.v1",
        "package_id": "ika_oven_125_task09_r15_instance_layout",
        "overall_status": "candidate_runtime_qualification_pending",
        "blocked_reasons": ["Isaac Sim 4.1 namespace qualification pending"],
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": ASSET_ROOT,
        },
        "source": {
            "r14_asset_sha256": _sha(source / "package/asset.usd"),
            "r14_receipt_sha256": _sha(receipt),
            "r14_unchanged": True,
        },
        "instance_layout": {
            "schema_version": "aan.articulated_instance_layout.v1",
            "instance_prim_path": instance,
            "link_prim_paths": audit["link_prim_paths"],
            "complete_subtree_wrapped": True,
        },
        "claims": {
            "all_links_under_instance": True,
            "joint_targets_retargeted": True,
            "complete_asset_subtree_under_instance": True,
            "r14_mechanics_preserved": False,
            "runtime_namespace_qualified": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = package / "evidence/task09_r15_manifest.json"
    _write_json(manifest_path, manifest)
    return OvenR15Result(output, package, asset, manifest_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args(argv)
    print(build(args.output, source=args.source).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
