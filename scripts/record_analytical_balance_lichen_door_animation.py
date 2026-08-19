#!/usr/bin/env python3
"""Write and optionally record the LICHEN balance door open/close animation.

The admitted package stays free of timeSamples.  This sidecar USDA references
that package and authors sequential prismatic-joint samples so Isaac can Play
the four-door cycle.  An optional Isaac session captures viewport frames.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


ANIMATION_OPEN_M = 0.105
FPS = 24
HOLD_FRAMES = 12
TRAVEL_FRAMES = 24
DOORS = (
    ("Front_Sliding_Glass_Door", "X"),
    ("Left_Sliding_Glass_Door", "Y"),
    ("Right_Sliding_Glass_Door", "Y"),
    ("Top_Sliding_Glass", "Y"),
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _samples_block(values: dict[int, float]) -> str:
    lines = ["            float state:linear:physics:position.timeSamples = {"]
    for time_code, value in sorted(values.items()):
        lines.append(f"                {time_code}: {value},")
    lines.append("            }")
    return "\n".join(lines)


def _door_curve(start: int) -> dict[int, float]:
    open_at = start + HOLD_FRAMES
    hold_open = open_at + HOLD_FRAMES
    closed_at = hold_open + TRAVEL_FRAMES
    return {
        start: 0.0,
        open_at: ANIMATION_OPEN_M,
        hold_open: ANIMATION_OPEN_M,
        closed_at: 0.0,
    }


def write_door_animation_timeline(*, package_asset: Path, out_usda: Path) -> Path:
    package_asset = package_asset.resolve()
    out_usda = out_usda.resolve()
    if not package_asset.is_file():
        raise FileNotFoundError(f"package asset USD is required: {package_asset}")
    relative_asset = Path(os_path_relative(out_usda.parent, package_asset))
    cursor = HOLD_FRAMES
    curves: list[tuple[str, dict[int, float]]] = []
    for prim_name, _axis in DOORS:
        curve = _door_curve(cursor)
        curves.append((prim_name, curve))
        cursor = max(curve) + HOLD_FRAMES
    end_time = cursor
    door_overlays = []
    for prim_name, curve in curves:
        door_overlays.append(
            f'''        over Xform "{prim_name}"
        {{
            over PhysicsPrismaticJoint "PrismaticJoint"
            {{
{_samples_block(curve)}
            }}
        }}'''
        )
    text = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    startTimeCode = 0
    endTimeCode = {end_time}
    timeCodesPerSecond = {FPS}
    framesPerSecond = {FPS}
    subLayers = [
        @{relative_asset.as_posix()}@
    ]
)

over Xform "World"
{{
    over Xform "AnalyticalBalanceLichen"
    {{
        over Xform "Source"
        {{
{chr(10).join(door_overlays)}
        }}
    }}
}}
'''
    out_usda.parent.mkdir(parents=True, exist_ok=True)
    out_usda.write_text(text.rstrip() + "\n", encoding="utf-8")
    return out_usda


def os_path_relative(origin: Path, target: Path) -> str:
    try:
        return str(target.relative_to(origin))
    except ValueError:
        return os_relpath(target, origin)


def os_relpath(target: Path, origin: Path) -> str:
    import os

    return os.path.relpath(str(target), str(origin))


def _write_mp4(frames_dir: Path, out_mp4: Path) -> Path | None:
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        return None
    try:
        import imageio.v2 as imageio
    except Exception:
        try:
            import imageio
        except Exception:
            return None
    writer = imageio.get_writer(str(out_mp4), fps=FPS)
    try:
        for frame in frames:
            writer.append_data(imageio.imread(frame))
    finally:
        writer.close()
    return out_mp4


def _record_isaac_frames(
    *,
    timeline: Path,
    frames_dir: Path,
    end_time: int,
) -> dict[str, Any]:
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    saved = 0
    try:
        import omni.usd
        from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport
        from pxr import Usd, UsdGeom

        context = omni.usd.get_context()
        if not context.open_stage(str(timeline)):
            raise RuntimeError(f"could not open timeline: {timeline}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Isaac did not provide an open timeline stage")
        camera = UsdGeom.Camera.Define(stage, "/World/DoorReviewCamera")
        xform = UsdGeom.Xformable(camera.GetPrim())
        xform.AddTranslateOp().Set((0.42, -0.48, 0.32))
        xform.AddRotateXYZOp().Set((65.0, 0.0, 40.0))
        viewport = get_active_viewport()
        if viewport is not None:
            try:
                viewport.set_active_camera("/World/DoorReviewCamera")
            except Exception:
                pass
        frames_dir.mkdir(parents=True, exist_ok=True)
        import omni.timeline

        clock = omni.timeline.get_timeline_interface()
        for time_code in range(0, end_time + 1):
            if clock is not None:
                clock.set_current_time(float(time_code) / float(FPS))
            app.update()
            frame_path = frames_dir / f"frame_{time_code:04d}.png"
            if viewport is not None:
                capture_viewport_to_file(viewport, str(frame_path))
                saved += 1
        blocked_reason = None if saved else "no_active_viewport"
        return {
            "frames_saved": saved,
            "end_time": end_time,
            "blocked_reason": blocked_reason,
        }
    finally:
        # Isaac 4.1 may hang in SimulationApp.close() in this headless host.
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-asset", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--record-isaac", action="store_true")
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    timeline = write_door_animation_timeline(
        package_asset=args.package_asset,
        out_usda=out_dir / "demo_timeline.usda",
    )
    payload: dict[str, Any] = {
        "timeline": str(timeline),
        "timeline_sha256": _sha(timeline),
        "open_m": ANIMATION_OPEN_M,
        "recorded": False,
    }
    if args.record_isaac:
        text = timeline.read_text(encoding="utf-8")
        end_time = 0
        for line in text.splitlines():
            if "endTimeCode" in line:
                end_time = int(line.split("=")[1].strip())
                break
        evidence = _record_isaac_frames(
            timeline=timeline,
            frames_dir=out_dir / "frames",
            end_time=end_time,
        )
        mp4 = _write_mp4(out_dir / "frames", out_dir / "doors_open_close.mp4")
        payload["recorded"] = True
        payload["frames"] = evidence
        payload["mp4"] = str(mp4) if mp4 else None
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
