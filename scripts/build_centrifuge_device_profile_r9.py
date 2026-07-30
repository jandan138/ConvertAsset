#!/usr/bin/env python3
"""Build the source-bound articulated device profile for centrifuge r9.

The r9 facade proves that all pre-existing world transforms are identical to
r8, so the five interaction frames and joint semantics are carried forward
byte-for-value from the measured r8 profile.  This builder binds them to the r9
source SHA, measures the new support collider, adds an authoritative root-local
``support`` frame, and requires the hash-bound ``benchtop_stability`` gate.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_R8_ROOT = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/outputs/centrifuge_identity_root_r8"
)
DEFAULT_R9_ROOT = REPO_ROOT / "outputs/centrifuge_identity_root_r9"
ROOT = "/World/Centrifuge"
BENCHTOP_SUPPORT_COLLIDER = (
    f"{ROOT}/group_0/__aan_collision_proxy/__aan_benchtop_support"
)
PROFILE_SCHEMA_VERSION = "aan.articulated_device_profile.v1"
MEASUREMENT_SCHEMA_VERSION = "aan.articulated_device_profile_measurement.v1"
DEFAULT_PROFILE_REVISION = "r5-identity-root-benchtop"


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to replace measured artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _semantic_joints() -> dict[str, dict[str, Any]]:
    """Return the unchanged three-DOF r8 centrifuge semantics."""
    return {
        "start_button": {
            "joint_prim": f"{ROOT}/group_2/PrismaticJoint",
            "part_prim": f"{ROOT}/group_2",
            "dof_index": 0,
            "runtime_reset_value": 0.0,
            "reset_state": "released",
            "states": {
                "released": [-0.0005, 0.0],
                "pressed": [-0.0055, -0.0045],
            },
        },
        "rotor": {
            "joint_prim": f"{ROOT}/group_6/RevoluteJoint",
            "part_prim": f"{ROOT}/group_6",
            "dof_index": 1,
            "runtime_reset_value": 0.0,
            "reset_state": "parked",
            "states": {"parked": [-0.05, 0.0]},
        },
        "lid": {
            "joint_prim": f"{ROOT}/group_23/RevoluteJoint",
            "part_prim": f"{ROOT}/group_23",
            "dof_index": 2,
            "runtime_reset_value": math.radians(-89.1323471069336),
            "reset_state": "open",
            "states": {
                "open": [math.radians(-89.1323471069336), -1.45],
                "closed": [-0.0872664626, 0.0],
            },
        },
    }


def _required_runtime_task_gates() -> list[str]:
    """Return all gates that the finalizer must require for r9."""
    return [
        "lid_contact_cycle",
        "button_contact_cycle",
        "button_reset_stability",
        "rotor_reset_stability",
        "socket_insertion_clearance",
        "benchtop_stability",
    ]


def _support_frame(support_plane_root_local_z_m: float) -> dict[str, Any]:
    """Describe the authoritative root-local benchtop support plane."""
    return {
        "parent_prim": ROOT,
        "translation_parent_local_m": [
            0.0,
            0.0,
            float(support_plane_root_local_z_m),
        ],
        "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
        "authoritative": True,
    }


def _verify_static_dof_mapping(manifest: dict[str, Any]) -> None:
    closure = manifest.get("articulation_closure")
    if not isinstance(closure, dict):
        raise ValueError("manifest articulation_closure is missing")
    mapping = closure.get("dof_mapping")
    expected = {
        value["dof_index"]: value["joint_prim"]
        for value in _semantic_joints().values()
    }
    actual = (
        {
            value.get("dof_index"): value.get("joint_prim")
            for value in mapping
            if isinstance(value, dict)
        }
        if isinstance(mapping, list)
        else {}
    )
    if actual != expected:
        raise ValueError("manifest DOF mapping does not match the r9 profile")


def _identity_matrix_error(matrix: Any) -> float:
    return max(
        abs(
            float(matrix[row][column])
            - (1.0 if row == column else 0.0)
        )
        for row in range(4)
        for column in range(4)
    )


def _world_bounds(
    stage: Any,
    prim_path: str,
    *,
    usd: Any,
    usd_geom: Any,
) -> tuple[list[float], list[float]]:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise ValueError(f"missing prim: {prim_path}")
    cache = usd_geom.BBoxCache(
        usd.TimeCode.Default(),
        [usd_geom.Tokens.default_],
    )
    bound = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    return (
        [float(value) for value in bound.GetMin()],
        [float(value) for value in bound.GetMax()],
    )


def _validate_predecessor_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ValueError("r8 device profile schema_version is unsupported")
    if profile.get("asset_entry_prim") != ROOT:
        raise ValueError("r8 device profile asset_entry_prim is unexpected")
    if profile.get("articulation_root_prim") != ROOT:
        raise ValueError("r8 device profile articulation_root_prim is unexpected")
    if profile.get("semantic_joints") != _semantic_joints():
        raise ValueError("r8 device profile joint semantics have drifted")
    expected_gates = _required_runtime_task_gates()[:-1]
    if profile.get("required_runtime_task_gates") != expected_gates:
        raise ValueError("r8 device profile required gates have drifted")
    frames = profile.get("named_frames")
    if not isinstance(frames, dict) or not frames:
        raise ValueError("r8 device profile named_frames are missing")
    if "support" in frames:
        raise ValueError("r8 device profile unexpectedly already has support")


def _build(args: argparse.Namespace) -> dict[str, Any]:
    from pxr import Usd, UsdGeom, UsdPhysics

    package = args.package.resolve()
    manifest_path = args.manifest.resolve()
    predecessor_profile_path = args.r8_profile.resolve()
    manifest = _json_object(manifest_path)
    _verify_static_dof_mapping(manifest)
    source = manifest.get("source")
    entrypoints = manifest.get("entrypoints")
    if (
        not isinstance(source, dict)
        or not isinstance(source.get("sha256"), str)
        or not isinstance(entrypoints, dict)
        or entrypoints.get("asset_entry_prim") != ROOT
    ):
        raise ValueError("manifest does not describe the r9 centrifuge")
    asset_path = package / "asset.usd"
    stage = Usd.Stage.Open(str(asset_path))
    if stage is None:
        raise RuntimeError(f"could not open r9 package: {asset_path}")
    root = stage.GetPrimAtPath(ROOT)
    if not root.IsValid():
        raise ValueError(f"r9 package is missing {ROOT}")
    root_matrix = UsdGeom.XformCache(
        Usd.TimeCode.Default()
    ).GetLocalToWorldTransform(root)
    identity_error = _identity_matrix_error(root_matrix)
    if identity_error > 1.0e-6:
        raise ValueError(f"r9 centrifuge root is not identity: {identity_error}")

    support_prim = stage.GetPrimAtPath(BENCHTOP_SUPPORT_COLLIDER)
    if not support_prim.IsValid() or support_prim.GetTypeName() != "Cube":
        raise ValueError("r9 package benchtop support Cube is missing")
    if UsdGeom.Cube(support_prim).GetSizeAttr().Get() != 1.0:
        raise ValueError("r9 benchtop support Cube must author size=1")
    if (
        UsdGeom.Imageable(support_prim).ComputeVisibility()
        != UsdGeom.Tokens.invisible
    ):
        raise ValueError("r9 benchtop support collider must be render-invisible")
    collision = UsdPhysics.CollisionAPI(support_prim)
    if not collision or collision.GetCollisionEnabledAttr().Get() is not True:
        raise ValueError("r9 benchtop support collision must be enabled")
    support_minimum, support_maximum = _world_bounds(
        stage,
        BENCHTOP_SUPPORT_COLLIDER,
        usd=Usd,
        usd_geom=UsdGeom,
    )
    support_plane_z = float(support_minimum[2])
    if abs(support_plane_z) <= 1.0e-6:
        support_plane_z = 0.0

    predecessor = _json_object(predecessor_profile_path)
    _validate_predecessor_profile(predecessor)
    profile = deepcopy(predecessor)
    profile.update(
        {
            "profile_id": "hci955350.centrifuge.identity-root.r9",
            "revision": args.revision,
            "source_sha256": source["sha256"],
            "semantic_joints": _semantic_joints(),
            "required_runtime_task_gates": _required_runtime_task_gates(),
        }
    )
    frames = deepcopy(predecessor["named_frames"])
    frames["support"] = _support_frame(support_plane_z)
    profile["named_frames"] = frames

    measurement = {
        "schema_version": MEASUREMENT_SCHEMA_VERSION,
        "status": "pass",
        "package_asset_sha256": _sha256_file(asset_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "source_sha256": source["sha256"],
        "predecessor_profile": {
            "path": str(predecessor_profile_path),
            "sha256": _sha256_file(predecessor_profile_path),
            "carried_forward_frames": sorted(predecessor["named_frames"]),
            "basis": (
                "r9 facade protected-state verification proves every existing "
                "world transform and drive is unchanged from r8"
            ),
        },
        "identity_root_maximum_error": identity_error,
        "support": {
            "frame": frames["support"],
            "collider_prim": BENCHTOP_SUPPORT_COLLIDER,
            "collider_world_bounds_m": {
                "min": support_minimum,
                "max": support_maximum,
            },
            "cube_size": 1.0,
            "visibility": "invisible",
            "collision_enabled": True,
        },
        "required_runtime_task_gates": _required_runtime_task_gates(),
        "claim_boundary": (
            "The profile binds r8's already measured articulation semantics "
            "and interaction frames to the protected-state r9 facade, adds a "
            "measured support frame, and requires benchtop stability. It does "
            "not claim robot-policy success or real-world physical parity."
        ),
    }
    _write_json(args.out_profile, profile)
    _write_json(args.out_measurement, measurement)
    return {
        "status": "pass",
        "profile": str(args.out_profile),
        "profile_sha256": _sha256_file(args.out_profile),
        "measurement": str(args.out_measurement),
        "support_plane_root_local_z_m": support_plane_z,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the r9 articulated centrifuge profile with an authoritative "
            "support frame and required benchtop stability gate."
        )
    )
    parser.add_argument("--package", type=Path, default=DEFAULT_R9_ROOT / "package")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_R9_ROOT / "package.manifest.json",
    )
    parser.add_argument(
        "--r8-profile",
        type=Path,
        default=DEFAULT_R8_ROOT
        / "centrifuge.articulated_device_profile_r4_identity_root.json",
    )
    parser.add_argument(
        "--out-profile",
        type=Path,
        default=DEFAULT_R9_ROOT
        / "centrifuge.articulated_device_profile_r5_identity_root_benchtop.json",
    )
    parser.add_argument(
        "--out-measurement",
        type=Path,
        default=DEFAULT_R9_ROOT
        / "centrifuge.articulated_device_profile_measurement_r5_identity_root_benchtop.json",
    )
    parser.add_argument("--revision", default=DEFAULT_PROFILE_REVISION)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.package = args.package.resolve()
    args.manifest = args.manifest.resolve()
    args.r8_profile = args.r8_profile.resolve()
    args.out_profile = args.out_profile.resolve()
    args.out_measurement = args.out_measurement.resolve()
    try:
        result = _build(args)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": f"{type(exc).__name__}: {exc}",
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
