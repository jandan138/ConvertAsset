#!/usr/bin/env python3
"""Build material-effect baseline summary tables from the conversion manifest."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_CONVERSION_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/baseline_conversion_manifest.json"
)
DEFAULT_CSV = PROJECT_ROOT / "paper/shared/tables/material_effect_baseline_summary.csv"
DEFAULT_TEX = PROJECT_ROOT / "paper/shared/tables/tab_material_effect_baseline_summary.tex"
DEFAULT_CASES = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/effect_failure_case_manifest.json"
)
DEFAULT_SUPPLEMENTAL_CONVERSION_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/supplemental_conversion_manifest.json"
)
DEFAULT_SUPPLEMENTAL_VISUAL_QA_MANIFEST = (
    PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline/supplemental_qualitative_visual_qa.json"
)

CONDITION_ORDER = [
    "original_MDL",
    "existing_noMDL",
    "nvidia_asset_converter_preview_or_bake",
]
EFFECT_ORDER = [
    "clearcoat",
    "opacity_transparency",
    "emission",
    "procedural_texture",
    "normal_bump",
    "displacement_height",
]
CSV_FIELDS = [
    "effect",
    "condition",
    "sample_count",
    "available_count",
    "static_gate_passed_count",
    "static_gate_failed_count",
    "planned_output_missing_count",
    "missing_count",
    "other_non_available_count",
    "active_mdl_zero_count",
    "target_category_count",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _latex_escape(value: Any) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def _effect_order(effects: set[str]) -> list[str]:
    ordered = [effect for effect in EFFECT_ORDER if effect in effects]
    ordered.extend(sorted(effect for effect in effects if effect not in EFFECT_ORDER))
    return ordered


def _status_bucket(status: str) -> str:
    if status in {"available", "static_gate_failed", "planned_output_missing", "missing"}:
        return f"{status}_count"
    return "other_non_available_count"


def merge_conversion_manifests(
    conversion_manifest: dict[str, Any],
    supplemental_conversion_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not supplemental_conversion_manifest:
        return conversion_manifest
    merged = dict(conversion_manifest)
    merged["samples"] = [
        *conversion_manifest.get("samples", []),
        *supplemental_conversion_manifest.get("samples", []),
    ]
    merged["supplemental_source_manifest"] = supplemental_conversion_manifest.get("generated_by")
    return merged


def build_effect_summary_rows(conversion_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    effects = {
        str(effect)
        for sample in conversion_manifest.get("samples", [])
        for effect in sample.get("present_effects", [])
    }
    effects.update(EFFECT_ORDER)
    rows: list[dict[str, Any]] = []
    for effect in _effect_order(effects):
        samples = [
            sample
            for sample in conversion_manifest.get("samples", [])
            if effect in (sample.get("present_effects") or [])
        ]
        for condition in CONDITION_ORDER:
            counts: Counter[str] = Counter()
            categories = {str(sample.get("target_category")) for sample in samples}
            for sample in samples:
                record = (sample.get("conditions") or {}).get(condition) or {}
                status = str(record.get("status") or "missing")
                counts[_status_bucket(status)] += 1
                if record.get("static_gate_passed"):
                    counts["static_gate_passed_count"] += 1
                elif status not in {"planned_output_missing", "static_gate_failed"}:
                    counts["static_gate_failed_count"] += 1
                if record.get("active_mdl_shader_count") == 0:
                    counts["active_mdl_zero_count"] += 1
            row = {
                "effect": effect,
                "condition": condition,
                "sample_count": len(samples),
                "available_count": counts["available_count"],
                "static_gate_passed_count": counts["static_gate_passed_count"],
                "static_gate_failed_count": counts["static_gate_failed_count"],
                "planned_output_missing_count": counts["planned_output_missing_count"],
                "missing_count": counts["missing_count"],
                "other_non_available_count": counts["other_non_available_count"],
                "active_mdl_zero_count": counts["active_mdl_zero_count"],
                "target_category_count": len(categories),
            }
            rows.append(row)
    return rows


def _visual_failure_lookup(visual_qa_manifest: dict[str, Any] | None = None) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    if not visual_qa_manifest:
        return lookup
    for case in visual_qa_manifest.get("failure_cases") or []:
        sample_id = str(case.get("sample_id") or "")
        condition = str(case.get("condition") or "")
        if sample_id and condition:
            lookup[(sample_id, condition)] = case
    return lookup


def build_case_records(
    conversion_manifest: dict[str, Any],
    *,
    visual_qa_manifest: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    visual_failures = _visual_failure_lookup(visual_qa_manifest)
    for sample in conversion_manifest.get("samples", []):
        sample_id = str(sample.get("sample_id") or "")
        for effect in sample.get("present_effects") or []:
            for condition in CONDITION_ORDER:
                record = (sample.get("conditions") or {}).get(condition) or {}
                status = str(record.get("status") or "missing")
                if status == "available" and record.get("static_gate_passed"):
                    continue
                case_id = f"{effect}:{sample_id}:{condition}"
                if case_id in seen:
                    continue
                seen.add(case_id)
                case = {
                    "case_id": case_id,
                    "effect": effect,
                    "sample_id": sample.get("sample_id"),
                    "target_category": sample.get("target_category"),
                    "target_prim_path": sample.get("target_prim_path"),
                    "condition": condition,
                    "status": status,
                    "reason": status if status != "available" else "static_gate_failed",
                    "usd_path": record.get("usd_path"),
                }
                visual_failure = visual_failures.get((sample_id, condition))
                if visual_failure:
                    case.update(
                        {
                            "has_rendered_failure_evidence": True,
                            "rendered_failure_reason": visual_failure.get("reason"),
                            "rendered_failure_evidence": visual_failure.get("evidence"),
                            "rendered_failure_image_path": visual_failure.get("image_path"),
                            "rendered_failure_source_status": visual_failure.get("source_condition_status"),
                        }
                    )
                cases.append(case)
    return cases


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_summary_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Auto-generated by build_effect_tables.py",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Effect & Condition & Samples & Available & Gate pass & NVIDIA missing \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(
                [
                    _latex_escape(row["effect"]),
                    _latex_escape(row["condition"]),
                    _latex_escape(row["sample_count"]),
                    _latex_escape(row["available_count"]),
                    _latex_escape(row.get("static_gate_passed_count", "")),
                    _latex_escape(row.get("planned_output_missing_count", "")),
                ]
            )
            + " \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_case_manifest(
    path: Path,
    cases: list[dict[str, Any]],
    *,
    generated_at_utc: str | None = None,
    source_manifest: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_reason: dict[str, int] = defaultdict(int)
    rendered_failure_count = 0
    for case in cases:
        by_reason[str(case.get("reason"))] += 1
        if case.get("has_rendered_failure_evidence"):
            rendered_failure_count += 1
    payload = {
        "schema_version": 1,
        "status": "material_effect_failure_case_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "source_manifest": source_manifest,
        "summary": {
            "case_count": len(cases),
            "rendered_failure_evidence_count": rendered_failure_count,
            "reason_counts": dict(sorted(by_reason.items())),
        },
        "cases": cases,
        "claim_boundary": {
            "allowed": [
                "These are selected non-available or static-gate-failed condition cases for follow-up.",
                "Cases with rendered_failure_* fields have linked rendered QA evidence.",
            ],
            "forbidden": [
                "Do not treat planned missing NVIDIA outputs as visual failures.",
                "Do not call this a final error distribution before broader sampling finishes.",
                "Do not call linked rendered evidence a successful qualitative panel if clean-room visual review failed.",
            ],
        },
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversion-manifest", type=Path, default=DEFAULT_CONVERSION_MANIFEST)
    parser.add_argument(
        "--supplemental-conversion-manifest",
        type=Path,
        default=DEFAULT_SUPPLEMENTAL_CONVERSION_MANIFEST,
    )
    parser.add_argument(
        "--supplemental-visual-qa-manifest",
        type=Path,
        default=DEFAULT_SUPPLEMENTAL_VISUAL_QA_MANIFEST,
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = _load_json(args.conversion_manifest)
    supplemental_manifest = (
        _load_json(args.supplemental_conversion_manifest)
        if args.supplemental_conversion_manifest and args.supplemental_conversion_manifest.exists()
        else None
    )
    supplemental_visual_qa = (
        _load_json(args.supplemental_visual_qa_manifest)
        if args.supplemental_visual_qa_manifest and args.supplemental_visual_qa_manifest.exists()
        else None
    )
    manifest = merge_conversion_manifests(manifest, supplemental_manifest)
    rows = build_effect_summary_rows(manifest)
    cases = build_case_records(manifest, visual_qa_manifest=supplemental_visual_qa)
    write_summary_csv(args.csv, rows)
    write_summary_tex(args.tex, rows)
    write_case_manifest(args.cases, cases, source_manifest=str(args.conversion_manifest))
    print(f"Wrote {args.csv} rows={len(rows)}")
    print(f"Wrote {args.tex} rows={len(rows)}")
    print(f"Wrote {args.cases} cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
