#!/usr/bin/env python3
"""Build the OVEN 125 r16 identity-Xform fixed-base articulation package."""

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
    audit_fixed_base_articulation_layout,
    author_fixed_base_articulation,
)


DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_task09_r15_instance_layout_20260901"
)
DEFAULT_OUTPUT = (
    REPO_ROOT / "outputs/ika_oven_125_task09_r16_fixed_articulation_20260904"
)
ASSET_ROOT = "/World/obj_oven"
INSTANCE = ASSET_ROOT + "/Instance"
BASE_LINK = INSTANCE + "/Body"
BASE_FIXED = INSTANCE + "/Joints/BaseFixed"


@dataclass(frozen=True)
class OvenR16Result:
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


def _replace_scope_with_identity_xform(stage: Any) -> None:
    from pxr import Sdf, UsdGeom

    instance = stage.GetPrimAtPath(INSTANCE)
    if not instance:
        raise ValueError(f"r15 Instance is missing: {INSTANCE}")
    if instance.IsA(UsdGeom.Xform):
        return
    if not instance.IsA(UsdGeom.Scope):
        raise ValueError(
            f"r15 Instance must be Scope or Xform, got {instance.GetTypeName()}"
        )
    layer = stage.GetRootLayer()
    spec = layer.GetPrimAtPath(Sdf.Path(INSTANCE))
    if spec is None:
        raise ValueError(f"cannot find root-layer Instance spec: {INSTANCE}")
    spec.typeName = "Xform"
    layer.Save()


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    source: Path = DEFAULT_SOURCE,
) -> OvenR16Result:
    from pxr import Usd

    output = output.resolve()
    source = source.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    receipt = source / "promotion_receipt.json"
    if json.loads(receipt.read_text()).get("status") != "promoted":
        raise ValueError("r15 source package is not promoted")

    package = output / "package"
    shutil.copytree(source / "package", package)
    provenance = output / "provenance/r15"
    provenance.mkdir(parents=True)
    shutil.copy2(receipt, provenance / "promotion_receipt.json")
    shutil.copy2(
        source / "qualification/full_report.json",
        provenance / "qualification_full_report.json",
    )

    asset = package / "asset.usd"
    stage = Usd.Stage.Open(str(asset))
    if stage is None:
        raise RuntimeError(f"cannot open copied r15 asset: {asset}")
    _replace_scope_with_identity_xform(stage)
    audit = author_fixed_base_articulation(
        stage,
        ASSET_ROOT,
        base_link=BASE_LINK,
        fixed_joint=BASE_FIXED,
    )
    stage.GetRootLayer().Save()
    audit = audit_fixed_base_articulation_layout(
        stage,
        ASSET_ROOT,
        base_link=BASE_LINK,
        fixed_joint=BASE_FIXED,
    )
    if audit["status"] != "pass":
        raise RuntimeError(f"r16 fixed-base articulation audit blocked: {audit}")
    _write_json(package / "evidence/fixed_base_articulation_audit.json", audit)

    old_manifest = package / "evidence/task09_r15_manifest.json"
    if old_manifest.exists():
        old_manifest.unlink()
    manifest = {
        "schema_version": "aan.ika_oven_125_task09_r16_fixed_articulation.v1",
        "package_id": "ika_oven_125_task09_r16_fixed_articulation",
        "overall_status": "candidate_runtime_qualification_pending",
        "blocked_reasons": [
            "Isaac Sim 4.1 fixed-base articulation qualification pending"
        ],
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": ASSET_ROOT,
        },
        "source": {
            "r15_asset_sha256": _sha(source / "package/asset.usd"),
            "r15_receipt_sha256": _sha(receipt),
            "r15_unchanged": True,
        },
        "articulation": {
            "root_prim_path": ASSET_ROOT,
            "instance_prim_path": INSTANCE,
            "instance_prim_type": "Xform",
            "base_link_prim_path": BASE_LINK,
            "fixed_joint_prim_path": BASE_FIXED,
            "existing_prim_paths_preserved": True,
        },
        "claims": {
            "all_links_under_instance": True,
            "instance_xform": True,
            "fixed_base_articulation": True,
            "all_links_nonkinematic": True,
            "existing_prim_paths_preserved": True,
            "task_controls_qualified": False,
            "runtime_namespace_qualified": False,
            "isaac45_compatibility_checked": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = package / "evidence/task09_r16_manifest.json"
    _write_json(manifest_path, manifest)
    return OvenR16Result(output, package, asset, manifest_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args(argv)
    print(build(args.output, source=args.source).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
