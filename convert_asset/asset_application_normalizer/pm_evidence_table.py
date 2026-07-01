"""AAN-09.5 PM-facing evidence table aggregation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_pm_evidence_table(
    manifest_paths: list[Path],
    negative_summary_paths: list[Path] | None = None,
) -> dict[str, Any]:
    manifests = [_load_json(path) for path in manifest_paths]
    negative_summaries = [_load_json(path) for path in negative_summary_paths or []]
    rows = [_row_from_manifest(path, manifest) for path, manifest in zip(manifest_paths, manifests)]
    rows.sort(key=lambda row: (row["pm_status"], row["asset_id"]))
    status_counts: dict[str, int] = {}
    for row in rows:
        status = row["pm_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    failure_modes = _merge_failure_modes(rows, negative_summaries)
    waiver_count = sum(int(row["waiver_count"]) for row in rows) + sum(
        int(summary.get("waiver_count", 0)) for summary in negative_summaries
    )
    return {
        "schema_version": "aan09_5.pm_evidence_table.v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "asset_count": len(rows),
            "status_counts": status_counts,
            "waiver_count": waiver_count,
            "failure_modes": failure_modes,
        },
        "rows": rows,
        "inputs": {
            "manifests": [str(path) for path in manifest_paths],
            "negative_summaries": [str(path) for path in negative_summary_paths or []],
        },
        "claim_boundary": {
            "ready": "Package/runtime/benchmark evidence exists for the recorded gates.",
            "blocked": "Do not claim task readiness; use blocked reason and required resolution.",
            "ready_with_waivers": "Only scoped claims are allowed; waiver forbidden claims remain binding.",
        },
    }


def render_pm_evidence_markdown(table: dict[str, Any]) -> str:
    lines = [
        "# AAN PM Evidence Table",
        "",
        "| Asset | Status | Gates | Evidence | Failure / Waiver | Claims boundary |",
        "|---|---|---|---|---|---|",
    ]
    for row in table["rows"]:
        evidence = _markdown_cell(
            ", ".join(
                f"{key}:{value}"
                for key, value in row["evidence_summary"].items()
                if value not in {None, "not_present"}
            )
        )
        failure = row.get("failure_mode") or ", ".join(row.get("waiver_ids", [])) or "none"
        forbidden = row.get("claim_boundary", {}).get("forbidden", [])
        boundary = _markdown_cell("; ".join(forbidden[:3]) if forbidden else "standard AAN claim boundary")
        lines.append(
            "| {asset} | {status} | {gates} | {evidence} | {failure} | {boundary} |".format(
                asset=_markdown_cell(str(row["asset_id"])),
                status=_markdown_cell(str(row["pm_status"])),
                gates=_markdown_cell(str(row["gate_summary"])),
                evidence=evidence,
                failure=_markdown_cell(str(failure)),
                boundary=boundary,
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Asset count: {table['summary']['asset_count']}",
            f"- Status counts: {json.dumps(table['summary']['status_counts'], ensure_ascii=False, sort_keys=True)}",
            f"- Waiver count: {table['summary']['waiver_count']}",
            f"- Failure modes: {json.dumps(table['summary']['failure_modes'], ensure_ascii=False, sort_keys=True)}",
            "",
        ]
    )
    return "\n".join(lines)


def write_pm_evidence_outputs(json_out: Path, markdown_out: Path, table: dict[str, Any]) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_pm_evidence_markdown(table), encoding="utf-8")


def _row_from_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    stage_statuses = {
        str(gate.get("stage")): str(gate.get("status"))
        for gate in manifest.get("stage_gates", [])
    }
    blocked_reasons = manifest.get("blocked_reasons", [])
    waivers = manifest.get("waivers", [])
    return {
        "manifest": str(path),
        "asset_id": manifest.get("asset_id"),
        "task_id": manifest.get("task_id"),
        "source_path": manifest.get("source", {}).get("path"),
        "target_runtime": manifest.get("target", {}).get("target_runtime_profile"),
        "target_benchmark": manifest.get("target", {}).get("target_benchmark_profile"),
        "milestone": manifest.get("milestone"),
        "overall_status": manifest.get("overall_status"),
        "pm_status": _pm_status(manifest),
        "gate_summary": _gate_summary(stage_statuses),
        "stage_statuses": stage_statuses,
        "evidence_summary": _evidence_summary(manifest),
        "failure_mode": _first_blocker_id(blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "waiver_count": len(waivers),
        "waiver_ids": [item.get("waiver_id") for item in waivers if item.get("waiver_id")],
        "claim_boundary": {
            "allowed": list(manifest.get("claims_allowed", [])),
            "forbidden": list(manifest.get("claims_forbidden", [])),
        },
    }


def _pm_status(manifest: dict[str, Any]) -> str:
    status = str(manifest.get("overall_status", "unknown"))
    if status in {"pass", "ready"}:
        if not _has_runtime_smoke_pass(manifest):
            return "contract_ready_runtime_pending"
        return "ready"
    if status == "ready_with_waivers":
        return "ready_with_waivers"
    if status == "blocked":
        return "blocked"
    if status == "dry_run_incomplete":
        return "incomplete"
    return status


def _has_runtime_smoke_pass(manifest: dict[str, Any]) -> bool:
    stage_statuses = {
        str(gate.get("stage")): str(gate.get("status"))
        for gate in manifest.get("stage_gates", [])
    }
    runtime = manifest.get("runtime_evidence", {})
    runtime_status = runtime.get("status") if isinstance(runtime, dict) else None
    if "runtime_smoke" in stage_statuses:
        return stage_statuses["runtime_smoke"] == "pass" and runtime_status == "pass"
    return False


def _gate_summary(stage_statuses: dict[str, str]) -> str:
    return ", ".join(f"{stage}={status}" for stage, status in stage_statuses.items())


def _evidence_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    runtime = manifest.get("runtime_evidence", {})
    benchmark = manifest.get("benchmark_contract", {})
    render = runtime.get("render_readback", {}) if isinstance(runtime, dict) else {}
    return {
        "manifest": "present",
        "runtime": runtime.get("status", "not_present") if isinstance(runtime, dict) else "not_present",
        "render_readback": render.get("status", "not_present") if isinstance(render, dict) else "not_present",
        "render_non_background_ratio": render.get("non_background_ratio") if isinstance(render, dict) else None,
        "benchmark_contract": benchmark.get("status", "not_present") if isinstance(benchmark, dict) else "not_present",
    }


def _first_blocker_id(blocked_reasons: list[dict[str, Any]]) -> str | None:
    for item in blocked_reasons:
        if item.get("blocker_id"):
            return str(item["blocker_id"])
    return None


def _merge_failure_modes(
    rows: list[dict[str, Any]],
    negative_summaries: list[dict[str, Any]],
) -> dict[str, int]:
    modes: dict[str, int] = {}
    for row in rows:
        mode = row.get("failure_mode")
        if mode:
            modes[mode] = modes.get(mode, 0) + 1
    for summary in negative_summaries:
        for mode, value in summary.get("failure_modes", {}).items():
            count = int(value.get("count", 0)) if isinstance(value, dict) else int(value)
            modes[mode] = max(modes.get(mode, 0), count)
    return modes


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build AAN-09.5 PM evidence table")
    parser.add_argument("--manifest", action="append", default=[], help="AAN manifest JSON path")
    parser.add_argument(
        "--negative-summary",
        action="append",
        default=[],
        help="AAN-09 negative summary JSON path",
    )
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--markdown-out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    table = build_pm_evidence_table(
        [Path(path) for path in args.manifest],
        [Path(path) for path in args.negative_summary],
    )
    write_pm_evidence_outputs(Path(args.json_out), Path(args.markdown_out), table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
