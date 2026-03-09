#!/usr/bin/env python3
"""Supplemental whole-scene startup benchmark for a large GRScenes stage.

Batch mode runs under the system Python and shells into Isaac Sim for each
fresh-process measurement. `once` mode runs inside Isaac Sim and measures a
single stage load.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCENE_DIR = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/"
    "GRScenes-test0/GRScenes100/commercial/"
    "MV4AFHQKTKJZ2AABAAAAADQ8_usd"
)
DEFAULT_MDL = DEFAULT_SCENE_DIR / "start_result_interaction.usd"
DEFAULT_NOMDL = DEFAULT_SCENE_DIR / "start_result_interaction_noMDL.usd"
DEFAULT_OUTPUT = PROJECT_ROOT / "paper" / "results" / "raw" / "perf_benchmark_grscene.csv"
RESULT_PREFIX = "RESULT_JSON="


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark startup for a GRScenes stage")
    parser.add_argument(
        "--mode",
        choices=["batch", "once"],
        default="batch",
        help="batch: orchestrate repeated fresh-process runs; once: run one Isaac Sim measurement",
    )
    parser.add_argument("--scene-mdl", default=str(DEFAULT_MDL), help="Path to the MDL scene")
    parser.add_argument("--scene-nomdl", default=str(DEFAULT_NOMDL), help="Path to the converted noMDL scene")
    parser.add_argument("--stage", help="Stage to measure in once mode")
    parser.add_argument("--version", help="Label to emit in once mode")
    parser.add_argument("--run-id", type=int, help="Run id to emit in once mode")
    parser.add_argument("--scene-label", default="grscene_mv4afhqk", help="Scene label in CSV output")
    parser.add_argument("--runs", type=int, default=3, help="Fresh-process runs per version in batch mode")
    parser.add_argument("--warmup-updates", type=int, default=30, help="Post-ready updates before timing ends")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT), help="CSV output path in batch mode")
    return parser.parse_args()


def _get_gpu_memory_mb() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            timeout=10,
        )
        values = [int(x.strip()) for x in out.splitlines() if x.strip()]
        return max(values) if values else 0
    except Exception:
        return 0


def _run_once(args: argparse.Namespace) -> int:
    if not args.stage or not args.version or args.run_id is None:
        raise SystemExit("--stage, --version, and --run-id are required in --mode once")

    t_script0 = time.perf_counter()

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
    sim_init_s = time.perf_counter() - t0

    import omni.kit.app
    import omni.usd

    app = omni.kit.app.get_app()
    ctx = omni.usd.get_context()

    def update(count: int = 1) -> None:
        for _ in range(max(1, count)):
            app.update()

    update(2)

    open_t0 = time.perf_counter()
    ctx.open_stage(args.stage)
    ready_updates = 0
    while True:
        loading = False
        standby_fn = getattr(ctx, "is_standby", None)
        if callable(standby_fn):
            try:
                loading = loading or bool(standby_fn())
            except Exception:
                loading = loading or False
        stage_loading_fn = getattr(ctx, "is_stage_loading", None)
        if callable(stage_loading_fn):
            try:
                loading = loading or bool(stage_loading_fn())
            except Exception:
                loading = loading or False
        if not loading:
            break
        update(1)
        ready_updates += 1

    open_ready_s = time.perf_counter() - open_t0

    warmup_t0 = time.perf_counter()
    update(args.warmup_updates)
    warmup_s = time.perf_counter() - warmup_t0
    total_ready_s = time.perf_counter() - open_t0

    result = {
        "scene_label": args.scene_label,
        "stage_path": args.stage,
        "version": args.version,
        "run_id": args.run_id,
        "sim_init_s": round(sim_init_s, 4),
        "open_ready_s": round(open_ready_s, 4),
        "warmup_s": round(warmup_s, 4),
        "total_ready_s": round(total_ready_s, 4),
        "gpu_memory_mb": _get_gpu_memory_mb(),
        "ready_updates": ready_updates,
        "script_wall_s": round(time.perf_counter() - t_script0, 4),
    }
    print(RESULT_PREFIX + json.dumps(result, sort_keys=True), flush=True)

    try:
        ctx.close_stage()
        update(2)
    finally:
        simulation_app.close()
    return 0


def _invoke_once(
    script_path: Path,
    scene_label: str,
    version: str,
    stage: Path,
    run_id: int,
    warmup_updates: int,
) -> dict:
    cmd = [
        str(PROJECT_ROOT / "scripts" / "isaac_python.sh"),
        str(script_path),
        "--mode",
        "once",
        "--scene-label",
        scene_label,
        "--version",
        version,
        "--run-id",
        str(run_id),
        "--stage",
        str(stage),
        "--warmup-updates",
        str(warmup_updates),
    ]
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"Isaac Sim run failed for {version} run {run_id} with code {proc.returncode}")

    result_line = None
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(RESULT_PREFIX):
            result_line = line[len(RESULT_PREFIX) :]
            break
    if result_line is None:
        raise RuntimeError(f"Did not find benchmark result JSON in output for {version} run {run_id}")
    return json.loads(result_line)


def _run_batch(args: argparse.Namespace) -> int:
    script_path = Path(__file__).resolve()
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    scenes = {
        "MDL": Path(args.scene_mdl),
        "noMDL": Path(args.scene_nomdl),
    }
    for stage in scenes.values():
        if not stage.exists():
            raise FileNotFoundError(stage)

    rows = []
    for run_id in range(1, args.runs + 1):
        for version, stage in scenes.items():
            result = _invoke_once(
                script_path=script_path,
                scene_label=args.scene_label,
                version=version,
                stage=stage,
                run_id=run_id,
                warmup_updates=args.warmup_updates,
            )
            rows.append(result)
            print(
                f"{version} run={run_id}: open_ready={result['open_ready_s']:.3f}s "
                f"warmup={result['warmup_s']:.3f}s total_ready={result['total_ready_s']:.3f}s "
                f"gpu={result['gpu_memory_mb']}MB"
            )

    fieldnames = [
        "scene_label",
        "stage_path",
        "version",
        "run_id",
        "sim_init_s",
        "open_ready_s",
        "warmup_s",
        "total_ready_s",
        "gpu_memory_mb",
        "ready_updates",
        "script_wall_s",
    ]
    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output_csv}")
    return 0


def main() -> int:
    args = _parse_args()
    if args.mode == "once":
        return _run_once(args)
    return _run_batch(args)


if __name__ == "__main__":
    raise SystemExit(main())
