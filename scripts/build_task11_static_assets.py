#!/usr/bin/env python3
"""Build source-bound static candidates for the Task 11 VR layout."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile


RACK_MEMBER = "packages/centrifuge_tube_15ml_50ml_mixed_rack/asset.usd"
RACK_PROFILE_MEMBER = (
    "packages/centrifuge_tube_15ml_50ml_mixed_rack/interaction_profile.json"
)
CENTRIFUGE_ENTRY = "/World/Centrifuge"
TUBE_ENTRY = "/World/CentrifugeTube15mlClosed"
LID_BUTTON_CENTER = (0.194, -0.263, 0.198)
TUBE_BODY_MESH = (
    f"{TUBE_ENTRY}/Visual/Source/centrifuge_tube_15ml_red_cap_ROOT/"
    "Tube_Body_Hollow/Tube_Body_Hollow_Mesh"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_rack(archive: Path, output: Path) -> Path:
    package = output / "mixed_rack/package"
    package.mkdir(parents=True)
    with zipfile.ZipFile(archive) as source:
        (package / "asset.usd").write_bytes(source.read(RACK_MEMBER))
        profile = json.loads(source.read(RACK_PROFILE_MEMBER))
    _write_json(package / "interaction/profile.json", profile)
    _write_json(
        package / "evidence/manifest.json",
        {
            "schema_version": "asset_application_normalizer.v1",
            "package_id": "mixed_tube_rack_18plus4_task11_static_r1",
            "asset_id": "mixed_tube_rack_18plus4",
            "asset_role": "static_support_object",
            "overall_status": "static_candidate_pending_isaac41",
            "blocked_reasons": ["isaac41_static_validation_not_run"],
            "source": {"archive_sha256": _sha(archive), "member": RACK_MEMBER},
            "entrypoints": {
                "root_usd": "asset.usd",
                "default_prim": "TubeRack15ml50ml_OriginalMesh",
                "asset_entry_prim": "/TubeRack15ml50ml_OriginalMesh",
                "asset_scope_prims": ["/TubeRack15ml50ml_OriginalMesh"],
                "consumer_profile": "scenario-forge",
            },
            "claims": {"isaac41_static_stability": False, "robot_policy_success": False},
        },
    )
    return package


def _upgrade_centrifuge(source: Path, output: Path) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    package = output / "centrifuge/package"
    shutil.copytree(source, package)
    stage = Usd.Stage.Open(str(package / "asset.usd"))
    button = UsdGeom.Xform.Define(stage, f"{CENTRIFUGE_ENTRY}/lid_open_button_link")
    UsdPhysics.RigidBodyAPI.Apply(button.GetPrim())
    mass = UsdPhysics.MassAPI.Apply(button.GetPrim())
    mass.CreateMassAttr(0.02)
    visual = UsdGeom.Cube.Define(stage, f"{button.GetPath()}/Visual")
    visual.CreateSizeAttr(1.0)
    UsdGeom.Xformable(visual).AddTranslateOp().Set(Gf.Vec3d(*LID_BUTTON_CENTER))
    UsdGeom.Xformable(visual).AddScaleOp().Set(Gf.Vec3f(0.063, 0.008, 0.018))
    visual.CreateDisplayColorAttr([(0.18, 0.72, 0.92)])
    collider = UsdGeom.Cube.Define(stage, f"{button.GetPath()}/__aan_collision_proxy/button")
    collider.CreateSizeAttr(1.0)
    UsdGeom.Xformable(collider).AddTranslateOp().Set(Gf.Vec3d(*LID_BUTTON_CENTER))
    UsdGeom.Xformable(collider).AddScaleOp().Set(Gf.Vec3f(0.063, 0.008, 0.018))
    UsdPhysics.CollisionAPI.Apply(collider.GetPrim())
    stage.OverridePrim(f"{CENTRIFUGE_ENTRY}/base_link/LidOpenStaticButton").CreateAttribute(
        "visibility", Sdf.ValueTypeNames.Token
    ).Set("invisible")
    joint = UsdPhysics.PrismaticJoint.Define(stage, f"{CENTRIFUGE_ENTRY}/lid_open_button_joint")
    joint.CreateBody0Rel().SetTargets([Sdf.Path(f"{CENTRIFUGE_ENTRY}/base_link")])
    joint.CreateBody1Rel().SetTargets([button.GetPath()])
    joint.CreateAxisAttr("Y")
    joint.CreateLocalPos0Attr(Gf.Vec3f(*LID_BUTTON_CENTER))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
    joint.CreateLowerLimitAttr(0.0)
    joint.CreateUpperLimitAttr(0.0025)
    drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "linear")
    drive.CreateStiffnessAttr(120.0)
    drive.CreateDampingAttr(2.0)
    drive.CreateMaxForceAttr(4.0)
    drive.CreateTargetPositionAttr(0.0)
    stage.GetRootLayer().Save()
    profile_path = package / "articulation/device_profile.json"
    profile = json.loads(profile_path.read_text())
    profile["revision"] = "r2-task11-static-controls"
    profile["buttons"] = {
        "lid_open_button": {
            "joint_prim": f"{CENTRIFUGE_ENTRY}/lid_open_button_joint",
            "part_prim": f"{CENTRIFUGE_ENTRY}/lid_open_button_link",
            "released_m": [0.0, 0.0004],
            "pressed_m": [0.0021, 0.0025],
            "causal_lid_transition": "pending",
        },
        "shutdown_button": {
            "joint_prim": f"{CENTRIFUGE_ENTRY}/stop_button_joint",
            "part_prim": f"{CENTRIFUGE_ENTRY}/stop_button_link",
            "released_m": [0.0, 0.0004],
            "pressed_m": [0.0021, 0.0025],
            "observable_power_off_transition": "pending",
        },
    }
    profile["required_runtime_task_gates"] = ["load_render_step_reset_static"]
    _write_json(profile_path, profile)
    _write_json(
        package / "evidence/task11_static_manifest.json",
        {
            "schema_version": "aan.task11_static_controls.v1",
            "status": "static_candidate_pending_isaac41",
            "asset_usd_sha256": _sha(package / "asset.usd"),
            "source_package": str(source),
            "raw_source_unchanged": True,
            "claims": {
                "lid_open_button_joint_authored": True,
                "shutdown_button_joint_authored": True,
                "button_causes_lid_open": False,
                "shutdown_causes_power_off": False,
            },
        },
    )
    return package


def _upgrade_tube(source: Path, output: Path) -> Path:
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    package = output / "closed_15ml_pbd_ready/package"
    shutil.copytree(source, package)
    stage = Usd.Stage.Open(str(package / "asset.usd"))
    stage.GetPrimAtPath(f"{TUBE_ENTRY}/__aan_collision_proxy/body").GetAttribute(
        "physics:collisionEnabled"
    ).Set(False)
    mesh = stage.GetPrimAtPath(TUBE_BODY_MESH)
    UsdPhysics.CollisionAPI.Apply(mesh)
    UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr("sdf")
    schemas = list(mesh.GetAppliedSchemas())
    for name in ("PhysxCollisionAPI", "PhysxSDFMeshCollisionAPI"):
        if name not in schemas:
            schemas.append(name)
    mesh.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))
    mesh.CreateAttribute(
        "physxSDFMeshCollision:sdfResolution", Sdf.ValueTypeNames.UInt
    ).Set(512)
    mesh.CreateAttribute(
        "physxSDFMeshCollision:sdfSubgridResolution", Sdf.ValueTypeNames.UInt
    ).Set(6)
    plug = UsdGeom.Cube.Define(stage, f"{TUBE_ENTRY}/__aan_collision_proxy/liquid_bottom_plug")
    plug.CreateSizeAttr(1.0)
    UsdGeom.Xformable(plug).AddTranslateOp().Set((0.0, 0.0, 0.002))
    UsdGeom.Xformable(plug).AddScaleOp().Set((0.014, 0.014, 0.004))
    UsdPhysics.CollisionAPI.Apply(plug.GetPrim())
    stage.GetRootLayer().Save()
    _write_json(
        package / "interaction/liquid_profile.json",
        {
            "schema_version": "aan.simple_sdf_container_profile.v1",
            "asset_entry_prim": TUBE_ENTRY,
            "visual_mesh_prim": TUBE_BODY_MESH,
            "collision": "sdf",
            "sdf_resolution": 512,
            "bottom_plug": "approved_cube",
            "particle_scale": "small_required",
            "compatible_device": "labspin_x8_24_socket_rotor",
            "compatible_rack_slot": "mixed_rack_18plus4.slot_15ml",
        },
    )
    _write_json(
        package / "evidence/task11_static_manifest.json",
        {
            "schema_version": "aan.task11_closed_liquid_tube.v1",
            "status": "static_candidate_pending_isaac41",
            "asset_usd_sha256": _sha(package / "asset.usd"),
            "raw_source_unchanged": True,
            "particles_included": False,
            "claims": {"pbd_static_retention": False, "robot_policy_success": False},
        },
    )
    return package


def build_assets(archive: Path, labspin: Path, tube: Path, output: Path) -> dict[str, Path]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return {
        "rack": _build_rack(archive.resolve(), output),
        "centrifuge": _upgrade_centrifuge(labspin.resolve(), output),
        "tube": _upgrade_tube(tube.resolve(), output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--labspin", type=Path, required=True)
    parser.add_argument("--tube", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for name, path in build_assets(args.archive, args.labspin, args.tube, args.out).items():
        print(name, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
