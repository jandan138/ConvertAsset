#!/usr/bin/env python3
"""Build the GRScenes VLM material-shift stress manifest and claim gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
EXPERIMENT_DIR = PROJECT_ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding"
DEFAULT_PROJECTION_REPORT = RAW_DIR / "retake_zoom_target_projection_qa_report.json"
DEFAULT_VISUAL_REVIEW_REPORT = RAW_DIR / "retake_zoom_visual_review_batch.json"
DEFAULT_PROTOCOL = EXPERIMENT_DIR / "protocol.yaml"
DEFAULT_OUTPUT = RAW_DIR / "stress_vlm_run_manifest.json"
DEFAULT_PREDICTIONS = RAW_DIR / "stress_predictions.jsonl"
DEFAULT_SCORE_SUMMARY = RAW_DIR / "stress_score_summary.json"
DEFAULT_MIN_STRESS_PAIRS = 30
DEFAULT_MIN_TARGET_CATEGORIES = 5
DEFAULT_SELECTION_ID = "zoom_material_shift_stress_v1"
CLAIM_BOUNDARY = "stress_input_manifest_only_not_final_model_metric_evidence"
CLAIM_STATUS = "pilot_only"
COORDINATE_FRAME = "normalized_1000"
RESPONSE_FORMAT = "structured_text"
PRIMARY_POINT_METRIC = "point_in_bbox_normalized_1000_accuracy"
RUNNER_PATH = EXPERIMENT_DIR / "run_vlm_predictions.py"
SCORER_PATH = EXPERIMENT_DIR / "score_grounding.py"
STRESS_VERDICTS = {"PASS", "WARN"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def _selected_pair_ids(projection_report: dict[str, Any]) -> list[str]:
    explicit = projection_report.get("selected_pair_ids")
    if isinstance(explicit, list) and explicit:
        return [str(pair_id) for pair_id in explicit]
    return [str(pair.get("pair_id")) for pair in projection_report.get("pairs", []) if pair.get("pair_id")]


def _source_ref(source: dict[str, Any]) -> dict[str, str]:
    return {"path": str(source["path"]), "hash_sha256": str(source["hash_sha256"])}


def _risk_text(pair: dict[str, Any]) -> str | None:
    for key in ["main_risk_or_retake", "main_risk", "retake_recommendation"]:
        value = pair.get(key)
        if value:
            return str(value)
    return None


def _review_packet(pair: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    packet = {
        "pair_id": str(pair.get("pair_id")),
        "target_category": pair.get("target_category"),
        "verdict": str(pair.get("verdict") or "UNKNOWN").upper(),
        "packet_id": pair.get("packet_id"),
        "visible_evidence": pair.get("visible_evidence"),
        "risk_or_retake": _risk_text(pair),
        "source_visual_review_report": _source_ref(source),
    }
    return {key: value for key, value in packet.items() if value is not None}


def _collect_visual_reviews(visual_review_sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    reviews: dict[str, dict[str, Any]] = {}
    for source in visual_review_sources:
        for pair in source["report"].get("pairs", []):
            pair_id = str(pair.get("pair_id") or "")
            if not pair_id:
                continue
            if pair_id in reviews:
                raise ValueError(f"visual review pair appears in multiple reports: {pair_id}")
            reviews[pair_id] = _review_packet(pair, source)
    return reviews


def _pair_lookup(projection_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(pair.get("pair_id")): pair for pair in projection_report.get("pairs", []) if pair.get("pair_id")}


def _records_by_pair(projection_report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    order = {"original": 0, "converted": 1}
    for record in projection_report.get("scoring_records", []):
        pair_id = str(record.get("pair_id") or "")
        if not pair_id:
            continue
        grouped.setdefault(pair_id, []).append(record)
    for records in grouped.values():
        records.sort(key=lambda record: order.get(str(record.get("version")), 99))
    return grouped


def _prompt_contract() -> dict[str, str]:
    return {
        "task_id": "s1_referred_object_localization",
        "coordinate_frame": COORDINATE_FRAME,
        "response_format": RESPONSE_FORMAT,
        "primary_point_metric": PRIMARY_POINT_METRIC,
        "answer_metric": "answer_accuracy",
        "pair_consistency_metric": "normalized_1000_point_hit_agreement",
        "diagnostic_point_metrics": "raw_pixel_point_in_bbox_and_point_in_image",
        "stress_interpretation": "material_shift_stress_not_clean_preservation",
    }


def _image_with_hash(record: dict[str, Any]) -> dict[str, Any]:
    image = dict(record.get("image") or {})
    path = image.get("path")
    image["hash_sha256"] = _sha256_file(Path(path)) if path and Path(path).exists() else None
    return image


def _category_for_pair(pair_id: str, records_by_pair: dict[str, list[dict[str, Any]]], review: dict[str, Any] | None) -> str:
    if review and review.get("target_category"):
        return str(review["target_category"])
    for record in records_by_pair.get(pair_id, []):
        category = (record.get("target") or {}).get("category")
        if category:
            return str(category)
    return "unknown"


def _enrich_scoring_record(record: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    enriched["image"] = _image_with_hash(record)
    enriched["prediction"] = None
    enriched["prompt_contract"] = _prompt_contract()
    enriched["claim_boundary"] = CLAIM_BOUNDARY
    enriched["visual_review"] = {
        "verdict": review["verdict"],
        "source_visual_review_report": review["source_visual_review_report"],
    }
    return enriched


def _claim_gate(blockers: list[str]) -> dict[str, Any]:
    return {
        "claim_status": CLAIM_STATUS,
        "final_benchmark_claimable": False,
        "blocked_by": blockers,
        "allowed_claims": [
            "pilot-only material-shift stress protocol definition",
            "pilot-only Gemma4/Qwen stress diagnostics if model outputs are generated under this manifest",
            "stress candidate selection and target-visible visual QA provenance",
        ],
        "forbidden_claims": [
            "not a final GRScenes benchmark result",
            "not a clean material-preservation benchmark",
            "not evidence that no-MDL conversion preserves VLM grounding in general",
            "not a Gemma4-vs-Qwen model comparison",
            "not a PIO dataset evaluation",
        ],
    }


def build_stress_vlm_run_manifest(
    projection_report: dict[str, Any],
    *,
    visual_review_sources: list[dict[str, Any]],
    protocol: dict[str, Any],
    min_stress_pairs: int = DEFAULT_MIN_STRESS_PAIRS,
    min_target_categories: int = DEFAULT_MIN_TARGET_CATEGORIES,
    predictions_path: Path = DEFAULT_PREDICTIONS,
    score_summary_path: Path = DEFAULT_SCORE_SUMMARY,
    selection_id: str = DEFAULT_SELECTION_ID,
) -> dict[str, Any]:
    reviews = _collect_visual_reviews(visual_review_sources)
    pairs_by_id = _pair_lookup(projection_report)
    records_by_pair = _records_by_pair(projection_report)
    selected_pair_ids = _selected_pair_ids(projection_report)

    selected_pairs = []
    excluded_pairs = []
    selected_records = []
    missing_review_pair_ids: list[str] = []
    projection_blocked_pair_ids: list[str] = []
    unsupported_verdict_pair_ids: list[str] = []

    for pair_id in selected_pair_ids:
        pair = dict(pairs_by_id.get(pair_id) or {"pair_id": pair_id})
        review = reviews.get(pair_id)
        if review is None:
            missing_review_pair_ids.append(pair_id)
            pair["visual_review"] = {"verdict": "MISSING"}
            excluded_pairs.append(pair)
            continue
        pair["visual_review"] = review
        pair["target_category"] = _category_for_pair(pair_id, records_by_pair, review)
        if pair.get("status") != "projection_ok":
            projection_blocked_pair_ids.append(pair_id)
            excluded_pairs.append(pair)
            continue
        verdict = str(review.get("verdict") or "UNKNOWN").upper()
        if verdict not in STRESS_VERDICTS:
            if verdict != "FAIL":
                unsupported_verdict_pair_ids.append(pair_id)
            excluded_pairs.append(pair)
            continue
        selected_pairs.append(pair)
        for record in records_by_pair.get(pair_id, []):
            selected_records.append(_enrich_scoring_record(record, review))

    stress_pair_count = len(selected_pairs)
    category_counts = Counter(str(pair.get("target_category") or "unknown") for pair in selected_pairs)
    verdict_counts = Counter(str((pair.get("visual_review") or {}).get("verdict") or "UNKNOWN") for pair in selected_pairs)

    model_run_blockers = []
    if not selected_records:
        model_run_blockers.append("empty_scoring_records")
    if missing_review_pair_ids:
        model_run_blockers.append("missing_visual_review_pairs")
    if projection_blocked_pair_ids:
        model_run_blockers.append("projection_blocked_pairs_present")
    if unsupported_verdict_pair_ids:
        model_run_blockers.append("unsupported_visual_review_verdicts_present")

    final_blockers = list(model_run_blockers)
    if stress_pair_count < int(min_stress_pairs):
        final_blockers.append("stress_pair_count_below_minimum_final_benchmark_gate")
    if len(category_counts) < int(min_target_categories):
        final_blockers.append("target_category_count_below_minimum_final_benchmark_gate")
    if not predictions_path.exists():
        final_blockers.append("canonical_predictions_missing")
    if not score_summary_path.exists():
        final_blockers.append("canonical_score_summary_missing")

    ready_for_model_run = not model_run_blockers
    ready_for_final_benchmark_run = ready_for_model_run and not final_blockers

    return {
        "schema_version": 1,
        "status": "stress_vlm_run_manifest",
        "claim_status": CLAIM_STATUS,
        "final_benchmark_claimable": False,
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_stress_vlm_run_manifest.py",
        "summary": {
            "selection_id": selection_id,
            "claim_boundary": CLAIM_BOUNDARY,
            "stress_pair_count": stress_pair_count,
            "stress_scoring_record_count": len(selected_records),
            "stress_verdict_counts": dict(sorted(verdict_counts.items())),
            "excluded_pair_count": len(excluded_pairs),
            "min_stress_pairs_for_final_benchmark": int(min_stress_pairs),
            "min_target_categories_for_final_benchmark": int(min_target_categories),
            "ready_for_model_run": ready_for_model_run,
            "ready_for_final_benchmark_run": ready_for_final_benchmark_run,
            "model_run_blockers": model_run_blockers,
            "blockers": final_blockers,
            "missing_visual_review_pair_ids": missing_review_pair_ids,
            "projection_blocked_pair_ids": projection_blocked_pair_ids,
            "unsupported_verdict_pair_ids": unsupported_verdict_pair_ids,
            "selected_target_category_counts": dict(sorted(category_counts.items())),
        },
        "protocol": {
            **_prompt_contract(),
            "runner": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py",
            "scorer": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py",
            "protocol_schema_version": protocol.get("schema_version"),
            "response_format_note": "Use structured_text for Qwen-family backends until direct JSON prompting is revalidated.",
        },
        "claim_gate": _claim_gate(final_blockers),
        "recommended_model_runs": [
            {
                "id": "gemma4_zoom_stress",
                "backend": "local_gemma4_multimodal",
                "coordinate_frame": COORDINATE_FRAME,
                "response_format": RESPONSE_FORMAT,
                "claim_boundary": "stress_pilot_model_run_until_final_gate_satisfied",
            },
            {
                "id": "qwen25_zoom_stress",
                "backend": "local_hf_qwen",
                "coordinate_frame": COORDINATE_FRAME,
                "response_format": RESPONSE_FORMAT,
                "claim_boundary": "stress_pilot_model_run_until_final_gate_satisfied",
            },
        ],
        "selected_pair_ids": [pair["pair_id"] for pair in selected_pairs],
        "selected_pairs": selected_pairs,
        "excluded_pairs": excluded_pairs,
        "scoring_records": selected_records,
        "source_projection_report_summary": projection_report.get("summary", {}),
    }


def _load_source_json(path: Path) -> dict[str, Any]:
    return {"path": str(path), "hash_sha256": _sha256_file(path), "report": _load_json(path)}


def _write_manifest(
    manifest: dict[str, Any],
    out: Path,
    *,
    projection_report: Path,
    visual_review_reports: list[Path],
    protocol_path: Path,
    predictions_path: Path,
    score_summary_path: Path,
    argv: list[str] | None,
) -> None:
    script_path = Path(__file__).resolve()
    manifest["inputs"] = {
        "projection_report": {"path": str(projection_report), "hash_sha256": _sha256_file(projection_report)},
        "visual_review_reports": [
            {"path": str(path), "hash_sha256": _sha256_file(path)} for path in visual_review_reports
        ],
        "protocol": {"path": str(protocol_path), "hash_sha256": _sha256_file(protocol_path)},
        "predictions_path": {"path": str(predictions_path), "exists": predictions_path.exists()},
        "score_summary_path": {"path": str(score_summary_path), "exists": score_summary_path.exists()},
        "runner": {"path": str(RUNNER_PATH), "hash_sha256": _sha256_file(RUNNER_PATH)},
        "scorer": {"path": str(SCORER_PATH), "hash_sha256": _sha256_file(SCORER_PATH)},
    }
    manifest["generator_provenance"] = {
        "command": [sys.executable, str(script_path), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(script_path),
        "script_hash_sha256": _sha256_file(script_path),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-report", type=Path, default=DEFAULT_PROJECTION_REPORT)
    parser.add_argument("--visual-review-report", type=Path, action="append", default=None)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--min-stress-pairs", type=int, default=DEFAULT_MIN_STRESS_PAIRS)
    parser.add_argument("--min-target-categories", type=int, default=DEFAULT_MIN_TARGET_CATEGORIES)
    parser.add_argument("--predictions-path", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--score-summary-path", type=Path, default=DEFAULT_SCORE_SUMMARY)
    parser.add_argument("--selection-id", default=DEFAULT_SELECTION_ID)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    visual_review_reports = args.visual_review_report or [DEFAULT_VISUAL_REVIEW_REPORT]
    projection_report = _load_json(args.projection_report)
    visual_sources = [_load_source_json(path) for path in visual_review_reports]
    protocol = _load_yaml(args.protocol) or {}
    manifest = build_stress_vlm_run_manifest(
        projection_report,
        visual_review_sources=visual_sources,
        protocol=protocol,
        min_stress_pairs=args.min_stress_pairs,
        min_target_categories=args.min_target_categories,
        predictions_path=args.predictions_path,
        score_summary_path=args.score_summary_path,
        selection_id=args.selection_id,
    )
    _write_manifest(
        manifest,
        args.out,
        projection_report=args.projection_report,
        visual_review_reports=visual_review_reports,
        protocol_path=args.protocol,
        predictions_path=args.predictions_path,
        score_summary_path=args.score_summary_path,
        argv=argv,
    )
    print(
        f"Wrote {args.out} stress_pairs={manifest['summary']['stress_pair_count']} "
        f"model_ready={manifest['summary']['ready_for_model_run']} "
        f"final_ready={manifest['summary']['ready_for_final_benchmark_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
