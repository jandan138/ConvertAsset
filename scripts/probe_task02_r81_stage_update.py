#!/usr/bin/env python3
"""Probe whether an Isaac Sim 4.1 scene completes five RTX updates."""

from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True)
    args = parser.parse_args()

    from isaacsim import SimulationApp

    parsed_argv = sys.argv
    sys.argv = [sys.argv[0]]
    started = time.perf_counter()
    try:
        application = SimulationApp(
            {"headless": True, "multi_gpu": False, "renderer": "RayTracedLighting"}
        )
    finally:
        sys.argv = parsed_argv
    print(f"APP_READY_SECONDS={time.perf_counter() - started:.6f}", flush=True)
    try:
        import omni.usd

        opened = time.perf_counter()
        if not omni.usd.get_context().open_stage(args.scene):
            print("OPEN_RETURNED=false", flush=True)
            return 2
        print(f"OPEN_RETURN_SECONDS={time.perf_counter() - opened:.6f}", flush=True)
        for index in range(1, 6):
            updated = time.perf_counter()
            application.update()
            print(
                f"UPDATE_{index:02d}_SECONDS={time.perf_counter() - updated:.6f}",
                flush=True,
            )
        return 0
    finally:
        application.close()


if __name__ == "__main__":
    raise SystemExit(main())
