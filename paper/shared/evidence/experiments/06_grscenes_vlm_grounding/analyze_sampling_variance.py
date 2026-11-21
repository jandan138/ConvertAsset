#!/usr/bin/env python3
"""Measure sampling-decoding variance vs material-conversion displacement.

Runs the frozen stress set K times per backend at temperature>0 with fixed
seeds, then answers: how much of the predicted-point movement is plain
sampling jitter, and how much is attributable to the material intervention?

Per backend and pair/condition:
- seed point spread: mean pairwise distance between the K seed points (px).
- seed hit instability: hit status is not constant across the K seeds.
- conversion displacement under sampling: distance between seed-mean points
  of original vs converted, compared against the deterministic (t=0)
  displacement reported in the canonical runs.

Outputs sampling_variance_summary.json and sampling_variance_pairs.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _finite_point(values: Any) -> tuple[float, float] | None:
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        return None
    try:
        point = (float(values[0]), float(values[1]))
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(v) for v in point):
        return None
    return point


def _n1k_to_px(point: tuple[float, float], image: dict[str, Any]) -> tuple[float, float] | None:
    try:
        width = float(image.get("width"))
        height = float(image.get("height"))
    except (TypeError, ValueError):
        return None
    return (point[0] * width / 1000.0, point[1] * height / 1000.0)


def _n1k_hit(point: tuple[float, float] | None, image: dict[str, Any], bbox: Any) -> bool | None:
    if point is None or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    px = _n1k_to_px(point, image)
    if px is None:
        return None
    x1, y1, x2, y2 = (float(v) for v in bbox)
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    return left <= px[0] <= right and top <= px[1] <= bottom


def analyze_backend(seed_files: list[Path], backend: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # seed_files: K jsonl for the same backend, aligned by sample_id
    per_seed: list[dict[str, dict[str, Any]]] = []
    for path in seed_files:
        rows = _load_jsonl(path)
        per_seed.append({r["sample_id"]: r for r in rows})
    sample_ids = [sid for sid in per_seed[0] if all(sid in ps for ps in per_seed)]

    pair_rows: list[dict[str, Any]] = []
    spreads: list[float] = []
    unstable = 0
    for sid in sorted(sample_ids):
        points_px: list[tuple[float, float]] = []
        hits: list[bool] = []
        for ps in per_seed:
            row = ps[sid]
            point = _finite_point((row.get("prediction") or {}).get("point_xy"))
            image = row.get("image") or {}
            bbox = (row.get("target") or {}).get("bbox_xyxy")
            px = _n1k_to_px(point, image) if point else None
            hit = _n1k_hit(point, image, bbox)
            if px is not None:
                points_px.append(px)
            if hit is not None:
                hits.append(bool(hit))
        spread = None
        if len(points_px) >= 2:
            dists = [
                math.dist(a, b)
                for i, a in enumerate(points_px)
                for b in points_px[i + 1 :]
            ]
            spread = sum(dists) / len(dists)
            spreads.append(spread)
        hit_unstable = len(set(hits)) > 1 if hits else None
        if hit_unstable:
            unstable += 1
        pair, _, cond = sid.rpartition(".")
        pair_rows.append(
            {
                "backend": backend,
                "sample_id": sid,
                "pair_id": pair,
                "condition": cond,
                "n_seed_points": len(points_px),
                "seed_spread_px": round(spread, 3) if spread is not None else None,
                "seed_hit_unstable": hit_unstable,
            }
        )

    # conversion displacement under sampling: seed-mean original vs converted
    by_pair: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    for row in pair_rows:
        pass  # placeholder to keep structure clear
    for ps in per_seed:
        for sid, row in ps.items():
            point = _finite_point((row.get("prediction") or {}).get("point_xy"))
            image = row.get("image") or {}
            px = _n1k_to_px(point, image) if point else None
            if px is None:
                continue
            pair, _, cond = sid.rpartition(".")
            by_pair[pair][cond].append(px)
    conv_disps: list[float] = []
    for pair, sides in by_pair.items():
        if "original" not in sides or "converted" not in sides:
            continue
        if not sides["original"] or not sides["converted"]:
            continue
        mo = (
            sum(p[0] for p in sides["original"]) / len(sides["original"]),
            sum(p[1] for p in sides["original"]) / len(sides["original"]),
        )
        mc = (
            sum(p[0] for p in sides["converted"]) / len(sides["converted"]),
            sum(p[1] for p in sides["converted"]) / len(sides["converted"]),
        )
        conv_disps.append(math.dist(mo, mc))

    summary = {
        "backend": backend,
        "n_seeds": len(seed_files),
        "samples_scored": len(pair_rows),
        "mean_seed_spread_px": round(sum(spreads) / len(spreads), 3) if spreads else None,
        "seed_hit_instability_rate": round(unstable / len(pair_rows), 4) if pair_rows else None,
        "mean_conversion_displacement_under_sampling_px": (
            round(sum(conv_disps) / len(conv_disps), 3) if conv_disps else None
        ),
        "conversion_displacement_pairs": len(conv_disps),
    }
    return pair_rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend-seeds",
        action="append",
        nargs="+",
        metavar=("BACKEND", "JSONL"),
        help="Backend name followed by K seed prediction JSONL files.",
    )
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    args = parser.parse_args()

    all_rows: list[dict[str, Any]] = []
    summaries = []
    for group in args.backend_seeds:
        backend, seed_paths = group[0], [Path(p) for p in group[1:]]
        rows, summary = analyze_backend(seed_paths, backend)
        all_rows.extend(rows)
        summaries.append(summary)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    doc = {
        "schema_version": 1,
        "status": "sampling_variance",
        "claim_boundary": "diagnostic_sampling_variance_over_frozen_stress_set",
        "generated_at_utc": _utc_now(),
        "backends": summaries,
    }
    args.out_summary.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_csv} rows={len(all_rows)}")
    print(f"Wrote {args.out_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
