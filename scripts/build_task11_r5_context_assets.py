#!/usr/bin/env python3
"""Build Task 11 r5 visual-static closed tubes and target-support rack."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile


PACKAGE_MEMBERS = {
    "body15": "packages/centrifuge_tube_15ml_body/",
    "cap15": "packages/centrifuge_tube_15ml_cap/",
    "body50": "packages/centrifuge_tube_50ml_body/",
    "cap50": "packages/centrifuge_tube_50ml_cap/",
}
TARGET_FRAME = "slot_15ml_r00_c02_inserted_bottom"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _extract_packages(archive: Path, root: Path) -> dict[str, Path]:
    result = {}
    with zipfile.ZipFile(archive) as source:
        for label, prefix in PACKAGE_MEMBERS.items():
            target = root / label
            for name in source.namelist():
                if name.startswith(prefix) and not name.endswith("/"):
                    destination = target / name[len(prefix) :]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read(name))
            result[label] = target
    return result


def _build_context(
    output: Path, sources: dict[str, Path], *, size: str, cap_z: float
) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom

    package = output / f"context_{size}_closed/package"
    package.mkdir(parents=True)
    deps = package / "deps"
    body_label = "body15" if size == "15ml" else "body50"
    cap_label = "cap15" if size == "15ml" else "cap50"
    shutil.copytree(sources[body_label], deps / "body")
    shutil.copytree(sources[cap_label], deps / "cap")
    entry_name = "ContextTube15mlClosed" if size == "15ml" else "ContextTube50mlClosed"
    body_entry = "CentrifugeTube15mlBody" if size == "15ml" else "CentrifugeTube50mlBody"
    cap_entry = "CentrifugeTube15mlCap" if size == "15ml" else "CentrifugeTube50mlCap"
    asset = Usd.Stage.CreateNew(str(package / "asset.usd"))
    UsdGeom.SetStageMetersPerUnit(asset, 1.0)
    UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(asset, "/World").GetPrim()
    asset.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(asset, f"/World/{entry_name}")
    body = UsdGeom.Xform.Define(asset, f"{root.GetPath()}/Body")
    body.GetPrim().GetReferences().AddReference(
        "deps/body/asset.usd", f"/World/{body_entry}"
    )
    cap_pose = UsdGeom.Xform.Define(asset, f"{root.GetPath()}/CapPose")
    if cap_z:
        cap_pose.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, cap_z))
    cap = UsdGeom.Xform.Define(asset, f"{cap_pose.GetPath()}/Cap")
    cap.GetPrim().GetReferences().AddReference(
        "deps/cap/asset.usd", f"/World/{cap_entry}"
    )
    asset.GetRootLayer().Save()
    for prim in Usd.PrimRange(root.GetPrim()):
        schemas = [
            name
            for name in prim.GetAppliedSchemas()
            if not name.startswith("Physics") and not name.startswith("Physx")
        ]
        prim.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))
        for attribute_name in (
            "physics:rigidBodyEnabled",
            "physics:kinematicEnabled",
            "physics:collisionEnabled",
        ):
            attribute = prim.GetAttribute(attribute_name)
            if attribute:
                attribute.Block()
    asset.GetRootLayer().Save()
    _write_json(
        package / "evidence/manifest.json",
        {
            "schema_version": "asset_application_normalizer.v1",
            "package_id": f"task11_context_{size}_closed_visual_static_r1_isaac41",
            "asset_id": f"task11_context_{size}_closed",
            "asset_role": "visual_static_context",
            "overall_status": "candidate_pending_runtime",
            "blocked_reasons": ["isaac41_runtime_qualification_not_run"],
            "entrypoints": {
                "root_usd": "asset.usd",
                "default_prim": "World",
                "asset_entry_prim": f"/World/{entry_name}",
                "asset_scope_prims": [f"/World/{entry_name}"],
                "consumer_profile": "scenario-forge",
            },
            "composition": {
                "body_visual": "deps/body/asset.usd",
                "cap_visual": "deps/cap/asset.usd",
                "cap_translation_z_m": cap_z,
            },
            "claims": {
                "visual_static_no_physics": True,
                "isaac41_load_render_step_reset": False,
                "robot_policy_success": False,
            },
        },
    )
    return package


def _build_rack(output: Path, rack_source: Path) -> Path:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    package = output / "mixed_rack_r2/package"
    shutil.copytree(rack_source, package)
    stage = Usd.Stage.Open(str(package / "asset.usd"))
    frame_path = (
        "/TubeRack15ml50ml_OriginalMesh/__frames/"
        f"{TARGET_FRAME}"
    )
    frame = stage.GetPrimAtPath(frame_path)
    point = UsdGeom.XformCache().GetLocalToWorldTransform(frame).ExtractTranslation()
    support = UsdGeom.Cylinder.Define(
        stage,
        "/TubeRack15ml50ml_OriginalMesh/__aan_collision_proxy/"
        "target_slot_bottom_support",
    )
    support.CreateAxisAttr("Z")
    support.CreateRadiusAttr(0.0089)
    support.CreateHeightAttr(0.002)
    support.CreateVisibilityAttr("invisible")
    UsdGeom.Xformable(support).AddTranslateOp().Set(
        Gf.Vec3d(point[0], point[1], point[2] - 0.001)
    )
    UsdPhysics.CollisionAPI.Apply(support.GetPrim())
    stage.GetRootLayer().Save()
    profile_path = package / "interaction/profile.json"
    profile = json.loads(profile_path.read_text())
    profile["revision"] = "r2-target-slot-bottom-support"
    profile["target_slot_support"] = {
        "slot": TARGET_FRAME.removesuffix("_inserted_bottom"),
        "frame": frame_path,
        "collider": str(support.GetPath()),
        "top_z_m": float(point[2]),
        "radius_m": 0.0089,
    }
    _write_json(profile_path, profile)
    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["package_id"] = "mixed_tube_rack_18plus4_task11_r2_isaac41"
    manifest["overall_status"] = "candidate_pending_runtime"
    manifest["blocked_reasons"] = ["isaac41_target_slot_qualification_not_run"]
    manifest["claims"] = {
        "isaac41_static_stability": False,
        "target_slot_bottom_support_authored": True,
        "target_slot_insertion": False,
        "robot_policy_success": False,
    }
    manifest["asset_usd_sha256"] = _sha(package / "asset.usd")
    _write_json(manifest_path, manifest)
    return package


def _build_target_tube(output: Path, source: Path) -> Path:
    package = output / "target_tube_r2/package"
    shutil.copytree(source, package)
    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["package_id"] = "task11_target_15ml_pbd_ready_r2_isaac41"
    manifest["overall_status"] = "candidate_pending_runtime"
    manifest["blocked_reasons"] = ["isaac41_target_slot_qualification_not_run"]
    manifest.setdefault("claims", {}).update(
        {
            "target_slot_insertion": False,
            "robot_policy_success": False,
        }
    )
    _write_json(manifest_path, manifest)
    return package


def build(archive: Path, rack: Path, tube: Path, output: Path) -> dict[str, Path]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    extracted = _extract_packages(archive.resolve(), output / "_source_packages")
    result = {
        "context15": _build_context(output, extracted, size="15ml", cap_z=0.0),
        "context50": _build_context(output, extracted, size="50ml", cap_z=0.1005),
        "rack": _build_rack(output, rack.resolve()),
        "target_tube": _build_target_tube(output, tube.resolve()),
    }
    shutil.rmtree(output / "_source_packages")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--rack", type=Path, required=True)
    parser.add_argument("--tube", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for name, path in build(args.archive, args.rack, args.tube, args.out).items():
        print(name, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
