#!/usr/bin/env python3
"""Build the source-bound fixed-benchtop Task 09/12 IKA OVEN 125 package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_xinyu/ika_oven_125_interactive_v3.7z"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task0912_fixed_benchtop_r1_20260831"
ARCHIVE_SHA256 = "c3549ad1ed967e79b5ec3612e04da1acb70479d6528a8a0b144ad93acf379de1"
PRIMARY_SHA256 = "8bbd61f9d987a38fc582d218d01c33dd23cfe006ebaa4a1776b18b6b6d63e310"
SOURCE_PREFIX = "ika_oven_125_interactive_v3"
SOURCE_USD_MEMBER = f"{SOURCE_PREFIX}/ika_oven_125_control_dry_interactive_v3.usd"
SOURCE_CONTROLLER_MEMBER = f"{SOURCE_PREFIX}/scripts/oven125_v3_controller_inline.py"
SOURCE_INTERACTIVE_SMOKE_MEMBER = (
    f"{SOURCE_PREFIX}/scripts/interactive_smoke_oven125_v3.py"
)
SOURCE_MANIFEST_MEMBER = f"{SOURCE_PREFIX}/package_manifest.json"
SOURCE_ENTRY_PATH = "/World/Oven125"
ENTRY_PATH = SOURCE_ENTRY_PATH
DEVICE_PATH = ENTRY_PATH
CONTROLLER_PATH = f"{ENTRY_PATH}/ControlPanel/Runtime/ControllerGraph/Controller"
STANDARD_BENCHTOP_HEIGHT_M = 0.755


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _member(archive: Path, member: str) -> bytes:
    result = subprocess.run(
        ["7z", "x", "-so", str(archive), member],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"cannot read archive member {member!r}: "
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result.stdout


def _replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise ValueError(f"controller {label} replacement expected once, found {count}")
    return value.replace(old, new, 1)


def transform_controller(source: str) -> str:
    """Make the producer controller instance-relative with context-local paths."""
    source = _replace_once(
        source,
        "import math\n",
        "import contextvars\nimport math\n",
        "contextvars import",
    )
    old_constants = '''ROOT = "/World/Oven125"
CP = ROOT + "/ControlPanel"
RUNTIME = CP + "/Runtime"
PAGES = RUNTIME + "/Pages"
OVERLAYS = RUNTIME + "/Overlays"
BUTTON_ROOT = CP + "/Buttons"
KNOB_ROOT = CP + "/ControlKnob"
LAMP_ROOT = ROOT + "/Interior/ChamberLamp"
'''
    new_constants = '''_INSTANCE_ROOT = contextvars.ContextVar(
    "oven125_instance_root", default="/World/Oven125"
)
_CONTROLLER_SUFFIX = "/ControlPanel/Runtime/ControllerGraph/Controller"


class _InstancePath:
    def __init__(self, root_context, suffix):
        self.root_context = root_context
        self.suffix = str(suffix)

    def __add__(self, suffix):
        return self.__class__(self.root_context, self.suffix + str(suffix))

    def __str__(self):
        return self.root_context.get() + self.suffix


def _bind_instance_root(db):
    node_path = str(db.node.get_prim_path())
    if not node_path.endswith(_CONTROLLER_SUFFIX):
        raise RuntimeError("unexpected OVEN 125 controller node path: " + node_path)
    root_path = node_path[: -len(_CONTROLLER_SUFFIX)]
    _INSTANCE_ROOT.set(root_path)
    db.per_instance_state.root_path = root_path
    return root_path


ROOT = _InstancePath(_INSTANCE_ROOT, "")
CP = ROOT + "/ControlPanel"
RUNTIME = CP + "/Runtime"
PAGES = RUNTIME + "/Pages"
OVERLAYS = RUNTIME + "/Overlays"
BUTTON_ROOT = CP + "/Buttons"
KNOB_ROOT = CP + "/ControlKnob"
LAMP_ROOT = ROOT + "/Interior/ChamberLamp"
'''
    source = _replace_once(source, old_constants, new_constants, "path constants")
    source = _replace_once(
        source,
        "def _prim(stage, path):\n    return stage.GetPrimAtPath(path)\n",
        "def _prim(stage, path):\n    return stage.GetPrimAtPath(str(path))\n",
        "USD path coercion",
    )
    source = _replace_once(
        source,
        "value = _PHYSX.get_rigidbody_transformation(path)",
        "value = _PHYSX.get_rigidbody_transformation(str(path))",
        "PhysX path coercion",
    )
    for function_name in ("setup", "compute", "cleanup"):
        marker = f"def {function_name}(db):\n"
        source = _replace_once(
            source,
            marker,
            marker + "    _bind_instance_root(db)\n",
            f"{function_name} instance binding",
        )
    compile(source, "<ika-oven-125-relocatable-controller>", "exec")
    return source


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _bake_standard_benchtop_translation(stage: Any) -> dict[str, int]:
    """Bake +Z into rigid roots and static render/physics leaves."""
    from pxr import Gf, UsdGeom, UsdPhysics

    device = stage.GetPrimAtPath(DEVICE_PATH)
    rigid_roots = [
        prim
        for prim in stage.Traverse()
        if prim.GetPath().HasPrefix(DEVICE_PATH)
        and prim.HasAPI(UsdPhysics.RigidBodyAPI)
    ]
    rigid_paths = {prim.GetPath() for prim in rigid_roots}

    def under_rigid(prim: Any) -> bool:
        current = prim.GetParent()
        while current and current.GetPath().HasPrefix(DEVICE_PATH):
            if current.GetPath() in rigid_paths:
                return True
            current = current.GetParent()
        return False

    static_leaves = []
    for prim in stage.Traverse():
        if not prim.GetPath().HasPrefix(DEVICE_PATH) or under_rigid(prim):
            continue
        if prim.IsA(UsdGeom.Gprim) or prim.GetTypeName().endswith("Light"):
            static_leaves.append(prim)

    def shift(prim: Any) -> None:
        attr = prim.GetAttribute("xformOp:translate")
        if attr.IsValid():
            value = attr.Get() or Gf.Vec3d(0.0)
            attr.Set(
                Gf.Vec3d(
                    float(value[0]),
                    float(value[1]),
                    float(value[2]) + STANDARD_BENCHTOP_HEIGHT_M,
                )
            )
            return
        UsdGeom.Xformable(prim).AddTranslateOp().Set(
            Gf.Vec3d(0.0, 0.0, STANDARD_BENCHTOP_HEIGHT_M)
        )

    for prim in (*rigid_roots, *static_leaves):
        shift(prim)
    device.SetCustomDataByKey("aan:fixedMountBakeApplied", True)
    return {
        "rigid_roots_shifted": len(rigid_roots),
        "static_leaves_shifted": len(static_leaves),
    }


def build_package(
    output: Path = DEFAULT_OUTPUT,
    *,
    archive: Path = DEFAULT_ARCHIVE,
) -> Path:
    from pxr import Gf, Sdf, Usd, UsdPhysics

    output = output.resolve()
    archive = archive.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    if not archive.is_file():
        raise FileNotFoundError(archive)
    if _sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("source archive SHA-256 mismatch")

    source_usd = _member(archive, SOURCE_USD_MEMBER)
    if _sha256_bytes(source_usd) != PRIMARY_SHA256:
        raise ValueError("source primary USD SHA-256 mismatch")
    source_manifest = _member(archive, SOURCE_MANIFEST_MEMBER)
    producer_manifest = json.loads(source_manifest.decode("utf-8"))
    if producer_manifest.get("primarySha256") != PRIMARY_SHA256:
        raise ValueError("producer manifest does not bind the pinned primary USD")
    controller_source = _member(archive, SOURCE_CONTROLLER_MEMBER).decode("utf-8")
    transformed_controller = transform_controller(controller_source)
    interactive_smoke = _member(archive, SOURCE_INTERACTIVE_SMOKE_MEMBER)

    input_root = output / "input"
    package = output / "package"
    deps = package / "deps"
    overlays = package / "overlays"
    controller_root = package / "controller"
    evidence = package / "evidence"
    for directory in (input_root, deps, overlays, controller_root, evidence):
        directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, input_root / "source.7z")
    (input_root / "package_manifest.json").write_bytes(source_manifest)
    (input_root / "controller_original.py").write_text(
        controller_source, encoding="utf-8"
    )
    source_usd_path = deps / "source.usd"
    source_usd_path.write_bytes(source_usd)
    (controller_root / "controller_inline.py").write_text(
        transformed_controller, encoding="utf-8"
    )
    (evidence / "producer_interactive_smoke.py").write_bytes(interactive_smoke)

    source_stage = Usd.Stage.Open(str(source_usd_path))
    if source_stage is None:
        raise RuntimeError("cannot open extracted producer USD")
    if source_stage.GetDefaultPrim().GetPath() != Sdf.Path("/World"):
        raise ValueError("producer default prim must remain /World")
    joints = [
        prim
        for prim in source_stage.Traverse()
        if prim.IsA(UsdPhysics.Joint) and prim.GetPath().HasPrefix(SOURCE_ENTRY_PATH)
    ]
    if len(joints) != 16:
        raise ValueError(f"expected 16 producer joints, found {len(joints)}")
    missing_body0 = [
        prim for prim in joints if not UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()
    ]
    if len(missing_body0) != 15:
        raise ValueError(
            f"expected 15 world-anchored joints, found {len(missing_body0)}"
        )

    asset_path = package / "asset.usd"
    asset_path.write_bytes(source_usd)
    asset_stage = Usd.Stage.Open(str(asset_path))
    if asset_stage is None:
        raise RuntimeError("cannot reopen fixed-mount package clone")
    entry = asset_stage.GetPrimAtPath(ENTRY_PATH)
    entry.SetCustomDataByKey("aan:fixedMountProfile", "standard_benchtop_0p755m")
    bake_counts = _bake_standard_benchtop_translation(asset_stage)
    for source_joint in missing_body0:
        relative = source_joint.GetPath().MakeRelativePath(Sdf.Path(SOURCE_ENTRY_PATH))
        target_path = Sdf.Path(DEVICE_PATH).AppendPath(relative)
        target_joint = UsdPhysics.Joint(asset_stage.GetPrimAtPath(target_path))
        local_pos = source_joint.GetAttribute("physics:localPos0").Get()
        if local_pos is None:
            local_pos = Gf.Vec3f(0.0, 0.0, 0.0)
        target_joint.CreateLocalPos0Attr().Set(
            Gf.Vec3f(
                float(local_pos[0]),
                float(local_pos[1]),
                float(local_pos[2]) + STANDARD_BENCHTOP_HEIGHT_M,
            )
        )
    controller = asset_stage.GetPrimAtPath(CONTROLLER_PATH)
    controller.CreateAttribute("inputs:script", Sdf.ValueTypeNames.String).Set(
        transformed_controller
    )
    controller.CreateAttribute(
        "runtime:inlineScriptSha256", Sdf.ValueTypeNames.String, custom=True
    ).Set(_sha256_bytes(transformed_controller.encode("utf-8")))
    asset_stage.GetRootLayer().Save()

    composed = Usd.Stage.Open(str(asset_path))
    if composed is None or not composed.GetPrimAtPath(ENTRY_PATH).IsValid():
        raise RuntimeError("relocatable package does not compose the producer entry")
    composed_joints = [
        prim
        for prim in composed.Traverse()
        if prim.IsA(UsdPhysics.Joint) and prim.GetPath().HasPrefix(DEVICE_PATH)
    ]
    if sum(not UsdPhysics.Joint(prim).GetBody0Rel().GetTargets() for prim in composed_joints) != 15:
        raise RuntimeError("fixed-mount package changed source world-joint semantics")

    manifest = {
        "schema_version": "aan.ika_oven_125_task0912_fixed_mount_candidate.v1",
        "package_id": "ika_oven_125_task0912_fixed_benchtop_r1",
        "overall_status": "candidate_runtime_qualification_pending",
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": ENTRY_PATH,
            "consumer_profile": "scenario-forge",
            "runtime_profile": "isaac41",
        },
        "source": {
            "archive_sha256": ARCHIVE_SHA256,
            "primary_sha256": PRIMARY_SHA256,
            "original_unchanged": True,
        },
        "mounting": {
            "motion_mode": "fixed_standard_benchtop",
            "device_prim": DEVICE_PATH,
            "device_transform": "identity_with_descendant_bake",
            "bake_counts": bake_counts,
            "consumer_entry_transform_required": "identity",
            "consumer_xy_randomization_allowed": False,
            "consumer_mode": "direct_stage_only",
            "required_runtime_prim_path": ENTRY_PATH,
            "parent_xform_allowed": False,
            "vr_scene_mount_allowed": False,
            "joint_count": len(composed_joints),
            "world_anchored_joint_count": len(missing_body0),
            "world_anchor_z_bake_m": STANDARD_BENCHTOP_HEIGHT_M,
            "controller_root_strategy": "context_local_db_node_prim_path",
        },
        "claims": {
            "full_functional_parity_fixed_mount": False,
            "task09_task12_subset": False,
            "arbitrary_root_translation": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = evidence / "manifest.json"
    _write_json(manifest_path, manifest)
    _write_json(
        output / "package.manifest.json",
        {
            **manifest,
            "package_root": "package",
            "package_asset_sha256": _sha256_file(asset_path),
            "controller_sha256": _sha256_bytes(
                transformed_controller.encode("utf-8")
            ),
        },
    )
    return manifest_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    print(build_package(args.output, archive=args.archive))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
