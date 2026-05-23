#!/usr/bin/env python3
"""Analyze paired original-vs-modified InternNav episode metrics."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


METRIC_KEYS = ("TL", "NE", "OS", "SR", "SPL", "FR", "StR", "Count", "steps")
REQUIRED_ROW_METRIC_KEYS = ("TL", "NE", "OS", "SR", "SPL", "steps")
LOWER_IS_BETTER = {"TL", "NE", "steps"}


def _condition_key(condition: str) -> str:
    if condition in {"modified", "converted", "nomdl", "no_mdl", "no-MDL"}:
        return "modified"
    return condition


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _median(values: list[float]) -> float:
    return round(float(statistics.median(values)), 4) if values else 0.0


def _sample_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(statistics.stdev(values))


def _cohen_dz(deltas: list[float]) -> float:
    std = _sample_std(deltas)
    if std == 0.0:
        return 0.0
    return round((sum(deltas) / len(deltas)) / std, 4)


def _metric_value(row: dict[str, Any], metric: str) -> float:
    if metric == "Count":
        return 1.0
    if metric == "FR":
        return 1.0 if row.get("failure_reason") == "fall" else 0.0
    if metric == "StR":
        return 1.0 if row.get("failure_reason") == "stuck" else 0.0
    metrics = row.get("metrics", {})
    if metric not in metrics:
        raise KeyError(f"missing metric {metric} for {row.get('condition')} {row.get('path_key')}")
    return float(metrics[metric])


def _pair_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    pairs: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        condition = _condition_key(str(row["condition"]))
        if condition not in {"original", "modified"}:
            continue
        pairs[str(row["path_key"])][condition] = row
    return {
        path_key: condition_rows
        for path_key, condition_rows in pairs.items()
        if {"original", "modified"}.issubset(condition_rows)
    }


def _paired_outcome(metric: str, delta: float) -> str:
    if delta == 0:
        return "tie"
    if metric in LOWER_IS_BETTER:
        return "modified_better" if delta < 0 else "original_better"
    return "modified_better" if delta > 0 else "original_better"


def _validate_row_metrics(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        metrics = row.get("metrics", {})
        missing = [metric for metric in REQUIRED_ROW_METRIC_KEYS if metric not in metrics]
        if missing:
            raise KeyError(
                f"missing metric {', '.join(missing)} for {row.get('condition')} {row.get('path_key')}"
            )


def analyze_paired_rows(
    rows: list[dict[str, Any]],
    *,
    has_video_manifest: bool = False,
    has_aggregate_result_json: bool = False,
) -> dict[str, Any]:
    _validate_row_metrics(rows)
    pairs = _pair_rows(rows)
    metrics: dict[str, dict[str, Any]] = {}
    paired_outcomes: dict[str, dict[str, int]] = {}
    failure_pairs: Counter[str] = Counter()

    for path_key, condition_rows in pairs.items():
        original_failure = str(condition_rows["original"].get("failure_reason", "unknown"))
        modified_failure = str(condition_rows["modified"].get("failure_reason", "unknown"))
        failure_pairs[f"original_{original_failure}__modified_{modified_failure}"] += 1

    for metric in METRIC_KEYS:
        original_values = [_metric_value(pair["original"], metric) for pair in pairs.values()]
        modified_values = [_metric_value(pair["modified"], metric) for pair in pairs.values()]
        deltas = [modified - original for original, modified in zip(original_values, modified_values)]
        outcome_counts = Counter(_paired_outcome(metric, delta) for delta in deltas)
        metrics[metric] = {
            "n": len(deltas),
            "original_mean": _mean(original_values),
            "modified_mean": _mean(modified_values),
            "mean_delta_modified_minus_original": _mean(deltas),
            "median_delta_modified_minus_original": _median(deltas),
            "cohen_dz": _cohen_dz(deltas),
            "lower_is_better": metric in LOWER_IS_BETTER,
        }
        paired_outcomes[metric] = {
            "modified_better": outcome_counts.get("modified_better", 0),
            "original_better": outcome_counts.get("original_better", 0),
            "tie": outcome_counts.get("tie", 0),
        }

    episode_count = len(pairs)
    scene_count = len({path_key.split("_usd", 1)[0] + "_usd" for path_key in pairs if "_usd" in path_key})
    row_count_pilot_ready = episode_count >= 30 and scene_count >= 5
    row_count_acl_ready = episode_count >= 100 and scene_count >= 10
    has_failure_classification = bool(failure_pairs) if episode_count > 0 else False
    pilot_main_ready = (
        row_count_pilot_ready and has_failure_classification and has_video_manifest and has_aggregate_result_json
    )
    acl_main_result_ready = (
        row_count_acl_ready and has_failure_classification and has_video_manifest and has_aggregate_result_json
    )
    return {
        "schema_version": 1,
        "episode_count": episode_count,
        "scene_count": scene_count,
        "metrics": metrics,
        "paired_outcomes": paired_outcomes,
        "failure_pairs": dict(sorted(failure_pairs.items())),
        "claim_gate": {
            "has_paired_episode_metrics": episode_count > 0,
            "has_failure_classification": has_failure_classification,
            "has_video_manifest": has_video_manifest,
            "has_aggregate_result_json": has_aggregate_result_json,
            "row_count_pilot_ready": row_count_pilot_ready,
            "row_count_acl_ready": row_count_acl_ready,
            "pilot_main_ready": pilot_main_ready,
            "acl_main_result_ready": acl_main_result_ready,
        },
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--has-video-manifest", action="store_true")
    parser.add_argument("--has-aggregate-result-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    for path in args.input_jsonl:
        rows.extend(load_jsonl(path))
    summary = analyze_paired_rows(
        rows,
        has_video_manifest=args.has_video_manifest,
        has_aggregate_result_json=args.has_aggregate_result_json,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"episode_count": summary["episode_count"], "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
