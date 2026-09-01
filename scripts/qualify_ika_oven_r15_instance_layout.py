#!/usr/bin/env python3
"""Qualify r15 Instance layout under canonical, prefixed, and VR namespaces."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.qualify_task09_r14_dual_knob_oven import (  # noqa: E402
    DEFAULT_ISAAC,
    INTERACTIVE_MEMBER,
    PHYSICS_MEMBER,
    _extract,
    evaluate_door_report,
    evaluate_interactive_report,
)


DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r15_instance_layout_20260901"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _fixture(source: Path, destination: Path, mount_root: str, scale: float) -> None:
    from pxr import Gf, Sdf, Usd, UsdGeom

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    stage = Usd.Stage.Open(str(destination))
    source_root = Sdf.Path("/World/obj_oven")
    target_root = Sdf.Path(mount_root)
    if target_root != source_root:
        parent = str(target_root.GetParentPath())
        if parent != "/World":
            UsdGeom.Xform.Define(stage, parent)
            stage.GetRootLayer().Save()
        edits = Sdf.BatchNamespaceEdit()
        edits.Add(source_root, target_root)
        if not stage.GetRootLayer().Apply(edits):
            raise RuntimeError(f"cannot materialize mount {mount_root}")
        stage.GetRootLayer().Save()
        for prim in stage.Traverse():
            for relationship in prim.GetRelationships():
                targets = relationship.GetTargets()
                rewritten = [
                    target.ReplacePrefix(source_root, target_root)
                    if target.HasPrefix(source_root)
                    else target
                    for target in targets
                ]
                if rewritten != targets:
                    relationship.SetTargets(rewritten)
            for attribute in prim.GetAttributes():
                targets = attribute.GetConnections()
                rewritten = [
                    target.ReplacePrefix(source_root, target_root)
                    if target.HasPrefix(source_root)
                    else target
                    for target in targets
                ]
                if rewritten != targets:
                    attribute.SetConnections(rewritten)
    mount = stage.GetPrimAtPath(target_root)
    scale_attr = mount.GetAttribute("xformOp:scale")
    if scale_attr:
        scale_attr.Set(Gf.Vec3d(scale))
    else:
        UsdGeom.Xformable(mount).AddScaleOp().Set(Gf.Vec3d(scale))
    stage.GetRootLayer().Save()


def _run(
    command: list[str], report: Path, *, environment: dict[str, str]
) -> dict[str, Any]:
    if not report.is_file():
        completed = subprocess.run(
            command,
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report.with_suffix(".stdout.log").write_bytes(completed.stdout)
        report.with_suffix(".stderr.log").write_bytes(completed.stderr)
    if not report.is_file():
        raise RuntimeError(f"qualification emitted no report: {report}")
    return json.loads(report.read_text(encoding="utf-8"))


def qualify(output: Path = DEFAULT_OUTPUT, *, isaac: Path = DEFAULT_ISAAC) -> Path:
    output = output.resolve()
    asset = output / "package/asset.usd"
    manifest_path = output / "package/evidence/task09_r15_manifest.json"
    qualification = output / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    interactive = qualification / "producer_interactive_smoke.py"
    physics = qualification / "producer_physics_smoke.py"
    _extract(INTERACTIVE_MEMBER, interactive)
    _extract(PHYSICS_MEMBER, physics)
    auxiliary = qualification / "producer_interactive_smoke_aux.py"
    source = interactive.read_text(encoding="utf-8")
    marker = 'KNOB_ROOT = CP + "/ControlKnob"'
    auxiliary.write_text(
        source.replace(marker, 'KNOB_ROOT = CP + "/AuxControlKnob"', 1),
        encoding="utf-8",
    )
    mounts = {
        "canonical": "/World/obj_oven",
        "prefixed": "/World/task_fixture/obj_oven",
        "vr": "/World/_scene/obj_oven",
    }
    fixtures = {}
    for label, mount in mounts.items():
        scale = {"canonical": 1.0, "prefixed": 0.85, "vr": 1.15}[label]
        path = qualification / f"fixtures/{label}.usd"
        _fixture(asset, path, mount, scale)
        fixtures[label] = path
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    interactive_runs = (
        ("canonical_primary", interactive, "canonical"),
        ("canonical_aux", auxiliary, "canonical"),
        ("prefixed_aux_scale085", auxiliary, "prefixed"),
        ("vr_aux_scale115", auxiliary, "vr"),
    )
    reports = {}
    evaluations = {}
    for name, script, label in interactive_runs:
        report = qualification / f"{name}.json"
        reports[name] = _run(
            [
                str(isaac),
                str(script),
                "--usd",
                str(fixtures[label]),
                "--output",
                str(report),
                "--root",
                mounts[label] + "/Instance",
                "--/app/omni.graph.scriptnode/opt_in=true",
            ],
            report,
            environment=environment,
        )
        evaluations[name] = evaluate_interactive_report(reports[name])
    door_path = qualification / "vr_door_60deg.json"
    door_report = _run(
        [
            str(isaac),
            str(physics),
            "--usd",
            str(fixtures["vr"]),
            "--output",
            str(door_path),
            "--root",
            mounts["vr"] + "/Instance",
            "--/app/omni.graph.scriptnode/opt_in=true",
        ],
        door_path,
        environment=environment,
    )
    door_evaluation = evaluate_door_report(door_report)
    passed = all(item["status"] == "pass" for item in evaluations.values()) and (
        door_evaluation["status"] == "pass"
    )
    aggregate = {
        "schema_version": "aan.ika_oven_125_task09_r15_qualification.v1",
        "status": "pass" if passed else "blocked",
        "runtime": "isaac41",
        "asset_sha256": _sha(asset),
        "mount_roots": mounts,
        "interactive_evaluations": evaluations,
        "door_evaluation": door_evaluation,
        "claim_boundary": (
            "The complete oven subtree is composed under Instance. R14 mechanics are "
            "qualified under canonical, arbitrary-prefix, and VR mount namespaces."
        ),
    }
    aggregate_path = qualification / "full_report.json"
    _write_json(aggregate_path, aggregate)
    manifest = json.loads(manifest_path.read_text())
    manifest["overall_status"] = aggregate["status"]
    manifest["blocked_reasons"] = [] if passed else ["runtime namespace qualification blocked"]
    manifest["claims"]["r14_mechanics_preserved"] = passed
    manifest["claims"]["runtime_namespace_qualified"] = passed
    manifest["qualification"] = {
        "report": "../../qualification/full_report.json",
        "sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if passed:
        _write_json(
            output / "promotion_receipt.json",
            {
                "schema_version": "aan.articulated_instance_promotion_receipt.v1",
                "status": "promoted",
                "asset_id": "ika_oven_125_task09_r15_instance_layout",
                "runtime": "isaac41",
                "asset_sha256": _sha(asset),
                "qualification_sha256": _sha(aggregate_path),
                "claims": manifest["claims"],
            },
        )
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac-python", type=Path, default=DEFAULT_ISAAC)
    args = parser.parse_args(argv)
    print(qualify(args.output, isaac=args.isaac_python))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
