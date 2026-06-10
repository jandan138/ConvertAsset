#!/usr/bin/env python3
"""Generate table artifacts for the expanded30 GRScenes VLM frozen stress set."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
TABLE_DIR = PROJECT_ROOT / "paper/shared/tables"
DEFAULT_CSV = TABLE_DIR / "grscenes_vlm_stress_expanded30.csv"
DEFAULT_TEX = TABLE_DIR / "tab_grscenes_vlm_stress_expanded30.tex"


PROBES = [
    {
        "row_id": "gemma4_expanded30",
        "model": "Gemma4 local",
        "role": "canonical",
        "response_format": "structured_text",
        "coordinate_policy": "normalized-1000 primary; raw-pixel diagnostic",
        "score_path": RAW_DIR / "stress_score_summary.json",
        "claim_boundary": "frozen_expanded30_target_centered_stress_set",
    },
    {
        "row_id": "qwen25_expanded30",
        "model": "Qwen2.5-VL",
        "role": "diagnostic",
        "response_format": "structured_text",
        "coordinate_policy": "normalized-1000 primary; raw-pixel diagnostic",
        "score_path": RAW_DIR
        / "stress_expanded30_probes/qwen25_stress_expanded30_structured_score_summary.json",
        "claim_boundary": "second_model_diagnostic_under_expanded30_manifest",
    },
]

CSV_FIELDS = [
    "row_id",
    "model",
    "role",
    "response_format",
    "coordinate_policy",
    "pair_count",
    "answer_rows",
    "point_rows_original",
    "point_rows_converted",
    "answer_original",
    "answer_converted",
    "raw_point_original",
    "raw_point_converted",
    "norm1000_point_original",
    "norm1000_point_converted",
    "raw_pair_hit_agreement",
    "raw_both_hit_pairs",
    "norm1000_pair_hit_agreement",
    "norm1000_both_hit_pairs",
    "answer_pair_agreement",
    "claim_boundary",
    "source_score_summary",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_by_version(score: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("version")): row for row in score.get("summary", [])}


def _hit_ratio(numerator: int | None, denominator: int | None) -> str:
    if numerator is None or denominator is None or denominator == 0:
        return "--"
    return f"{numerator}/{denominator}"


def _metric_ratio(summary: dict[str, dict[str, Any]], version: str, n_key: str, accuracy_key: str) -> str:
    row = summary.get(version, {})
    denominator = row.get(n_key)
    accuracy = row.get(accuracy_key)
    if not isinstance(denominator, int) or denominator == 0 or accuracy is None:
        return "--"
    return _hit_ratio(round(float(accuracy) * denominator), denominator)


def _pair_ratio(pair: dict[str, Any], count_key: str, accuracy_key: str) -> str:
    denominator = pair.get(count_key)
    accuracy = pair.get(accuracy_key)
    if not isinstance(denominator, int) or denominator == 0 or accuracy is None:
        return "--"
    return _hit_ratio(round(float(accuracy) * denominator), denominator)


def _both_hit_ratio(pair: dict[str, Any], count_key: str, hit_key: str) -> str:
    denominator = pair.get(count_key)
    numerator = pair.get(hit_key)
    if not isinstance(denominator, int) or denominator == 0 or not isinstance(numerator, int):
        return "--"
    return _hit_ratio(numerator, denominator)


def _answer_rows(score: dict[str, Any]) -> str:
    total = score.get("num_records")
    if not isinstance(total, int) or total == 0:
        return "--"
    scored = sum(int(row.get("n_answer") or 0) for row in score.get("summary", []) if isinstance(row, dict))
    return _hit_ratio(scored, total)


def _version_record_count(score: dict[str, Any], version: str) -> int:
    records = score.get("records", [])
    count = sum(1 for record in records if isinstance(record, dict) and record.get("version") == version)
    if count:
        return count
    pair_count = score.get("pair_consistency", {}).get("pair_count")
    return int(pair_count) if isinstance(pair_count, int) else 0


def _scored_rows(summary: dict[str, dict[str, Any]], score: dict[str, Any], version: str, n_key: str) -> str:
    row = summary.get(version, {})
    scored = row.get(n_key)
    total = _version_record_count(score, version)
    if not isinstance(scored, int) or total == 0:
        return "--"
    return _hit_ratio(scored, total)


def _relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_rows(*, probes: list[dict[str, Any]] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for probe in probes or PROBES:
        score_path = Path(probe["score_path"])
        score = _load_json(score_path)
        summary = _summary_by_version(score)
        pair = score.get("pair_consistency", {})
        rows.append(
            {
                "row_id": str(probe["row_id"]),
                "model": str(probe["model"]),
                "role": str(probe["role"]),
                "response_format": str(probe["response_format"]),
                "coordinate_policy": str(probe["coordinate_policy"]),
                "pair_count": str(pair.get("pair_count", score.get("num_records", "--"))),
                "answer_rows": _answer_rows(score),
                "point_rows_original": _scored_rows(summary, score, "original", "n_point"),
                "point_rows_converted": _scored_rows(summary, score, "converted", "n_point"),
                "answer_original": _metric_ratio(summary, "original", "n_answer", "answer_accuracy"),
                "answer_converted": _metric_ratio(summary, "converted", "n_answer", "answer_accuracy"),
                "raw_point_original": _metric_ratio(summary, "original", "n_point", "point_in_bbox_accuracy"),
                "raw_point_converted": _metric_ratio(summary, "converted", "n_point", "point_in_bbox_accuracy"),
                "norm1000_point_original": _metric_ratio(
                    summary,
                    "original",
                    "n_point_normalized_1000",
                    "point_in_bbox_normalized_1000_accuracy",
                ),
                "norm1000_point_converted": _metric_ratio(
                    summary,
                    "converted",
                    "n_point_normalized_1000",
                    "point_in_bbox_normalized_1000_accuracy",
                ),
                "raw_pair_hit_agreement": _pair_ratio(pair, "point_pair_count", "point_hit_agreement"),
                "raw_both_hit_pairs": _both_hit_ratio(pair, "point_pair_count", "both_point_hit_count"),
                "norm1000_pair_hit_agreement": _pair_ratio(
                    pair,
                    "normalized_1000_point_pair_count",
                    "normalized_1000_point_hit_agreement",
                ),
                "norm1000_both_hit_pairs": _both_hit_ratio(
                    pair,
                    "normalized_1000_point_pair_count",
                    "normalized_1000_both_point_hit_count",
                ),
                "answer_pair_agreement": _pair_ratio(pair, "answer_pair_count", "answer_match_agreement"),
                "claim_boundary": str(probe["claim_boundary"]),
                "source_score_summary": _relative_or_absolute(score_path),
            }
        )
    return rows


def _latex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def _latex_pair(row: dict[str, str], prefix: str) -> str:
    return f"{row[f'{prefix}_original']} / {row[f'{prefix}_converted']}"


def render_latex(rows: list[dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            " & ".join(
                [
                    _latex_escape(row["model"]),
                    _latex_escape(row["role"]),
                    _latex_escape(row["answer_rows"]),
                    _latex_escape(_latex_pair(row, "answer")),
                    _latex_escape(_latex_pair(row, "raw_point")),
                    _latex_escape(_latex_pair(row, "norm1000_point")),
                    _latex_escape(row["norm1000_pair_hit_agreement"]),
                    _latex_escape(row["norm1000_both_hit_pairs"]),
                ]
            )
            + r" \\"
        )
    body_text = "\n".join(body)
    return rf"""\begin{{table*}}[t]
\centering
\caption{{Frozen 30-pair GRScenes material-shift stress set. Gemma4 is the canonical run; Qwen2.5-VL is a coordinate-format diagnostic under the same manifest. Values are O/C hit counts. Norm-1000 point hits are primary; raw point hits are diagnostic.}}
\label{{tab:grscenes_vlm_stress_expanded30}}
\scriptsize
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{lllccccc}}
\toprule
\textbf{{Model}} & \textbf{{Role}} & \textbf{{Answer rows}} & \textbf{{Answer O/C}} & \textbf{{Raw point O/C}} & \textbf{{Norm-1000 point O/C}} & \textbf{{Norm hit agree}} & \textbf{{Norm both-hit}} \\
\midrule
{body_text}
\bottomrule
\end{{tabular}}%
}}
\end{{table*}}
"""


def write_outputs(*, csv_path: Path = DEFAULT_CSV, tex_path: Path = DEFAULT_TEX) -> None:
    rows = build_rows()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(render_latex(rows), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    args = parser.parse_args(argv)
    write_outputs(csv_path=args.csv, tex_path=args.tex)
    print(f"Wrote {args.csv} and {args.tex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
