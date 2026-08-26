#!/usr/bin/env python3
"""Record live Isaac Sim 4.1 GPU-PBD funnel-to-tube evidence."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


FPS = 30
PHYSICS_DT = 1.0 / 120.0
SUBSTEPS_PER_FRAME = 1
SIMULATED_SECONDS = 3
SLOW_MOTION_FACTOR = 4
PLAYBACK_SECONDS = SIMULATED_SECONDS * SLOW_MOTION_FACTOR
VIDEO_FRAME_COUNT = int(SIMULATED_SECONDS / PHYSICS_DT)
WIDTH = 1920
HEIGHT = 1080
CAMERA = {
    "target": (0.0, 0.0, 0.12),
    "distance": 0.72,
    "elevation": 12.0,
    "azimuth": -75.0,
    "focal_mm": 32.0,
}
VISUAL_MODES = ("evidence_blue", "exact")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def frame_quality(rgb: Any) -> dict[str, Any]:
    """Return compact flat-frame diagnostics for one RGB array."""
    import numpy as np

    array = np.asarray(rgb, dtype=np.float32)
    if array.ndim != 3 or array.shape[2] < 3 or array.size == 0:
        raise ValueError("expected a non-empty HxWx3 RGB frame")
    luma = (
        0.2126 * array[:, :, 0]
        + 0.7152 * array[:, :, 1]
        + 0.0722 * array[:, :, 2]
    )
    luma_std = float(luma.std())
    dynamic_range = float(luma.max() - luma.min())
    return {
        "mean_luma": float(luma.mean()),
        "luma_std": luma_std,
        "dynamic_range": dynamic_range,
        "effectively_flat": luma_std < 2.0 or dynamic_range < 12.0,
    }


def blue_pixel_fraction(rgb: Any) -> float:
    """Fraction of pixels with a deliberately strong evidence-blue signal."""
    import numpy as np

    array = np.asarray(rgb, dtype=np.int16)
    if array.ndim != 3 or array.shape[2] < 3 or array.size == 0:
        raise ValueError("expected a non-empty HxWx3 RGB frame")
    red = array[:, :, 0]
    green = array[:, :, 1]
    blue = array[:, :, 2]
    mask = (blue >= 120) & (blue - red >= 40) & (blue - green >= 25)
    return float(mask.mean())


def _video_label(visual_mode: str) -> str:
    if visual_mode == "exact":
        return "Isaac Sim 4.1 | 4x slow motion | EXACT PACKAGE MATERIAL"
    if visual_mode == "evidence_blue":
        return (
            "Isaac Sim 4.1 | 4x slow motion | HIGH-CONTRAST BLUE - "
            "SESSION ONLY - PHYSICS UNCHANGED"
        )
    raise ValueError(f"unknown visual mode: {visual_mode}")


def encode_mp4(frames_dir: Path, output: Path, *, visual_mode: str) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    video_filter = (
        "scale=in_range=pc:out_range=tv,"
        f"drawtext=fontfile={font}:text='{_video_label(visual_mode)}':"
        "x=40:y=40:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.60,"
        "format=yuv420p"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            "-color_range",
            "tv",
            "-colorspace",
            "bt709",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    return output


def evidence_payload(
    *,
    scene: Path,
    fixture: Path,
    video: Path,
    observation: dict[str, Any],
    visual_quality: dict[str, Any],
    kit_version: str,
    visual_mode: str,
    session_visual_override: dict[str, Any],
) -> dict[str, Any]:
    passed = (
        str(kit_version).startswith("4.1")
        and observation.get("overall_status") == "pass"
        and visual_quality.get("overall_status") == "pass"
    )
    return {
        "schema_version": "aan.funnel_tube15_isaac_video_evidence.v1",
        "overall_status": "pass" if passed else "blocked",
        "engine": "isaac_sim_4.1",
        "kit_version": str(kit_version),
        "method": "live_gpu_pbd_simulation_with_isaac_camera_rgb_capture",
        "scene": str(scene.resolve()),
        "scene_sha256": _sha(scene),
        "fixture": str(fixture.resolve()),
        "fixture_sha256": _sha(fixture),
        "video": str(video.resolve()),
        "video_sha256": _sha(video),
        "fps": FPS,
        "resolution": [WIDTH, HEIGHT],
        "frame_count": VIDEO_FRAME_COUNT,
        "physics_dt_s": PHYSICS_DT,
        "substeps_per_frame": SUBSTEPS_PER_FRAME,
        "simulated_duration_s": SIMULATED_SECONDS,
        "playback_duration_s": PLAYBACK_SECONDS,
        "slow_motion_factor": SLOW_MOTION_FACTOR,
        "camera": CAMERA,
        "visual_mode": visual_mode,
        "session_visual_override": session_visual_override,
        "observation": observation,
        "visual_quality": visual_quality,
        "robot_policy_success": False,
        "benchmark_success": False,
        "claim_boundary": (
            "Isaac Sim 4.1 live GPU-PBD funnel conduit and 15 mL tube capture "
            "evidence only; not robot-policy or benchmark success."
        ),
    }


def _setup_recording_backdrop(stage: Any) -> None:
    """Add session-layer-only neutral geometry; it has no physics APIs."""
    from pxr import Gf, UsdGeom

    wall = UsdGeom.Cube.Define(stage, "/World/__VideoBackdrop")
    wall.CreateSizeAttr(1.0)
    wall.CreateDisplayColorAttr([Gf.Vec3f(0.30, 0.31, 0.32)])
    wall.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.13, 0.13))
    wall.AddScaleOp().Set(Gf.Vec3f(0.24, 0.006, 0.17))
    floor = UsdGeom.Cube.Define(stage, "/World/__VideoFloor")
    floor.CreateSizeAttr(1.0)
    floor.CreateDisplayColorAttr([Gf.Vec3f(0.16, 0.17, 0.18)])
    floor.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.006))
    floor.AddScaleOp().Set(Gf.Vec3f(0.24, 0.18, 0.006))


def _apply_visual_mode(stage: Any, visual_mode: str) -> dict[str, Any]:
    """Author a render-only session override without touching physics."""
    if visual_mode not in VISUAL_MODES:
        raise ValueError(f"unknown visual mode: {visual_mode}")

    from pxr import Gf, Sdf, UsdShade

    system_path = "/__ScenarioForgeLiquid_Funnel/ParticleSystem"
    material_path = "/__ScenarioForgeLiquid_Funnel/LiquidMaterial"
    shader_path = "/__ScenarioForgeLiquid_Funnel/LiquidMaterial/PreviewSurface"
    system_prim = stage.GetPrimAtPath(system_path)
    material_prim = stage.GetPrimAtPath(material_path)
    shader_prim = stage.GetPrimAtPath(shader_path)
    if not system_prim or not system_prim.IsValid():
        raise RuntimeError(f"particle system is missing: {system_path}")
    if not material_prim or not material_prim.IsValid():
        raise RuntimeError(f"liquid material is missing: {material_path}")
    if not shader_prim or not shader_prim.IsValid():
        raise RuntimeError(f"liquid shader is missing: {shader_path}")
    # Isaac 4.1's generated isosurface reads the render material from the
    # ParticleSystem, not from the Points particle set. The source package
    # binds the material to Points, so repeat that existing material binding
    # on the system in this anonymous recording session.
    material = UsdShade.Material(material_prim)
    UsdShade.MaterialBindingAPI.Apply(system_prim).Bind(material)
    common = {
        "applied": True,
        "physics_unchanged": True,
        "particle_system_material_binding": {
            "prim": system_path,
            "material": material_path,
        },
        "persistence": "anonymous_session_layer_only",
    }
    if visual_mode == "exact":
        return {
            **common,
            "description": "package-authored material bound to generated isosurface",
            "shader_parameters_changed": False,
        }

    shader = UsdShade.Shader(shader_prim)
    values = {
        "diffuseColor": Gf.Vec3f(0.02, 0.20, 0.95),
        "emissiveColor": Gf.Vec3f(0.0, 0.035, 0.18),
        "opacity": 0.92,
        "roughness": 0.12,
    }
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        values["diffuseColor"]
    )
    shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(
        values["emissiveColor"]
    )
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(values["opacity"])
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(
        values["roughness"]
    )
    return {
        **common,
        "scope": shader_path,
        "diffuse_color": list(values["diffuseColor"]),
        "emissive_color": list(values["emissiveColor"]),
        "opacity": values["opacity"],
        "roughness": values["roughness"],
        "shader_parameters_changed": True,
    }


def _capture_rgb(camera: Any, destination: Path) -> Any:
    from convert_asset.render.single import _camera_rgba, _rgba_to_rgb, _save_rgb_png

    rgba = _camera_rgba(camera)
    if rgba is None:
        raise RuntimeError("camera returned no RGBA frame after rendered physics step")
    rgb = _rgba_to_rgb(rgba, background_color=(26, 30, 38))
    if rgb is None or not _save_rgb_png(destination, rgb):
        raise RuntimeError(f"could not save frame: {destination}")
    return rgb


def _mean_abs_diff(first: Any, second: Any) -> float:
    import numpy as np

    a = np.asarray(first, dtype=np.float32)
    b = np.asarray(second, dtype=np.float32)
    if a.shape != b.shape:
        raise ValueError("checkpoint frames must have identical shapes")
    return float(np.mean(np.abs(a - b)))


def decode_video_quality(video: Path, *, visual_mode: str) -> dict[str, Any]:
    """Decode the deliverable MP4 and judge sampled frames, not source PNGs."""
    import cv2

    sample_indices = (0, 15, 30, 60, 120, VIDEO_FRAME_COUNT - 1)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"could not decode final MP4: {video}")
    decoded: dict[int, Any] = {}
    try:
        for index in sample_indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, bgr = capture.read()
            if not ok or bgr is None:
                raise RuntimeError(f"could not decode MP4 frame {index}: {video}")
            decoded[index] = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    finally:
        capture.release()

    qualities = {str(index): frame_quality(rgb) for index, rgb in decoded.items()}
    first = decoded[0]
    motion = {
        str(index): _mean_abs_diff(first, rgb)
        for index, rgb in decoded.items()
        if index != 0
    }
    blue = {
        str(index): blue_pixel_fraction(rgb) for index, rgb in decoded.items()
    }
    flat = any(item["effectively_flat"] for item in qualities.values())
    maximum_motion = max(motion.values())
    maximum_blue = max(blue.values())
    blue_ok = visual_mode != "evidence_blue" or maximum_blue >= 0.0005
    return {
        "source": "decoded_final_mp4",
        "sample_indices": list(sample_indices),
        "frame_quality": qualities,
        "mean_abs_rgb_diff_from_first": motion,
        "blue_pixel_fraction": blue,
        "maximum_blue_pixel_fraction": maximum_blue,
        "overall_status": "pass"
        if not flat and maximum_motion >= 0.25 and blue_ok
        else "blocked",
    }


def _observe_and_record(
    *, scene: Path, fixture_path: Path, frames_dir: Path, visual_mode: str
) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    from isaacsim import SimulationApp

    saved_argv = sys.argv
    sys.argv = [sys.argv[0]]
    app = SimulationApp(
        {"headless": True, "renderer": "RayTracedLighting", "multi_gpu": False}
    )
    sys.argv = saved_argv
    try:
        print("[INFO] phase=runtime_ready", flush=True)
        import carb
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.physx.bindings._physx as pb
        import omni.usd
        from omni.isaac.core import World

        from convert_asset.render.single import (
            _camera_rgba,
            _init_camera,
            _set_camera_look_at,
            _setup_environment,
        )

        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        print("[INFO] phase=fixture_loaded", flush=True)
        settings = carb.settings.get_settings()
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.exists() else 0
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)

        context = omni.usd.get_context()
        print(f"[INFO] phase=open_stage scene={scene}", flush=True)
        if not context.open_stage(str(scene.resolve())):
            raise RuntimeError(f"could not open integration scene: {scene}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        print("[INFO] phase=stage_loaded", flush=True)
        stage.SetEditTarget(stage.GetSessionLayer())
        _setup_environment(stage)
        _setup_recording_backdrop(stage)
        session_visual_override = _apply_visual_mode(stage, visual_mode)

        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path=fixture["physics_scene_path"],
            set_defaults=False,
            backend="numpy",
            device="cpu",
            physics_dt=PHYSICS_DT,
            rendering_dt=PHYSICS_DT,
        )
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        world.reset()
        camera = _init_camera(
            "FunnelTube15EvidenceCamera", WIDTH, HEIGHT, CAMERA["focal_mm"]
        )
        _set_camera_look_at(
            camera,
            np.asarray(CAMERA["target"], dtype=float),
            distance=CAMERA["distance"],
            elevation=CAMERA["elevation"],
            azimuth=CAMERA["azimuth"],
        )
        camera.set_focal_length(CAMERA["focal_mm"])
        camera_warmup_steps = 0
        for camera_warmup_steps in range(1, 9):
            world.step(render=True)
            if _camera_rgba(camera) is not None:
                break
        else:
            raise RuntimeError("camera returned no frame after eight rendered warmup steps")
        print(
            f"[INFO] phase=camera_ready warmup_steps={camera_warmup_steps}",
            flush=True,
        )
        print("[INFO] phase=physics_ready", flush=True)
        particle = stage.GetPrimAtPath(fixture["particle_set_prim"])
        previous = particle.GetAttribute("points").Get()
        initial = int(fixture["particle_count"])
        legal: set[int] = set()
        leaks: set[int] = set()
        recipe = fixture["liquid_recipe"]["payload"]
        outlet_z = float(fixture["funnel_outlet_z_m"])
        tolerance = (
            float(fixture["funnel_outer_outlet_radius_m"])
            + 0.5 * float(recipe["particle_set"]["width_m"])
            + float(recipe["particle_system"]["max_velocity_m_s"]) / 120.0
        )

        frames_dir.mkdir(parents=True, exist_ok=True)
        checkpoints: dict[int, Any] = {}
        checkpoint_indices = {0, 15, 30, 60, 120, VIDEO_FRAME_COUNT - 1}
        checkpoint_quality: dict[str, Any] = {}
        for frame_index in range(VIDEO_FRAME_COUNT):
            for substep in range(SUBSTEPS_PER_FRAME):
                world.step(render=substep == SUBSTEPS_PER_FRAME - 1)
                live = particle.GetAttribute("points").Get()
                for index, point in enumerate(live):
                    before = previous[index]
                    if before[2] > outlet_z >= point[2]:
                        alpha = (before[2] - outlet_z) / max(
                            before[2] - point[2], 1e-9
                        )
                        radius = math.hypot(
                            before[0] + alpha * (point[0] - before[0]),
                            before[1] + alpha * (point[1] - before[1]),
                        )
                        (legal if radius <= tolerance else leaks).add(index)
                previous = live
            rgb = _capture_rgb(
                camera, frames_dir / f"frame_{frame_index:04d}.png"
            )
            if frame_index in checkpoint_indices:
                checkpoints[frame_index] = np.asarray(rgb).copy()
                checkpoint_quality[str(frame_index)] = frame_quality(rgb)
            if frame_index % 30 == 0:
                print(
                    f"[INFO] frame={frame_index}/{VIDEO_FRAME_COUNT} "
                    f"legal_crossings={len(legal)} structural_leaks={len(leaks)}",
                    flush=True,
                )

        tube = fixture["tube"]
        profile = tube["retention_profile"]
        contact = float(recipe["particle_system"]["particle_contact_offset_m"])

        def tube_radius(z_value: float) -> float:
            if z_value <= float(profile[0]["z_m"]):
                return float(profile[0]["inner_radius_m"])
            for lower, upper in zip(profile, profile[1:]):
                if z_value <= float(upper["z_m"]):
                    alpha = (z_value - float(lower["z_m"])) / max(
                        float(upper["z_m"]) - float(lower["z_m"]), 1e-9
                    )
                    return (1.0 - alpha) * float(
                        lower["inner_radius_m"]
                    ) + alpha * float(upper["inner_radius_m"])
            return float(profile[-1]["inner_radius_m"])

        captured = sum(
            math.hypot(point[0], point[1])
            <= tube_radius(float(point[2])) + contact
            and float(tube["floor_z_m"]) - contact
            <= point[2]
            <= float(tube["rim_z_m"]) + contact
            for point in previous
        )
        below_floor = sum(
            point[2] < float(tube["floor_z_m"]) - 0.001 for point in previous
        )
        log = (
            log_path.read_text(errors="replace")[log_offset:]
            if log_path.exists()
            else ""
        )
        markers = (
            "CUDA error",
            "illegal memory access",
            "Particles feature is only supported on GPU",
        )
        hard = [
            line for line in log.splitlines() if any(marker in line for marker in markers)
        ]
        observation = {
            "particle_count": initial,
            "legal_outlet_ratio": len(legal) / initial,
            "tube_capture_ratio": captured / initial,
            "structural_leak_count": len(leaks),
            "below_tube_floor_count": below_floor,
            "hard_errors": hard,
            "liquid_recipe": {
                key: fixture["liquid_recipe"][key] for key in ("id", "sha256")
            },
        }
        acceptance = fixture["acceptance"]
        observation["overall_status"] = "pass" if (
            observation["legal_outlet_ratio"]
            >= acceptance["minimum_legal_outlet_ratio"]
            and observation["tube_capture_ratio"]
            >= acceptance["minimum_tube_capture_ratio"]
            and observation["structural_leak_count"]
            <= acceptance["maximum_structural_leak_count"]
            and not hard
        ) else "blocked"

        first = checkpoints[0]
        differences = {
            str(index): _mean_abs_diff(first, frame)
            for index, frame in checkpoints.items()
            if index != 0
        }
        flat = any(
            item["effectively_flat"] for item in checkpoint_quality.values()
        )
        visual_quality = {
            "source": "isaac_camera_source_pngs",
            "checkpoint_frames": checkpoint_quality,
            "mean_abs_rgb_diff_from_first": differences,
            "overall_status": "pass"
            if not flat and max(differences.values()) >= 0.25
            else "blocked",
        }
        kit_version = str(omni.kit.app.get_app().get_app_version())
        return observation, visual_quality, kit_version, session_visual_override
    except BaseException:
        print("[FAIL] live Isaac recording aborted", flush=True)
        traceback.print_exc()
        raise
    finally:
        # Isaac Sim 4.1's fast shutdown can terminate this interpreter from
        # ``close()`` before ffmpeg and the evidence JSON run.  Keep Kit alive
        # until main has persisted both, then use the repository's controlled
        # process-exit pattern below.
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--visual-mode",
        choices=VISUAL_MODES,
        default="evidence_blue",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Retain intermediate PNGs after MP4 encoding (default: discard).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    scene = args.scene.resolve()
    fixture = args.fixture.resolve()
    out_dir = args.out_dir.resolve()
    suffix = "" if args.visual_mode == "evidence_blue" else "_exact_material"
    frames_dir = out_dir / f"frames{suffix}"
    video = out_dir / f"funnel_to_tube_isaac41{suffix}.mp4"
    evidence = out_dir / f"funnel_to_tube_isaac41{suffix}.json"
    observation, source_visual_quality, kit_version, session_visual_override = (
        _observe_and_record(
            scene=scene,
            fixture_path=fixture,
            frames_dir=frames_dir,
            visual_mode=args.visual_mode,
        )
    )
    encode_mp4(frames_dir, video, visual_mode=args.visual_mode)
    decoded_visual_quality = decode_video_quality(
        video, visual_mode=args.visual_mode
    )
    decoded_visual_quality["source_frame_quality"] = source_visual_quality
    if not args.keep_frames:
        shutil.rmtree(frames_dir)
    payload = evidence_payload(
        scene=scene,
        fixture=fixture,
        video=video,
        observation=observation,
        visual_quality=decoded_visual_quality,
        kit_version=kit_version,
        visual_mode=args.visual_mode,
        session_visual_override=session_visual_override,
    )
    evidence.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"video": str(video), "evidence": str(evidence), **payload},
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0 if payload["overall_status"] == "pass" else 2


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    import os

    os._exit(code)
