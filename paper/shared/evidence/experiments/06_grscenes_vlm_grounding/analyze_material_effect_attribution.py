#!/usr/bin/env python3
"""Attribute VLM grounding instability to material-effect bins.

Joins frozen stress-set VLM predictions with the material-effect sample
manifest and answers the mechanism question: which converted-material cue
moves the predicted point or flips the hit status?

For every prediction JSONL (one file per backend) and every pair in the
frozen expanded30 stress set, this computes:

- answer_changed: expected-answer match differs between original/converted
- point displacement in pixels between the two conditions (normalized-1000
  interpretation, projected back to image space)
- hit-status flip under the normalized-1000 scoring frame

Then each effect bin (clearcoat, opacity_transparency, emission,
procedural_texture, normal_bump, displacement_height) gets present-vs-absent
group stats: mean displacement, flip rate, and pair count.

Outputs:
- material_effect_attribution.csv       (one row per backend x pair)
- material_effect_attribution_summary.json (group stats per backend x effect)
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

PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
EFFECT_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/effect_sample_manifest.json"
)
EFFECT_BINS = [
    "clearcoat",
    "opacity_transparency",
    "emission",
    "procedural_texture",
    "normal_bump",
    "displacement_height",
]


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
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


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


def _norm1000_point_to_image(point: tuple[float, float], image: dict[str, Any]) -> tuple[float, float] | None:
    try:
        width = float(image.get("width"))
        height = float(image.get("height"))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
        return None
    x, y = point
    return (x * width / 1000.0, y * height / 1000.0)


def _point_in_box_norm1000(point: tuple[float, float] | None, image: dict[str, Any], bbox: Any) -> bool | None:
    """Hit test treating the predicted point as normalized-1000 coordinates."""
    if point is None or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    projected = _norm1000_point_to_image(point, image)
    if projected is None:
        return None
    try:
        x1, y1, x2, y2 = (float(v) for v in bbox)
    except (TypeError, ValueError):
        return None
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    x, y = projected
    return left <= x <= right and top <= y <= bottom


def _point_in_box_pixel(point: tuple[float, float] | None, bbox: Any) -> bool | None:
    """Hit test treating the predicted point as raw image pixels."""
    if point is None or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    try:
        x1, y1, x2, y2 = (float(v) for v in bbox)
    except (TypeError, ValueError):
        return None
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    x, y = point
    return left <= x <= right and top <= y <= bottom


def _answer_matches(answer: Any, expected: Any) -> bool | None:
    if answer is None or expected is None:
        return None
    answer_norm = str(answer).strip().lower()
    expected_values = expected if isinstance(expected, list) else [expected]
    expected_norm = [str(v).strip().lower() for v in expected_values]
    return any(value and value in answer_norm for value in expected_norm)


def _pair_key(sample_id: str, condition: str) -> str:
    suffix = f".{condition}"
    return sample_id[: -len(suffix)] if sample_id.endswith(suffix) else sample_id


def _condition_of(row: dict[str, Any]) -> str | None:
    sample_id = str(row.get("sample_id") or "")
    for condition in ("original", "converted"):
        if sample_id.endswith(f".{condition}"):
            return condition
    version = row.get("version")
    return str(version) if version else None


def analyze_backend(
    rows: list[dict[str, Any]],
    *,
    backend: str,
    effects_by_pair: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_pair: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        condition = _condition_of(row)
        if condition not in {"original", "converted"}:
            continue
        by_pair[_pair_key(str(row.get("sample_id")), condition)][condition] = row

    pair_rows: list[dict[str, Any]] = []
    flips = 0
    displacements: list[float] = []
    for pair_id in sorted(by_pair):
        sides = by_pair[pair_id]
        if "original" not in sides or "converted" not in sides:
            continue
        original, converted = sides["original"], sides["converted"]
        image = original.get("image") or {}
        target = original.get("target") or {}
        bbox = target.get("bbox_xyxy")
        expected = original.get("expected_answers") or (
            (original.get("target") or {}).get("expected_answers")
        )

        o_point = _finite_point((original.get("prediction") or {}).get("point_xy"))
        c_point = _finite_point((converted.get("prediction") or {}).get("point_xy"))

        o_hit = _point_in_box_norm1000(o_point, image, bbox)
        c_hit = _point_in_box_norm1000(c_point, image, bbox)
        o_hit_px = _point_in_box_pixel(o_point, bbox)
        c_hit_px = _point_in_box_pixel(c_point, bbox)

        o_ans = _answer_matches((original.get("prediction") or {}).get("answer"), expected)
        c_ans = _answer_matches((converted.get("prediction") or {}).get("answer"), expected)

        displacement_px = None
        if o_point is not None and c_point is not None:
            o_img = _norm1000_point_to_image(o_point, image)
            c_img = _norm1000_point_to_image(c_point, image)
            if o_img is not None and c_img is not None:
                displacement_px = math.dist(o_img, c_img)
                displacements.append(displacement_px)

        flip = None
        if o_hit is not None and c_hit is not None:
            flip = o_hit != c_hit
            if flip:
                flips += 1

        present = effects_by_pair.get(pair_id, [])
        pair_rows.append(
            {
                "backend": backend,
                "pair_id": pair_id,
                "target_category": target.get("category"),
                "effects_present": ";".join(present),
                "answer_original_hit": o_ans,
                "answer_converted_hit": c_ans,
                "answer_changed": (o_ans is not None and c_ans is not None and o_ans != c_ans),
                "point_hit_norm1000_original": o_hit,
                "point_hit_norm1000_converted": c_hit,
                "hit_flip_norm1000": flip,
                "point_hit_pixel_original": o_hit_px,
                "point_hit_pixel_converted": c_hit_px,
                "hit_flip_pixel": (o_hit_px is not None and c_hit_px is not None and o_hit_px != c_hit_px),
                "point_displacement_px": (round(displacement_px, 3) if displacement_px is not None else None),
            }
        )

    effect_summary: dict[str, Any] = {}
    for effect in EFFECT_BINS:
        with_effect = [r for r in pair_rows if effect in (r["effects_present"] or "").split(";")]
        without = [r for r in pair_rows if effect not in (r["effects_present"] or "").split(";")]

        def _stats(group: list[dict[str, Any]]) -> dict[str, Any]:
            disps = [r["point_displacement_px"] for r in group if r["point_displacement_px"] is not None]
            flips_g = [r["hit_flip_norm1000"] for r in group if r["hit_flip_norm1000"] is not None]
            ans_chg = [r["answer_changed"] for r in group]
            return {
                "pairs": len(group),
                "mean_displacement_px": (round(sum(disps) / len(disps), 3) if disps else None),
                "median_displacement_px": (round(sorted(disps)[len(disps) // 2], 3) if disps else None),
                "hit_flip_rate_norm1000": (round(sum(flips_g) / len(flips_g), 4) if flips_g else None),
                "answer_change_rate": (round(sum(ans_chg) / len(ans_chg), 4) if ans_chg else None),
            }

        effect_summary[effect] = {"present": _stats(with_effect), "absent": _stats(without)}

    summary = {
        "backend": backend,
        "pairs_scored": len(pair_rows),
        "overall": {
            "hit_flips_norm1000": flips,
            "mean_displacement_px": (
                round(sum(displacements) / len(displacements), 3) if displacements else None
            ),
        },
        "per_effect": effect_summary,
    }
    return pair_rows, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions",
        type=Path,
        nargs="+",
        required=True,
        help="Prediction JSONL files (one per backend).",
    )
    parser.add_argument("--effect-manifest", type=Path, default=EFFECT_MANIFEST)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-summary", type=Path, required=True)
    args = parser.parse_args(argv)

    effect_doc = _load_json(args.effect_manifest)
    effects_by_pair = {
        str(sample.get("pair_id")): list(sample.get("present_effects") or [])
        for sample in effect_doc.get("samples", [])
        if sample.get("pair_id")
    }

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    input_descriptors = []
    for predictions_path in args.predictions:
        rows = _load_jsonl(predictions_path)
        backend = rows[0].get("model_checkpoint") or predictions_path.stem if rows else predictions_path.stem
        backend_name = str(backend)
        pair_rows, summary = analyze_backend(rows, backend=backend_name, effects_by_pair=effects_by_pair)
        all_rows.extend(pair_rows)
        summaries.append(summary)
        input_descriptors.append(
            {
                "path": str(predictions_path),
                "hash_sha256": _sha256_file(predictions_path),
                "backend": backend_name,
                "rows": len(rows),
            }
        )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(all_rows[0].keys()) if all_rows else []
    with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    summary_doc = {
        "schema_version": 1,
        "status": "material_effect_attribution",
        "claim_boundary": "diagnostic_attribution_over_frozen_stress_set",
        "generated_at_utc": _utc_now(),
        "effect_manifest": {
            "path": str(args.effect_manifest),
            "hash_sha256": _sha256_file(args.effect_manifest),
        },
        "inputs": input_descriptors,
        "backends": summaries,
        "generator_provenance": {
            "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
            "git_commit": _git_commit(),
        },
    }
    args.out_summary.write_text(json.dumps(summary_doc, indent=2), encoding="utf-8")
    print(f"Wrote {args.out_csv} rows={len(all_rows)}")
    print(f"Wrote {args.out_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
