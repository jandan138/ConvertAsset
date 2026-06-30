"""Isaac Sim 4.1 runtime smoke evidence for AAN-06."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

from .model import MILESTONE_AAN06, NormalizeAssetRequest
from .package_layout import TargetPackageLayout


@dataclass(frozen=True)
class RuntimeSmokeResult:
    overall_status: str
    return_code: int
    runtime_evidence: dict[str, Any]
    stage_gate: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]
    extra_commands: dict[str, Any] = field(default_factory=dict)


def build_not_run_runtime_smoke(reason: str) -> RuntimeSmokeResult:
    return RuntimeSmokeResult(
        overall_status="blocked",
        return_code=0,
        runtime_evidence={
            "status": "not_run",
            "reason": reason,
            "required_gate": "runtime",
        },
        stage_gate={
            "check_id": MILESTONE_AAN06,
            "stage": "runtime_smoke",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
    )


def build_runtime_smoke(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
    *,
    timeout_seconds: int = 240,
) -> RuntimeSmokeResult:
    repo_root = Path(__file__).resolve().parents[2]
    evidence_dir = layout.root / "evidence" / "runtime_smoke"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report_path = evidence_dir / "report.json"
    render_path = evidence_dir / "render.png"
    stdout_path = evidence_dir / "stdout.log"
    stderr_path = evidence_dir / "stderr.log"
    wrapper = repo_root / "scripts" / "isaac_python.sh"
    argv = [
        str(wrapper),
        "-m",
        "convert_asset.asset_application_normalizer.runtime_smoke",
        "--worker",
        "--root-usd",
        str(layout.root_usd),
        "--report-out",
        str(report_path),
        "--render-out",
        str(render_path),
        "--asset-id",
        request.asset_id,
        "--width",
        "512",
        "--height",
        "512",
        "--warmup-steps",
        "16",
        "--render-steps",
        "8",
        "--step-frames",
        "4",
    ]
    for prim_path in request.required_prims:
        argv.extend(["--required-prim", prim_path])

    command_record = {
        "stage": "runtime_smoke",
        "cwd": str(repo_root),
        "argv": argv,
        "env_policy": {
            "allowed_existing_conda_env": "isaac41",
            "mutation_allowed": False,
            "headless_only": True,
            "wrapper": "scripts/isaac_python.sh",
        },
        "stdout_path": _package_relative(layout.root, stdout_path),
        "stderr_path": _package_relative(layout.root, stderr_path),
        "report_path": _package_relative(layout.root, report_path),
        "render_path": _package_relative(layout.root, render_path),
    }

    try:
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        stderr_path.write_text(completed.stderr or "", encoding="utf-8")
        exit_code = int(completed.returncode)
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(exc.stdout or "", encoding="utf-8")
        stderr_path.write_text(exc.stderr or "", encoding="utf-8")
        exit_code = 124
        report = {
            "status": "blocked",
            "cold_load": {
                "status": "blocked",
                "reason": f"runtime smoke timed out after {timeout_seconds} seconds",
            },
        }
        return _runtime_result(layout, report, command_record, exit_code)

    report = _read_report(report_path)
    if report is None:
        report = {
            "status": "blocked",
            "cold_load": {
                "status": "blocked",
                "reason": "runtime worker did not write a report JSON",
            },
        }
    return _runtime_result(layout, report, command_record, exit_code)


def _runtime_result(
    layout: TargetPackageLayout,
    report: dict[str, Any],
    command_record: dict[str, Any],
    exit_code: int,
) -> RuntimeSmokeResult:
    command_record = {**command_record, "exit_code": exit_code}
    report = {
        **report,
        "command_id": "runtime_smoke_001",
        "stdout_path": command_record["stdout_path"],
        "stderr_path": command_record["stderr_path"],
    }
    status = "pass" if exit_code == 0 and report.get("status") == "pass" else "blocked"
    if status == "pass":
        blockers: list[dict[str, Any]] = []
        summary = "AAN-06 Isaac Sim runtime smoke passed."
        return_code = 0
    else:
        blockers = [
            {
                "blocker_id": "aan06_block_runtime_smoke",
                "severity": "blocking",
                "summary": "Isaac Sim runtime smoke did not complete successfully.",
                "exit_code": exit_code,
                "required_resolution": "Inspect runtime smoke stdout/stderr and fix load, render, step, or reset failures.",
            }
        ]
        summary = "AAN-06 Isaac Sim runtime smoke blocked."
        return_code = 5
        report["status"] = "blocked"

    return RuntimeSmokeResult(
        overall_status=status,
        return_code=return_code,
        runtime_evidence=report,
        stage_gate={
            "check_id": MILESTONE_AAN06,
            "stage": "runtime_smoke",
            "status": status,
            "summary": summary,
        },
        blocked_reasons=blockers,
        extra_commands={"runtime_smoke_001": command_record},
    )


def _read_report(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _package_relative(package_root: Path, path: Path) -> str:
    try:
        return path.relative_to(package_root).as_posix()
    except ValueError:
        return str(path)


def _worker_report(args: argparse.Namespace) -> dict[str, Any]:
    root_usd = Path(args.root_usd).resolve()
    required_prims = list(args.required_prim or [])
    render_path = Path(args.render_out).resolve()
    report_path = Path(args.report_out).resolve()
    report: dict[str, Any] = {
        "status": "blocked",
        "runtime_profile": "isaac41",
        "asset_id": str(args.asset_id),
        "root_usd": str(root_usd),
        "required_prims": required_prims,
        "cold_load": {"status": "not_run"},
        "render_readback": {"status": "not_run"},
        "physics_step": {"status": "not_run"},
        "reset": {"status": "not_run"},
        "environment": {},
    }
    if not root_usd.exists():
        report["cold_load"] = {
            "status": "blocked",
            "reason": f"root USD not found: {root_usd}",
        }
        return report

    simulation_app = None
    world = None
    try:
        from isaacsim import SimulationApp  # type: ignore

        simulation_app = SimulationApp(
            {
                "headless": True,
                "anti_aliasing": 2,
                "multi_gpu": False,
                "renderer": str(args.renderer),
            }
        )

        import numpy as np  # type: ignore
        import omni  # type: ignore
        from pxr import Usd, UsdGeom  # type: ignore

        from convert_asset.render.single import (  # noqa: PLC0415
            DEFAULT_BACKGROUND_COLOR,
            _camera_rgba,
            _compute_bbox,
            _init_camera,
            _init_world,
            _is_valid_bbox,
            _rgba_to_rgb,
            _save_rgb_png,
            _set_camera_look_at,
            _setup_environment,
        )

        report["environment"] = _runtime_environment()
        ctx = omni.usd.get_context()
        opened = bool(ctx.open_stage(str(root_usd)))
        for _ in range(240):
            simulation_app.update()
            try:
                if not ctx.is_stage_loading():
                    break
            except Exception:
                break
        stage = ctx.get_stage()
        if not opened or stage is None:
            report["cold_load"] = {
                "status": "blocked",
                "opened": opened,
                "reason": "omni.usd context did not return a loaded stage",
            }
            return report

        prim_records = _runtime_required_prims(stage, required_prims)
        if any(item["status"] == "blocked" for item in prim_records):
            report["cold_load"] = {
                "status": "blocked",
                "opened": opened,
                "required_prims": prim_records,
                "reason": "required prim missing after runtime stage open",
            }
            return report

        report["cold_load"] = {
            "status": "pass",
            "opened": opened,
            "required_prims": prim_records,
            "default_prim": _default_prim_path(stage),
        }

        world = _init_world()
        _setup_environment(stage)
        target_prim = _target_prim(stage, required_prims)
        bbox, bbox_source = _compute_bbox(target_prim)
        if not _is_valid_bbox(bbox):
            report["render_readback"] = {
                "status": "blocked",
                "reason": "target prim has invalid runtime bounding box",
                "bbox_source": bbox_source,
            }
            return report

        bbox_min, bbox_max = bbox
        center = (bbox_min + bbox_max) / 2.0
        distance = max(0.25, float(np.linalg.norm(bbox_max - bbox_min)))
        camera = _init_camera(
            "aan_runtime_smoke_camera",
            int(args.width),
            int(args.height),
            18.0,
        )
        _set_camera_look_at(camera, center, distance=distance, elevation=35.0, azimuth=45.0)

        for _ in range(max(0, int(args.warmup_steps))):
            world.step(render=False)
        for _ in range(max(1, int(args.render_steps))):
            world.step(render=True)

        rgba = _wait_for_camera_rgba(
            camera=camera,
            world=world,
            camera_rgba=_camera_rgba,
            max_attempts=20,
        )
        rgb = _rgba_to_rgb(rgba, background_color=DEFAULT_BACKGROUND_COLOR) if rgba is not None else None
        if rgb is None:
            report["render_readback"] = {
                "status": "blocked",
                "reason": "camera returned empty RGBA readback",
            }
            return report
        render_path.parent.mkdir(parents=True, exist_ok=True)
        if not _save_rgb_png(render_path, rgb):
            report["render_readback"] = {
                "status": "blocked",
                "reason": f"failed to write render PNG: {render_path}",
            }
            return report

        render_metrics = _render_metrics(rgb, render_path, DEFAULT_BACKGROUND_COLOR)
        if render_metrics["non_background_ratio"] <= float(args.min_non_background_ratio):
            report["render_readback"] = {
                **render_metrics,
                "status": "blocked",
                "reason": "render readback appears blank or all background",
                "bbox_source": bbox_source,
            }
            return report
        report["render_readback"] = {
            **render_metrics,
            "status": "pass",
            "bbox_source": bbox_source,
            "path": str(render_path),
        }

        before = _world_transforms(stage, required_prims)
        for _ in range(max(1, int(args.step_frames))):
            world.step(render=False)
        after = _world_transforms(stage, required_prims)
        finite_step = _transforms_finite(after)
        report["physics_step"] = {
            "status": "pass" if finite_step else "blocked",
            "frames": int(args.step_frames),
            "finite_transforms": finite_step,
            "max_abs_delta": _max_abs_delta(before, after),
        }
        if not finite_step:
            return report

        try:
            world.reset()
            simulation_app.update()
        except Exception as exc:
            report["reset"] = {
                "status": "blocked",
                "reason": f"world.reset failed: {exc}",
            }
            return report
        reset = _world_transforms(stage, required_prims)
        finite_reset = _transforms_finite(reset)
        report["reset"] = {
            "status": "pass" if finite_reset else "blocked",
            "finite_transforms": finite_reset,
            "max_abs_delta_from_initial": _max_abs_delta(before, reset),
        }
        if not finite_reset:
            return report

        report["status"] = "pass"
        return report
    except Exception as exc:
        failed_stage = "cold_load"
        if report["cold_load"].get("status") == "pass":
            failed_stage = "runtime_execution"
        report[failed_stage] = {
            "status": "blocked",
            "reason": str(exc),
        }
        return report
    finally:
        if world is not None:
            try:
                world.reset()
            except Exception:
                pass
        if simulation_app is not None:
            _close_simulation_app_with_report(simulation_app, report_path, report)


def _runtime_environment() -> dict[str, Any]:
    env = {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "headless": True,
    }
    try:
        import isaacsim  # type: ignore

        env["isaacsim_file"] = getattr(isaacsim, "__file__", None)
    except Exception:
        env["isaacsim_file"] = None
    try:
        from pxr import Tf  # type: ignore

        env["pxr_version"] = getattr(Tf, "__doc__", None) or "available"
    except Exception:
        env["pxr_version"] = None
    return env


def _runtime_required_prims(stage: Any, required_prims: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "exists": bool(stage.GetPrimAtPath(path).IsValid()),
            "status": "pass" if stage.GetPrimAtPath(path).IsValid() else "blocked",
        }
        for path in required_prims
    ]


def _default_prim_path(stage: Any) -> str | None:
    prim = stage.GetDefaultPrim()
    if prim and prim.IsValid():
        return prim.GetPath().pathString
    return None


def _target_prim(stage: Any, required_prims: list[str]) -> Any:
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            return prim
    default_prim = stage.GetDefaultPrim()
    if default_prim and default_prim.IsValid():
        return default_prim
    return next(iter(stage.Traverse()))


def _render_metrics(rgb: Any, render_path: Path, background_color: tuple[int, int, int]) -> dict[str, Any]:
    import numpy as np  # type: ignore

    arr = np.asarray(rgb)
    bg = np.asarray(background_color, dtype=np.int16).reshape(1, 1, 3)
    diff = np.abs(arr.astype(np.int16) - bg)
    mask = np.any(diff > 5, axis=2)
    ys, xs = np.where(mask)
    height, width = arr.shape[:2]
    if xs.size and ys.size:
        bbox_ratio = float((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)) / float(width * height)
    else:
        bbox_ratio = 0.0
    return {
        "mean_rgb": [round(float(item), 6) for item in arr[:, :, :3].mean(axis=(0, 1)).tolist()],
        "non_background_ratio": round(float(mask.mean()), 8),
        "bbox_ratio": round(bbox_ratio, 8),
        "sha256": _sha256_file(render_path),
        "bytes": render_path.stat().st_size,
        "resolution": [int(width), int(height)],
    }


def _wait_for_camera_rgba(
    *,
    camera: Any,
    world: Any,
    camera_rgba: Any,
    max_attempts: int,
) -> Any | None:
    for attempt in range(max(1, int(max_attempts))):
        rgba = camera_rgba(camera)
        if rgba is not None:
            return rgba
        if attempt < max(1, int(max_attempts)) - 1:
            world.step(render=True)
    return None


def _world_transforms(stage: Any, prim_paths: list[str]) -> dict[str, list[list[float]] | None]:
    try:
        from pxr import Usd, UsdGeom  # type: ignore
    except Exception:
        return {}
    time = Usd.TimeCode.Default()
    transforms = {}
    for path in prim_paths:
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            transforms[path] = None
            continue
        try:
            matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(time)
            transforms[path] = _matrix_to_lists(matrix)
        except Exception:
            transforms[path] = None
    return transforms


def _matrix_to_lists(matrix: Any) -> list[list[float]]:
    rows = []
    for row_idx in range(4):
        rows.append([round(float(matrix[row_idx][col_idx]), 8) for col_idx in range(4)])
    return rows


def _transforms_finite(transforms: dict[str, list[list[float]] | None]) -> bool:
    for matrix in transforms.values():
        if matrix is None:
            return False
        for row in matrix:
            for value in row:
                if not math.isfinite(float(value)):
                    return False
    return True


def _max_abs_delta(
    before: dict[str, list[list[float]] | None],
    after: dict[str, list[list[float]] | None],
) -> float | None:
    deltas = []
    for path, before_matrix in before.items():
        after_matrix = after.get(path)
        if before_matrix is None or after_matrix is None:
            continue
        for row_idx in range(4):
            for col_idx in range(4):
                deltas.append(abs(float(after_matrix[row_idx][col_idx]) - float(before_matrix[row_idx][col_idx])))
    return round(max(deltas), 8) if deltas else None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _close_simulation_app_with_report(
    simulation_app: Any,
    report_path: Path,
    report: dict[str, Any],
) -> None:
    _write_report(report_path, report)
    simulation_app.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AAN runtime smoke worker")
    parser.add_argument("--worker", action="store_true", help="Run the runtime smoke worker")
    parser.add_argument("--root-usd", required=True)
    parser.add_argument("--report-out", required=True)
    parser.add_argument("--render-out", required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--required-prim", action="append", default=[])
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=120)
    parser.add_argument("--warmup-steps", type=int, default=8)
    parser.add_argument("--render-steps", type=int, default=2)
    parser.add_argument("--step-frames", type=int, default=4)
    parser.add_argument("--renderer", default="RayTracedLighting")
    parser.add_argument("--min-non-background-ratio", type=float, default=0.001)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.worker:
        parser.error("--worker is required")
    report = _worker_report(args)
    _write_report(Path(args.report_out), report)
    return 0 if report.get("status") == "pass" else 5


if __name__ == "__main__":
    raise SystemExit(main())
