#!/usr/bin/env python3
"""Distill the backend/protocol matrix into paper-facing summary tables.

Consumes `backend_protocol_matrix.csv` (produced by
`aggregate_stress_backend_matrix.py`) and emits three paper-facing CSVs:

1. canonical_backend_table.csv — one row per backend under the canonical
   structured_text + normalized-1000 s1 protocol, on both the frozen
   stress30 pool and the extended80 diagnostic pool.
2. protocol_sensitivity_table.csv — per backend, the 2x2 coordinate-frame x
   response-format grid with normalized-1000 hit rates and material deltas.
3. task_family_table.csv — s1 localization vs s2 interaction per backend.

All numbers come from frozen prediction JSONL artifacts; this script adds no
new measurements.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

BACKEND_ORDER = [
    "gemma4-E4B-it-4bit",
    "Qwen2.5-VL-7B-Instruct",
    "qwen3vl-2b",
    "qwen3vl-8b",
    "internvl3-8b",
    "molmo-7b",
]
BACKEND_LABELS = {
    "9746c23553347b443ebdc1caba1d41b52223d0c8": "gemma4-E4B-it-4bit",
    "89644892e4d85e24eaac8bacfd4f463576704203": "qwen3vl-2b",
    "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b": "qwen3vl-8b",
    "Qwen2.5-VL-7B-Instruct": "Qwen2.5-VL-7B-Instruct",
}


def _short(backend: str, backend_full: str = "") -> str:
    text = f"{backend} {backend_full}"
    if "internvl3-8b" in text.lower() or "InternVL3-8B" in text:
        return "internvl3-8b"
    if "molmo" in text.lower():
        return "molmo-7b"
    return BACKEND_LABELS.get(backend, backend)


def _f(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(args.matrix_csv.open()))
    for row in rows:
        row["backend"] = _short(row["backend"], row.get("backend_full", ""))
        # distinguish stress30 vs extended80 by record count / file path
        row["pool"] = "extended80" if "extended80" in row.get("prediction_file", "") else "stress30"

    # ---- canonical backend table (structured_text + normalized_1000 + s1)
    canonical = [
        r for r in rows
        if r["prompt_type"] == "s1_point" and r["coordinate_frame"] == "normalized_1000"
        and r["response_format"] == "structured_text"
    ]
    with (args.out_dir / "canonical_backend_table.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "backend", "pool", "answer_orig", "answer_conv",
            "n1000_hit_orig", "n1000_hit_conv", "n1000_hit_delta",
            "hit_agreement", "mean_point_delta_px",
        ])
        for backend in BACKEND_ORDER:
            for pool in ("stress30", "extended80"):
                match = [r for r in canonical if r["backend"] == backend and r["pool"] == pool]
                if not match:
                    continue
                r = match[0]
                writer.writerow([
                    backend, pool, _fmt(_f(r["answer_acc_original"])), _fmt(_f(r["answer_acc_converted"])),
                    _fmt(_f(r["n1000_hit_original"])), _fmt(_f(r["n1000_hit_converted"])),
                    _fmt(_f(r["n1000_hit_delta"])), _fmt(_f(r["hit_agreement_n1000"])),
                    _fmt(_f(r["mean_point_delta_px"])),
                ])

    # ---- protocol sensitivity grid (stress30, s1)
    grid = defaultdict(dict)
    for r in rows:
        if r["prompt_type"] != "s1_point" or r["pool"] != "stress30":
            continue
        grid[r["backend"]][(r["coordinate_frame"], r["response_format"])] = r
    with (args.out_dir / "protocol_sensitivity_table.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "backend", "coordinate_frame", "response_format",
            "n1000_hit_orig", "n1000_hit_conv", "n1000_hit_delta",
            "px_hit_orig", "px_hit_conv",
        ])
        for backend in BACKEND_ORDER:
            for (coord, fmt), r in sorted(grid.get(backend, {}).items()):
                writer.writerow([
                    backend, coord, fmt,
                    _fmt(_f(r["n1000_hit_original"])), _fmt(_f(r["n1000_hit_converted"])),
                    _fmt(_f(r["n1000_hit_delta"])),
                    _fmt(_f(r["px_hit_original"])), _fmt(_f(r["px_hit_converted"])),
                ])

    # ---- task family table (s1 vs s2, structured+n1000)
    by_family = defaultdict(dict)
    for r in rows:
        if r["coordinate_frame"] != "normalized_1000" or r["response_format"] != "structured_text":
            continue
        by_family[(r["backend"], r["pool"])][r["prompt_type"]] = r
    with (args.out_dir / "task_family_table.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "backend", "pool", "task", "answer_orig", "answer_conv",
            "n1000_hit_orig", "n1000_hit_conv", "n1000_hit_delta",
        ])
        for backend in BACKEND_ORDER:
            for pool in ("stress30", "extended80"):
                for task in ("s1_point", "s2_interaction"):
                    r = by_family.get((backend, pool), {}).get(task)
                    if not r:
                        continue
                    writer.writerow([
                        backend, pool, task, _fmt(_f(r["answer_acc_original"])), _fmt(_f(r["answer_acc_converted"])),
                        _fmt(_f(r["n1000_hit_original"])), _fmt(_f(r["n1000_hit_converted"])),
                        _fmt(_f(r["n1000_hit_delta"])),
                    ])

    # machine-readable digest of the headline spread
    digest: dict[str, Any] = {"canonical": [], "protocol_spread": []}
    for r in canonical:
        digest["canonical"].append({
            "backend": r["backend"], "pool": r["pool"],
            "n1000_hit_orig": _f(r["n1000_hit_original"]),
            "n1000_hit_conv": _f(r["n1000_hit_converted"]),
        })
    for backend, cells in grid.items():
        deltas = [_f(r["n1000_hit_delta"]) for r in cells.values()]
        deltas = [d for d in deltas if d is not None]
        if len(deltas) >= 2:
            digest["protocol_spread"].append({
                "backend": backend,
                "min_delta": min(deltas), "max_delta": max(deltas),
                "spread": round(max(deltas) - min(deltas), 4),
            })
    (args.out_dir / "headline_digest.json").write_text(json.dumps(digest, indent=2))
    print(f"Wrote tables to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
