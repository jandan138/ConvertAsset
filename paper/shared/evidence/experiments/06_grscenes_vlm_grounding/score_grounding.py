#!/usr/bin/env python3
"""Score GRScenes VLM grounding predictions.

The script is intentionally model-agnostic. It scores JSONL records produced by
any VLM runner as long as each record includes a target box and either a
predicted point or answer text.

Input JSONL record schema:
{
  "sample_id": "scene.target.view.prompt.version",
  "version": "original",
  "task": "s1_referred_object_localization",
  "target": {"bbox_xyxy": [10, 20, 200, 240], "category": "cabinet"},
  "prediction": {"point_xy": [80, 100], "answer": "cabinet"},
  "expected_answers": ["cabinet", "wooden cabinet"]
}
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
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


def _point_in_box(point: Any, box: Any) -> bool | None:
    if point is None or box is None:
        return None
    if len(point) != 2 or len(box) != 4:
        return None

    x, y = float(point[0]), float(point[1])
    x1, y1, x2, y2 = [float(v) for v in box]
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


def score(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    aggregates: dict[tuple[str, str], dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))

    for record in records:
        version = str(record.get("version", "unknown"))
        task = str(record.get("task", "unknown"))
        target = record.get("target") or {}
        prediction = record.get("prediction") or {}

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

    return {"schema_version": 1, "num_records": len(records), "summary": summary_rows, "records": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True, help="Input JSONL predictions file.")
    parser.add_argument("--out", type=Path, required=True, help="Output score summary JSON.")
    args = parser.parse_args()

    records = _load_jsonl(args.predictions)
    result = score(records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} with {len(records)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
