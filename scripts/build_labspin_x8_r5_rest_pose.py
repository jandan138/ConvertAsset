#!/usr/bin/env python3
"""Derive LABSPIN X8 r5 with a joint-satisfied closed preview rest pose."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import traceback


ROOT = "/World/Centrifuge"
DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "labspin_x8_task11_r4_20260824/package"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "labspin_x8_task11_r5_rest_pose_20260824/package"
)
LINK_JOINTS = {
    "lid_link": "lid_hinge_joint",
    "rotor_link": "rotor_spin_joint",
    "encoder_link": "encoder_joint",
    "start_button_link": "start_button_joint",
    "stop_button_link": "stop_button_joint",
    "lid_open_button_link": "lid_open_button_joint",
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _identity(quat) -> bool:
    return abs(float(quat.GetReal()) - 1.0) <= 1e-7 and all(
        abs(float(value)) <= 1e-7 for value in quat.GetImaginary()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.out.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite: {output}")
    shutil.copytree(source, output)

    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "multi_gpu": False})
    sys.argv = original
    try:
        import omni.usd
        from pxr import Gf, UsdGeom, UsdPhysics

        asset = output / "asset.usd"
        context = omni.usd.get_context()
        if not context.open_stage(str(asset)):
            raise RuntimeError(f"cannot open {asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetRootLayer())
        records = []
        for link_name, joint_name in LINK_JOINTS.items():
            joint = UsdPhysics.Joint.Get(stage, f"{ROOT}/{joint_name}")
            local_pos0 = joint.GetLocalPos0Attr().Get()
            local_pos1 = joint.GetLocalPos1Attr().Get()
            local_rot0 = joint.GetLocalRot0Attr().Get()
            local_rot1 = joint.GetLocalRot1Attr().Get()
            if any(abs(float(value)) > 1e-7 for value in local_pos1):
                raise RuntimeError(f"{joint_name} localPos1 is not zero")
            if not _identity(local_rot0) or not _identity(local_rot1):
                raise RuntimeError(f"{joint_name} localRot0/localRot1 are not identity")
            prim = stage.GetPrimAtPath(f"{ROOT}/{link_name}")
            xform = UsdGeom.Xformable(prim)
            ops = {op.GetOpType(): op for op in xform.GetOrderedXformOps()}
            translate = ops.get(UsdGeom.XformOp.TypeTranslate) or xform.AddTranslateOp(
                UsdGeom.XformOp.PrecisionFloat
            )
            orient = ops.get(UsdGeom.XformOp.TypeOrient) or xform.AddOrientOp(
                UsdGeom.XformOp.PrecisionFloat
            )
            scale = ops.get(UsdGeom.XformOp.TypeScale) or xform.AddScaleOp(
                UsdGeom.XformOp.PrecisionFloat
            )
            translate.Set(Gf.Vec3f(*local_pos0))
            orient.Set(Gf.Quatf(1.0, Gf.Vec3f(0.0)))
            scale.Set(Gf.Vec3f(1.0))
            records.append(
                {
                    "link": link_name,
                    "joint": joint_name,
                    "translation_parent_local_m": [float(value) for value in local_pos0],
                    "orientation_wxyz": [1.0, 0.0, 0.0, 0.0],
                    "derivation": "body0_T_local0_inverse_body1_local1_at_q0",
                }
            )
        stage.GetRootLayer().Save()

        profile_path = output / "articulation/device_profile.json"
        profile = json.loads(profile_path.read_text())
        profile["revision"] = "r5-joint-satisfied-preview-rest-pose"
        profile["preview_rest_pose"] = {
            "state": "closed_rotor_stopped_buttons_released",
            "links": records,
        }
        profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
        build_report = {
            "schema_version": "aan.labspin_x8_r5_rest_pose_build.v1",
            "status": "built_pending_runtime_qualification",
            "source_package": str(source),
            "source_asset_sha256": _sha(source / "asset.usd"),
            "asset_usd_sha256": _sha(asset),
            "rest_pose_links": records,
            "unchanged": [
                "joint_local_frames_and_limits",
                "joint_drives",
                "collision_geometry",
                "mass_and_inertia",
                "base_fixed_joint",
                "device_behavior_graph",
                "source_visual_facade",
            ],
        }
        evidence = output / "evidence"
        (evidence / "r5_rest_pose_build.json").write_text(
            json.dumps(build_report, indent=2, sort_keys=True) + "\n"
        )
        manifest_path = evidence / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["package_id"] = "labspin_x8_centrifuge_task11_r5_rest_pose_isaac41"
        manifest["overall_status"] = "candidate"
        manifest["blocked_reasons"] = ["r5_rest_pose_runtime_qualification_pending"]
        manifest.setdefault("claims", {})["static_rest_pose_assembled"] = False
        manifest["claims"]["first_step_pose_continuity"] = False
        manifest["source"]["r5_rest_pose_derivation"] = {
            "source_package": str(source),
            "source_asset_sha256": _sha(source / "asset.usd"),
            "raw_files_unchanged": True,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(output)
        return 0
    except BaseException:
        traceback.print_exc()
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
