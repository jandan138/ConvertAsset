#!/usr/bin/env python3
"""Experiment #0: Render paired images (MDL vs noMDL) from 6 camera angles.

Usage (must be run via Isaac Sim python):
    /isaac-sim/python.sh paper/experiments/01_render_pairs/run.py
"""
from __future__ import annotations

import math
import os
import shutil
import sys
import time
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR = PROJECT_ROOT / "assets" / "usd" / "chestofdrawers_nomdl"
OUTPUT_DIR = PROJECT_ROOT / "paper" / "results" / "raw" / "renders"

SCENE_IDS = [
    "chestofdrawers_0004",
    "chestofdrawers_0011",
    "chestofdrawers_0023",
    "chestofdrawers_0029",
]

# Camera angles: (name, azimuth_deg, elevation_deg)
# azimuth=0 => looking from +Z toward -Z (front, Y-up)
CAMERA_ANGLES = [
    ("front",             0,    0),
    ("back",            180,    0),
    ("left",             90,    0),
    ("right",           -90,    0),
    ("top_front_left",   45,   45),
    ("top_front_right", -45,   45),
]

IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 768
WARMUP_FRAMES = 50
SETTLE_FRAMES = 30

LOG_PATH = "/tmp/exp0_render_log.txt"


def _log(msg):
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")


def _camera_eye(center, distance, azimuth_deg, elevation_deg, y_up=True):
    """Compute camera position on an orbit.

    Convention: azimuth=0 => +Z direction (front), Y-up.
    """
    from pxr import Gf
    elev = math.radians(elevation_deg)
    azim = math.radians(azimuth_deg)
    if y_up:
        x = float(center[0]) + distance * math.cos(elev) * math.sin(azim)
        y = float(center[1]) + distance * math.sin(elev)
        z = float(center[2]) + distance * math.cos(elev) * math.cos(azim)
    else:
        x = float(center[0]) + distance * math.cos(elev) * math.sin(azim)
        y = float(center[1]) + distance * math.cos(elev) * math.cos(azim)
        z = float(center[2]) + distance * math.sin(elev)
    return Gf.Vec3d(x, y, z)


def _set_camera_lookat(cam_prim, eye, target, y_up=True):
    """Set camera transform to look at target from eye position."""
    from pxr import Gf, UsdGeom

    fwd = target - eye
    fwd_len = fwd.GetLength()
    if fwd_len < 1e-9:
        return
    fwd = fwd / fwd_len

    world_up = Gf.Vec3d(0, 1, 0) if y_up else Gf.Vec3d(0, 0, 1)
    right = Gf.Cross(fwd, world_up)
    rlen = right.GetLength()
    if rlen < 1e-6:
        alt = Gf.Vec3d(1, 0, 0)
        right = Gf.Cross(fwd, alt)
        rlen = right.GetLength()
    right = right / max(rlen, 1e-9)
    up = Gf.Cross(right, fwd)
    up = up / max(up.GetLength(), 1e-9)

    mat = Gf.Matrix4d(1.0)
    mat.SetRow(0, Gf.Vec4d(right[0], right[1], right[2], 0))
    mat.SetRow(1, Gf.Vec4d(up[0], up[1], up[2], 0))
    mat.SetRow(2, Gf.Vec4d(-fwd[0], -fwd[1], -fwd[2], 0))
    mat.SetRow(3, Gf.Vec4d(eye[0], eye[1], eye[2], 1))

    xf = UsdGeom.Xformable(cam_prim)
    xf.ClearXformOpOrder()
    xf_op = xf.AddTransformOp()
    xf_op.Set(mat)


def main():
    open(LOG_PATH, "w").close()  # clear log
    _log("[Exp#0] Starting render pairs experiment")

    from isaacsim import SimulationApp
    simulation_app = SimulationApp({
        "headless": True,
        "anti_aliasing": 4,
        "multi_gpu": False,
        "renderer": "RayTracedLighting",
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
    })

    import numpy as np
    import omni.usd
    import omni.kit.app
    import omni.replicator.core as rep
    from pxr import Usd, UsdGeom, Sdf, Gf, UsdLux

    app = omni.kit.app.get_app()

    def update(n=10):
        for _ in range(n):
            app.update()

    results = {}
    tmp_dir = "/tmp/exp0_render_tmp"

    for scene_id in SCENE_IDS:
        scene_dir = ASSETS_DIR / scene_id
        out_scene_dir = OUTPUT_DIR / scene_id
        out_scene_dir.mkdir(parents=True, exist_ok=True)

        versions = {
            "A": scene_dir / "instance.usd",
            "B": scene_dir / "instance_noMDL.usd",
        }

        for version_label, usd_path in versions.items():
            if not usd_path.exists():
                _log(f"[WARN] Missing: {usd_path}")
                continue

            _log(f"\n[Exp#0] {scene_id} / {version_label} ({usd_path.name})")

            ctx = omni.usd.get_context()
            ctx.open_stage(str(usd_path))
            update(WARMUP_FRAMES)

            stage = ctx.get_stage()
            if stage is None:
                _log(f"  [ERROR] Stage is None")
                continue

            # Compute scene AABB
            cache = UsdGeom.BBoxCache(
                Usd.TimeCode.Default(),
                [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
                useExtentsHint=True,
            )
            root = stage.GetPseudoRoot()
            rng = cache.ComputeWorldBound(root).ComputeAlignedRange()
            if rng.IsEmpty():
                _log(f"  [WARN] Empty bbox, using defaults")
                center = Gf.Vec3d(0, 0, 0)
                diag = 2.0
            else:
                mn, mx = rng.GetMin(), rng.GetMax()
                center = (mn + mx) * 0.5
                size = mx - mn
                diag = size.GetLength()

            up_axis = UsdGeom.GetStageUpAxis(stage)
            y_up = (up_axis == UsdGeom.Tokens.y)
            distance = max(diag * 1.8, 1.0)
            _log(f"  center={center}, diag={diag:.1f}, up={up_axis}, dist={distance:.1f}")

            # Add lighting if missing
            has_light = any(
                p.GetTypeName() in ("DistantLight", "DomeLight", "SphereLight", "RectLight")
                for p in stage.Traverse()
            )
            if not has_light:
                dome = UsdLux.DomeLight.Define(stage, "/AutoDomeLight")
                dome.GetIntensityAttr().Set(1000.0)
                dlight = UsdLux.DistantLight.Define(stage, "/AutoDistLight")
                dlight.GetIntensityAttr().Set(3000.0)
                dlight.GetAngleAttr().Set(1.0)
                xf = UsdGeom.Xformable(dlight.GetPrim())
                xf.AddRotateXYZOp().Set(Gf.Vec3f(-45, 30, 0))
                _log(f"  Added auto-lights")

            update(10)

            # Create camera
            cam_path = "/RenderCam"
            if stage.GetPrimAtPath(cam_path):
                stage.RemovePrim(cam_path)
            cam_usd = UsdGeom.Camera.Define(stage, cam_path)
            cam_usd.GetFocalLengthAttr().Set(24.0)
            cam_usd.GetHorizontalApertureAttr().Set(20.955)
            cam_usd.GetVerticalApertureAttr().Set(15.2908)
            cam_usd.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 100000.0))

            update(10)

            # Create render product + writer
            rp = rep.create.render_product(cam_path, (IMAGE_WIDTH, IMAGE_HEIGHT))

            for angle_name, azim_deg, elev_deg in CAMERA_ANGLES:
                eye = _camera_eye(center, distance, azim_deg, elev_deg, y_up=y_up)
                target = Gf.Vec3d(float(center[0]), float(center[1]), float(center[2]))
                _set_camera_lookat(cam_usd.GetPrim(), eye, target, y_up=y_up)

                update(SETTLE_FRAMES)

                # Use BasicWriter for each angle: write to temp then move
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir)
                os.makedirs(tmp_dir, exist_ok=True)

                writer = rep.WriterRegistry.get("BasicWriter")
                writer.initialize(output_dir=tmp_dir, rgb=True)
                writer.attach([rp])

                update(5)
                rep.orchestrator.step()
                update(10)

                writer.detach()

                # Move the rendered image
                src_img = os.path.join(tmp_dir, "rgb_0000.png")
                if os.path.exists(src_img):
                    dst_img = out_scene_dir / f"{version_label}_{angle_name}.png"
                    shutil.copy2(src_img, str(dst_img))
                    _log(f"  Saved: {version_label}_{angle_name}.png")
                    results.setdefault(scene_id, []).append(str(dst_img))
                else:
                    _log(f"  [WARN] No image for {angle_name}")
                    # List what is in tmp
                    for fn in os.listdir(tmp_dir):
                        _log(f"    tmp/{fn}")

            rp.destroy()

            # Clean up
            for p in ["/RenderCam", "/AutoDomeLight", "/AutoDistLight"]:
                if stage.GetPrimAtPath(p):
                    stage.RemovePrim(p)
            update(5)

    # Clean up temp
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    total = sum(len(v) for v in results.values())
    _log(f"\n[Exp#0] Done. Rendered {total} images across {len(results)} scenes.")

    simulation_app.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
