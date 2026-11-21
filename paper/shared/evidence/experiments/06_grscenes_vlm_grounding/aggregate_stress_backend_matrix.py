#!/usr/bin/env python3
"""Aggregate cross-backend x protocol-config grounding matrix.

Scans stress-set prediction JSONL files, reads each file's metadata sidecar
(backend, checkpoint, coordinate frame, response format, prompt type), scores
every file with the canonical scorer, and emits:

- backend_protocol_matrix.csv: one row per (backend, prompt_type,
  coordinate_frame, response_format) with original/converted answer accuracy,
  pixel-frame hit rate, normalized-1000 hit rate, pair hit agreement, both-hit
  count, and mean original/converted point displacement.
- multiview_consistency.json: per-target cross-view hit consistency under each
  material condition and view-set agreement changes induced by conversion.

This is the analysis layer for the backend/protocol reliability story: the
measurement interface (backend family, coordinate frame, response format)
changes the measured grounding stability under the same material intervention.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_grounding  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), text=True,
            stderr=subprocess.DEVNULL, timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _short_backend(checkpoint: str, backend: str) -> str:
    name = Path(str(checkpoint)).name or str(checkpoint)
    for token in ("unsloth-bnb-4bit", "releases"):
        name = name.replace(token, "")
    if "gemma" in name.lower():
        return "gemma4-E4B-it-4bit"
    return name


def _condition_of(row: dict[str, Any]) -> str | None:
    sample_id = str(row.get("sample_id") or "")
    for condition in ("original", "converted"):
        if sample_id.endswith(f".{condition}"):
            return condition
    version = row.get("version")
    return str(version) if version else None


def _summary_by_version(scored: dict[str, Any], version: str) -> dict[str, Any]:
    for entry in scored.get("summary", []):
        if entry.get("version") == version:
            return entry
    return {}


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


def _norm1000_hit(row: dict[str, Any]) -> bool | None:
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


def multiview_consistency(rows: list[dict[str, Any]], backend: str) -> dict[str, Any]:
    """Per-target cross-view hit consistency and conversion-induced changes."""
    by_target: dict[str, dict[str, dict[str, dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        condition = _condition_of(row)
        if condition not in {"original", "converted"}:
            continue
        sid = str(row.get("sample_id"))
        target_id, view, _ = sid.rsplit(".", 2)
        by_target[target_id][view][condition] = row

    targets = []
    for target_id, views in sorted(by_target.items()):
        if len(views) < 2:
            continue
        entry: dict[str, Any] = {"target_id": target_id, "n_views": len(views)}
        for condition in ("original", "converted"):
            hits = []
            for view in sorted(views):
                row = views[view].get(condition)
                if row is None:
                    continue
                hit = _norm1000_hit(row)
                if hit is not None:
                    hits.append(bool(hit))
            if hits:
                entry[f"{condition}_hit_views"] = sum(hits)
                entry[f"{condition}_scored_views"] = len(hits)
                entry[f"{condition}_all_views_agree"] = len(set(hits)) == 1
        if "original_hit_views" in entry and "converted_hit_views" in entry:
            entry["hit_view_count_delta"] = entry["converted_hit_views"] - entry["original_hit_views"]
            entry["view_set_changed_by_conversion"] = entry["hit_view_count_delta"] != 0
        targets.append(entry)

    multi = [t for t in targets if t.get("original_scored_views", 0) >= 2 and t.get("converted_scored_views", 0) >= 2]
    summary = {
        "backend": backend,
        "targets_with_multiple_scored_views": len(multi),
        "original_all_views_agree_rate": (
            round(sum(1 for t in multi if t.get("original_all_views_agree")) / len(multi), 4) if multi else None
        ),
        "converted_all_views_agree_rate": (
            round(sum(1 for t in multi if t.get("converted_all_views_agree")) / len(multi), 4) if multi else None
        ),
        "view_set_changed_by_conversion_count": sum(1 for t in multi if t.get("view_set_changed_by_conversion")),
        "targets": targets,
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-multiview", type=Path, required=True)
    args = parser.parse_args(argv)

    csv_rows: list[dict[str, Any]] = []
    multiview: list[dict[str, Any]] = []
    inputs = []
    for path in args.predictions:
        meta_path = path.with_suffix(path.suffix + ".metadata.json")
        meta = _load_json(meta_path) if meta_path.exists() else {}
        rows = _load_jsonl(path)
        if not rows:
            continue
        checkpoint = str(meta.get("model_checkpoint") or rows[0].get("model_checkpoint") or path.stem)
        backend = str(meta.get("backend") or (rows[0].get("prediction") or {}).get("backend") or "unknown")
        prompt = rows[0].get("prompt") or {}
        coord = str(meta.get("coordinate_frame") or prompt.get("coordinate_frame") or "unknown")
        fmt = str(meta.get("response_format") or prompt.get("response_format") or "unknown")
        ptype = str(meta.get("prompt_type") or prompt.get("type") or "s1_point")
        short = _short_backend(checkpoint, backend)

        scored = score_grounding.score(rows)
        original = _summary_by_version(scored, "original")
        converted = _summary_by_version(scored, "converted")
        pair = scored.get("pair_consistency") or {}

        csv_rows.append(
            {
                "backend": short,
                "backend_full": checkpoint,
                "prompt_type": ptype,
                "coordinate_frame": coord,
                "response_format": fmt,
                "n_records": len(rows),
                "answer_acc_original": original.get("answer_accuracy"),
                "answer_acc_converted": converted.get("answer_accuracy"),
                "px_hit_original": original.get("point_in_bbox_accuracy"),
                "px_hit_converted": converted.get("point_in_bbox_accuracy"),
                "n1000_hit_original": original.get("point_in_bbox_normalized_1000_accuracy"),
                "n1000_hit_converted": converted.get("point_in_bbox_normalized_1000_accuracy"),
                "n1000_hit_delta": (
                    round(converted["point_in_bbox_normalized_1000_accuracy"] - original["point_in_bbox_normalized_1000_accuracy"], 4)
                    if original.get("point_in_bbox_normalized_1000_accuracy") is not None
                    and converted.get("point_in_bbox_normalized_1000_accuracy") is not None
                    else None
                ),
                "hit_agreement_n1000": pair.get("normalized_1000_point_hit_agreement"),
                "both_hit_n1000": pair.get("normalized_1000_both_point_hit_count"),
                "mean_point_delta_px": (
                    round(pair["mean_prediction_point_delta_px"], 3)
                    if pair.get("mean_prediction_point_delta_px") is not None
                    else None
                ),
                "prediction_file": str(path),
            }
        )
        if ptype == "s1_point" and coord == "normalized_1000":
            multiview.append(multiview_consistency(rows, short))
        inputs.append({"path": str(path), "hash_sha256": _sha256_file(path)})

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(csv_rows[0].keys()) if csv_rows else []
    with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    doc = {
        "schema_version": 1,
        "status": "multiview_consistency",
        "claim_boundary": "diagnostic_multiview_analysis_over_frozen_stress_set",
        "generated_at_utc": _utc_now(),
        "inputs": inputs,
        "backends": multiview,
        "generator_provenance": {
            "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
            "git_commit": _git_commit(),
        },
    }
    args.out_multiview.parent.mkdir(parents=True, exist_ok=True)
    args.out_multiview.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_csv} rows={len(csv_rows)}")
    print(f"Wrote {args.out_multiview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
