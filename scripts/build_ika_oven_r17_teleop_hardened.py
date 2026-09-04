#!/usr/bin/env python3
"""Build OVEN 125 r17 with loss-tolerant VR knob sampling."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.articulated_instance_layout import (  # noqa: E402
    audit_fixed_base_articulation_layout,
)


DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_task09_r16_fixed_articulation_20260904"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r17_teleop_hardened_20260904"
ASSET_ROOT = "/World/obj_oven"
INSTANCE = ASSET_ROOT + "/Instance"
BASE_LINK = INSTANCE + "/Body"
BASE_FIXED = INSTANCE + "/Joints/BaseFixed"
CONTROLLER = INSTANCE + "/ControlPanel/Runtime/ControllerGraph/Controller"
KNOBS = (
    INSTANCE + "/ControlPanel/ControlKnob",
    INSTANCE + "/ControlPanel/AuxControlKnob",
)
R16_CONTROLLER_SHA256 = (
    "e7b90b783ddff0ad0f20406f94b596ea7ee17ba2c8116e29c71d223621eb14e9"
)
DETENT_DEGREES = 15.0
MAX_DETENTS_PER_TICK = 4


@dataclass(frozen=True)
class KnobRotationStep:
    angle: float | None
    accumulator: float
    detents: int
    delta: float
    sample_valid: bool


@dataclass(frozen=True)
class OvenR17Result:
    output: Path
    package: Path
    asset_usd: Path
    manifest: Path


def _wrap_degrees(value: float) -> float:
    return (float(value) + 180.0) % 360.0 - 180.0


def advance_knob_rotation(
    previous_angle: float | None,
    accumulator: float,
    current_angle: float | None,
) -> KnobRotationStep:
    """Advance one physical sample without losing pending detents on gaps."""

    if current_angle is None or not math.isfinite(float(current_angle)):
        return KnobRotationStep(previous_angle, float(accumulator), 0, 0.0, False)
    current = float(current_angle)
    if previous_angle is None:
        return KnobRotationStep(current, float(accumulator), 0, 0.0, True)
    delta = _wrap_degrees(current - float(previous_angle))
    pending = float(accumulator) + delta
    detents = max(
        -MAX_DETENTS_PER_TICK,
        min(MAX_DETENTS_PER_TICK, int(pending / DETENT_DEGREES)),
    )
    pending -= float(detents) * DETENT_DEGREES
    return KnobRotationStep(current, pending, detents, delta, True)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"r16 controller {label} expected once, found {count}")
    return source.replace(old, new, 1)


def harden_controller(source: str) -> str:
    if sha256(source.encode("utf-8")).hexdigest() != R16_CONTROLLER_SHA256:
        raise ValueError("r16 controller source SHA-256 changed")

    helper = """def _advance_knob_rotation(previous_angle, accumulator, current_angle):
    if current_angle is None or not math.isfinite(float(current_angle)):
        return previous_angle, float(accumulator), 0, 0.0, False
    current = float(current_angle)
    if previous_angle is None:
        return current, float(accumulator), 0, 0.0, True
    delta = _wrap_degrees(current - float(previous_angle))
    pending = float(accumulator) + delta
    detents = max(-4, min(4, int(pending / 15.0)))
    pending -= float(detents) * 15.0
    return current, pending, detents, delta, True


"""
    source = _replace_once(
        source,
        "def _update_knob_inputs(stage, state):\n",
        helper + "def _update_knob_inputs(stage, state):\n",
        "rotation helper insertion",
    )
    old_update = """def _update_knob_inputs(stage, state):
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


"""
    new_update = """def _update_knob_inputs(stage, state):
    threshold_scale = _root_uniform_scale(stage)
    for knob_root in KNOB_ROOTS:
        carrier_path = knob_root + "/PressCarrier"
        rotor_path = knob_root + "/Rotor"
        carrier_pose = _physx_pose(carrier_path)
        rotor_pose = _physx_pose(rotor_path)
        if carrier_pose is None or rotor_pose is None:
            state.knob_pose_miss_count[knob_root] += 1
            _set(stage, knob_root, "oven:physicalPoseSampleValid", False)
            _set(stage, knob_root, "oven:poseMissCount", state.knob_pose_miss_count[knob_root])
            continue

        _set(stage, knob_root, "oven:physicalPoseSampleValid", True)
        travel = carrier_pose[0][1] - state.knob_rest_y[knob_root]
        previous_press = bool(state.knob_pressed[knob_root])
        pressed = travel > ((0.00050 if previous_press else 0.00110) * threshold_scale)
        state.knob_pressed[knob_root] = pressed
        _set(stage, knob_root, "oven:pressed", pressed)
        if pressed and not previous_press:
            _handle_knob_press(stage)

        relative = _q_multiply(_q_conjugate(carrier_pose[1]), rotor_pose[1])
        current_angle = _twist_degrees(relative, 1)
        angle, accumulator, detents, delta, _ = _advance_knob_rotation(
            state.rotor_angle[knob_root],
            state.rotor_accumulator[knob_root],
            current_angle,
        )
        state.rotor_angle[knob_root] = angle
        state.rotor_accumulator[knob_root] = accumulator
        _set(stage, knob_root, "oven:lastPhysicalDeltaDegrees", float(delta))
        if detents:
            state.knob_detent_event_count[knob_root] += abs(int(detents))
            _set(
                stage,
                knob_root,
                "oven:detentEventCount",
                state.knob_detent_event_count[knob_root],
            )
            _handle_detents(stage, detents)


"""
    source = _replace_once(source, old_update, new_update, "knob update")
    old_init = """    state.knob_rest_y = {}
    state.knob_pressed = {}
    state.rotor_angle = {}
    state.rotor_accumulator = {}
    for knob_root in KNOB_ROOTS:
        carrier_pose = _pose(stage, knob_root + "/PressCarrier")
        state.knob_rest_y[knob_root] = carrier_pose[0][1] if carrier_pose is not None else -0.329
        state.knob_pressed[knob_root] = False
        state.rotor_angle[knob_root] = None
        state.rotor_accumulator[knob_root] = 0.0
"""
    new_init = """    state.knob_rest_y = {}
    state.knob_pressed = {}
    state.rotor_angle = {}
    state.rotor_accumulator = {}
    state.knob_pose_miss_count = {}
    state.knob_detent_event_count = {}
    for knob_root in KNOB_ROOTS:
        carrier_pose = _pose(stage, knob_root + "/PressCarrier")
        state.knob_rest_y[knob_root] = carrier_pose[0][1] if carrier_pose is not None else -0.329
        state.knob_pressed[knob_root] = False
        state.rotor_angle[knob_root] = None
        state.rotor_accumulator[knob_root] = 0.0
        state.knob_pose_miss_count[knob_root] = 0
        state.knob_detent_event_count[knob_root] = 0
        _set(stage, knob_root, "oven:physicalPoseSampleValid", False)
        _set(stage, knob_root, "oven:poseMissCount", 0)
        _set(stage, knob_root, "oven:lastPhysicalDeltaDegrees", 0.0)
        _set(stage, knob_root, "oven:detentEventCount", 0)
"""
    source = _replace_once(source, old_init, new_init, "knob initialization")
    compile(source, "<oven-r17-teleop-hardened-controller>", "exec")
    return source


def _author_diagnostics(stage: Any) -> None:
    from pxr import Sdf

    for path in KNOBS:
        knob = stage.GetPrimAtPath(path)
        knob.CreateAttribute(
            "oven:physicalPoseSampleValid", Sdf.ValueTypeNames.Bool, custom=True
        ).Set(False)
        knob.CreateAttribute(
            "oven:poseMissCount", Sdf.ValueTypeNames.Int, custom=True
        ).Set(0)
        knob.CreateAttribute(
            "oven:lastPhysicalDeltaDegrees", Sdf.ValueTypeNames.Float, custom=True
        ).Set(0.0)
        knob.CreateAttribute(
            "oven:detentEventCount", Sdf.ValueTypeNames.Int, custom=True
        ).Set(0)


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    source: Path = DEFAULT_SOURCE,
) -> OvenR17Result:
    from pxr import Usd

    output = output.resolve()
    source = source.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    receipt = source / "promotion_receipt.json"
    report = source / "qualification/full_report.json"
    if json.loads(receipt.read_text()).get("status") != "promoted":
        raise ValueError("r16 source package is not promoted")

    package = output / "package"
    shutil.copytree(source / "package", package)
    provenance = output / "provenance/r16"
    provenance.mkdir(parents=True)
    shutil.copy2(receipt, provenance / "promotion_receipt.json")
    shutil.copy2(report, provenance / "qualification_full_report.json")

    asset = package / "asset.usd"
    stage = Usd.Stage.Open(str(asset))
    if stage is None:
        raise RuntimeError(f"cannot open copied r16 asset: {asset}")
    controller = stage.GetPrimAtPath(CONTROLLER).GetAttribute("inputs:script")
    controller.Set(harden_controller(controller.Get()))
    _author_diagnostics(stage)
    stage.GetPrimAtPath(ASSET_ROOT).SetCustomDataByKey(
        "aan:teleopKnobController", "r17"
    )
    stage.GetRootLayer().Save()

    audit = audit_fixed_base_articulation_layout(
        stage,
        ASSET_ROOT,
        base_link=BASE_LINK,
        fixed_joint=BASE_FIXED,
    )
    if audit["status"] != "pass":
        raise RuntimeError(f"r17 fixed-base articulation audit blocked: {audit}")
    _write_json(package / "evidence/fixed_base_articulation_audit.json", audit)
    old_manifest = package / "evidence/task09_r16_manifest.json"
    if old_manifest.exists():
        old_manifest.unlink()
    manifest = {
        "schema_version": "aan.ika_oven_125_task09_r17_teleop_hardened.v1",
        "package_id": "ika_oven_125_task09_r17_teleop_hardened",
        "overall_status": "candidate_runtime_qualification_pending",
        "blocked_reasons": ["Isaac 4.5 teleop control qualification pending"],
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": ASSET_ROOT,
        },
        "source": {
            "r16_asset_sha256": _sha(source / "package/asset.usd"),
            "r16_receipt_sha256": _sha(receipt),
            "r16_unchanged": True,
            "controller_source_sha256": R16_CONTROLLER_SHA256,
        },
        "controller": {
            "revision": "r17",
            "detent_degrees": DETENT_DEGREES,
            "max_detents_per_tick": MAX_DETENTS_PER_TICK,
            "pose_source": "omni.physx.get_rigidbody_transformation",
            "runtime_usd_pose_fallback": False,
            "missing_sample_policy": "retain_last_valid_angle_and_accumulator",
            "large_delta_policy": "accumulate_and_rate_limit_without_clearing",
            "diagnostic_attributes": [
                "oven:physicalPoseSampleValid",
                "oven:poseMissCount",
                "oven:lastPhysicalDeltaDegrees",
                "oven:detentEventCount",
            ],
        },
        "claims": {
            "fixed_base_articulation_preserved": True,
            "existing_prim_paths_preserved": True,
            "loss_tolerant_knob_sampling_authored": True,
            "isaac45_teleop_controls_qualified": False,
            "isaac41_regression_passed": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = package / "evidence/task09_r17_manifest.json"
    _write_json(manifest_path, manifest)
    return OvenR17Result(output, package, asset, manifest_path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args(argv)
    print(build(args.output, source=args.source).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
