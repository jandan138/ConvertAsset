#!/usr/bin/env python3
"""Render closed/open visual-versus-collider overlays for LABSPIN X8 r6."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys


ROOT = "/World/Centrifuge"
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    original = sys.argv
    sys.argv = [sys.argv[0]]
    from isaacsim import SimulationApp

    app = SimulationApp(
        {"headless": True, "renderer": "RayTracedLighting", "multi_gpu": False}
    )
    sys.argv = original
    try:
        import numpy as np
        import omni.timeline
        import omni.usd
        from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdPhysics, UsdShade

        from convert_asset.render.single import (
            _camera_rgba,
            _init_camera,
            _rgba_to_rgb,
            _save_rgb_png,
            _set_camera_look_at,
        )

        context = omni.usd.get_context()
        if not context.open_stage(str(args.asset.resolve())):
            raise RuntimeError(f"cannot open asset: {args.asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        stage = context.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        material = UsdShade.Material.Define(stage, "/World/__Evidence/ColliderGreen")
        shader = UsdShade.Shader.Define(stage, "/World/__Evidence/ColliderGreen/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0.02, 0.82, 0.18)
        )
        shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0.0, 0.12, 0.02)
        )
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.42)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.25)
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        proxy_paths = []
        for prim in stage.Traverse():
            path = str(prim.GetPath())
            if "/__aan_collision_proxy/" not in path or not prim.IsA(UsdGeom.Gprim):
                continue
            imageable = UsdGeom.Imageable(prim)
            imageable.MakeVisible()
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
            proxy_paths.append(path)
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                UsdPhysics.RigidBodyAPI(prim).CreateRigidBodyEnabledAttr().Set(False)
            if prim.IsA(UsdPhysics.Joint):
                prim.SetActive(False)
        dome = UsdLux.DomeLight.Define(stage, "/World/__Evidence/Dome")
        dome.CreateIntensityAttr(900.0)
        distant = UsdLux.DistantLight.Define(stage, "/World/__Evidence/Key")
        distant.CreateIntensityAttr(1600.0)
        distant.AddRotateXYZOp().Set(Gf.Vec3f(42.0, -25.0, -35.0))
        camera = _init_camera("LabspinCollisionOverlay", 1280, 720, 42.0)
        _set_camera_look_at(
            camera,
            np.asarray([0.0, -0.02, 0.30]),
            distance=1.55,
            elevation=24.0,
            azimuth=-135.0,
        )
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for _ in range(40):
            app.update()

        out = args.out_dir.resolve()
        out.mkdir(parents=True, exist_ok=True)
        lid = stage.GetPrimAtPath(f"{ROOT}/lid_link")
        orient = lid.GetAttribute("xformOp:orient")
        images = []
        for name, angle in (("closed", 0.0), ("open", -1.361356817)):
            orient.Set(
                Gf.Quatf(
                    math.cos(angle * 0.5),
                    Gf.Vec3f(math.sin(angle * 0.5), 0.0, 0.0),
                )
            )
            for _ in range(20):
                app.update()
            rgba = _camera_rgba(camera)
            if rgba is None:
                raise RuntimeError("camera returned no frame")
            rgb = _rgba_to_rgb(rgba, background_color=(28, 31, 38))
            path = out / f"{name}_overlay.png"
            if rgb is None or not _save_rgb_png(path, rgb):
                raise RuntimeError(f"could not save {path}")
            images.append(
                {"state": name, "path": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}
            )
        report = {
            "schema_version": "aan.labspin_x8_r6_collision_overlay.v1",
            "runtime": "isaac41",
            "asset_usd_sha256": sha256(args.asset.read_bytes()).hexdigest(),
            "collider_prim_count": len(proxy_paths),
            "images": images,
            "visual_review": "pending",
        }
        (out / "render_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(report, indent=2, sort_keys=True), flush=True)
        timeline.stop()
        return 0
    except BaseException:
        import traceback

        traceback.print_exc()
        return 2
    finally:
        pass


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
