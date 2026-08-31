#!/usr/bin/env python3
"""Build a materialized /World/obj_oven stage-base package for Task 09 VR."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_OUTPUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_identity_root_r1_20260831"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r13_materialized_20260831"


@dataclass(frozen=True)
class MaterializedOvenResult:
    output: Path
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


def build_materialized_oven(
    output: Path = DEFAULT_OUTPUT,
    *,
    source_output: Path = SOURCE_OUTPUT,
) -> MaterializedOvenResult:
    from pxr import Sdf, Usd, UsdPhysics

    output = output.resolve()
    source_output = source_output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    source_asset = source_output / "package/asset.usd"
    source_manifest = source_output / "package/evidence/manifest.json"
    source_receipt = source_output / "promotion_receipt.json"
    if not all(path.is_file() for path in (source_asset, source_manifest, source_receipt)):
        raise FileNotFoundError("identity-root oven source package is incomplete")
    receipt = json.loads(source_receipt.read_text(encoding="utf-8"))
    if receipt.get("status") != "promoted":
        raise ValueError("identity-root oven source is not promoted")

    input_root = output / "input/source_package"
    package = output / "package"
    shutil.copytree(source_output, input_root)
    shutil.copytree(source_output / "package", package)
    asset = package / "asset.usd"
    layer = Sdf.Layer.FindOrOpen(str(asset))
    if layer is None:
        raise RuntimeError("cannot open materialized oven root layer")
    edits = Sdf.BatchNamespaceEdit()
    edits.Add("/World/Oven125", "/World/obj_oven")
    if not layer.Apply(edits):
        raise RuntimeError("cannot rename materialized oven entry")
    layer.Save()

    stage = Usd.Stage.Open(str(asset))
    if stage is None or not stage.GetPrimAtPath("/World/obj_oven").IsValid():
        raise RuntimeError("renamed oven package cannot be composed")
    old_prefix = Sdf.Path("/World/Oven125")
    new_prefix = Sdf.Path("/World/obj_oven")
    for prim in stage.Traverse():
        for relationship in prim.GetRelationships():
            targets = relationship.GetTargets()
            rewritten = [
                target.ReplacePrefix(old_prefix, new_prefix)
                if target.HasPrefix(old_prefix)
                else target
                for target in targets
            ]
            if rewritten != targets:
                relationship.SetTargets(rewritten)
        for attribute in prim.GetAttributes():
            connections = attribute.GetConnections()
            rewritten = [
                target.ReplacePrefix(old_prefix, new_prefix)
                if target.HasPrefix(old_prefix)
                else target
                for target in connections
            ]
            if rewritten != connections:
                attribute.SetConnections(rewritten)
    stage.GetRootLayer().Save()
    joints = [
        prim
        for prim in stage.Traverse()
        if prim.IsA(UsdPhysics.Joint)
        and str(prim.GetPath()).startswith("/World/obj_oven/")
    ]
    if len(joints) != 16:
        raise RuntimeError("materialized oven joint graph is incomplete")
    if sum(
        [str(path) for path in UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()]
        == ["/World/obj_oven/Body"]
        for prim in joints
    ) != 15:
        raise RuntimeError("materialized oven chassis targets were not retargeted")

    manifest = {
        "schema_version": "aan.ika_oven_125_task09_materialized_candidate.v1",
        "package_id": "ika_oven_125_task09_r13_materialized",
        "overall_status": "candidate_runtime_qualification_pending",
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": "/World/obj_oven",
            "runtime": "isaac41",
        },
        "source": {
            "asset_sha256": _sha(source_asset),
            "manifest_sha256": _sha(source_manifest),
            "promotion_receipt_sha256": _sha(source_receipt),
            "original_unchanged": True,
        },
        "mounting": {
            "consumer_mode": "materialized_stage_base",
            "reference_mount_allowed": False,
            "sublayer_mount_allowed": False,
            "scenario_forge_must_copy_stage_then_append_scene": True,
            "entry_transform_allowed": True,
            "controller_graph_authored_directly": True,
        },
        "claims": {
            "task09_control_sequence": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = package / "evidence/task09_materialized_manifest.json"
    _write_json(manifest_path, manifest)
    return MaterializedOvenResult(
        output=output,
        asset_usd=asset,
        manifest=manifest_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-output", type=Path, default=SOURCE_OUTPUT)
    args = parser.parse_args(argv)
    print(build_materialized_oven(args.output, source_output=args.source_output).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
