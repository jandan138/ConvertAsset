#!/usr/bin/env python3
"""Paired bootstrap CIs for the canonical backend table.

For every backend's canonical (structured_text + normalized-1000, s1) run on
the frozen stress30 pool and the extended80 diagnostic pool, compute paired
bootstrap 95% CIs for:

- answer-accuracy delta (converted - original)
- normalized-1000 point-hit delta
- point displacement (px, converted vs original, per-pair mean CI)

Same bootstrap settings as the reviewer closure package (2000 rounds,
seed 20260525 equivalent structure). Output: canonical_paired_cis.csv/json.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BOOTSTRAP_ROUNDS = 2000
BOOTSTRAP_SEED = 20260913


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _percentile(sorted_values: list[float], q: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = q * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def bootstrap_mean_ci(values: list[float]) -> dict[str, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    means = sorted(_mean([values[rng.randrange(n)] for _ in range(n)]) for _ in range(BOOTSTRAP_ROUNDS))
    return {
        "mean": round(_mean(values), 4),
        "ci95_low": round(_percentile(means, 0.025), 4),
        "ci95_high": round(_percentile(means, 0.975), 4),
    }


def _finite_point(values: Any) -> tuple[float, float] | None:
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        return None
    try:
        point = (float(values[0]), float(values[1]))
    except (TypeError, ValueError):
        return None
    return point if all(math.isfinite(v) for v in point) else None


def _n1k_hit(row: dict[str, Any]) -> bool | None:
    point = _finite_point((row.get("prediction") or {}).get("point_xy"))
    bbox = (row.get("target") or {}).get("bbox_xyxy")
    image = row.get("image") or {}
    if point is None or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    try:
        width = float(image.get("width"))
        height = float(image.get("height"))
    except (TypeError, ValueError):
        return None
    x, y = point[0] * width / 1000.0, point[1] * height / 1000.0
    x1, y1, x2, y2 = (float(v) for v in bbox)
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    return left <= x <= right and top <= y <= bottom


def _answer_match(row: dict[str, Any]) -> bool | None:
    answer = (row.get("prediction") or {}).get("answer")
    expected = row.get("expected_answers") or (row.get("target") or {}).get("expected_answers")
    if answer is None or not expected:
        return None
    answer_norm = str(answer).strip().lower()
    return any(str(e).strip().lower() in answer_norm for e in expected if str(e).strip())


def _pair_key(sample_id: str) -> tuple[str, str] | None:
    for cond in ("original", "converted"):
        if sample_id.endswith(f".{cond}"):
            return sample_id[: -len(f".{cond}")], cond
    return None


def analyze(path: Path, backend: str, pool: str) -> dict[str, Any] | None:
    rows = _load_jsonl(path)
    pairs: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = _pair_key(str(row.get("sample_id") or ""))
        if not key:
            continue
        pair_id, cond = key
        pairs[pair_id][cond] = row
    ans_deltas: list[float] = []
    hit_deltas: list[float] = []
    disps: list[float] = []
    for sides in pairs.values():
        if "original" not in sides or "converted" not in sides:
            continue
        o, c = sides["original"], sides["converted"]
        oa, ca = _answer_match(o), _answer_match(c)
        if oa is not None and ca is not None:
            ans_deltas.append(float(ca) - float(oa))
        oh, ch = _n1k_hit(o), _n1k_hit(c)
        if oh is not None and ch is not None:
            hit_deltas.append(float(ch) - float(oh))
        po = _finite_point((o.get("prediction") or {}).get("point_xy"))
        pc = _finite_point((c.get("prediction") or {}).get("point_xy"))
        image = o.get("image") or {}
        if po and pc and image.get("width"):
            width, height = float(image["width"]), float(image["height"])
            disps.append(math.dist((po[0] * width / 1000, po[1] * height / 1000), (pc[0] * width / 1000, pc[1] * height / 1000)))
    if not pairs:
        return None
    result: dict[str, Any] = {
        "backend": backend,
        "pool": pool,
        "n_pairs": len(pairs),
        "n_hit_scored": len(hit_deltas),
        "n_answer_scored": len(ans_deltas),
    }
    if ans_deltas:
        ci = bootstrap_mean_ci(ans_deltas)
        result["answer_delta"] = ci
    if hit_deltas:
        ci = bootstrap_mean_ci(hit_deltas)
        result["n1000_hit_delta"] = ci
    if disps:
        ci = bootstrap_mean_ci(disps)
        result["point_displacement_px"] = ci
        result["median_displacement_px"] = round(sorted(disps)[len(disps) // 2], 3)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        action="append",
        nargs=3,
        metavar=("BACKEND", "POOL", "JSONL"),
        required=True,
    )
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()

    results = []
    for backend, pool, jsonl in args.run:
        r = analyze(Path(jsonl), backend, pool)
        if r:
            results.append(r)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "backend", "pool", "n_pairs",
        "answer_delta_mean", "answer_delta_ci95_low", "answer_delta_ci95_high",
        "n1000_hit_delta_mean", "n1000_hit_delta_ci95_low", "n1000_hit_delta_ci95_high",
        "disp_px_mean", "disp_px_ci95_low", "disp_px_ci95_high", "median_displacement_px",
    ]
    with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "backend": r["backend"],
                "pool": r["pool"],
                "n_pairs": r["n_pairs"],
                "answer_delta_mean": r.get("answer_delta", {}).get("mean"),
                "answer_delta_ci95_low": r.get("answer_delta", {}).get("ci95_low"),
                "answer_delta_ci95_high": r.get("answer_delta", {}).get("ci95_high"),
                "n1000_hit_delta_mean": r.get("n1000_hit_delta", {}).get("mean"),
                "n1000_hit_delta_ci95_low": r.get("n1000_hit_delta", {}).get("ci95_low"),
                "n1000_hit_delta_ci95_high": r.get("n1000_hit_delta", {}).get("ci95_high"),
                "disp_px_mean": r.get("point_displacement_px", {}).get("mean"),
                "disp_px_ci95_low": r.get("point_displacement_px", {}).get("ci95_low"),
                "disp_px_ci95_high": r.get("point_displacement_px", {}).get("ci95_high"),
                "median_displacement_px": r.get("median_displacement_px"),
            })
    doc = {
        "schema_version": 1,
        "status": "canonical_paired_cis",
        "claim_boundary": "paired_bootstrap_ci_descriptive",
        "bootstrap_rounds": BOOTSTRAP_ROUNDS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "generated_at_utc": _utc_now(),
        "results": results,
    }
    args.out_json.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_csv} rows={len(results)}")
    print(f"Wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
