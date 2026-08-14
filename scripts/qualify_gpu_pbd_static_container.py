#!/usr/bin/env python3
"""Qualify one unified container against the Isaac 4.1 GPU-PBD static gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time
import traceback
from typing import Any, NamedTuple


PARTICLES = "/World/ParticleSet"
CONTAINER = "/World/Container"
PARTICLE_COUNT = 548
INNER_RADIUS_M = 0.019185
FLOOR_Z_M = 0.011705
RIM_Z_M = 0.27824
PHYSICS_HZ = 30


class ContainmentBounds(NamedTuple):
    """World-space bounds used to score one static container fixture."""

    center_xy_m: tuple[float, float]
    radius_m: float
    floor_z_m: float
    rim_z_m: float
    support_z_m: float


DEFAULT_BOUNDS = ContainmentBounds(
    center_xy_m=(0.0, 0.0),
    radius_m=INNER_RADIUS_M,
    floor_z_m=FLOOR_Z_M,
    rim_z_m=RIM_Z_M,
    support_z_m=0.0,
)


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def hard_runtime_errors(log_text: str) -> list[str]:
    markers = (
        "failed to cook GPU-compatible mesh",
        "Non-GPU-compatible convex mesh",
        "Particles feature is only supported on GPU",
        "CUDA error",
        "illegal memory access",
    )
    return [
        line.strip()
        for line in log_text.splitlines()
        if any(marker in line for marker in markers)
    ]


def classify_positions(
    positions: Any, np: Any, bounds: ContainmentBounds = DEFAULT_BOUNDS
) -> dict[str, int]:
    center = np.asarray(bounds.center_xy_m, dtype=float)
    radial = np.linalg.norm(positions[:, :2] - center, axis=1)
    inside = (
        (radial <= bounds.radius_m)
        & (positions[:, 2] >= bounds.floor_z_m - 0.001)
        & (positions[:, 2] <= bounds.rim_z_m)
    )
    below = positions[:, 2] < bounds.support_z_m - 0.002
    return {
        "inside": int(inside.sum()),
        "outside": int((~inside).sum()),
        "below_support": int(below.sum()),
        "particle_count": int(len(positions)),
    }


def summarize_positions(
    positions: Any, np: Any, bounds: ContainmentBounds = DEFAULT_BOUNDS
) -> dict[str, Any]:
    center = np.asarray(bounds.center_xy_m, dtype=float)
    radial = np.linalg.norm(positions[:, :2] - center, axis=1)
    return {
        "radial_max_m": float(radial.max()),
        "radial_quantiles_m": [
            float(value) for value in np.quantile(radial, [0.5, 0.9, 0.99])
        ],
        "z_range_m": [
            float(positions[:, 2].min()),
            float(positions[:, 2].max()),
        ],
    }


def load_containment_bounds(path: Path) -> ContainmentBounds:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("containment_bounds", payload)
    center = raw["center_xy_m"]
    return ContainmentBounds(
        center_xy_m=(float(center[0]), float(center[1])),
        radius_m=float(raw["radius_m"]),
        floor_z_m=float(raw["floor_z_m"]),
        rim_z_m=float(raw["rim_z_m"]),
        support_z_m=float(raw["support_z_m"]),
    )


def finalize_checks(
    *,
    minimum_inside: int,
    maximum_below: int,
    particle_count: int,
    mean_rtx_fps: float,
    hard_runtime_errors: list[str],
) -> dict[str, Any]:
    checks = {
        "gpu_cooking": not hard_runtime_errors,
        "particle_count": particle_count == PARTICLE_COUNT,
        "static_retention": minimum_inside / PARTICLE_COUNT >= 0.95,
        "below_support": maximum_below == 0,
        "performance": mean_rtx_fps >= 40.0,
    }
    return {
        **checks,
        "overall_status": "pass" if all(checks.values()) else "blocked",
    }


def _read_positions(stage: Any, np: Any) -> Any:
    prim = stage.GetPrimAtPath(PARTICLES)
    for name in ("physxParticle:simulationPoints", "points"):
        values = prim.GetAttribute(name).Get()
        if values is not None:
            return np.asarray(values, dtype=float)
    raise RuntimeError("particle positions unavailable")


def _run(args: argparse.Namespace) -> dict[str, Any]:
    from isaacsim import SimulationApp

    scene = args.scene.resolve()
    bounds_profile = args.bounds_profile
    if bounds_profile is None:
        candidate = scene.parent / "fixture_profile.json"
        if not candidate.is_file():
            raise FileNotFoundError(
                "containment bounds are required: pass --bounds-profile or "
                "place fixture_profile.json beside the scene"
            )
        bounds_profile = candidate
    bounds_profile = bounds_profile.resolve()
    bounds = load_containment_bounds(bounds_profile)
    parsed = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        app = SimulationApp(
            {
                "headless": True,
                "multi_gpu": False,
                "renderer": "RayTracedLighting",
                "width": 960,
                "height": 540,
            }
        )
    finally:
        sys.argv = parsed
    try:
        import carb
        import numpy as np
        import omni.kit.app
        import omni.physx
        import omni.usd
        from omni.isaac.core import World
        from pxr import PhysxSchema

        import omni.physx.bindings._physx as pb

        settings = carb.settings.get_settings()
        settings.set(pb.SETTING_UPDATE_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_PARTICLES_TO_USD, True)
        settings.set(pb.SETTING_UPDATE_VELOCITIES_TO_USD, True)
        settings.set_bool(pb.SETTING_SUPPRESS_READBACK, False)
        settings.set_bool("/physics/suppressReadback", False)
        log_path = Path(str(settings.get("/log/file")))
        log_offset = log_path.stat().st_size if log_path.is_file() else 0

        # Set the runtime lane before stage loading can trigger mesh cooking.
        omni.physx.get_physx_interface().overwrite_gpu_setting(1)
        context = omni.usd.get_context()
        if not context.open_stage(str(scene)):
            raise RuntimeError(f"could not open {scene}")
        for _ in range(40):
            app.update()
        stage = context.get_stage()
        if stage is None or Path(stage.GetRootLayer().realPath) != scene:
            raise RuntimeError(f"could not open {scene}")
        particle_prim = stage.GetPrimAtPath(PARTICLES)
        particle_api = PhysxSchema.PhysxParticleAPI(particle_prim)
        particle_set_api = PhysxSchema.PhysxParticleSetAPI(particle_prim)
        resolved_particle_semantics = {
            "fluid": particle_set_api.GetFluidAttr().Get(),
            "self_collision": particle_api.GetSelfCollisionAttr().Get(),
            "particle_group": particle_api.GetParticleGroupAttr().Get(),
        }
        world = World(
            stage_units_in_meters=1.0,
            physics_prim_path="/World/PhysicsScene",
            set_defaults=False,
            backend="numpy",
            device="cpu",
            physics_dt=1 / PHYSICS_HZ,
            rendering_dt=1 / PHYSICS_HZ,
        )
        world.reset()
        for _ in range(30):
            world.step(render=False)

        scores: list[dict[str, int]] = []
        for _ in range(8 * PHYSICS_HZ):
            world.step(render=False)
            scores.append(classify_positions(_read_positions(stage, np), np, bounds))
        minimum_inside = min(score["inside"] for score in scores)
        maximum_below = max(score["below_support"] for score in scores)
        final = scores[-1]
        final_positions = _read_positions(stage, np)
        final_positions_path = args.out.with_name("final_particle_positions.json")
        _write(
            final_positions_path,
            {"positions": final_positions.tolist()},
        )

        render_timings: list[float] = []
        for _ in range(90):
            started = time.perf_counter()
            world.step(render=True)
            render_timings.append((time.perf_counter() - started) * 1000.0)
        mean_rtx_fps = 1000.0 / statistics.fmean(render_timings[30:])
        log_text = ""
        log_read_error = None
        if log_path.is_file():
            try:
                with log_path.open(
                    "r", encoding="utf-8", errors="replace"
                ) as stream:
                    stream.seek(log_offset)
                    log_text = stream.read()
            except OSError as exc:
                # The parent process independently scans captured stdout/stderr.
                # Some CPFS deployments return ENOSPC while opening Kit's log
                # for reading even after the physics run has completed.
                log_read_error = f"{type(exc).__name__}: {exc}"
        errors = hard_runtime_errors(log_text)
        checks = finalize_checks(
            minimum_inside=minimum_inside,
            maximum_below=maximum_below,
            particle_count=final["particle_count"],
            mean_rtx_fps=mean_rtx_fps,
            hard_runtime_errors=errors,
        )
        result = {
            "schema_version": "aan.gpu_pbd_static_observation.v1",
            "run_index": args.run_index,
            "runtime": {
                "kit_version": str(omni.kit.app.get_app().get_app_version()),
                "gpu": "NVIDIA GeForce RTX 4090",
                "resolution": [960, 540],
            },
            "resolved_particle_semantics": resolved_particle_semantics,
            "static_hold": {
                "seconds": 8,
                "minimum_inside": minimum_inside,
                "minimum_inside_ratio": minimum_inside / PARTICLE_COUNT,
                "maximum_below_support": maximum_below,
                "final": final,
                "final_distribution": summarize_positions(final_positions, np, bounds),
                "final_positions": final_positions_path.name,
            },
            "containment_bounds": {
                "profile": str(bounds_profile),
                "center_xy_m": list(bounds.center_xy_m),
                "radius_m": bounds.radius_m,
                "floor_z_m": bounds.floor_z_m,
                "rim_z_m": bounds.rim_z_m,
                "support_z_m": bounds.support_z_m,
            },
            "performance": {
                "mean_rtx_fps": mean_rtx_fps,
                "sample_count": len(render_timings[30:]),
            },
            "hard_runtime_errors": errors,
            "in_process_log_read_error": log_read_error,
            "checks": {key: value for key, value in checks.items() if key != "overall_status"},
            "overall_status": checks["overall_status"],
            "claim_boundary": (
                "Static GPU-PBD containment only; no pour or robot claim."
            ),
        }
        _write(args.out, result)
        return result
    except BaseException as exc:
        # SimulationApp teardown can terminate the interpreter before Python's
        # default traceback reaches the parent process. Persist the diagnostic
        # first so a clean process return cannot be mistaken for qualification.
        result = {
            "schema_version": "aan.gpu_pbd_static_observation.v1",
            "run_index": args.run_index,
            "overall_status": "blocked",
            "blocked_reason": "runtime_exception",
            "runtime_exception": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
            "claim_boundary": (
                "Static GPU-PBD containment only; no pour or robot claim."
            ),
        }
        _write(args.out, result)
        return result
    finally:
        app.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--run-index", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--bounds-profile", type=Path)
    args = parser.parse_args()
    result = _run(args)
    _write(args.out, result)
    print(args.out)
    return 0 if result["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
