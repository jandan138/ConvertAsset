#!/usr/bin/env python3
"""Build a selected subset from one or more GRScenes projection reports."""

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


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_OUTPUT = RAW_DIR / "pass_only_target_projection_qa_report.json"
DEFAULT_CLAIM_BOUNDARY = "projection_subset_labels_only_not_vlm_metric_evidence"


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


def _records_for_pair(report: dict[str, Any], pair_id: str) -> list[dict[str, Any]]:
    records = [record for record in report.get("scoring_records", []) if record.get("pair_id") == pair_id]
    order = {"original": 0, "converted": 1}
    return sorted(records, key=lambda record: order.get(str(record.get("version")), 99))


def build_projection_subset(
    source_reports: list[dict[str, Any]],
    *,
    pair_ids: list[str],
    selection_id: str,
    claim_boundary: str = DEFAULT_CLAIM_BOUNDARY,
) -> dict[str, Any]:
    if not pair_ids:
        raise ValueError("pair_ids must not be empty")
    duplicate_requests = sorted(pair_id for pair_id, count in Counter(pair_ids).items() if count > 1)
    if duplicate_requests:
        raise ValueError(f"selected pair requested more than once: {duplicate_requests[0]}")

    pair_locations: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for source in source_reports:
        report = source["report"]
        for pair in report.get("pairs", []):
            pair_id = str(pair.get("pair_id") or "")
            if pair_id:
                pair_locations.setdefault(pair_id, []).append((source, pair))

    selected_pairs = []
    selected_records = []
    for pair_id in pair_ids:
        locations = pair_locations.get(pair_id)
        if not locations:
            raise KeyError(f"selected pair missing from projection reports: {pair_id}")
        if len(locations) > 1:
            raise ValueError(f"selected pair appears in multiple reports: {pair_id}")
        source, pair = locations[0]
        report = source["report"]
        records = _records_for_pair(report, pair_id)
        if not records:
            raise ValueError(f"selected pair has no scoring records: {pair_id}")
        selected_pair = dict(pair)
        selected_pair["source_projection_report"] = {
            "path": source["path"],
            "hash_sha256": source["hash_sha256"],
        }
        selected_pairs.append(selected_pair)
        selected_records.extend(records)

    status_counts = Counter(str(pair.get("status") or "unknown") for pair in selected_pairs)
    projection_ok_pair_count = int(status_counts.get("projection_ok", 0))
    image_widths = {
        (source.get("report", {}).get("summary") or {}).get("image_width")
        for source in source_reports
        if (source.get("report", {}).get("summary") or {}).get("image_width") is not None
    }
    image_heights = {
        (source.get("report", {}).get("summary") or {}).get("image_height")
        for source in source_reports
        if (source.get("report", {}).get("summary") or {}).get("image_height") is not None
    }

    return {
        "schema_version": 1,
        "status": "projection_subset_report",
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/select_projection_subset.py",
        "summary": {
            "selection_id": selection_id,
            "selection_mode": "explicit_pair_ids_from_projection_reports",
            "selected_pair_count": len(selected_pairs),
            "projection_ok_pair_count": projection_ok_pair_count,
            "projection_blocked_pair_count": len(selected_pairs) - projection_ok_pair_count,
            "scoring_record_count": len(selected_records),
            "source_report_count": len(source_reports),
            "image_width": next(iter(image_widths)) if len(image_widths) == 1 else None,
            "image_height": next(iter(image_heights)) if len(image_heights) == 1 else None,
            "status_counts": dict(status_counts),
            "claim_boundary": claim_boundary,
        },
        "source_projection_reports": [
            {"path": source["path"], "hash_sha256": source["hash_sha256"]} for source in source_reports
        ],
        "selected_pair_ids": list(pair_ids),
        "pairs": selected_pairs,
        "scoring_records": selected_records,
    }


def _load_source_reports(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        {
            "path": str(path),
            "hash_sha256": _sha256_file(path),
            "report": _load_json(path),
        }
        for path in paths
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-report", type=Path, action="append", required=True)
    parser.add_argument("--pair-id", action="append", dest="pair_ids", required=True)
    parser.add_argument("--selection-id", required=True)
    parser.add_argument("--claim-boundary", default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    source_reports = _load_source_reports(args.projection_report)
    report = build_projection_subset(
        source_reports,
        pair_ids=args.pair_ids,
        selection_id=args.selection_id,
        claim_boundary=args.claim_boundary,
    )
    script_path = Path(__file__).resolve()
    report["generator_provenance"] = {
        "command": [sys.executable, str(script_path), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(script_path),
        "script_hash_sha256": _sha256_file(script_path),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.out} selected={report['summary']['selected_pair_count']} "
        f"records={report['summary']['scoring_record_count']}"
    )
    return 0 if report["summary"]["projection_blocked_pair_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
