"""Profile-driven relocation of one-chassis articulated appliances."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil

from .articulated_relocation_profile import (
    ArticulatedRelocationProfile,
    ControllerHook,
)


@dataclass(frozen=True)
class ArticulatedRelocationResult:
    asset_usd: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise ValueError(f"controller {label} replacement expected once, found {count}")
    return value.replace(old, new, 1)


def _rewrite_contextvar_node_path(source: str, hook: ControllerHook) -> str:
    actual_hash = sha256(source.encode("utf-8")).hexdigest()
    if actual_hash != hook.source_script_sha256:
        raise ValueError("controller script SHA-256 does not match the profile")
    source = _replace_once(
        source,
        "import math\n",
        "import contextvars\nimport math\n",
        "contextvars import",
    )
    root = hook.source_root
    old_constants = f'''ROOT = "{root}"
CP = ROOT + "/ControlPanel"
RUNTIME = CP + "/Runtime"
PAGES = RUNTIME + "/Pages"
OVERLAYS = RUNTIME + "/Overlays"
BUTTON_ROOT = CP + "/Buttons"
KNOB_ROOT = CP + "/ControlKnob"
LAMP_ROOT = ROOT + "/Interior/ChamberLamp"
'''
    new_constants = f'''_INSTANCE_ROOT = contextvars.ContextVar(
    "articulated_instance_root", default="{root}"
)
_CONTROLLER_SUFFIX = "{hook.controller_suffix}"


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
        raise RuntimeError("unexpected controller node path: " + node_path)
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
    compile(source, "<relocatable-articulated-controller>", "exec")
    return source


def _is_identity_entry(stage: object, path: str) -> bool:
    from pxr import Gf, UsdGeom

    prim = stage.GetPrimAtPath(path)
    xformable = UsdGeom.Xformable(prim)
    matrix = xformable.GetLocalTransformation()
    return not xformable.GetResetXformStack() and Gf.IsClose(
        matrix, Gf.Matrix4d(1.0), 1e-9
    )


def _world_anchor_to_body_local(stage: object, joint: object, chassis: object) -> None:
    from pxr import Gf, Usd, UsdGeom

    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    chassis_world = cache.GetLocalToWorldTransform(chassis)
    pos = joint.GetLocalPos0Attr().Get() or Gf.Vec3f(0.0)
    rot = joint.GetLocalRot0Attr().Get() or Gf.Quatf(1.0)
    world_anchor = Gf.Matrix4d(1.0)
    world_anchor.SetRotateOnly(
        Gf.Quatd(float(rot.GetReal()), Gf.Vec3d(rot.GetImaginary()))
    )
    world_anchor.SetTranslateOnly(Gf.Vec3d(pos))
    local_anchor = world_anchor * chassis_world.GetInverse()
    local_pos = local_anchor.ExtractTranslation()
    local_rot = local_anchor.ExtractRotationQuat()
    joint.CreateLocalPos0Attr().Set(Gf.Vec3f(local_pos))
    joint.CreateLocalRot0Attr().Set(
        Gf.Quatf(float(local_rot.GetReal()), Gf.Vec3f(local_rot.GetImaginary()))
    )


def normalize_articulated(
    source_usd: Path, out_dir: Path, profile_path: Path
) -> ArticulatedRelocationResult:
    """Create an unpromoted identity-root candidate; runtime qualification is separate."""
    from pxr import Sdf, Usd, UsdPhysics

    source_usd = source_usd.resolve()
    out_dir = out_dir.resolve()
    profile = ArticulatedRelocationProfile.from_path(profile_path.resolve())
    if not source_usd.is_file():
        raise FileNotFoundError(source_usd)
    if _sha256_file(source_usd) != profile.source_usd_sha256:
        raise ValueError("source USD SHA-256 does not match the profile")
    if out_dir.exists():
        raise FileExistsError(f"refusing to replace output: {out_dir}")

    stage = Usd.Stage.Open(str(source_usd))
    if stage is None:
        raise ValueError("source USD cannot be opened")
    entry = stage.GetPrimAtPath(profile.entry_prim)
    chassis = stage.GetPrimAtPath(profile.chassis_prim)
    if not entry.IsValid() or not chassis.IsValid():
        raise ValueError("profile entry_prim or chassis_prim is missing")
    if not _is_identity_entry(stage, profile.entry_prim):
        raise ValueError("entry_prim must have an identity local transform")

    joint_prims = [
        prim
        for prim in stage.Traverse()
        if prim.IsA(UsdPhysics.Joint)
        and prim.GetPath().HasPrefix(Sdf.Path(profile.joint_scope_prim))
    ]
    if not joint_prims:
        raise ValueError("joint_scope_prim contains no USD physics joints")
    world_anchored = []
    for prim in joint_prims:
        joint = UsdPhysics.Joint(prim)
        body0 = joint.GetBody0Rel().GetTargets()
        body1 = joint.GetBody1Rel().GetTargets()
        if not body1:
            raise ValueError(f"joint has no body1: {prim.GetPath()}")
        if any(not path.HasPrefix(Sdf.Path(profile.entry_prim)) for path in body1):
            raise ValueError(f"joint body1 crosses entry scope: {prim.GetPath()}")
        if not body0:
            world_anchored.append(str(prim.GetPath()))
        elif any(not path.HasPrefix(Sdf.Path(profile.entry_prim)) for path in body0):
            raise ValueError(f"joint body0 crosses entry scope: {prim.GetPath()}")

    package = out_dir / "package"
    deps = package / "deps"
    evidence = package / "evidence"
    deps.mkdir(parents=True)
    evidence.mkdir(parents=True)
    dependency = deps / ("source" + source_usd.suffix)
    shutil.copy2(source_usd, dependency)
    asset_usd = package / "asset.usd"
    shutil.copy2(source_usd, asset_usd)

    candidate = Usd.Stage.Open(str(asset_usd))
    if candidate is None:
        raise RuntimeError("copied candidate cannot be opened")
    candidate_chassis = candidate.GetPrimAtPath(profile.chassis_prim)
    rigid = UsdPhysics.RigidBodyAPI.Apply(candidate_chassis)
    rigid.CreateRigidBodyEnabledAttr(True)
    rigid.CreateKinematicEnabledAttr(True)
    candidate_chassis.SetCustomDataByKey(
        "aan:role", "relocatable_mount_link"
    )
    for path in world_anchored:
        joint = UsdPhysics.Joint(candidate.GetPrimAtPath(path))
        _world_anchor_to_body_local(candidate, joint, candidate_chassis)
        joint.CreateBody0Rel().SetTargets([Sdf.Path(profile.chassis_prim)])

    controller_evidence = []
    for hook in profile.controller_hooks:
        controller = candidate.GetPrimAtPath(hook.controller_prim)
        if not controller.IsValid():
            raise ValueError(f"controller hook prim is missing: {hook.controller_prim}")
        attr = controller.GetAttribute("inputs:script")
        script = attr.Get() if attr.IsValid() else None
        if not isinstance(script, str):
            raise ValueError(f"controller has no inline inputs:script: {hook.controller_prim}")
        rewritten = _rewrite_contextvar_node_path(script, hook)
        attr.Set(rewritten)
        controller_evidence.append(
            {
                "controller_prim": hook.controller_prim,
                "strategy": hook.strategy,
                "source_script_sha256": hook.source_script_sha256,
                "package_script_sha256": sha256(rewritten.encode()).hexdigest(),
            }
        )
    entry = candidate.GetPrimAtPath(profile.entry_prim)
    entry.SetCustomDataByKey("aan:articulatedRelocationProfile", profile.profile_id)
    candidate.GetRootLayer().Save()

    reopened = Usd.Stage.Open(str(asset_usd))
    if reopened is None or not _is_identity_entry(reopened, profile.entry_prim):
        raise RuntimeError("candidate did not preserve the identity entry transform")
    rebound = [
        prim
        for prim in reopened.Traverse()
        if prim.IsA(UsdPhysics.Joint)
        and prim.GetPath().HasPrefix(Sdf.Path(profile.joint_scope_prim))
        and UsdPhysics.Joint(prim).GetBody0Rel().GetTargets()
        == [Sdf.Path(profile.chassis_prim)]
    ]
    if len(rebound) != len(world_anchored):
        raise RuntimeError("not all world-anchored joints were rebound to the chassis")

    manifest = {
        "schema_version": "aan.articulated_relocation_candidate.v1",
        "profile_id": profile.profile_id,
        "overall_status": "candidate_runtime_qualification_pending",
        "source": {
            "usd_sha256": profile.source_usd_sha256,
            "package_local_copy": f"deps/{dependency.name}",
            "original_unchanged": True,
        },
        "entrypoints": {
            "root_usd": "asset.usd",
            "asset_entry_prim": profile.entry_prim,
            "default_prim": str(reopened.GetDefaultPrim().GetPath()),
        },
        "relocatability": {
            "topology": profile.topology,
            "identity_entry": True,
            "chassis_prim": profile.chassis_prim,
            "chassis_kinematic": True,
            "joint_count": len(joint_prims),
            "world_anchored_joints_rebound": len(world_anchored),
            "support_frame": {
                "prim": profile.support_frame_prim,
                "local_support_z_m": profile.local_support_z_m,
            },
            "controller_hooks": controller_evidence,
        },
        "promotion": {
            "requested_tier": profile.promotion.requested_tier,
            "required_functions": list(profile.promotion.required_functions),
            "portability_gates_passed": False,
            "functional_gates_passed": False,
        },
        "claims": {
            "relocatable_full": False,
            "relocatable_task_scoped": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    manifest_path = evidence / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return ArticulatedRelocationResult(
        asset_usd=asset_usd, manifest_path=manifest_path
    )
