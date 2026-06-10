#!/usr/bin/env python3
"""Build the reviewer-closure statistics, baselines, and recommender package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from importlib import util as importlib_util
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_ROOT = PROJECT_ROOT / "paper/shared/evidence/raw"
OUT_RAW = RAW_ROOT / "reviewer_closure_package"
TABLE_ROOT = PROJECT_ROOT / "paper/shared/tables"

GRSCENES_RAW = RAW_ROOT / "grscene_vlm_grounding"
INTERNNAV_RAW = RAW_ROOT / "internnav_vln_downstream/official_val_unseen_99"
MATERIAL_RAW = RAW_ROOT / "material_effect_baseline"

DEFAULT_GEMMA_STRESS_SCORE = GRSCENES_RAW / "stress_score_summary.json"
DEFAULT_QWEN_STRESS_SCORE = (
    GRSCENES_RAW / "stress_expanded30_probes/qwen25_stress_expanded30_structured_score_summary.json"
)
DEFAULT_STRESS_MANIFEST = GRSCENES_RAW / "stress_vlm_run_manifest_expanded30.json"
DEFAULT_INTERNNAV_TRANSITIONS = INTERNNAV_RAW / "paired_episode_transitions.json"
DEFAULT_MATERIAL_RISK_PROFILE = MATERIAL_RAW / "material_effect_risk_profile.json"

DEFAULT_STAT_JSON = OUT_RAW / "reviewer_closure_statistical_summary.json"
DEFAULT_BASELINE_JSON = OUT_RAW / "vlm_coordinate_baseline_summary.json"
DEFAULT_RECOMMENDER_JSON = OUT_RAW / "material_safe_conversion_recommender.json"

DEFAULT_STAT_CSV = TABLE_ROOT / "reviewer_closure_paired_ci.csv"
DEFAULT_STAT_TEX = TABLE_ROOT / "tab_reviewer_closure_paired_ci.tex"
DEFAULT_BASELINE_CSV = TABLE_ROOT / "vlm_coordinate_baselines.csv"
DEFAULT_BASELINE_TEX = TABLE_ROOT / "tab_vlm_coordinate_baselines.tex"
DEFAULT_RECOMMENDER_CSV = TABLE_ROOT / "material_safe_conversion_recommender.csv"
DEFAULT_RECOMMENDER_TEX = TABLE_ROOT / "tab_material_safe_conversion_recommender.tex"

BOOTSTRAP_SEED = 20260526
BOOTSTRAP_ROUNDS = 10000

STAT_CSV_FIELDS = [
    "dataset",
    "evidence_id",
    "metric_id",
    "metric",
    "n",
    "original_mean",
    "converted_mean",
    "mean_delta_converted_minus_original",
    "ci95_low",
    "ci95_high",
    "direction",
    "claim_boundary",
]

BASELINE_CSV_FIELDS = [
    "baseline_id",
    "point_policy",
    "coordinate_space",
    "n_records",
    "raw_point_original",
    "raw_point_converted",
    "norm1000_point_original",
    "norm1000_point_converted",
    "raw_pair_agreement",
    "norm1000_pair_agreement",
    "claim_boundary",
]

RECOMMENDER_CSV_FIELDS = [
    "effect",
    "sample_source",
    "risk_level",
    "convertasset_action",
    "nvidia_action",
    "review_gate",
    "paper_claim_use",
    "evidence_status",
]

VLM_METRICS = [
    ("answer_accuracy", "Answer accuracy", "answer_match"),
    ("norm1000_point", "Norm-1000 point hit", "point_in_bbox_normalized_1000"),
    ("raw_point", "Raw point diagnostic", "point_in_bbox"),
]

INTERNNAV_METRICS = [
    ("SR", "Success rate", False),
    ("SPL", "SPL", False),
    ("OS", "Oracle success", False),
    ("NE", "Navigation error", True),
    ("TL", "Trajectory length", True),
]


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
        tracked_output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        untracked_output = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    lines = [line for line in tracked_output.splitlines() if line]
    untracked_count = len([line for line in untracked_output.splitlines() if line])
    if untracked_count:
        lines.append(f"?? {untracked_count} untracked files omitted from provenance")
    return lines


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _round(value: float | int | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot compute mean of empty list")
    return sum(values) / len(values)


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("cannot compute percentile of empty list")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = q * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def bootstrap_mean_ci(
    values: list[float], *, rounds: int = BOOTSTRAP_ROUNDS, seed: int = BOOTSTRAP_SEED
) -> dict[str, float]:
    if not values:
        raise ValueError("bootstrap requires at least one value")
    means: list[float] = []
    rng = random.Random(seed)
    n = len(values)
    for _ in range(rounds):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(_mean(sample))
    means.sort()
    return {
        "mean": _round(_mean(values)),
        "ci95_low": _round(_percentile(means, 0.025)),
        "ci95_high": _round(_percentile(means, 0.975)),
    }


def _bool_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return None


def _pair_id_from_sample(sample_id: Any, version: str) -> str | None:
    if not isinstance(sample_id, str) or not sample_id:
        return None
    suffix = f".{version}"
    if sample_id.endswith(suffix):
        return sample_id[: -len(suffix)]
    return sample_id.rsplit(".", 1)[0] if "." in sample_id else sample_id


def _paired_records(records: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        version = str(record.get("version"))
        if version not in {"original", "converted"}:
            continue
        pair_id = _pair_id_from_sample(record.get("sample_id"), version)
        if not pair_id:
            continue
        grouped.setdefault(pair_id, {})[version] = record
    return [
        (versions["original"], versions["converted"])
        for _, versions in sorted(grouped.items())
        if "original" in versions and "converted" in versions
    ]


def _direction(mean_delta: float, *, converted_name: str = "converted") -> str:
    if mean_delta > 0:
        return f"{converted_name} higher"
    if mean_delta < 0:
        return f"{converted_name} lower"
    return "tie"


def build_vlm_stat_rows(score: dict[str, Any], *, evidence_id: str, model: str) -> list[dict[str, Any]]:
    paired = _paired_records([record for record in score.get("records", []) if isinstance(record, dict)])
    rows: list[dict[str, Any]] = []
    for metric_id, metric_label, field in VLM_METRICS:
        original_values: list[float] = []
        converted_values: list[float] = []
        deltas: list[float] = []
        for original, converted in paired:
            original_value = _bool_value(original.get(field))
            converted_value = _bool_value(converted.get(field))
            if original_value is None or converted_value is None:
                continue
            original_values.append(original_value)
            converted_values.append(converted_value)
            deltas.append(converted_value - original_value)
        if not deltas:
            continue
        ci = bootstrap_mean_ci(deltas)
        rows.append(
            {
                "dataset": "GRScenes VLM expanded30",
                "evidence_id": evidence_id,
                "metric_id": metric_id,
                "metric": f"{model} {metric_label}",
                "n": len(deltas),
                "original_mean": _round(_mean(original_values)),
                "converted_mean": _round(_mean(converted_values)),
                "mean_delta_converted_minus_original": ci["mean"],
                "ci95_low": ci["ci95_low"],
                "ci95_high": ci["ci95_high"],
                "direction": _direction(ci["mean"]),
                "claim_boundary": "paired_bootstrap_ci_descriptive",
            }
        )
    return rows


def build_internnav_stat_rows(transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric_id, metric_label, lower_is_better in INTERNNAV_METRICS:
        original_key = f"original_{metric_id}"
        converted_key = f"nomdl_{metric_id}"
        delta_key = f"delta_{metric_id}_nomdl_minus_original"
        original_values: list[float] = []
        converted_values: list[float] = []
        deltas: list[float] = []
        for row in transitions:
            try:
                original = float(row[original_key])
                converted = float(row[converted_key])
                delta = float(row[delta_key])
            except (KeyError, TypeError, ValueError):
                continue
            original_values.append(original)
            converted_values.append(converted)
            deltas.append(delta)
        if not deltas:
            continue
        ci = bootstrap_mean_ci(deltas)
        direction = _direction(ci["mean"], converted_name="noMDL")
        if lower_is_better and ci["mean"] < 0:
            direction = "noMDL lower"
        rows.append(
            {
                "dataset": "Official KuJiaLe InternNav val-unseen",
                "evidence_id": "internnav_official_val_unseen_99",
                "metric_id": metric_id,
                "metric": metric_label,
                "n": len(deltas),
                "original_mean": _round(_mean(original_values)),
                "converted_mean": _round(_mean(converted_values)),
                "mean_delta_converted_minus_original": ci["mean"],
                "ci95_low": ci["ci95_low"],
                "ci95_high": ci["ci95_high"],
                "direction": direction,
                "claim_boundary": "paired_bootstrap_ci_descriptive_official_sanity",
            }
        )
    return rows


def _load_score_module():
    script = PROJECT_ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py"
    spec = importlib_util.spec_from_file_location("score_grounding_for_reviewer_closure", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer: {script}")
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bbox_center(box: list[float]) -> list[float]:
    x1, y1, x2, y2 = [float(value) for value in box]
    return [round((x1 + x2) * 0.5, 3), round((y1 + y2) * 0.5, 3)]


def _image_size(record: dict[str, Any]) -> tuple[float, float]:
    image = record.get("image") if isinstance(record.get("image"), dict) else {}
    width = float(image.get("width"))
    height = float(image.get("height"))
    return width, height


def _baseline_point(record: dict[str, Any], baseline_id: str) -> list[float]:
    width, height = _image_size(record)
    target = record.get("target") if isinstance(record.get("target"), dict) else {}
    bbox = [float(value) for value in target.get("bbox_xyxy")]
    if baseline_id == "image_center_pixel":
        return [round(width * 0.5, 3), round(height * 0.5, 3)]
    if baseline_id == "bbox_center_pixel":
        return _bbox_center(bbox)
    if baseline_id == "bbox_center_normalized_1000":
        cx, cy = _bbox_center(bbox)
        return [round(cx * 1000.0 / width, 3), round(cy * 1000.0 / height, 3)]
    if baseline_id == "random_seeded_pixel":
        digest = hashlib.sha256(str(record.get("sample_id")).encode("utf-8")).hexdigest()
        rng = random.Random(int(digest[:16], 16))
        return [round(rng.random() * (width - 1), 3), round(rng.random() * (height - 1), 3)]
    raise ValueError(f"unknown coordinate baseline: {baseline_id}")


BASELINE_DEFS = [
    {
        "baseline_id": "random_seeded_pixel",
        "point_policy": "deterministic hash-seeded random in image bounds",
        "coordinate_space": "pixel",
    },
    {
        "baseline_id": "image_center_pixel",
        "point_policy": "image center, no target information",
        "coordinate_space": "pixel",
    },
    {
        "baseline_id": "bbox_center_pixel",
        "point_policy": "oracle projected bbox center in pixel coordinates",
        "coordinate_space": "pixel",
    },
    {
        "baseline_id": "bbox_center_normalized_1000",
        "point_policy": "oracle projected bbox center in normalized-1000 coordinates",
        "coordinate_space": "normalized_1000",
    },
]


def _build_baseline_predictions(records: list[dict[str, Any]], baseline_id: str) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for record in records:
        out = dict(record)
        out["prediction"] = {
            "point_xy": _baseline_point(record, baseline_id),
            "backend": baseline_id,
            "rationale": "Deterministic coordinate-only baseline; not a VLM prediction.",
        }
        out["model_checkpoint"] = f"{baseline_id}_no_vlm"
        predictions.append(out)
    return predictions


def _summary_by_version(score: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("version")): row for row in score.get("summary", [])}


def _hit_ratio(row: dict[str, Any], n_key: str, accuracy_key: str) -> str:
    n = row.get(n_key)
    accuracy = row.get(accuracy_key)
    if not isinstance(n, int) or n == 0 or accuracy is None:
        return "--"
    return f"{round(float(accuracy) * n)}/{n}"


def _pair_ratio(pair: dict[str, Any], n_key: str, accuracy_key: str) -> str:
    n = pair.get(n_key)
    accuracy = pair.get(accuracy_key)
    if not isinstance(n, int) or n == 0 or accuracy is None:
        return "--"
    return f"{round(float(accuracy) * n)}/{n}"


def _baseline_row(defn: dict[str, str], score: dict[str, Any]) -> dict[str, str]:
    summary = _summary_by_version(score)
    pair = score.get("pair_consistency", {})
    return {
        "baseline_id": defn["baseline_id"],
        "point_policy": defn["point_policy"],
        "coordinate_space": defn["coordinate_space"],
        "n_records": str(score.get("num_records", "--")),
        "raw_point_original": _hit_ratio(summary.get("original", {}), "n_point", "point_in_bbox_accuracy"),
        "raw_point_converted": _hit_ratio(summary.get("converted", {}), "n_point", "point_in_bbox_accuracy"),
        "norm1000_point_original": _hit_ratio(
            summary.get("original", {}),
            "n_point_normalized_1000",
            "point_in_bbox_normalized_1000_accuracy",
        ),
        "norm1000_point_converted": _hit_ratio(
            summary.get("converted", {}),
            "n_point_normalized_1000",
            "point_in_bbox_normalized_1000_accuracy",
        ),
        "raw_pair_agreement": _pair_ratio(pair, "point_pair_count", "point_hit_agreement"),
        "norm1000_pair_agreement": _pair_ratio(
            pair,
            "normalized_1000_point_pair_count",
            "normalized_1000_point_hit_agreement",
        ),
        "claim_boundary": "coordinate_only_baseline_not_vlm_evidence",
    }


def build_coordinate_baseline_package(
    projection_report: dict[str, Any],
) -> tuple[list[dict[str, str]], dict[str, dict[str, Any]]]:
    score_module = _load_score_module()
    scoring_records = [
        record for record in projection_report.get("scoring_records", []) if isinstance(record, dict)
    ]
    rows: list[dict[str, str]] = []
    artifacts: dict[str, dict[str, Any]] = {}
    for defn in BASELINE_DEFS:
        baseline_id = defn["baseline_id"]
        predictions = _build_baseline_predictions(scoring_records, baseline_id)
        score = score_module.score(predictions)
        rows.append(_baseline_row(defn, score))
        artifacts[baseline_id] = {"predictions": predictions, "score_summary": score}
    return rows, artifacts


def build_safe_conversion_recommender_rows(risk_profile: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in risk_profile.get("rows", []):
        if not isinstance(row, dict):
            continue
        effect = str(row.get("effect"))
        claim = str(row.get("claim_allowed", ""))
        convertasset_risk = str(row.get("convertasset_risk", ""))
        nvidia_risk = str(row.get("nvidia_risk", ""))
        if effect == "procedural_texture" or "checker_not_preserved" in convertasset_risk:
            risk_level = "high"
            convertasset_action = "keep_mdl_or_bake_before_claiming_preservation"
            nvidia_action = "keep_mdl_or_bake_before_claiming_preservation"
            review_gate = "procedural_texture_static_and_visual_preservation_audit"
            paper_claim_use = "limitation_or_investigation_only"
        elif effect == "clearcoat" or "target_missing" in nvidia_risk:
            risk_level = "manual_review_high"
            convertasset_action = "manual_visual_review_of_preview_approximation"
            nvidia_action = "do_not_trust_without_target_retention_gate"
            review_gate = "target_retention_plus_material_appearance_gate"
            paper_claim_use = "selected_failure_case_only"
        elif claim == "bounded_static_and_selected_qualitative":
            risk_level = "bounded_low"
            convertasset_action = "convert_with_static_gate_and_selected_visual_review"
            nvidia_action = "usable_as_bounded_baseline_with_same_gate"
            review_gate = "static_gate_plus_selected_qualitative_review"
            paper_claim_use = "bounded_evidence_only"
        else:
            risk_level = "unknown_manual_review"
            convertasset_action = "manual_review_required"
            nvidia_action = "manual_review_required"
            review_gate = "manual_material_effect_review"
            paper_claim_use = "do_not_claim_success"
        rows.append(
            {
                "effect": effect,
                "sample_source": str(row.get("sample_source", "")),
                "risk_level": risk_level,
                "convertasset_action": convertasset_action,
                "nvidia_action": nvidia_action,
                "review_gate": review_gate,
                "paper_claim_use": paper_claim_use,
                "evidence_status": str(row.get("qualitative_status", "")),
            }
        )
    return rows


def _latex_escape(value: Any) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_stat_latex(rows: list[dict[str, Any]]) -> str:
    body = []
    selected = [
        row
        for row in rows
        if row["metric_id"] in {"norm1000_point", "raw_point", "SR", "SPL", "NE", "TL"}
    ]
    for row in selected:
        ci = f"{row['mean_delta_converted_minus_original']} [{row['ci95_low']}, {row['ci95_high']}]"
        body.append(
            " & ".join(
                [
                    _latex_escape(row["dataset"]),
                    _latex_escape(row["metric"]),
                    str(row["n"]),
                    str(row["original_mean"]),
                    str(row["converted_mean"]),
                    _latex_escape(ci),
                    _latex_escape(row["direction"]),
                ]
            )
            + r" \\"
        )
    return rf"""\begin{{table*}}[t]
\centering
\caption{{Paired bootstrap confidence intervals for frozen VLM and InternNav evidence pools. Deltas are noMDL minus original MDL; they are descriptive claim-boundary checks, not population-level claims.}}
\label{{tab:reviewer_closure_paired_ci}}
\scriptsize
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{lllrrrr}}
\toprule
\textbf{{Evidence}} & \textbf{{Metric}} & \textbf{{N}} & \textbf{{Original}} & \textbf{{Converted}} & \textbf{{Delta [95\% CI]}} & \textbf{{Direction}} \\
\midrule
{chr(10).join(body)}
\bottomrule
\end{{tabular}}%
}}
\end{{table*}}
"""


def write_stat_table(csv_path: Path, tex_path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(csv_path, rows, STAT_CSV_FIELDS)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(render_stat_latex(rows), encoding="utf-8")


def render_baseline_latex(rows: list[dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            " & ".join(
                [
                    _latex_escape(row["baseline_id"]),
                    _latex_escape(row["coordinate_space"]),
                    _latex_escape(f"{row['raw_point_original']} / {row['raw_point_converted']}"),
                    _latex_escape(f"{row['norm1000_point_original']} / {row['norm1000_point_converted']}"),
                    _latex_escape(row["raw_pair_agreement"]),
                    _latex_escape(row["norm1000_pair_agreement"]),
                ]
            )
            + r" \\"
        )
    return rf"""\begin{{table}}[t]
\centering
\caption{{Coordinate-only baselines for the expanded30 VLM grounding stress set. These rows are sanity baselines for point scoring, not VLM evidence.}}
\label{{tab:vlm_coordinate_baselines}}
\scriptsize
\resizebox{{\linewidth}}{{!}}{{%
\begin{{tabular}}{{llllll}}
\toprule
\textbf{{Baseline}} & \textbf{{Space}} & \textbf{{Raw O/C}} & \textbf{{Norm O/C}} & \textbf{{Raw agree}} & \textbf{{Norm agree}} \\
\midrule
{chr(10).join(body)}
\bottomrule
\end{{tabular}}%
}}
\end{{table}}
"""


def render_recommender_latex(rows: list[dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            " & ".join(
                [
                    _latex_escape(row["effect"]),
                    _latex_escape(row["risk_level"]),
                    _latex_escape(row["convertasset_action"]),
                    _latex_escape(row["paper_claim_use"]),
                ]
            )
            + r" \\"
        )
    return rf"""\begin{{table*}}[t]
\centering
\caption{{Lightweight safe-conversion recommender derived from the material-effect risk matrix. The rules are evidence-gated reviewer-closure guidance rather than a learned classifier.}}
\label{{tab:material_safe_conversion_recommender}}
\scriptsize
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{llll}}
\toprule
\textbf{{Effect}} & \textbf{{Risk}} & \textbf{{ConvertAsset action}} & \textbf{{Paper use}} \\
\midrule
{chr(10).join(body)}
\bottomrule
\end{{tabular}}%
}}
\end{{table*}}
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")


def _provenance(argv: list[str] | None) -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    return {
        "generated_at_utc": _utc_now(),
        "command": [sys.executable, str(script_path), *(argv if argv is not None else sys.argv[1:])],
        "script_path": _relative(script_path),
        "script_hash_sha256": _sha256_file(script_path),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }


def build_stat_rows(gemma_score: dict[str, Any], qwen_score: dict[str, Any], transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(build_vlm_stat_rows(gemma_score, evidence_id="gemma4_expanded30", model="Gemma4"))
    rows.extend(build_vlm_stat_rows(qwen_score, evidence_id="qwen25_expanded30", model="Qwen2.5-VL"))
    rows.extend(build_internnav_stat_rows(transitions))
    return rows


def write_coordinate_baseline_outputs(
    *, rows: list[dict[str, str]], artifacts: dict[str, dict[str, Any]], output_root: Path
) -> None:
    baseline_root = output_root / "vlm_coordinate_baselines"
    for baseline_id, artifact in artifacts.items():
        predictions_path = baseline_root / f"{baseline_id}_predictions.jsonl"
        score_path = baseline_root / f"{baseline_id}_score_summary.json"
        _write_jsonl(predictions_path, artifact["predictions"])
        _write_json(score_path, artifact["score_summary"])
    write_csv(DEFAULT_BASELINE_CSV, rows, BASELINE_CSV_FIELDS)
    DEFAULT_BASELINE_TEX.write_text(render_baseline_latex(rows), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gemma-score", type=Path, default=DEFAULT_GEMMA_STRESS_SCORE)
    parser.add_argument("--qwen-score", type=Path, default=DEFAULT_QWEN_STRESS_SCORE)
    parser.add_argument("--stress-manifest", type=Path, default=DEFAULT_STRESS_MANIFEST)
    parser.add_argument("--internnav-transitions", type=Path, default=DEFAULT_INTERNNAV_TRANSITIONS)
    parser.add_argument("--material-risk-profile", type=Path, default=DEFAULT_MATERIAL_RISK_PROFILE)
    parser.add_argument("--stat-json", type=Path, default=DEFAULT_STAT_JSON)
    parser.add_argument("--baseline-json", type=Path, default=DEFAULT_BASELINE_JSON)
    parser.add_argument("--recommender-json", type=Path, default=DEFAULT_RECOMMENDER_JSON)
    parser.add_argument("--stat-csv", type=Path, default=DEFAULT_STAT_CSV)
    parser.add_argument("--stat-tex", type=Path, default=DEFAULT_STAT_TEX)
    parser.add_argument("--baseline-csv", type=Path, default=DEFAULT_BASELINE_CSV)
    parser.add_argument("--baseline-tex", type=Path, default=DEFAULT_BASELINE_TEX)
    parser.add_argument("--recommender-csv", type=Path, default=DEFAULT_RECOMMENDER_CSV)
    parser.add_argument("--recommender-tex", type=Path, default=DEFAULT_RECOMMENDER_TEX)
    args = parser.parse_args(argv)

    gemma_score = _load_json(args.gemma_score)
    qwen_score = _load_json(args.qwen_score)
    transitions = _load_json(args.internnav_transitions)
    stress_manifest = _load_json(args.stress_manifest)
    risk_profile = _load_json(args.material_risk_profile)

    stat_rows = build_stat_rows(gemma_score, qwen_score, transitions)
    baseline_rows, baseline_artifacts = build_coordinate_baseline_package(stress_manifest)
    recommender_rows = build_safe_conversion_recommender_rows(risk_profile)
    provenance = _provenance(argv)

    write_stat_table(args.stat_csv, args.stat_tex, stat_rows)
    write_csv(args.baseline_csv, baseline_rows, BASELINE_CSV_FIELDS)
    args.baseline_tex.parent.mkdir(parents=True, exist_ok=True)
    args.baseline_tex.write_text(render_baseline_latex(baseline_rows), encoding="utf-8")
    write_csv(args.recommender_csv, recommender_rows, RECOMMENDER_CSV_FIELDS)
    args.recommender_tex.parent.mkdir(parents=True, exist_ok=True)
    args.recommender_tex.write_text(render_recommender_latex(recommender_rows), encoding="utf-8")

    baseline_root = args.baseline_json.parent / "vlm_coordinate_baselines"
    for baseline_id, artifact in baseline_artifacts.items():
        _write_jsonl(baseline_root / f"{baseline_id}_predictions.jsonl", artifact["predictions"])
        _write_json(baseline_root / f"{baseline_id}_score_summary.json", artifact["score_summary"])

    _write_json(
        args.stat_json,
        {
            "schema_version": 1,
            "status": "reviewer_closure_statistical_summary",
            "summary": {
                "row_count": len(stat_rows),
                "vlm_row_count": len([row for row in stat_rows if row["dataset"].startswith("GRScenes")]),
                "internnav_row_count": len([row for row in stat_rows if row["dataset"].startswith("Official")]),
                "bootstrap_rounds": BOOTSTRAP_ROUNDS,
                "bootstrap_seed": BOOTSTRAP_SEED,
            },
            "rows": stat_rows,
            "claim_boundary": {
                "allowed": ["paired descriptive deltas with bootstrap confidence intervals"],
                "forbidden": ["population-level robustness guarantee", "unscoped benchmark win claim"],
            },
            "inputs": {
                "gemma_score": {"path": _relative(args.gemma_score), "hash_sha256": _sha256_file(args.gemma_score)},
                "qwen_score": {"path": _relative(args.qwen_score), "hash_sha256": _sha256_file(args.qwen_score)},
                "internnav_transitions": {
                    "path": _relative(args.internnav_transitions),
                    "hash_sha256": _sha256_file(args.internnav_transitions),
                },
            },
            "generator_provenance": provenance,
        },
    )
    _write_json(
        args.baseline_json,
        {
            "schema_version": 1,
            "status": "vlm_coordinate_baseline_summary",
            "summary": {
                "baseline_count": len(baseline_rows),
                "scoring_record_count": len(stress_manifest.get("scoring_records", [])),
                "claim_boundary": "coordinate_only_baselines_not_vlm_evidence",
            },
            "rows": baseline_rows,
            "baseline_artifacts": {
                baseline_id: {
                    "predictions": _relative(baseline_root / f"{baseline_id}_predictions.jsonl"),
                    "score_summary": _relative(baseline_root / f"{baseline_id}_score_summary.json"),
                }
                for baseline_id in baseline_artifacts
            },
            "inputs": {
                "stress_manifest": {
                    "path": _relative(args.stress_manifest),
                    "hash_sha256": _sha256_file(args.stress_manifest),
                }
            },
            "generator_provenance": provenance,
        },
    )
    _write_json(
        args.recommender_json,
        {
            "schema_version": 1,
            "status": "material_safe_conversion_recommender",
            "summary": {
                "rule_count": len(recommender_rows),
                "high_or_manual_review_count": len(
                    [row for row in recommender_rows if row["risk_level"] in {"high", "manual_review_high"}]
                ),
                "bounded_low_count": len([row for row in recommender_rows if row["risk_level"] == "bounded_low"]),
                "claim_boundary": "rule_table_derived_from_selected_risk_matrix_not_learned_classifier",
            },
            "rows": recommender_rows,
            "inputs": {
                "material_risk_profile": {
                    "path": _relative(args.material_risk_profile),
                    "hash_sha256": _sha256_file(args.material_risk_profile),
                }
            },
            "generator_provenance": provenance,
        },
    )
    print(f"Wrote {args.stat_json}")
    print(f"Wrote {args.baseline_json}")
    print(f"Wrote {args.recommender_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
