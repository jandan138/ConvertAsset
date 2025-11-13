#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch-count faces for many USD files under a root directory.

- Scans for files named exactly 'instance.usd' (customizable via --pattern)
- For each, counts total faces in eligible Mesh prims (using same rules as faces.count_mesh_faces)
- Writes results into a new folder under /opt/my_dev/ConvertAsset/reports by default
  - faces.csv (path,faces)
  - summary.txt

Usage:
  /isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/batch_count_faces.py \
      /shared/.../Asset_Library \
      --pattern instance.usd \
      --reports-root /opt/my_dev/ConvertAsset/reports
"""
from __future__ import annotations
import os
import sys
import csv
import time
import argparse
from typing import List, Tuple

try:
    from pxr import Usd  # noqa: F401  # ensure pxr is available
except Exception as e:
    print("[ERROR] pxr not available:", e)
    sys.exit(2)

# Use our library function for counting
try:
    # When executed as a script, ensure import path includes project root
    HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(HERE)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from convert_asset.mesh.faces import count_mesh_faces  # type: ignore
except Exception as e:
    print("[ERROR] failed to import count_mesh_faces:", e)
    sys.exit(3)


def find_usd_files(root: str, pattern: str) -> List[str]:
    print(f"[SCAN] Scanning root: {root} for pattern: {pattern}")
    paths: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden dirs for speed
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in filenames:
            if fn == pattern:
                paths.append(os.path.join(dirpath, fn))
    paths = sorted(paths)
    print(f"[SCAN] Found {len(paths)} file(s) matching {pattern}")
    return paths


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Batch count faces for many USD files")
    ap.add_argument("root", help="Root directory to scan")
    ap.add_argument("--pattern", default="instance.usd", help="File name to match (default: instance.usd)")
    ap.add_argument("--reports-root", default="/opt/my_dev/ConvertAsset/reports", help="Where to create output folder")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("Not a directory:", root)
        return 2

    usd_paths = find_usd_files(root, args.pattern)
    if not usd_paths:
        print("No files matched pattern:", args.pattern)
        return 0

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.abspath(args.reports_root), f"faces_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    csv_path = os.path.join(out_dir, "faces.csv")
    sum_path = os.path.join(out_dir, "summary.txt")

    total_faces = 0
    ok = 0
    failed: List[Tuple[str, str]] = []

    print(f"[OUT] Writing reports to: {out_dir}")
    with open(csv_path, "w", newline="") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["path", "faces"])  # header
        total_files = len(usd_paths)
        t0 = time.time()
        for idx, p in enumerate(usd_paths, 1):
            print(f"[RUN] ({idx}/{total_files}) Counting faces: {p}")
            try:
                faces = count_mesh_faces(p)
                total_faces += int(faces)
                ok += 1
                w.writerow([p, faces])
                print(f"[OK] faces={faces} | ok={ok} fail={len(failed)} total_faces={total_faces}")
            except Exception as e:
                failed.append((p, str(e)))
                print(f"[FAIL] {e} | ok={ok} fail={len(failed)} total_faces={total_faces}")
            # Periodic progress ETA every 50 files or first few
            if idx <= 3 or idx % 50 == 0:
                dt = max(1e-6, time.time() - t0)
                rps = idx / dt
                remaining = total_files - idx
                eta = remaining / rps if rps > 0 else float('inf')
                print(f"[PROGRESS] {idx}/{total_files} processed | {rps:.2f} files/s | ETA ~ {eta:.1f}s")

    with open(sum_path, "w") as fs:
        fs.write(f"Scanned root: {root}\n")
        fs.write(f"Matched files: {len(usd_paths)}\n")
        fs.write(f"Succeeded: {ok}\n")
        fs.write(f"Failed: {len(failed)}\n")
        fs.write(f"TOTAL faces: {total_faces}\n")
        if failed:
            fs.write("\nFailures:\n")
            for p, msg in failed:
                fs.write(f"- {p}: {msg}\n")

    print("----- Summary -----")
    print("Output dir:", out_dir)
    print("CSV:", csv_path)
    print("Summary:", sum_path)
    print("Matched:", len(usd_paths), "Succeeded:", ok, "Failed:", len(failed))
    print("TOTAL faces:", total_faces)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
