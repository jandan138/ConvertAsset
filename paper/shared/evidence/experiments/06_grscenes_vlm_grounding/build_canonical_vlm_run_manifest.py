#!/usr/bin/env python3
"""Build the canonical GRScenes VLM input manifest and claim gate."""

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
DEFAULT_PROJECTION_REPORT = RAW_DIR / "pass_only_target_projection_qa_report.json"
DEFAULT_VISUAL_REVIEW_REPORTS = [
    RAW_DIR / "paired_render_visual_review_batch.json",
    RAW_DIR / "alternative_centerline_visual_review_batch.json",
]
DEFAULT_PROTOCOL = EXPERIMENT_DIR / "protocol.yaml"
DEFAULT_OUTPUT = RAW_DIR / "canonical_vlm_run_manifest.json"
DEFAULT_MIN_PASS_PAIRS = 20
DEFAULT_SELECTION_ID = "canonical_pass_only_v1"
CLAIM_BOUNDARY = "canonical_input_manifest_only_not_model_metric_evidence"
CLAIM_STATUS = "pilot_only"
COORDINATE_FRAME = "normalized_1000"
RESPONSE_FORMAT = "structured_text"
PRIMARY_POINT_METRIC = "point_in_bbox_normalized_1000_accuracy"
RUNNER_PATH = EXPERIMENT_DIR / "run_vlm_predictions.py"
SCORER_PATH = EXPERIMENT_DIR / "score_grounding.py"


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
    for key in ["main_risk", "main_risk_or_retake", "retake_recommendation"]:
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
    for pair_id, records in grouped.items():
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
    }


def _image_with_hash(record: dict[str, Any]) -> dict[str, Any]:
    image = dict(record.get("image") or {})
    path = image.get("path")
    image["hash_sha256"] = _sha256_file(Path(path)) if path and Path(path).exists() else None
    return image


def _enrich_scoring_record(record: dict[str, Any], review: dict[str, Any] | None) -> dict[str, Any]:
    enriched = dict(record)
    enriched["image"] = _image_with_hash(record)
    enriched["prediction"] = None
    enriched["prompt_contract"] = _prompt_contract()
    enriched["claim_boundary"] = CLAIM_BOUNDARY
    if review is not None:
        enriched["visual_review"] = {
            "verdict": review["verdict"],
            "source_visual_review_report": review["source_visual_review_report"],
        }
    return enriched


def _classify_reviews(reviews: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    warn_pairs = [review for review in reviews.values() if review["verdict"] == "WARN"]
    fail_pairs = [review for review in reviews.values() if review["verdict"] == "FAIL"]
    return warn_pairs, fail_pairs


def _claim_gate(*, pass_pair_count: int, min_pass_pairs: int, final_blockers: list[str]) -> dict[str, Any]:
    blocked_by = [
        "canonical_predictions_missing",
        "canonical_score_summary_missing",
        "probe_outputs_under_probes_not_canonical_predictions_jsonl",
        "legacy_gemma4_probe_not_frozen_protocol",
        "qwen_coordinate_semantics_unresolved",
    ]
    if pass_pair_count < int(min_pass_pairs):
        blocked_by.insert(0, "only_four_visual_qa_pass_pairs")
    for blocker in final_blockers:
        if blocker not in blocked_by:
            blocked_by.append(blocker)
    return {
        "claim_status": CLAIM_STATUS,
        "final_benchmark_claimable": False,
        "blocked_by": blocked_by,
        "allowed_claims": [
            "pipeline plumbing and provenance for the current PASS-only VLM pilot",
            "pilot-only Gemma4/Qwen protocol diagnostics over the selected visual-QA PASS pairs",
            "retake queue identification for WARN visual-QA pairs",
        ],
        "forbidden_claims": [
            "not a final GRScenes benchmark result",
            "not evidence that no-MDL conversion preserves VLM grounding in general",
            "not a Gemma4-vs-Qwen model comparison",
            "not a PIO dataset evaluation",
        ],
    }


def build_canonical_vlm_run_manifest(
    projection_report: dict[str, Any],
    *,
    visual_review_sources: list[dict[str, Any]],
    protocol: dict[str, Any],
    min_pass_pairs: int = DEFAULT_MIN_PASS_PAIRS,
    selection_id: str = DEFAULT_SELECTION_ID,
) -> dict[str, Any]:
    reviews = _collect_visual_reviews(visual_review_sources)
    pairs_by_id = _pair_lookup(projection_report)
    records_by_pair = _records_by_pair(projection_report)
    selected_pair_ids = _selected_pair_ids(projection_report)

    selected_pairs = []
    rejected_selected_pairs = []
    selected_records = []
    pilot_blockers: list[str] = []
    projection_blocked_pair_ids: list[str] = []
    non_pass_selected_pair_ids: list[str] = []
    missing_review_pair_ids: list[str] = []
    for pair_id in selected_pair_ids:
        pair = dict(pairs_by_id.get(pair_id) or {"pair_id": pair_id})
        review = reviews.get(pair_id)
        if review is None:
            missing_review_pair_ids.append(pair_id)
            visual_packet = {"verdict": "MISSING"}
        else:
            visual_packet = review
            if review.get("verdict") != "PASS":
                non_pass_selected_pair_ids.append(pair_id)
        pair["visual_review"] = visual_packet
        if visual_packet.get("verdict") == "PASS":
            selected_pairs.append(pair)
            for record in records_by_pair.get(pair_id, []):
                selected_records.append(_enrich_scoring_record(record, review))
        else:
            rejected_selected_pairs.append(pair)
        if pair.get("status") != "projection_ok":
            projection_blocked_pair_ids.append(pair_id)

    if not selected_records:
        pilot_blockers.append("empty_scoring_records")
    if missing_review_pair_ids or non_pass_selected_pair_ids:
        pilot_blockers.append("selected_pair_without_pass_visual_review")
    if projection_blocked_pair_ids:
        pilot_blockers.append("projection_blocked_pairs_present")

    warn_pairs, fail_pairs = _classify_reviews(reviews)
    pass_pair_count = sum(1 for pair in selected_pairs if (pair.get("visual_review") or {}).get("verdict") == "PASS")
    final_blockers = list(pilot_blockers)
    if pass_pair_count < int(min_pass_pairs):
        final_blockers.append("pass_pair_count_below_minimum_final_benchmark_gate")
    ready_for_pilot_model_run = not pilot_blockers
    ready_for_final_benchmark_run = ready_for_pilot_model_run and not final_blockers
    category_counts = Counter(
        str((pair.get("visual_review") or {}).get("target_category") or "unknown") for pair in selected_pairs
    )

    return {
        "schema_version": 1,
        "status": "canonical_vlm_run_manifest",
        "claim_status": CLAIM_STATUS,
        "final_benchmark_claimable": False,
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/build_canonical_vlm_run_manifest.py",
        "summary": {
            "selection_id": selection_id,
            "claim_boundary": CLAIM_BOUNDARY,
            "pass_pair_count": pass_pair_count,
            "pass_scoring_record_count": len(selected_records),
            "warn_pair_count": len(warn_pairs),
            "fail_pair_count": len(fail_pairs),
            "min_pass_pairs_for_final_benchmark": int(min_pass_pairs),
            "ready_for_pilot_model_run": ready_for_pilot_model_run,
            "ready_for_final_benchmark_run": ready_for_final_benchmark_run,
            "pilot_blockers": pilot_blockers,
            "blockers": final_blockers,
            "non_pass_selected_pair_ids": non_pass_selected_pair_ids,
            "missing_visual_review_pair_ids": missing_review_pair_ids,
            "projection_blocked_pair_ids": projection_blocked_pair_ids,
            "selected_target_category_counts": dict(sorted(category_counts.items())),
        },
        "protocol": {
            **_prompt_contract(),
            "runner": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_vlm_predictions.py",
            "scorer": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/score_grounding.py",
            "protocol_schema_version": protocol.get("schema_version"),
            "response_format_note": (
                "Use structured_text for Qwen-family backends until direct JSON prompting is revalidated."
            ),
        },
        "claim_gate": _claim_gate(
            pass_pair_count=pass_pair_count,
            min_pass_pairs=min_pass_pairs,
            final_blockers=final_blockers,
        ),
        "recommended_model_runs": [
            {
                "id": "gemma4_canonical_pass_only",
                "backend": "local_gemma4_multimodal",
                "coordinate_frame": COORDINATE_FRAME,
                "response_format": RESPONSE_FORMAT,
                "claim_boundary": "pilot_model_run_until_final_pass_pool_gate_satisfied",
            },
            {
                "id": "qwen25_canonical_pass_only",
                "backend": "local_hf_qwen",
                "coordinate_frame": COORDINATE_FRAME,
                "response_format": RESPONSE_FORMAT,
                "claim_boundary": "pilot_model_run_until_final_pass_pool_gate_satisfied",
            },
        ],
        "selected_pair_ids": selected_pair_ids,
        "selected_pairs": selected_pairs,
        "rejected_selected_pairs": rejected_selected_pairs,
        "scoring_records": selected_records,
        "source_projection_reports": projection_report.get("source_projection_reports", []),
        "retake_candidates": warn_pairs,
        "excluded_pairs": fail_pairs,
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
    argv: list[str] | None,
) -> None:
    script_path = Path(__file__).resolve()
    manifest["inputs"] = {
        "projection_report": {"path": str(projection_report), "hash_sha256": _sha256_file(projection_report)},
        "visual_review_reports": [
            {"path": str(path), "hash_sha256": _sha256_file(path)} for path in visual_review_reports
        ],
        "protocol": {"path": str(protocol_path), "hash_sha256": _sha256_file(protocol_path)},
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
    parser.add_argument("--min-pass-pairs", type=int, default=DEFAULT_MIN_PASS_PAIRS)
    parser.add_argument("--selection-id", default=DEFAULT_SELECTION_ID)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    visual_review_reports = args.visual_review_report or DEFAULT_VISUAL_REVIEW_REPORTS
    projection_report = _load_json(args.projection_report)
    visual_sources = [_load_source_json(path) for path in visual_review_reports]
    protocol = _load_yaml(args.protocol) or {}
    manifest = build_canonical_vlm_run_manifest(
        projection_report,
        visual_review_sources=visual_sources,
        protocol=protocol,
        min_pass_pairs=args.min_pass_pairs,
        selection_id=args.selection_id,
    )
    _write_manifest(
        manifest,
        args.out,
        projection_report=args.projection_report,
        visual_review_reports=visual_review_reports,
        protocol_path=args.protocol,
        argv=argv,
    )
    print(
        f"Wrote {args.out} pass_pairs={manifest['summary']['pass_pair_count']} "
        f"pilot_ready={manifest['summary']['ready_for_pilot_model_run']} "
        f"final_ready={manifest['summary']['ready_for_final_benchmark_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
