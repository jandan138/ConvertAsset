#!/usr/bin/env python3
"""Record the scripted-kinematic HCI closed-15 mL insert-and-lid-close demo.

This producer-owned Isaac 4.1 session drives the r9 centrifuge lid joint and
one or two closed-tube kinematic probes through the qualified socket paths
while capturing sensor-camera frames, then encodes an mp4 with system ffmpeg.
The default cut uses the balanced socket pair (tube_socket_1 + tube_socket_2):
two identical closed tubes seated in opposite arm-plate holes at equal radii
about the measured rotor spin center. The admitted packages stay free of
timeSamples; the motion is keyframed here and no robot policy is involved.
The k=0.365 glass test-tube hash is rejected.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from scripts.build_hci_15ml_closed_insert_lid_assets import (
    ENTRY_PRIM,
    assert_not_forbidden_k0365_tube_hash,
)
from scripts.qualify_centrifuge_task_interactions import (
    CENTRIFUGE_ROOT,
    EXPECTED_DOF_MAPPING,
    LID_OPEN_BAND,
    TUBE_PROBE_ROOT,
    _load_device_profile,
    _prepare_tube,
    _profile_frame_world_pose,
    _reset_and_sync,
)


FPS = 24
PHYSICS_DT = 1.0 / 240.0
SUBSTEPS_PER_FRAME = 10
LID_CLOSED_RAD = 0.0
LID_OPEN_RAD = LID_OPEN_BAND[0]
TUBE_HOVER_ABOVE_APERTURE_M = 0.09
TUBE_PARK_LATERAL_M = 0.10
# The tube is held kinematically 5 mm above the cup rim, then released into a
# free physical drop. The r10 centrifuge package carries the cup floor pads
# and wall panels as rotor colliders, so the landing contact is package-true
# physics — no session-layer helpers.
TUBE_HOLD_ABOVE_RIM_M = 0.005
RIM_TOP_Z_M = 0.145
PARKED_TUBE_PROBE_ROOT = "/World/__aan_task_contact_probe/TestTubeB"
DEFAULT_SOCKET_NAMES = ("tube_socket_1", "tube_socket_2")
SPIN_CENTER_WORLD_M = (-0.0404004111, -0.0482212505)

# Whole-device narrative view and the fixed steep view; both cover the two
# balanced sockets (87 mm apart across the basket).
CAMERA_MAIN = {
    "target": (-0.04, -0.048, 0.15),
    "distance": 0.55,
    "elevation": 33.0,
    "azimuth": 50.0,
    "focal_mm": 20.0,
}
CAMERA_REVEAL = {
    "target": (SPIN_CENTER_WORLD_M[0], SPIN_CENTER_WORLD_M[1], 0.16),
    "distance": 0.32,
    "elevation": 60.0,
    "azimuth": 50.0,
    "focal_mm": 28.0,
}
CAMERA_TOPDOWN = {
    "target": (SPIN_CENTER_WORLD_M[0], SPIN_CENTER_WORLD_M[1], 0.185),
    "distance": 0.45,
    "elevation": 63.0,
    "azimuth": 50.0,
    "focal_mm": 22.0,
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _smoothstep(ratio: float) -> float:
    t = min(1.0, max(0.0, ratio))
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp3(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t), _lerp(a[2], b[2], t))


def _lerp_camera(a: dict[str, Any], b: dict[str, Any], t: float) -> dict[str, Any]:
    return {
        "target": _lerp3(a["target"], b["target"], t),
        "distance": _lerp(a["distance"], b["distance"], t),
        "elevation": _lerp(a["elevation"], b["elevation"], t),
        "azimuth": _lerp(a["azimuth"], b["azimuth"], t),
        "focal_mm": _lerp(a["focal_mm"], b["focal_mm"], t),
    }


def demo_phases(socket_count: int) -> list[tuple[str, int]]:
    """Phase list honouring lid_open -> tube insert(s) -> lid_close order.

    Each tube is positioned kinematically above its cup and then released
    into a free physical drop onto the session seat disc.
    """
    phases: list[tuple[str, int]] = [
        ("closed_hold", 12),
        ("lid_open", 30),
        ("open_hold", 8),
    ]
    for index in range(socket_count):
        phases.append((f"tube_{index}_position", 16))
        phases.append((f"tube_{index}_release", 30))
    phases.extend(
        [
            ("inserted_hold", 8),
            ("socket_reveal", 24),
            ("reveal_hold", 20),
            ("reveal_return", 24),
            ("lid_close", 48),
            ("final_hold", 24),
        ]
    )
    return phases


def demo_frame_count(socket_count: int = len(DEFAULT_SOCKET_NAMES)) -> int:
    return sum(frames for _, frames in demo_phases(socket_count))


def apply_fixed_camera(
    keyframes: list[dict[str, Any]], spec: dict[str, Any]
) -> list[dict[str, Any]]:
    """Pin every keyframe to one camera spec (the top-down cut)."""
    fixed = {
        "target": list(spec["target"]),
        "distance": spec["distance"],
        "elevation": spec["elevation"],
        "azimuth": spec["azimuth"],
        "focal_mm": spec["focal_mm"],
    }
    return [{**keyframe, "camera": dict(fixed)} for keyframe in keyframes]


def build_demo_keyframes(
    *,
    sockets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One keyframe per output frame: lid joint rad and per-tube intent.

    Each socket dict carries ``aperture``, ``axis`` and ``depth`` triples plus
    an optional ``park_offset``. A tube entry is a world position while the
    tube is kinematic, and ``None`` once the tube is released into its free
    physical drop; ``None`` entries are never teleported again.
    """
    tube_paths: list[dict[str, tuple[float, float, float] | None]] = []
    for index, socket in enumerate(sockets):
        aperture = socket["aperture"]
        axis = socket["axis"]
        hold = (
            aperture[0],
            aperture[1],
            RIM_TOP_Z_M + TUBE_HOLD_ABOVE_RIM_M,
        )
        offset = socket.get("park_offset") or (
            TUBE_PARK_LATERAL_M if index % 2 == 0 else -TUBE_PARK_LATERAL_M,
            0.0,
            0.0,
        )
        hover = tuple(aperture[i] + axis[i] * TUBE_HOVER_ABOVE_APERTURE_M for i in range(3))
        parked = (hover[0] + offset[0], hover[1] + offset[1], hover[2] + offset[2])
        tube_paths.append({"parked": parked, "hold": hold})
    keyframes: list[dict[str, Any]] = []
    for phase, frames in demo_phases(len(sockets)):
        for index in range(frames):
            t = _smoothstep(index / (frames - 1)) if frames > 1 else 1.0
            camera = CAMERA_MAIN
            positions: list[tuple[float, float, float] | None] = []
            if phase in {"closed_hold", "lid_open", "open_hold"}:
                positions = [path["parked"] for path in tube_paths]
            elif phase.startswith("tube_"):
                parts = phase.split("_")
                active = int(parts[1])
                action = parts[2]
                for tube_index, path in enumerate(tube_paths):
                    if tube_index < active:
                        positions.append(None)  # already released and seated
                    elif tube_index > active:
                        positions.append(path["parked"])
                    elif action == "position":
                        positions.append(_lerp3(path["parked"], path["hold"], t))
                    else:  # release: free physical drop
                        positions.append(None)
            else:
                positions = [None for _ in tube_paths]
                if phase == "socket_reveal":
                    camera = _lerp_camera(CAMERA_MAIN, CAMERA_REVEAL, t)
                elif phase == "reveal_hold":
                    camera = CAMERA_REVEAL
                elif phase == "reveal_return":
                    camera = _lerp_camera(CAMERA_REVEAL, CAMERA_MAIN, t)
            if phase == "closed_hold":
                lid = LID_CLOSED_RAD
            elif phase == "lid_open":
                lid = _lerp(LID_CLOSED_RAD, LID_OPEN_RAD, t)
            elif phase in {
                "open_hold",
                "inserted_hold",
                "socket_reveal",
                "reveal_hold",
                "reveal_return",
            } or phase.startswith("tube_"):
                lid = LID_OPEN_RAD
            elif phase == "lid_close":
                lid = _lerp(LID_OPEN_RAD, LID_CLOSED_RAD, t)
            else:
                lid = LID_CLOSED_RAD
            keyframes.append(
                {
                    "phase": phase,
                    "lid_rad": lid,
                    "tube_positions_m": [
                        list(position) if position is not None else None
                        for position in positions
                    ],
                    "camera": {
                        "target": list(camera["target"]),
                        "distance": camera["distance"],
                        "elevation": camera["elevation"],
                        "azimuth": camera["azimuth"],
                        "focal_mm": camera["focal_mm"],
                    },
                }
            )
    return keyframes


def encode_mp4(frames_dir: Path, out_mp4: Path, *, fps: int = FPS) -> Path | None:
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        return None
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(out_mp4),
        ],
        check=True,
        capture_output=True,
    )
    return out_mp4


def evidence_payload(
    *,
    centrifuge_package: Path,
    tube_package: Path,
    device_profile: Path,
    qualification_reports: list[Path],
    mp4: Path | None,
    frames_dir: Path,
    keyframes: list[dict[str, Any]],
    camera_mode: str = "orbit_beats",
    socket_names: tuple[str, ...] = DEFAULT_SOCKET_NAMES,
    seated_measurements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    frames = sorted(frames_dir.glob("frame_*.png"))
    return {
        "schema_version": "aan.hci_15ml_closed_insert_lid_demo.v1",
        "request_id": "scientific_workbench_hci_15ml_closed_insert_lid_20260818",
        "engine": "isaac_sim_4.1",
        "method": (
            "scripted_kinematic_positioning_then_physical_free_drop"
        ),
        "robot_policy_forbidden": True,
        "sequence": ["lid_open", "tube_insert", "lid_close"],
        "camera_mode": camera_mode,
        "socket_names": list(socket_names),
        "balanced_pair": len(socket_names) == 2,
        "tube_dynamics": (
            "rigid_body_free_drop_from_cup_rim_hold; kinematic during "
            "positioning beats, released 5 mm above each cup rim"
        ),
        "cup_colliders": (
            "Package-level: the r10 centrifuge facade authors cup floor pads "
            "and wall panels as rotor colliders, so the landing contact is "
            "package-true physics with no session-layer helpers."
        ),
        "seated_measurements": seated_measurements or [],
        "phases": [
            {"phase": name, "frames": count}
            for name, count in demo_phases(len(socket_names))
        ],
        "fps": FPS,
        "physics_dt": PHYSICS_DT,
        "substeps_per_frame": SUBSTEPS_PER_FRAME,
        "frame_count": len(frames),
        "keyframe_count": len(keyframes),
        "centrifuge_asset_usd_sha256": _sha(centrifuge_package / "asset.usd"),
        "tube_asset_usd_sha256": _sha(tube_package / "asset.usd"),
        "device_profile_sha256": _sha(device_profile),
        "qualification_report_sha256": [
            _sha(report) for report in qualification_reports
        ],
        "mp4": str(mp4) if mp4 else None,
        "mp4_sha256": _sha(mp4) if mp4 else None,
        "tube_entry_prim": ENTRY_PRIM,
        "claim_boundary": (
            "Scripted-kinematic HCI balanced-pair insert-and-lid-close "
            "demonstration only. Not Feishu Task 10/11, not robot policy, not "
            "real 15 mL parity, and not cap-tightening on this scaled tube."
        ),
    }


def _record_isaac(
    *,
    centrifuge_package: Path,
    centrifuge_manifest: Path,
    tube_package: Path,
    device_profile: Path,
    frames_dir: Path,
    socket_names: tuple[str, ...] = DEFAULT_SOCKET_NAMES,
    fixed_camera: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = json.loads(centrifuge_manifest.read_text(encoding="utf-8"))
    source = manifest.get("source")
    entrypoints = manifest.get("entrypoints")
    if (
        not isinstance(source, dict)
        or not isinstance(source.get("sha256"), str)
        or not isinstance(entrypoints, dict)
        or entrypoints.get("asset_entry_prim") != CENTRIFUGE_ROOT
    ):
        raise ValueError("centrifuge manifest does not describe the expected articulation root")
    profile = _load_device_profile(
        device_profile,
        source_sha256=source["sha256"],
        articulation_root_prim=CENTRIFUGE_ROOT,
        socket_names=socket_names,
    )
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    saved = 0
    try:
        import numpy as np
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.prims import RigidPrimView
        from pxr import Gf, Usd, UsdGeom, UsdPhysics

        from convert_asset.render.single import (
            _camera_rgba,
            _init_camera,
            _rgba_to_rgb,
            _save_rgb_png,
            _set_camera_look_at,
            _setup_environment,
        )

        centrifuge_asset = centrifuge_package / "asset.usd"
        tube_asset = tube_package / "asset.usd"
        for path in (centrifuge_asset, tube_asset):
            if not path.is_file():
                raise FileNotFoundError(path)
        context = omni.usd.get_context()
        if not context.open_stage(str(centrifuge_asset)):
            raise RuntimeError(f"could not open centrifuge package: {centrifuge_asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(60):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Isaac did not provide an open USD stage")
        stage.SetEditTarget(stage.GetSessionLayer())
        _setup_environment(stage)
        probe_paths = [TUBE_PROBE_ROOT, PARKED_TUBE_PROBE_ROOT][: len(socket_names)]
        kinematic_attrs = []
        for probe_path in probe_paths:
            _prepare_tube(
                stage, tube_asset, UsdPhysics, entry_prim=ENTRY_PRIM, probe_path=probe_path
            )
            prim = stage.GetPrimAtPath(probe_path)
            kinematic_attrs.append(
                UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr()
            )

        world = World(
            stage_units_in_meters=1.0,
            physics_dt=PHYSICS_DT,
            rendering_dt=PHYSICS_DT,
        )
        articulation = Articulation(CENTRIFUGE_ROOT, name="centrifuge_demo")
        world.scene.add(articulation)
        tube_views = []
        for index, probe_path in enumerate(probe_paths):
            view = RigidPrimView(
                probe_path,
                name=f"tube_insertion_demo_{index}",
                track_contact_forces=False,
                max_contact_count=1,
                disable_stablization=False,
            )
            tube_views.append(view)
        _reset_and_sync(world, app, steps=30, unregistered_kinematic_views=tube_views)
        if not articulation.handles_initialized:
            raise RuntimeError("centrifuge Articulation handle did not initialize")
        if articulation.num_dof != len(EXPECTED_DOF_MAPPING):
            raise RuntimeError(
                f"expected {len(EXPECTED_DOF_MAPPING)} centrifuge DOFs, found {articulation.num_dof}"
            )

        sockets: list[dict[str, Any]] = []
        for socket_name in socket_names:
            aperture, axis = _profile_frame_world_pose(
                stage, profile, f"{socket_name}_aperture",
                usd=Usd, usd_geom=UsdGeom, gf=Gf, np=np,
            )
            target, _ = _profile_frame_world_pose(
                stage, profile, f"{socket_name}_inserted_bottom_parked_root",
                usd=Usd, usd_geom=UsdGeom, gf=Gf, np=np,
            )
            depth = float(np.dot(target - aperture, axis)) * -1.0
            if depth <= 0.0:
                raise RuntimeError(
                    f"profile socket frames for {socket_name} do not define an insertion depth"
                )
            sockets.append(
                {
                    "name": socket_name,
                    "aperture": tuple(float(v) for v in aperture),
                    "axis": tuple(float(v) for v in axis),
                    "depth": depth,
                    "seat_z_m": float(target[2]),
                }
            )
        # The r10 package carries cup floor pads and wall panels as rotor
        # colliders, so the physical drop seats against package geometry.
        keyframes = build_demo_keyframes(sockets=sockets)
        if fixed_camera is not None:
            keyframes = apply_fixed_camera(keyframes, fixed_camera)

        camera = _init_camera("HciDemoCamera", 1280, 720, 20.0)

        identity = np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
        frames_dir.mkdir(parents=True, exist_ok=True)
        lid_dof = 2
        # Isaac 4.1's single-Articulation wrapper does not expose drive
        # targets; the underlying view's PD-target API is the intended path.
        articulation_view = articulation._articulation_view
        released = [False] * len(tube_views)
        seated_measurements: list[dict[str, Any] | None] = [None] * len(tube_views)

        def apply_keyframe(keyframe: dict[str, Any]) -> None:
            lid_rad = float(keyframe["lid_rad"])
            positions = np.asarray([0.0, 0.0, lid_rad], dtype=float)
            articulation.set_joint_positions(positions)
            articulation_view.set_joint_position_targets(
                positions=np.asarray([positions], dtype=float),
            )
            for tube_index, (view, position) in enumerate(
                zip(tube_views, keyframe["tube_positions_m"])
            ):
                if position is None:
                    if not released[tube_index]:
                        kinematic_attrs[tube_index].Set(False)
                        released[tube_index] = True
                    continue
                view.set_world_poses(
                    positions=np.asarray([position], dtype=np.float32),
                    orientations=identity,
                )
            view_spec = keyframe["camera"]
            _set_camera_look_at(
                camera,
                np.asarray(view_spec["target"], dtype=float),
                distance=view_spec["distance"],
                elevation=view_spec["elevation"],
                azimuth=view_spec["azimuth"],
            )
            camera.set_focal_length(float(view_spec["focal_mm"]))

        # Prime the render pipeline with the first keyframe so the first
        # captured frame is not the pre-loop reset state.
        apply_keyframe(keyframes[0])
        for _ in range(10):
            world.step(render=True)

        for frame_index, keyframe in enumerate(keyframes):
            apply_keyframe(keyframe)
            for _ in range(SUBSTEPS_PER_FRAME - 1):
                world.step(render=False)
            # The sensor render product lags one render; the second rendered
            # step carries this frame's poses into the RGBA readback.
            world.step(render=True)
            world.step(render=True)
            rgba = None
            for _ in range(6):
                rgba = _camera_rgba(camera)
                if rgba is not None:
                    break
                world.step(render=True)
            if rgba is None:
                raise RuntimeError(f"camera produced no RGBA frame at {frame_index}")
            rgb = _rgba_to_rgb(rgba)
            if rgb is None or not _save_rgb_png(frames_dir / f"frame_{frame_index:04d}.png", rgb):
                raise RuntimeError(f"could not save demo frame {frame_index}")
            saved += 1
            phase = keyframe["phase"]
            if phase.startswith("tube_") and phase.endswith("_release"):
                active = int(phase.split("_")[1])
                is_last_of_phase = (
                    frame_index + 1 == len(keyframes)
                    or keyframes[frame_index + 1]["phase"] != phase
                )
                if is_last_of_phase:
                    pose_p, pose_q = tube_views[active].get_world_poses()
                    seated_measurements[active] = {
                        "socket_name": sockets[active]["name"],
                        "seated_position_m": [
                            round(float(v), 6) for v in pose_p[0]
                        ],
                        "upright_quaternion_w": round(float(pose_q[0][0]), 6),
                        "seat_z_m": sockets[active]["seat_z_m"],
                    }
        for measurement in seated_measurements:
            if measurement is None:
                raise RuntimeError("a tube was never released and measured")
            z_error = abs(measurement["seated_position_m"][2] - measurement["seat_z_m"])
            if measurement["upright_quaternion_w"] < 0.97:
                raise RuntimeError(f"tube did not settle upright: {measurement}")
            if z_error > 0.005:
                raise RuntimeError(f"tube did not settle on the cup floor: {measurement}")
        observed_lid = float(np.asarray(articulation.get_joint_positions(), dtype=float)[lid_dof])
        return {
            "frames_saved": saved,
            "sockets": sockets,
            "seated_measurements": seated_measurements,
            "final_lid_rad": observed_lid,
            "keyframes": keyframes,
        }
    finally:
        # Mirror the centrifuge qualifier: Isaac Sim 4.1 ``close()`` can
        # terminate the interpreter before evidence persists, so this
        # short-lived CLI leaves Kit teardown to process exit.
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--centrifuge-package",
        type=Path,
        default=Path("outputs/centrifuge_identity_root_r10v2_proxy_invisible/package"),
    )
    parser.add_argument(
        "--tube-package",
        type=Path,
        default=Path("outputs/hci_15ml_closed_insert_lid_r2_20260818/package"),
    )
    parser.add_argument(
        "--centrifuge-manifest",
        type=Path,
        default=Path(
            "outputs/centrifuge_identity_root_r10v2_proxy_invisible/package.manifest.json"
        ),
    )
    parser.add_argument(
        "--device-profile",
        type=Path,
        default=Path(
            "outputs/centrifuge_identity_root_r10v2_proxy_invisible/articulation/device_profile_r11_visual_cup_sockets.json"
        ),
    )
    parser.add_argument(
        "--qualification-report",
        type=Path,
        action="append",
        default=None,
        help="Qualification report bound into the demo evidence; may repeat.",
    )
    parser.add_argument(
        "--socket-name",
        action="append",
        default=None,
        help=(
            "Profile socket frame prefix used by the demo; repeat for a "
            "balanced pair. Defaults to the balanced pair "
            f"{DEFAULT_SOCKET_NAMES}."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help=(
            "Demo output directory; defaults to the demo dir, or the "
            "demo_topdown dir when --top-down is set."
        ),
    )
    parser.add_argument(
        "--top-down",
        action="store_true",
        help="Lock every frame to the fixed overhead camera (CAMERA_TOPDOWN).",
    )
    parser.add_argument("--skip-record", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    tube_asset = args.tube_package.resolve() / "asset.usd"
    if tube_asset.is_file():
        assert_not_forbidden_k0365_tube_hash(_sha(tube_asset))
    socket_names = (
        tuple(args.socket_name) if args.socket_name else DEFAULT_SOCKET_NAMES
    )
    if args.out_dir is not None:
        out_dir = args.out_dir.resolve()
    else:
        base = Path("outputs/hci_15ml_closed_insert_lid_r2_20260818")
        out_dir = (base / "demo_topdown" if args.top_down else base / "demo").resolve()
    frames_dir = out_dir / "frames"
    keyframes: list[dict[str, Any]] = []
    seated: list[dict[str, Any]] = []
    if not args.skip_record:
        evidence = _record_isaac(
            centrifuge_package=args.centrifuge_package.resolve(),
            centrifuge_manifest=args.centrifuge_manifest.resolve(),
            tube_package=args.tube_package.resolve(),
            device_profile=args.device_profile.resolve(),
            frames_dir=frames_dir,
            socket_names=socket_names,
            fixed_camera=CAMERA_TOPDOWN if args.top_down else None,
        )
        keyframes = evidence["keyframes"]
        seated = evidence["seated_measurements"]
        if evidence["frames_saved"] != len(keyframes):
            raise RuntimeError("captured frame count does not match the demo keyframes")
        if not (abs(evidence["final_lid_rad"] - LID_CLOSED_RAD) <= 0.09):
            raise RuntimeError(
                f"lid did not finish in the closed band: {evidence['final_lid_rad']}"
            )
    mp4_name = (
        "hci_15ml_closed_insert_lid_demo_topdown.mp4"
        if args.top_down
        else "hci_15ml_closed_insert_lid_demo.mp4"
    )
    mp4 = encode_mp4(frames_dir, out_dir / mp4_name, fps=FPS)
    reports = [report.resolve() for report in args.qualification_report or [] if report.is_file()]
    payload = evidence_payload(
        centrifuge_package=args.centrifuge_package.resolve(),
        tube_package=args.tube_package.resolve(),
        device_profile=args.device_profile.resolve(),
        qualification_reports=reports,
        mp4=mp4,
        frames_dir=frames_dir,
        keyframes=keyframes,
        camera_mode="top_down" if args.top_down else "orbit_beats",
        socket_names=socket_names,
        seated_measurements=seated,
    )
    evidence_path = out_dir / "demo_evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"evidence": str(evidence_path), "mp4": payload["mp4"]}, indent=2))
    return 0


if __name__ == "__main__":
    # The mp4 and evidence are durable by the time main returns. Flush and
    # exit directly: Isaac Sim 4.1 Kit teardown can segfault the interpreter,
    # which must not mask this CLI's exit code (same pattern as runtime_smoke).
    import os

    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
