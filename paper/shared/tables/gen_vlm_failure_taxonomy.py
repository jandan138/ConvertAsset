#!/usr/bin/env python3
"""Generate a compact failure taxonomy table for GRScenes VLM pilot cases."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GROUNDING_RAW = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
TABLE_DIR = PROJECT_ROOT / "paper/shared/tables"
DEFAULT_CSV = TABLE_DIR / "grscenes_vlm_failure_taxonomy.csv"
DEFAULT_TEX = TABLE_DIR / "tab_grscenes_vlm_failure_taxonomy.tex"


CASE_SPECS = [
    {
        "row_id": "clean_gemma_faucet_norm_flip",
        "split": "clean",
        "model": "Gemma4",
        "pair_id": "c8ee4b66274b05d242c2.retake_008",
        "predictions": GROUNDING_RAW / "clean_pool_probes/gemma4_clean_pool_pass15_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "clean_pool_probes/gemma4_clean_pool_pass15_score_summary.json",
        "point_metric": "norm1000",
        "failure_type": "normalized_point_hit_flip",
        "note": "normalized point hit on original, miss on converted; answer stays correct",
    },
    {
        "row_id": "clean_qwen_bottle_raw_flip",
        "split": "clean",
        "model": "Qwen2.5-VL",
        "pair_id": "c27086f557d316584264.view_001",
        "predictions": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_score_summary.json",
        "point_metric": "raw_diagnostic",
        "failure_type": "raw_point_hit_flip",
        "note": "raw point hit on original, miss on converted; raw-image scoring diagnostic over normalized-1000-requested outputs",
    },
    {
        "row_id": "clean_qwen_clock_answer_flip",
        "split": "clean",
        "model": "Qwen2.5-VL",
        "pair_id": "1e397951c1926c7f0a0b.retake_009",
        "predictions": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_score_summary.json",
        "point_metric": "raw_diagnostic",
        "failure_type": "answer_flip",
        "note": "original answer is literal prompt text while converted answer matches target; raw-image scoring diagnostic over normalized-1000-requested outputs",
    },
    {
        "row_id": "clean_qwen_faucet_parse_truncation",
        "split": "clean",
        "model": "Qwen2.5-VL",
        "pair_id": "c8ee4b66274b05d242c2.retake_008",
        "predictions": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_score_summary.json",
        "point_metric": "raw_diagnostic",
        "failure_type": "parse_or_truncated_answer",
        "note": "original answer is unscorable and converted answer is truncated as fauc; raw-image scoring diagnostic over normalized-1000-requested outputs",
    },
    {
        "row_id": "zoom_qwen_picture_null_answer",
        "split": "zoom-stress",
        "model": "Qwen2.5-VL",
        "pair_id": "ef6a4fe9448f672c2ecc.zoom_017",
        "predictions": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_score_summary.json",
        "point_metric": "raw_diagnostic",
        "failure_type": "null_answer_and_point_flip",
        "note": "converted answer becomes null and raw point changes from hit to miss; raw-image scoring diagnostic over normalized-1000-requested outputs",
    },
    {
        "row_id": "zoom_qwen_faucet_answer_truncation",
        "split": "zoom-stress",
        "model": "Qwen2.5-VL",
        "pair_id": "c8ee4b66274b05d242c2.zoom_017",
        "predictions": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_score_summary.json",
        "point_metric": "raw_diagnostic",
        "failure_type": "material_shift_sensitive_answer_truncation",
        "note": "converted answer truncates faucet to fauc and raw point misses; raw-image scoring diagnostic over normalized-1000-requested outputs",
    },
    {
        "row_id": "zoom_qwen_clock_counterexample",
        "split": "zoom-stress",
        "model": "Qwen2.5-VL",
        "pair_id": "f35ef3d86c42446b7ddf.zoom_018",
        "predictions": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl",
        "score_summary": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_score_summary.json",
        "point_metric": "raw_diagnostic",
        "failure_type": "converted_raw_point_counterexample",
        "note": "raw point misses on original but hits on converted, so conversion is not uniformly worse; raw-image scoring diagnostic over normalized-1000-requested outputs",
    },
]


CSV_FIELDS = [
    "row_id",
    "split",
    "model",
    "pair_id",
    "target",
    "point_metric",
    "original_answer",
    "converted_answer",
    "original_status",
    "converted_status",
    "failure_type",
    "note",
    "source_predictions",
    "source_score_summary",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _score_records(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    return {record["sample_id"]: record for record in data.get("records", [])}


def _status(value: bool | None) -> str:
    if value is True:
        return "hit"
    if value is False:
        return "miss"
    return "n/a"


def _point_key(point_metric: str) -> str:
    if point_metric in {"raw", "raw_diagnostic"}:
        return "point_in_bbox"
    if point_metric == "norm1000":
        return "point_in_bbox_normalized_1000"
    raise ValueError(f"Unsupported point metric: {point_metric}")


def _load_pair(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    rows = [row for row in _read_jsonl(Path(spec["predictions"])) if row.get("pair_id") == spec["pair_id"]]
    by_version = {row.get("version"): row for row in rows}
    if set(by_version) != {"original", "converted"}:
        raise ValueError(f"Expected original and converted prediction rows for {spec['pair_id']}")
    scores = _score_records(Path(spec["score_summary"]))
    score_by_version = {}
    for version in ("original", "converted"):
        sample_id = by_version[version]["sample_id"]
        if sample_id not in scores:
            raise ValueError(f"Missing score record for selected sample: {sample_id}")
        score_by_version[version] = scores[sample_id]
    return by_version["original"], by_version["converted"], score_by_version


def _entry_status(score: dict[str, Any], point_metric: str) -> str:
    label = "raw" if point_metric == "raw_diagnostic" else point_metric
    return f"ans={_status(score.get('answer_match'))}; point={_status(score.get(_point_key(point_metric)))}({label})"


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in CASE_SPECS:
        original, converted, scores = _load_pair(spec)
        target = str(original["target"]["category"])
        point_metric = str(spec["point_metric"])
        rows.append(
            {
                "row_id": str(spec["row_id"]),
                "split": str(spec["split"]),
                "model": str(spec["model"]),
                "pair_id": str(spec["pair_id"]),
                "target": target,
                "point_metric": point_metric,
                "original_answer": str((original.get("prediction") or {}).get("answer") or "null"),
                "converted_answer": str((converted.get("prediction") or {}).get("answer") or "null"),
                "original_status": _entry_status(scores["original"], point_metric),
                "converted_status": _entry_status(scores["converted"], point_metric),
                "failure_type": str(spec["failure_type"]),
                "note": str(spec["note"]),
                "source_predictions": str(Path(spec["predictions"]).relative_to(PROJECT_ROOT)),
                "source_score_summary": str(Path(spec["score_summary"]).relative_to(PROJECT_ROOT)),
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


def render_latex(rows: list[dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            " & ".join(
                [
                    _latex_escape(row["split"]),
                    _latex_escape(row["model"]),
                    _latex_escape(row["target"]),
                    _latex_escape(row["original_status"]),
                    _latex_escape(row["converted_status"]),
                    _latex_escape(row["failure_type"]),
                    _latex_escape(row["note"]),
                ]
            )
            + r" \\"
        )
    body_text = "\n".join(body)
    return rf"""\begin{{table*}}[t]
\centering
\caption{{Selected GRScenes VLM pilot failure taxonomy. Rows are illustrative diagnostics sampled from checked prediction and score artifacts, not a final benchmark distribution. Point status uses the metric most relevant to the selected case; Qwen rows marked as raw use raw-image scoring diagnostic over normalized-1000-requested outputs because coordinate semantics remain unresolved.}}
\label{{tab:grscenes_vlm_failure_taxonomy}}
\scriptsize
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{llllllp{{0.28\textwidth}}}}
\toprule
\textbf{{Split}} & \textbf{{Model}} & \textbf{{Target}} & \textbf{{Original status}} & \textbf{{Converted status}} & \textbf{{Failure type}} & \textbf{{Note}} \\
\midrule
{body_text}
\bottomrule
\end{{tabular}}%
}}
\end{{table*}}
"""


def write_outputs(csv_path: Path = DEFAULT_CSV, tex_path: Path = DEFAULT_TEX) -> None:
    rows = build_rows()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tex_path.write_text(render_latex(rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    args = parser.parse_args()
    write_outputs(csv_path=args.csv, tex_path=args.tex)
    print(args.csv)
    print(args.tex)


if __name__ == "__main__":
    main()
