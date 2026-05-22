#!/usr/bin/env python3
"""Generate a projection-center scoring smoke baseline.

This is not a VLM runner. It writes deterministic predictions at each
projected target bbox center to validate the scoring pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_PROJECTION_REPORT = RAW_DIR / "target_projection_qa_report.json"
DEFAULT_OUTPUT = RAW_DIR / "projection_center_baseline_predictions.jsonl"
BACKEND = "projection_center_smoke_baseline"
MODEL_CHECKPOINT = "projection_center_smoke_baseline_no_vlm"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
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
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    return [line for line in output.splitlines() if line]


def _bbox_center(box: list[float]) -> list[float]:
    if len(box) != 4:
        raise ValueError("bbox_xyxy must have four values")
    x1, y1, x2, y2 = [float(value) for value in box]
    return [round((x1 + x2) * 0.5, 3), round((y1 + y2) * 0.5, 3)]


def build_prediction(record: dict[str, Any]) -> dict[str, Any]:
    target = dict(record.get("target") or {})
    category = str(target.get("category") or "")
    bbox = target.get("bbox_xyxy")
    if bbox is None:
        raise ValueError(f"record missing target.bbox_xyxy: {record.get('sample_id')}")
    out = dict(record)
    out["prediction"] = {
        "point_xy": _bbox_center(list(bbox)),
        "answer": category,
        "backend": BACKEND,
        "rationale": "Deterministic bbox-center scorer smoke baseline; not a VLM prediction.",
    }
    out["model_checkpoint"] = MODEL_CHECKPOINT
    return out


def build_predictions(projection_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [build_prediction(record) for record in projection_report.get("scoring_records", [])]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-report", type=Path, default=DEFAULT_PROJECTION_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    projection_report = _load_json(args.projection_report)
    predictions = build_predictions(projection_report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for prediction in predictions:
            handle.write(json.dumps(prediction, sort_keys=True) + "\n")
    metadata = {
        "schema_version": 1,
        "status": "projection_center_baseline_predictions",
        "prediction_count": len(predictions),
        "backend": BACKEND,
        "model_checkpoint": MODEL_CHECKPOINT,
        "claim_boundary": "scoring_smoke_only_not_vlm_evidence",
        "generated_at_utc": _utc_now(),
        "projection_report": {
            "path": str(args.projection_report),
            "hash_sha256": _sha256_file(args.projection_report),
        },
        "output_jsonl": {
            "path": str(args.out),
            "hash_sha256": _sha256_file(args.out),
        },
        "generator_provenance": {
            "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
            "script_path": str(Path(__file__).resolve()),
            "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
            "git_commit": _git_commit(),
            "git_status_porcelain": _git_status_porcelain(),
        },
    }
    metadata_path = args.out.with_suffix(args.out.suffix + ".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} predictions={len(predictions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
