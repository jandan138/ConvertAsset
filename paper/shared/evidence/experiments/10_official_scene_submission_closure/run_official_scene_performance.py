#!/usr/bin/env python3
"""Run official-scene load/render performance measurements.

Batch mode runs under normal Python and launches one fresh Isaac Sim process
per scene/condition/run. Once mode runs inside Isaac Sim and emits one
RESULT_JSON line that batch mode captures into a CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
DEFAULT_PLAN = PROJECT_ROOT / "paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_plan.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_runs.csv"
RESULT_PREFIX = "RESULT_JSON="
REQUIRED_CONDITIONS = ("original_mdl", "convertasset_nomdl")
OPTIONAL_CONDITIONS = ("nvidia_baseline",)

FIELDNAMES = [
    "scene_id",
    "condition",
    "run_id",
    "status",
    "stage_path",
    "sim_init_s",
    "open_ready_s",
    "warmup_s",
    "total_ready_s",
    "gpu_memory_mb",
    "warmup_updates",
    "warmup_fps",
    "ready_updates",
    "script_wall_s",
    "error",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_batch_tasks(plan: dict[str, Any], *, runs: int, include_optional: bool = False) -> list[dict[str, Any]]:
    conditions = list(REQUIRED_CONDITIONS)
    if include_optional:
        conditions.extend(OPTIONAL_CONDITIONS)

    tasks = []
    for scene in plan.get("scene_inventory", []):
        scene_id = scene["scene_id"]
        condition_map = scene.get("conditions", {})
        for condition in conditions:
            record = condition_map.get(condition, {})
            if record.get("status") != "planned" or not record.get("stage_path"):
                continue
            for run_id in range(1, runs + 1):
                tasks.append(
                    {
                        "scene_id": scene_id,
                        "condition": condition,
                        "run_id": run_id,
                        "stage_path": record["stage_path"],
                    }
                )
    return tasks


def _gpu_memory_mb() -> int | None:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            timeout=10,
        )
        values = [int(value.strip()) for value in out.splitlines() if value.strip()]
        return max(values) if values else None
    except Exception:
        return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["batch", "once"], default="batch")
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--warmup-updates", type=int, default=30)
    parser.add_argument("--scene-id")
    parser.add_argument("--condition")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--stage")
    return parser.parse_args()


def _update(app: Any, count: int) -> None:
    for _ in range(max(1, count)):
        app.update()


def _run_once(args: argparse.Namespace) -> int:
    if not args.scene_id or not args.condition or args.run_id is None or not args.stage:
        raise SystemExit("--scene-id, --condition, --run-id, and --stage are required in once mode")

    t_script0 = time.perf_counter()
    result: dict[str, Any] = {
        "scene_id": args.scene_id,
        "condition": args.condition,
        "run_id": args.run_id,
        "status": "success",
        "stage_path": args.stage,
        "warmup_updates": args.warmup_updates,
        "error": "",
    }
    simulation_app = None
    try:
        from isaacsim import SimulationApp

        t0 = time.perf_counter()
        simulation_app = SimulationApp(
            {
                "headless": True,
                "renderer": "RayTracedLighting",
                "sync_loads": True,
                "width": 1024,
                "height": 768,
            }
        )
        result["sim_init_s"] = round(time.perf_counter() - t0, 4)

        import omni.kit.app
        import omni.usd

        app = omni.kit.app.get_app()
        ctx = omni.usd.get_context()
        _update(app, 2)

        open_t0 = time.perf_counter()
        ctx.open_stage(args.stage)
        ready_updates = 0
        while True:
            loading = False
            for name in ("is_standby", "is_stage_loading"):
                fn = getattr(ctx, name, None)
                if callable(fn):
                    try:
                        loading = loading or bool(fn())
                    except Exception:
                        loading = loading or False
            if not loading:
                break
            _update(app, 1)
            ready_updates += 1
        result["open_ready_s"] = round(time.perf_counter() - open_t0, 4)

        warmup_t0 = time.perf_counter()
        _update(app, args.warmup_updates)
        warmup_s = time.perf_counter() - warmup_t0
        result["warmup_s"] = round(warmup_s, 4)
        result["warmup_fps"] = round(args.warmup_updates / max(warmup_s, 1e-9), 4)
        result["total_ready_s"] = round(time.perf_counter() - open_t0, 4)
        result["gpu_memory_mb"] = _gpu_memory_mb()
        result["ready_updates"] = ready_updates
        ctx.close_stage()
        _update(app, 2)
    except Exception as exc:  # noqa: BLE001 - this is an experiment recorder.
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["script_wall_s"] = round(time.perf_counter() - t_script0, 4)
        print(RESULT_PREFIX + json.dumps(result, sort_keys=True), flush=True)
        if simulation_app is not None:
            simulation_app.close()
    return 0 if result["status"] == "success" else 1


def _invoke_once(task: dict[str, Any], *, warmup_updates: int) -> dict[str, Any]:
    cmd = [
        str(PROJECT_ROOT / "scripts/isaac_python.sh"),
        str(Path(__file__).resolve()),
        "--mode",
        "once",
        "--scene-id",
        str(task["scene_id"]),
        "--condition",
        str(task["condition"]),
        "--run-id",
        str(task["run_id"]),
        "--stage",
        str(task["stage_path"]),
        "--warmup-updates",
        str(warmup_updates),
    ]
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), text=True, capture_output=True, check=False)
    result_line = None
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(RESULT_PREFIX):
            result_line = line[len(RESULT_PREFIX) :]
            break
    if result_line:
        result = json.loads(result_line)
    else:
        result = {
            "scene_id": task["scene_id"],
            "condition": task["condition"],
            "run_id": task["run_id"],
            "status": "failed",
            "stage_path": task["stage_path"],
            "warmup_updates": warmup_updates,
            "error": (proc.stderr or proc.stdout)[-2000:],
        }
    if proc.returncode != 0 and result.get("status") == "success":
        result["status"] = "failed"
        result["error"] = f"process_returncode={proc.returncode}"
    return result


def write_result_rows(output_csv: Path, rows: list[dict[str, Any]]) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in FIELDNAMES})


def _run_batch(args: argparse.Namespace) -> int:
    plan = load_json(Path(args.plan))
    tasks = build_batch_tasks(plan, runs=args.runs, include_optional=args.include_optional)
    output_csv = Path(args.output_csv)

    rows = []
    for task in tasks:
        print(f"{task['scene_id']} {task['condition']} run={task['run_id']}", flush=True)
        rows.append(_invoke_once(task, warmup_updates=args.warmup_updates))

    write_result_rows(output_csv, rows)
    success_count = sum(1 for row in rows if row.get("status") == "success")
    failure_count = len(rows) - success_count
    print(f"Wrote {len(rows)} rows to {output_csv} ({success_count} success, {failure_count} failed)")
    return 0 if failure_count == 0 else 1


def main() -> int:
    args = _parse_args()
    if args.mode == "once":
        return _run_once(args)
    return _run_batch(args)


if __name__ == "__main__":
    raise SystemExit(main())
