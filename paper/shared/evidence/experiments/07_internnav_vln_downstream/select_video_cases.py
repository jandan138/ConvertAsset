#!/usr/bin/env python3
"""Select storage-bounded InternNav cases for paper video reruns."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


REQUIRED_METRIC_KEYS = ("TL", "NE", "OS", "SR", "SPL", "steps")
CASE_TYPE_PRIORITY = (
    "original_only_success",
    "modified_only_success",
    "both_failure_divergent",
    "both_success_divergent",
    "both_failure_neutral",
    "both_success_neutral",
)


def _condition_key(condition: str) -> str:
    if condition in {"modified", "converted", "nomdl", "no_mdl", "no-MDL"}:
        return "modified"
    return condition


def _pair_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    pairs: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        condition = _condition_key(str(row["condition"]))
        if condition in {"original", "modified"}:
            pairs[str(row["path_key"])][condition] = row
    return {
        path_key: condition_rows
        for path_key, condition_rows in pairs.items()
        if {"original", "modified"}.issubset(condition_rows)
    }


def _metric(row: dict[str, Any], key: str) -> float:
    metrics = row.get("metrics", {})
    if key not in metrics:
        raise KeyError(f"missing metric {key} for {row.get('condition')} {row.get('path_key')}")
    return float(metrics[key])


def _validate_row_metrics(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        metrics = row.get("metrics", {})
        missing = [metric for metric in REQUIRED_METRIC_KEYS if metric not in metrics]
        if missing:
            raise KeyError(
                f"missing metric {', '.join(missing)} for {row.get('condition')} {row.get('path_key')}"
            )


def _case_type(original: dict[str, Any], modified: dict[str, Any]) -> str:
    original_sr = _metric(original, "SR")
    modified_sr = _metric(modified, "SR")
    ne_delta = abs(_metric(modified, "NE") - _metric(original, "NE"))
    tl_delta = abs(_metric(modified, "TL") - _metric(original, "TL"))
    if original_sr > 0 and modified_sr <= 0:
        return "original_only_success"
    if modified_sr > 0 and original_sr <= 0:
        return "modified_only_success"
    if original_sr > 0 and modified_sr > 0:
        return "both_success_divergent" if ne_delta > 1.0 or tl_delta > 5.0 else "both_success_neutral"
    return "both_failure_divergent" if ne_delta > 5.0 or tl_delta > 10.0 else "both_failure_neutral"


def _score_case(original: dict[str, Any], modified: dict[str, Any]) -> float:
    return abs(_metric(modified, "NE") - _metric(original, "NE")) + 0.1 * abs(
        _metric(modified, "TL") - _metric(original, "TL")
    )


def select_video_cases(rows: list[dict[str, Any]], *, max_cases: int = 8) -> dict[str, Any]:
    if max_cases <= 0:
        raise ValueError("max_cases must be positive")
    _validate_row_metrics(rows)
    pairs = _pair_rows(rows)
    candidates = []
    for path_key, pair in pairs.items():
        original = pair["original"]
        modified = pair["modified"]
        candidates.append(
            {
                "path_key": path_key,
                "case_type": _case_type(original, modified),
                "divergence_score": round(_score_case(original, modified), 4),
                "rerun_profile": "video_selected_only",
                "recommended_config_overrides": {
                    "eval_settings.vis_output": True,
                    "agent.model_settings.vis_debug": False,
                },
                "metrics": {
                    "original": original.get("metrics", {}),
                    "modified": modified.get("metrics", {}),
                },
                "failure_reason": {
                    "original": original.get("failure_reason", "unknown"),
                    "modified": modified.get("failure_reason", "unknown"),
                },
            }
        )

    priority = {case_type: index for index, case_type in enumerate(CASE_TYPE_PRIORITY)}
    candidates.sort(key=lambda item: (priority.get(item["case_type"], 99), -item["divergence_score"], item["path_key"]))
    selected = []
    selected_keys = set()
    for case_type in CASE_TYPE_PRIORITY:
        if len(selected) >= max_cases:
            break
        matching = [item for item in candidates if item["case_type"] == case_type]
        if matching:
            selected.append(matching[0])
            selected_keys.add(matching[0]["path_key"])
    for item in candidates:
        if len(selected) >= max_cases:
            break
        if item["path_key"] in selected_keys:
            continue
        selected.append(item)
        selected_keys.add(item["path_key"])
    return {
        "schema_version": 1,
        "case_quota": {
            "max_cases": max_cases,
            "selected_count": len(selected),
            "candidate_count": len(candidates),
        },
        "storage_policy": {
            "metric_runs_keep_video_disabled": True,
            "rerun_only_selected_cases_with_video": True,
            "keep_compressed_mp4_not_raw_frames": True,
        },
        "selected_cases": selected,
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
    parser.add_argument("--max-cases", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    for path in args.input_jsonl:
        rows.extend(load_jsonl(path))
    manifest = select_video_cases(rows, max_cases=args.max_cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"selected_count": manifest["case_quota"]["selected_count"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
