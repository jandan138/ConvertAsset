#!/usr/bin/env python3
"""Score GRScenes VLM grounding predictions.

The script is intentionally model-agnostic. It scores JSONL records produced by
any VLM runner as long as each record includes a target box and either a
predicted point or answer text.

Input JSONL record schema:
{
  "sample_id": "scene.target.view.prompt.version",
  "pair_id": "scene.target.view.prompt",
  "version": "original",
  "task": "s1_referred_object_localization",
  "target": {"bbox_xyxy": [10, 20, 200, 240], "category": "cabinet"},
  "prediction": {
    "point_xy": [80, 100],
    "answer": "cabinet",
    "backend": "qwen2_5_vl_local_hf"
  },
  "expected_answers": ["cabinet", "wooden cabinet"],
  "model_checkpoint": "/path/to/model-or-api-model-name"
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSONL record: {exc}") from exc
    return records


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_project_root()),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=str(_project_root()),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    return [line for line in output.splitlines() if line]


def _finite_float_list(values: Any, expected_len: int) -> list[float] | None:
    if values is None or isinstance(values, (str, bytes)):
        return None
    if not isinstance(values, Sequence):
        return None
    try:
        if len(values) != expected_len:
            return None
        floats = [float(value) for value in values]
    except (TypeError, ValueError):
        return None
    if any(not math.isfinite(value) for value in floats):
        return None
    return floats


def _point_in_box(point: Any, box: Any) -> bool | None:
    point_values = _finite_float_list(point, 2)
    box_values = _finite_float_list(box, 4)
    if point_values is None or box_values is None:
        return None

    x, y = point_values
    x1, y1, x2, y2 = box_values
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    return left <= x <= right and top <= y <= bottom


def _answer_matches(answer: Any, expected: Any) -> bool | None:
    if answer is None or expected is None:
        return None

    answer_norm = str(answer).strip().lower()
    expected_values = expected if isinstance(expected, list) else [expected]
    expected_norm = [str(v).strip().lower() for v in expected_values]
    return any(value and value in answer_norm for value in expected_norm)


def _mean(values: list[bool]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def _float_pair(values: Any) -> tuple[float, float] | None:
    pair = _finite_float_list(values, 2)
    if pair is None:
        return None
    return pair[0], pair[1]


def _mean_float(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _pair_consistency(rows: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    duplicate_pair_version_count = 0
    for record, row in zip(records, rows):
        pair_id = record.get("pair_id")
        task = str(record.get("task", "unknown"))
        version = record.get("version")
        if not pair_id or version not in {"original", "converted"}:
            continue
        pair_key = (str(pair_id), task)
        version_key = str(version)
        if version_key in grouped[pair_key]:
            duplicate_pair_version_count += 1
            continue
        grouped[pair_key][version_key] = {"record": record, "row": row}

    comparable = [item for item in grouped.values() if "original" in item and "converted" in item]
    point_agreements: list[bool] = []
    answer_agreements: list[bool] = []
    both_point_hit_count = 0
    point_deltas: list[float] = []
    for item in comparable:
        original = item["original"]
        converted = item["converted"]
        original_point_hit = original["row"].get("point_in_bbox")
        converted_point_hit = converted["row"].get("point_in_bbox")
        if original_point_hit is not None and converted_point_hit is not None:
            point_agreements.append(bool(original_point_hit) == bool(converted_point_hit))
            if original_point_hit and converted_point_hit:
                both_point_hit_count += 1
        original_answer_hit = original["row"].get("answer_match")
        converted_answer_hit = converted["row"].get("answer_match")
        if original_answer_hit is not None and converted_answer_hit is not None:
            answer_agreements.append(bool(original_answer_hit) == bool(converted_answer_hit))
        original_point = _float_pair(_prediction_dict(original["record"]).get("point_xy"))
        converted_point = _float_pair(_prediction_dict(converted["record"]).get("point_xy"))
        if original_point is not None and converted_point is not None:
            point_deltas.append(math.dist(original_point, converted_point))

    mean_delta = _mean_float(point_deltas)
    return {
        "pair_count": len(comparable),
        "point_pair_count": len(point_agreements),
        "point_hit_agreement": _mean(point_agreements),
        "both_point_hit_count": both_point_hit_count,
        "mean_prediction_point_delta_px": round(mean_delta, 6) if mean_delta is not None else None,
        "answer_pair_count": len(answer_agreements),
        "answer_match_agreement": _mean(answer_agreements),
        "duplicate_pair_version_count": duplicate_pair_version_count,
    }


def _prediction_backends(records: list[dict[str, Any]]) -> list[str]:
    backends = []
    for record in records:
        prediction = _prediction_dict(record)
        backends.append(str(prediction.get("backend") or "unknown"))
    return sorted(set(backends))


def _prediction_dict(record: dict[str, Any]) -> dict[str, Any]:
    prediction = record.get("prediction")
    return prediction if isinstance(prediction, dict) else {}


def _model_checkpoints(records: list[dict[str, Any]]) -> list[str]:
    checkpoints = [str(record.get("model_checkpoint") or "unknown") for record in records]
    return sorted(set(checkpoints))


def _claim_boundary(backends: list[str]) -> str:
    if backends == ["projection_center_smoke_baseline"]:
        return "scoring_smoke_only_not_vlm_evidence"
    if "projection_center_smoke_baseline" in backends:
        return "mixed_projection_baseline_and_model_predictions_not_claimable"
    return "model_prediction_scores_require_model_provenance_review"


def score(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    aggregates: dict[tuple[str, str], dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))

    for record in records:
        version = str(record.get("version", "unknown"))
        task = str(record.get("task", "unknown"))
        target_raw = record.get("target")
        prediction_raw = record.get("prediction")
        target = target_raw if isinstance(target_raw, dict) else {}
        prediction = prediction_raw if isinstance(prediction_raw, dict) else {}

        point_hit = _point_in_box(prediction.get("point_xy"), target.get("bbox_xyxy"))
        answer_hit = _answer_matches(prediction.get("answer"), record.get("expected_answers"))
        row = {
            "sample_id": record.get("sample_id"),
            "version": version,
            "task": task,
            "point_in_bbox": point_hit,
            "answer_match": answer_hit,
        }
        rows.append(row)

        bucket = aggregates[(version, task)]
        if point_hit is not None:
            bucket["point_in_bbox"].append(point_hit)
        if answer_hit is not None:
            bucket["answer_match"].append(answer_hit)

    summary_rows = []
    for (version, task), metrics in sorted(aggregates.items()):
        summary_rows.append(
            {
                "version": version,
                "task": task,
                "n_point": len(metrics["point_in_bbox"]),
                "point_in_bbox_accuracy": _mean(metrics["point_in_bbox"]),
                "n_answer": len(metrics["answer_match"]),
                "answer_accuracy": _mean(metrics["answer_match"]),
            }
        )

    backends = _prediction_backends(records)
    return {
        "schema_version": 2,
        "num_records": len(records),
        "prediction_backends": backends,
        "model_checkpoints": _model_checkpoints(records),
        "claim_boundary": _claim_boundary(backends),
        "summary": summary_rows,
        "pair_consistency": _pair_consistency(rows, records),
        "records": rows,
    }


def _score_provenance(predictions_path: Path, argv: list[str] | None) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "generated_at_utc": _utc_now(),
        "command": [sys.executable, str(script_path), *(argv if argv is not None else sys.argv[1:])],
        "input_predictions": {
            "path": str(predictions_path),
            "hash_sha256": _sha256_file(predictions_path),
        },
        "scorer": {
            "script_path": str(script_path),
            "script_hash_sha256": _sha256_file(script_path),
        },
        "git": {
            "commit": _git_commit(),
            "status_porcelain": _git_status_porcelain(),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True, help="Input JSONL predictions file.")
    parser.add_argument("--out", type=Path, required=True, help="Output score summary JSON.")
    args = parser.parse_args(argv)

    records = _load_jsonl(args.predictions)
    result = score(records)
    result["score_provenance"] = _score_provenance(args.predictions, argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {args.out} with {len(records)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
