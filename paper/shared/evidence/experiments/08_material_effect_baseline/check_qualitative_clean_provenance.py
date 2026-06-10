#!/usr/bin/env python3
"""Check whether the material-effect qualitative panel has clean render provenance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
GRSCENES_RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_MANIFEST = RAW_DIR / "qualitative_render_manifest.json"
DEFAULT_LOG_ROOTS = [
    GRSCENES_RAW_DIR / "retake_zoom_render_logs",
    RAW_DIR / "qualitative_render_logs",
]
REQUIRED_CONDITIONS = [
    "original_MDL",
    "existing_noMDL",
    "nvidia_asset_converter_preview_or_bake",
]
ORIGINAL_ERROR_TERMS = [
    "C108",
    "C120",
    "Failed to create MDL shade node",
    "KooPbr",
    "KooPbr_maps",
    "could not find module",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _records_by_case(manifest: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    records: dict[str, dict[str, dict[str, Any]]] = {}
    for record in manifest.get("records", []):
        sample_id = str(record.get("sample_id") or "")
        condition = str(record.get("condition") or "")
        if sample_id and condition:
            records.setdefault(sample_id, {})[condition] = record
    return records


def _selected_sample_ids(manifest: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for case in manifest.get("selected_cases", []):
        sample_id = str(case.get("sample_id") or "")
        if sample_id and sample_id not in ids:
            ids.append(sample_id)
    if ids:
        return ids
    for record in manifest.get("records", []):
        sample_id = str(record.get("sample_id") or "")
        if sample_id and sample_id not in ids:
            ids.append(sample_id)
    return ids


def _image_is_ready(record: dict[str, Any]) -> bool:
    image = record.get("image") or {}
    path = Path(str(image.get("path") or ""))
    return image.get("status") == "ready" and path.is_file()


def _explicit_log_path(record: dict[str, Any]) -> Path | None:
    for key in ("stderr_log_path", "log_path"):
        value = record.get(key)
        if value:
            return Path(str(value))
    for key in ("render_log", "logs", "provenance"):
        value = record.get(key)
        if isinstance(value, dict):
            for nested_key in ("stderr_path", "stderr_log_path", "log_path"):
                nested = value.get(nested_key)
                if nested:
                    return Path(str(nested))
    return None


def _candidate_original_log_paths(record: dict[str, Any], log_roots: list[Path]) -> list[Path]:
    sample_id = str(record.get("sample_id") or "")
    explicit = _explicit_log_path(record)
    candidates: list[Path] = [explicit] if explicit else []
    if sample_id:
        for root in log_roots:
            candidates.extend(
                [
                    root / sample_id / f"{sample_id}.original.stderr.txt",
                    root / sample_id / "original.stderr.txt",
                ]
            )
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        if path is None:
            continue
        key = str(path)
        if key not in seen:
            out.append(path)
            seen.add(key)
    return out


def _find_existing_path(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def _matched_error_terms(text: str) -> list[str]:
    return [term for term in ORIGINAL_ERROR_TERMS if term in text]


def check_qualitative_clean_provenance(
    manifest: dict[str, Any],
    *,
    log_roots: list[Path] | None = None,
) -> dict[str, Any]:
    roots = [Path(root) for root in (log_roots or DEFAULT_LOG_ROOTS)]
    records_by_case = _records_by_case(manifest)
    selected_ids = _selected_sample_ids(manifest)
    violations: list[dict[str, Any]] = []
    complete_case_count = 0
    checked_original_logs = 0
    missing_original_logs = 0
    original_error_signal_count = 0

    for sample_id in selected_ids:
        case_records = records_by_case.get(sample_id, {})
        missing_conditions = [
            condition
            for condition in REQUIRED_CONDITIONS
            if condition not in case_records or not _image_is_ready(case_records[condition])
        ]
        if missing_conditions:
            violations.append(
                {
                    "sample_id": sample_id,
                    "condition": "case",
                    "reason": "incomplete_three_condition_case",
                    "missing_or_unready_conditions": missing_conditions,
                }
            )
            continue

        complete_case_count += 1
        original_record = case_records["original_MDL"]
        candidates = _candidate_original_log_paths(original_record, roots)
        log_path = _find_existing_path(candidates)
        if log_path is None:
            missing_original_logs += 1
            violations.append(
                {
                    "sample_id": sample_id,
                    "condition": "original_MDL",
                    "reason": "missing_original_mdl_stderr_log",
                    "candidate_paths": [str(path) for path in candidates],
                }
            )
            continue

        checked_original_logs += 1
        text = log_path.read_text(encoding="utf-8", errors="replace")
        matched_terms = _matched_error_terms(text)
        if matched_terms:
            original_error_signal_count += 1
            violations.append(
                {
                    "sample_id": sample_id,
                    "condition": "original_MDL",
                    "reason": "original_mdl_error_signal",
                    "log_path": str(log_path),
                    "matched_error_terms": matched_terms,
                }
            )

    blockers: list[str] = []
    if any(item["reason"] == "incomplete_three_condition_case" for item in violations):
        blockers.append("incomplete_three_condition_case")
    if missing_original_logs:
        blockers.append("missing_original_mdl_stderr_log")
    if original_error_signal_count:
        blockers.append("original_mdl_error_signal")

    ok = not violations and bool(selected_ids)
    return {
        "ok": ok,
        "status": "clean_material_effect_panel_ready" if ok else "blocked_material_effect_panel",
        "summary": {
            "selected_case_count": len(selected_ids),
            "complete_case_count": complete_case_count,
            "checked_original_mdl_log_count": checked_original_logs,
            "missing_original_mdl_log_count": missing_original_logs,
            "original_mdl_error_signal_count": original_error_signal_count,
            "blockers": blockers,
        },
        "claim_boundary": {
            "figure_can_be_reintroduced_to_acl_main_text": ok,
            "requires": [
                "all selected cases have ready original_MDL, existing_noMDL, and NVIDIA images",
                "every selected original_MDL render has a stderr log",
                "original_MDL stderr logs contain no KooPbr/KooPbr_maps/module/shade-node error signal",
            ],
        },
        "violations": violations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--log-root",
        type=Path,
        action="append",
        default=None,
        help="Directory containing per-sample stderr logs; may be passed multiple times.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print the report but exit 0 even when the panel is blocked.",
    )
    args = parser.parse_args(argv)

    report = check_qualitative_clean_provenance(
        _load_json(args.manifest),
        log_roots=args.log_root,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.report_only:
        return 0
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
