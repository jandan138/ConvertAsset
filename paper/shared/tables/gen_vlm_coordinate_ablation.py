#!/usr/bin/env python3
"""Generate raw-vs-normalized coordinate ablation for GRScenes VLM probes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GROUNDING_RAW = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
TABLE_DIR = PROJECT_ROOT / "paper/shared/tables"
DEFAULT_CSV = TABLE_DIR / "grscenes_vlm_coordinate_ablation.csv"
DEFAULT_TEX = TABLE_DIR / "tab_grscenes_vlm_coordinate_ablation.tex"


PROBES = [
    {
        "row_id": "clean_gemma4",
        "split": "clean",
        "model": "Gemma4",
        "score_summary": GROUNDING_RAW / "clean_pool_probes/gemma4_clean_pool_pass15_score_summary.json",
        "metadata": GROUNDING_RAW / "clean_pool_probes/gemma4_clean_pool_pass15_predictions.jsonl.metadata.json",
        "interpretation": "normalized-1000 scoring is the intended protocol",
    },
    {
        "row_id": "clean_qwen25",
        "split": "clean",
        "model": "Qwen2.5-VL",
        "score_summary": GROUNDING_RAW / "clean_pool_probes/qwen25_clean_pool_pass15_structured_score_summary.json",
        "metadata": GROUNDING_RAW
        / "clean_pool_probes/qwen25_clean_pool_pass15_structured_predictions.jsonl.metadata.json",
        "interpretation": "raw diagnostic scores higher; coordinate semantics unresolved",
    },
    {
        "row_id": "zoom_gemma4",
        "split": "zoom-stress",
        "model": "Gemma4",
        "score_summary": GROUNDING_RAW / "zoom_stress_probes/gemma4_zoom_stress_score_summary.json",
        "metadata": GROUNDING_RAW / "zoom_stress_probes/gemma4_zoom_stress_predictions.jsonl.metadata.json",
        "interpretation": "normalized-1000 scoring is the intended protocol",
    },
    {
        "row_id": "zoom_qwen25",
        "split": "zoom-stress",
        "model": "Qwen2.5-VL",
        "score_summary": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_score_summary.json",
        "metadata": GROUNDING_RAW / "zoom_stress_probes/qwen25_zoom_stress_structured_predictions.jsonl.metadata.json",
        "interpretation": "raw and normalized diagnostics disagree; coordinate semantics unresolved",
    },
]


CSV_FIELDS = [
    "row_id",
    "split",
    "model",
    "prompt_frame",
    "answer",
    "raw_point",
    "norm1000_point",
    "raw_pair",
    "norm1000_pair",
    "interpretation",
    "source_score_summary",
    "source_metadata",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_by_version(score: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("version")): row for row in score.get("summary", [])}


def _hit_ratio(accuracy: float | int | None, denominator: int | None) -> str:
    if accuracy is None or not isinstance(denominator, int) or denominator == 0:
        return "--"
    return f"{round(float(accuracy) * denominator)}/{denominator}"


def _metric(summary: dict[str, dict[str, Any]], version: str, n_key: str, accuracy_key: str) -> str:
    row = summary.get(version, {})
    return _hit_ratio(row.get(accuracy_key), row.get(n_key))


def _version_pair(summary: dict[str, dict[str, Any]], n_key: str, accuracy_key: str) -> str:
    return f"{_metric(summary, 'original', n_key, accuracy_key)} / {_metric(summary, 'converted', n_key, accuracy_key)}"


def _pair_summary(pair: dict[str, Any], count_key: str, agreement_key: str, both_hit_key: str) -> str:
    count = pair.get(count_key)
    agreement = _hit_ratio(pair.get(agreement_key), count)
    both = pair.get(both_hit_key)
    both_text = f"{both}/{count}" if isinstance(both, int) and isinstance(count, int) and count else "--"
    return f"{agreement} same; {both_text} both-hit"


def _prompt_frame(metadata: dict[str, Any]) -> str:
    coordinate_frame = metadata.get("coordinate_frame")
    if isinstance(coordinate_frame, str) and coordinate_frame:
        return coordinate_frame
    argv = metadata.get("argv") or []
    if "--coordinate-frame" in argv:
        idx = argv.index("--coordinate-frame")
        if idx + 1 < len(argv):
            return str(argv[idx + 1])
    return "unknown"


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for probe in PROBES:
        score_path = Path(probe["score_summary"])
        metadata_path = Path(probe["metadata"])
        score = _load_json(score_path)
        metadata = _load_json(metadata_path)
        summary = _summary_by_version(score)
        pair = score.get("pair_consistency", {})
        rows.append(
            {
                "row_id": str(probe["row_id"]),
                "split": str(probe["split"]),
                "model": str(probe["model"]),
                "prompt_frame": _prompt_frame(metadata),
                "answer": _version_pair(summary, "n_answer", "answer_accuracy"),
                "raw_point": _version_pair(summary, "n_point", "point_in_bbox_accuracy"),
                "norm1000_point": _version_pair(
                    summary,
                    "n_point_normalized_1000",
                    "point_in_bbox_normalized_1000_accuracy",
                ),
                "raw_pair": _pair_summary(pair, "point_pair_count", "point_hit_agreement", "both_point_hit_count"),
                "norm1000_pair": _pair_summary(
                    pair,
                    "normalized_1000_point_pair_count",
                    "normalized_1000_point_hit_agreement",
                    "normalized_1000_both_point_hit_count",
                ),
                "interpretation": str(probe["interpretation"]),
                "source_score_summary": str(score_path.relative_to(PROJECT_ROOT)),
                "source_metadata": str(metadata_path.relative_to(PROJECT_ROOT)),
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
                    _latex_escape(row["answer"]),
                    _latex_escape(row["raw_point"]),
                    _latex_escape(row["norm1000_point"]),
                    _latex_escape(row["raw_pair"]),
                    _latex_escape(row["norm1000_pair"]),
                    _latex_escape(row["interpretation"]),
                ]
            )
            + r" \\"
        )
    body_text = "\n".join(body)
    return rf"""\begin{{table*}}[t]
\centering
\caption{{Coordinate-frame ablation for GRScenes VLM pilot grounding. All rows were prompted for normalized-1000 coordinates; raw point columns are diagnostic rescoring in image-pixel space and are not the final benchmark metric. Values are original/converted hit counts unless marked as pair agreement.}}
\label{{tab:grscenes_vlm_coordinate_ablation}}
\scriptsize
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{lllccccp{{0.24\textwidth}}}}
\toprule
\textbf{{Split}} & \textbf{{Model}} & \textbf{{Answer O/C}} & \textbf{{Raw point O/C}} & \textbf{{Norm-1000 point O/C}} & \textbf{{Raw pair}} & \textbf{{Norm pair}} & \textbf{{Interpretation}} \\
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
