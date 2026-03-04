#!/usr/bin/env python3
"""Experiment #1: Performance Benchmark — load time, GPU memory, FPS.

Usage:
    /isaac-sim/python.sh paper/experiments/02_perf_benchmark/run.py
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR = PROJECT_ROOT / "assets" / "usd" / "chestofdrawers_nomdl"
OUTPUT_CSV = PROJECT_ROOT / "paper" / "results" / "raw" / "perf_benchmark.csv"

SCENE_IDS = [
    "chestofdrawers_0004",
    "chestofdrawers_0011",
    "chestofdrawers_0023",
    "chestofdrawers_0029",
]

NUM_RUNS = 3
FPS_FRAMES = 120

LOG_PATH = "/tmp/exp1_perf_log.txt"


def _log(msg):
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")


def _get_gpu_memory_mb():
    """Get current GPU memory usage in MB via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, timeout=10,
        )
        values = [int(x.strip()) for x in out.strip().split("\n") if x.strip()]
        return max(values) if values else 0
    except Exception:
        return 0


def main():
    open(LOG_PATH, "w").close()
    _log("[Exp#1] Starting performance benchmark")

    from isaacsim import SimulationApp
    simulation_app = SimulationApp({
        "headless": True,
        "renderer": "RayTracedLighting",
        "width": 1024,
        "height": 768,
    })

    import omni.usd
    import omni.kit.app

    app = omni.kit.app.get_app()

    def update(n=10):
        for _ in range(n):
            app.update()

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for scene_id in SCENE_IDS:
        scene_dir = ASSETS_DIR / scene_id
        versions = {
            "MDL": scene_dir / "instance.usd",
            "noMDL": scene_dir / "instance_noMDL.usd",
        }

        for version_label, usd_path in versions.items():
            if not usd_path.exists():
                _log(f"[WARN] Missing: {usd_path}")
                continue

            for run_id in range(1, NUM_RUNS + 1):
                _log(f"\n[Exp#1] {scene_id}/{version_label} run={run_id}")

                # Baseline GPU memory
                gpu_mem_before = _get_gpu_memory_mb()

                # Measure load time
                ctx = omni.usd.get_context()
                t0 = time.perf_counter()
                ctx.open_stage(str(usd_path))
                update(30)  # let stage fully load + render warm up
                load_time = time.perf_counter() - t0

                # Peak GPU memory after load
                gpu_mem_after = _get_gpu_memory_mb()
                gpu_memory_mb = gpu_mem_after  # absolute peak

                # Measure FPS
                t_start = time.perf_counter()
                for _ in range(FPS_FRAMES):
                    app.update()
                t_end = time.perf_counter()
                elapsed = t_end - t_start
                fps = FPS_FRAMES / max(elapsed, 1e-9)

                row = {
                    "scene_id": scene_id,
                    "version": version_label,
                    "load_time_s": round(load_time, 4),
                    "gpu_memory_mb": gpu_memory_mb,
                    "fps": round(fps, 2),
                    "run_id": run_id,
                }
                rows.append(row)
                _log(f"  load={load_time:.3f}s, gpu={gpu_memory_mb}MB, fps={fps:.1f}")

                # Close stage to get clean measurement for next run
                ctx.close_stage()
                update(10)

    # Write CSV
    with open(str(OUTPUT_CSV), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "version", "load_time_s", "gpu_memory_mb", "fps", "run_id"])
        writer.writeheader()
        writer.writerows(rows)

    _log(f"\n[Exp#1] Done. Wrote {len(rows)} rows to {OUTPUT_CSV}")

    simulation_app.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
