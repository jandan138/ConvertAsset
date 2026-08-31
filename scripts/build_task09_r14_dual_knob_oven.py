#!/usr/bin/env python3
"""Build the Task 09 r14 materialized oven with a second physical knob."""

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
    "ika_oven_125_task09_r13_materialized_20260831"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r14_dual_knob_20260831"
PRIMARY = "/World/obj_oven/ControlPanel/ControlKnob"
AUXILIARY = "/World/obj_oven/ControlPanel/AuxControlKnob"


@dataclass(frozen=True)
class DualKnobOvenResult:
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


def _replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise ValueError(f"controller {label} expected once, found {count}")
    return value.replace(old, new, 1)


def _dual_knob_controller(source: str) -> str:
    source = _replace_once(
        source,
        'KNOB_ROOT = CP + "/ControlKnob"\n',
        'KNOB_ROOT = CP + "/ControlKnob"\n'
        'AUX_KNOB_ROOT = CP + "/AuxControlKnob"\n'
        "KNOB_ROOTS = (KNOB_ROOT, AUX_KNOB_ROOT)\n",
        "knob constants",
    )
    old_update = '''def _update_knob_inputs(stage, state):
    carrier_path = KNOB_ROOT + "/PressCarrier"
    rotor_path = KNOB_ROOT + "/Rotor"
    carrier_pose = _pose(stage, carrier_path)
    rotor_pose = _pose(stage, rotor_path)
    if carrier_pose is None or rotor_pose is None:
        return

    travel = carrier_pose[0][1] - state.knob_rest_y
    previous_press = bool(state.knob_pressed)
    state.knob_pressed = travel > (0.00050 if previous_press else 0.00110)
    _set(stage, KNOB_ROOT, "oven:pressed", state.knob_pressed)
    if state.knob_pressed and not previous_press:
        _handle_knob_press(stage)

    relative = _q_multiply(_q_conjugate(carrier_pose[1]), rotor_pose[1])
    angle = _twist_degrees(relative, 1)
    if state.rotor_angle is None:
        state.rotor_angle = angle
        return
    delta = _wrap_degrees(angle - state.rotor_angle)
    state.rotor_angle = angle
    if abs(delta) > 60.0:
        state.rotor_accumulator = 0.0
        return
    state.rotor_accumulator += delta
    detents = 0
    while state.rotor_accumulator >= 15.0:
        state.rotor_accumulator -= 15.0
        detents += 1
    while state.rotor_accumulator <= -15.0:
        state.rotor_accumulator += 15.0
        detents -= 1
    if detents:
        _handle_detents(stage, detents)
'''
    new_update = '''def _root_uniform_scale(stage):
    root = _prim(stage, ROOT)
    if not root:
        return 1.0
    matrix = UsdGeom.Xformable(root).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    return max(1.0e-6, math.sqrt(sum(float(matrix[0][index]) ** 2 for index in range(3))))


def _update_knob_inputs(stage, state):
    threshold_scale = _root_uniform_scale(stage)
    for knob_root in KNOB_ROOTS:
        carrier_path = knob_root + "/PressCarrier"
        rotor_path = knob_root + "/Rotor"
        carrier_pose = _pose(stage, carrier_path)
        rotor_pose = _pose(stage, rotor_path)
        if carrier_pose is None or rotor_pose is None:
            continue

        travel = carrier_pose[0][1] - state.knob_rest_y[knob_root]
        previous_press = bool(state.knob_pressed[knob_root])
        pressed = travel > ((0.00050 if previous_press else 0.00110) * threshold_scale)
        state.knob_pressed[knob_root] = pressed
        _set(stage, knob_root, "oven:pressed", pressed)
        if pressed and not previous_press:
            _handle_knob_press(stage)

        relative = _q_multiply(_q_conjugate(carrier_pose[1]), rotor_pose[1])
        angle = _twist_degrees(relative, 1)
        previous_angle = state.rotor_angle[knob_root]
        if previous_angle is None:
            state.rotor_angle[knob_root] = angle
            continue
        delta = _wrap_degrees(angle - previous_angle)
        state.rotor_angle[knob_root] = angle
        if abs(delta) > 60.0:
            state.rotor_accumulator[knob_root] = 0.0
            continue
        state.rotor_accumulator[knob_root] += delta
        detents = 0
        while state.rotor_accumulator[knob_root] >= 15.0:
            state.rotor_accumulator[knob_root] -= 15.0
            detents += 1
        while state.rotor_accumulator[knob_root] <= -15.0:
            state.rotor_accumulator[knob_root] += 15.0
            detents -= 1
        if detents:
            _handle_detents(stage, detents)
'''
    source = _replace_once(source, old_update, new_update, "knob update")
    old_init = '''    carrier_pose = _pose(stage, KNOB_ROOT + "/PressCarrier")
    state.knob_rest_y = carrier_pose[0][1] if carrier_pose is not None else -0.329
    state.knob_pressed = False
    state.rotor_angle = None
    state.rotor_accumulator = 0.0
'''
    new_init = '''    state.knob_rest_y = {}
    state.knob_pressed = {}
    state.rotor_angle = {}
    state.rotor_accumulator = {}
    for knob_root in KNOB_ROOTS:
        carrier_pose = _pose(stage, knob_root + "/PressCarrier")
        state.knob_rest_y[knob_root] = carrier_pose[0][1] if carrier_pose is not None else -0.329
        state.knob_pressed[knob_root] = False
        state.rotor_angle[knob_root] = None
        state.rotor_accumulator[knob_root] = 0.0
'''
    source = _replace_once(source, old_init, new_init, "knob initialization")
    compile(source, "<oven-r14-dual-knob-controller>", "exec")
    return source


def build_dual_knob_oven(
    output: Path = DEFAULT_OUTPUT,
    *,
    source_output: Path = SOURCE_OUTPUT,
) -> DualKnobOvenResult:
    from pxr import Gf, Sdf, Usd, UsdGeom

    output = output.resolve()
    source_output = source_output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    source_asset = source_output / "package/asset.usd"
    source_receipt = source_output / "promotion_receipt.json"
    if not source_asset.is_file() or not source_receipt.is_file():
        raise FileNotFoundError("r13 materialized oven package is incomplete")
    if json.loads(source_receipt.read_text(encoding="utf-8")).get("status") != "promoted":
        raise ValueError("r13 materialized oven is not promoted")
    input_root = output / "input/source_package"
    package = output / "package"
    shutil.copytree(source_output, input_root)
    shutil.copytree(source_output / "package", package)
    asset = package / "asset.usd"
    layer = Sdf.Layer.FindOrOpen(str(asset))
    if layer is None:
        raise RuntimeError("cannot open r14 target layer")
    Sdf.CopySpec(layer, PRIMARY, layer, AUXILIARY)
    layer.Save()
    stage = Usd.Stage.Open(str(asset))
    if stage is None:
        raise RuntimeError("cannot open copied dual-knob stage")
    old_prefix = Sdf.Path(PRIMARY)
    new_prefix = Sdf.Path(AUXILIARY)
    for prim in stage.Traverse():
        if not prim.GetPath().HasPrefix(new_prefix):
            continue
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
    for suffix in ("/PressCarrier", "/Rotor"):
        prim = stage.GetPrimAtPath(AUXILIARY + suffix)
        value = prim.GetAttribute("xformOp:translate").Get()
        prim.GetAttribute("xformOp:translate").Set(
            Gf.Vec3d(-0.22, float(value[1]), float(value[2]))
        )
    press_joint = stage.GetPrimAtPath(AUXILIARY + "/Joints/Press")
    press_joint.GetAttribute("physics:localPos0").Set(
        Gf.Vec3f(-0.22, -0.329, 0.724)
    )
    door = stage.GetPrimAtPath("/World/obj_oven/Joints/DoorHinge")
    door.GetAttribute("drive:angular:physics:damping").Set(9.0)
    door.GetAttribute("physics:upperLimit").Set(60.0)
    root = UsdGeom.Xformable(stage.GetPrimAtPath("/World/obj_oven"))
    root.ClearXformOpOrder()
    root.AddTranslateOp().Set(Gf.Vec3d(0.0))
    root.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(1.0))
    root.AddScaleOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(1.0))
    controller = stage.GetPrimAtPath(
        "/World/obj_oven/ControlPanel/Runtime/ControllerGraph/Controller"
    )
    controller.GetAttribute("inputs:script").Set(
        _dual_knob_controller(controller.GetAttribute("inputs:script").Get())
    )
    stage.GetRootLayer().Save()
    manifest = {
        "schema_version": "aan.ika_oven_125_task09_r14_dual_knob_candidate.v1",
        "package_id": "ika_oven_125_task09_r14_dual_knob",
        "overall_status": "candidate_runtime_qualification_pending",
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": "/World/obj_oven",
            "consumer_mode": "materialized_stage_base",
        },
        "source": {
            "asset_sha256": _sha(source_asset),
            "promotion_receipt_sha256": _sha(source_receipt),
            "original_unchanged": True,
        },
        "interaction": {
            "primary_knob": PRIMARY,
            "auxiliary_knob": AUXILIARY,
            "shared_logical_state": True,
            "mechanically_synchronized": False,
            "door_drive_damping": 9.0,
            "door_lower_limit_deg": 0.0,
            "door_upper_limit_deg": 60.0,
            "qualified_uniform_scale_range": [0.85, 1.15],
        },
        "claims": {
            "dual_physical_knobs": False,
            "door_60deg_limit": False,
            "uniform_scale_0p85_1p15": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = package / "evidence/task09_r14_manifest.json"
    _write_json(manifest_path, manifest)
    return DualKnobOvenResult(output=output, asset_usd=asset, manifest=manifest_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-output", type=Path, default=SOURCE_OUTPUT)
    args = parser.parse_args(argv)
    print(build_dual_knob_oven(args.output, source_output=args.source_output).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
