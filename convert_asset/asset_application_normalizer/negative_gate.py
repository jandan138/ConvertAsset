"""AAN-09 negative-gate manifest aggregation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACCEPTED_NEGATIVE_STATUSES = {"blocked", "ready_with_waivers"}
WAIVER_REQUIRED_FIELDS = (
    "waiver_id",
    "owner",
    "reason",
    "expires_or_review_by",
    "impact",
    "claims_forbidden",
)


def build_negative_gate_summary(manifest_paths: list[Path]) -> dict[str, Any]:
    """Aggregate blocked/waived negative manifests for AAN-09 weekly evidence."""
    manifests = [_load_manifest(path) for path in manifest_paths]
    cases = [_case_record(path, manifest) for path, manifest in manifests]
    invalid_cases = []
    for case, (_path, manifest) in zip(cases, manifests):
        invalid_cases.extend(_invalid_case_records(case, manifest))

    status_counts: dict[str, int] = {}
    for case in cases:
        status = case["overall_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    failure_modes = _failure_modes(cases)
    waiver_count = sum(len(case["waiver_ids"]) for case in cases)
    not_run_treated_as_pass = any(
        "not_run" in case["stage_statuses"].values()
        and case["overall_status"] not in ACCEPTED_NEGATIVE_STATUSES
        for case in cases
    )

    return {
        "schema_version": "aan09.negative_gate_summary.v1",
        "status": "pass" if cases and not invalid_cases else "fail",
        "case_count": len(cases),
        "status_counts": status_counts,
        "waiver_count": waiver_count,
        "blocked_reason_count": sum(len(case["blocker_ids"]) for case in cases),
        "failure_modes": failure_modes,
        "representative_artifacts": cases,
        "invalid_cases": invalid_cases,
        "claim_boundary": {
            "accepted_negative_statuses": sorted(ACCEPTED_NEGATIVE_STATUSES),
            "not_run_treated_as_pass": not_run_treated_as_pass,
        },
    }


def write_negative_gate_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_manifest(path: Path) -> tuple[Path, dict[str, Any]]:
    return path, json.loads(path.read_text(encoding="utf-8"))


def _case_record(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    blocked_reasons = manifest.get("blocked_reasons", [])
    waivers = manifest.get("waivers", [])
    stage_statuses = {
        str(gate.get("stage")): str(gate.get("status"))
        for gate in manifest.get("stage_gates", [])
    }
    return {
        "manifest": str(path),
        "asset_id": manifest.get("asset_id"),
        "task_id": manifest.get("task_id"),
        "source_path": manifest.get("source", {}).get("path"),
        "overall_status": manifest.get("overall_status"),
        "stage_statuses": stage_statuses,
        "blocker_ids": [
            str(item.get("blocker_id"))
            for item in blocked_reasons
            if item.get("blocker_id")
        ],
        "waiver_ids": [
            str(item.get("waiver_id"))
            for item in waivers
            if item.get("waiver_id")
        ],
        "claims_forbidden": list(manifest.get("claims_forbidden", [])),
    }


def _invalid_case_records(case: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    status = case.get("overall_status")
    if status not in ACCEPTED_NEGATIVE_STATUSES:
        return [
            {
                "manifest": case["manifest"],
                "asset_id": case.get("asset_id"),
                "reason": "negative manifest was not blocked or waived",
                "overall_status": status,
            }
        ]

    if status == "blocked":
        if not case["blocker_ids"]:
            return [
                {
                    "manifest": case["manifest"],
                    "asset_id": case.get("asset_id"),
                    "reason": "blocked manifest has no blocked_reasons",
                }
            ]
        if "blocked" not in case["stage_statuses"].values():
            return [
                {
                    "manifest": case["manifest"],
                    "asset_id": case.get("asset_id"),
                    "reason": "blocked manifest has no blocked stage gate",
                }
            ]
        return []

    waivers = manifest.get("waivers", [])
    if not waivers:
        return [
            {
                "manifest": case["manifest"],
                "asset_id": case.get("asset_id"),
                "reason": "ready_with_waivers manifest has no waiver records",
            }
        ]

    invalid = []
    for waiver in waivers:
        missing = sorted(
            field for field in WAIVER_REQUIRED_FIELDS if _missing(waiver.get(field))
        )
        if missing:
            invalid.append(
                {
                    "manifest": case["manifest"],
                    "asset_id": case.get("asset_id"),
                    "waiver_id": waiver.get("waiver_id"),
                    "reason": "waiver record is incomplete",
                    "missing_fields": missing,
                }
            )
    return invalid


def _failure_modes(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    modes: dict[str, dict[str, Any]] = {}
    for case in cases:
        for blocker_id in case["blocker_ids"]:
            mode = modes.setdefault(
                blocker_id,
                {
                    "count": 0,
                    "representative_manifest": case["manifest"],
                    "asset_ids": [],
                },
            )
            mode["count"] += 1
            if case.get("asset_id") and case["asset_id"] not in mode["asset_ids"]:
                mode["asset_ids"].append(case["asset_id"])
    return modes


def _missing(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, (list, tuple, dict, set)) and not value:
        return True
    return False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an AAN-09 negative-gate summary")
    parser.add_argument("manifest", nargs="+", help="Negative manifest JSON path")
    parser.add_argument("--out", required=True, help="Summary JSON output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = build_negative_gate_summary([Path(path) for path in args.manifest])
    write_negative_gate_summary(Path(args.out), summary)
    return 0 if summary["status"] == "pass" else 5


if __name__ == "__main__":
    raise SystemExit(main())
