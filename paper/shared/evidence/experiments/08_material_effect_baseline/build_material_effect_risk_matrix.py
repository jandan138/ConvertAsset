#!/usr/bin/env python3
"""Build a claim-boundary risk matrix for the material-effect baseline."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_ROOT = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
TABLE_ROOT = PROJECT_ROOT / "paper/shared/tables"

DEFAULT_CONVERSION_MANIFEST = RAW_ROOT / "baseline_conversion_manifest.json"
DEFAULT_SUPPLEMENTAL_CONVERSION_MANIFEST = RAW_ROOT / "supplemental_conversion_manifest.json"
DEFAULT_QUALITATIVE_RENDER_MANIFEST = RAW_ROOT / "qualitative_render_manifest.json"
DEFAULT_SUPPLEMENTAL_VISUAL_REVIEW = RAW_ROOT / "supplemental_clean_room_visual_review.json"
DEFAULT_SUPPLEMENTAL_MATERIAL_DIAGNOSTIC = RAW_ROOT / "supplemental_material_preservation_diagnostic.json"
DEFAULT_CSV = TABLE_ROOT / "material_effect_risk_matrix.csv"
DEFAULT_TEX = TABLE_ROOT / "tab_material_effect_risk_matrix.tex"
DEFAULT_PROFILE = RAW_ROOT / "material_effect_risk_profile.json"

CONDITION_LABELS = {
    "original_MDL": "original",
    "existing_noMDL": "convertasset",
    "nvidia_asset_converter_preview_or_bake": "nvidia",
}
CONVERTASSET_CONDITION = "existing_noMDL"
NVIDIA_CONDITION = "nvidia_asset_converter_preview_or_bake"
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
    "sample_source",
    "sample_count",
    "static_gate_summary",
    "qualitative_status",
    "convertasset_risk",
    "nvidia_risk",
    "relative_interpretation",
    "claim_allowed",
    "claim_forbidden",
    "evidence_sources",
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


def _merge_samples(
    conversion_manifest: dict[str, Any],
    supplemental_conversion_manifest: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    samples = list(conversion_manifest.get("samples") or [])
    if supplemental_conversion_manifest:
        samples.extend(supplemental_conversion_manifest.get("samples") or [])
    return samples


def _effect_order(effects: set[str]) -> list[str]:
    ordered = [effect for effect in EFFECT_ORDER if effect in effects]
    ordered.extend(sorted(effect for effect in effects if effect not in EFFECT_ORDER))
    return ordered


def _is_supplemental_sample(sample: dict[str, Any]) -> bool:
    sample_id = str(sample.get("sample_id") or "")
    category = str(sample.get("target_category") or "")
    return sample_id.startswith("supplemental_") or category == "supplemental_material_fixture"


def _sample_source(samples: list[dict[str, Any]]) -> str:
    if not samples:
        return "no_sample"
    supplemental_count = sum(1 for sample in samples if _is_supplemental_sample(sample))
    if supplemental_count == len(samples):
        return "supplemental_official_or_sample_wrapper"
    if supplemental_count == 0:
        return "GRScenes expanded30"
    return "mixed_grscenes_and_supplemental"


def _static_gate_summary(samples: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for condition, label in CONDITION_LABELS.items():
        passed = 0
        for sample in samples:
            record = (sample.get("conditions") or {}).get(condition) or {}
            if record.get("static_gate_passed"):
                passed += 1
        parts.append(f"{label}={passed}/{len(samples)}")
    return ", ".join(parts)


def _qualitative_status_by_effect(qualitative_render_manifest: dict[str, Any] | None) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if not qualitative_render_manifest:
        return statuses
    for case in qualitative_render_manifest.get("selected_cases") or []:
        condition_statuses = case.get("condition_statuses") or {}
        all_ready = all(str(status) in {"image_ready", "render_ready"} for status in condition_statuses.values())
        for effect in case.get("covered_effects") or []:
            if all_ready:
                statuses[str(effect)] = "selected_panel_ready"
    return statuses


def _supplemental_panel_status_by_effect(supplemental_visual_review: dict[str, Any] | None) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if not supplemental_visual_review:
        return statuses
    for panel in supplemental_visual_review.get("panel_reviews") or []:
        effect = str(panel.get("effect") or "")
        verdict = str(panel.get("verdict") or "").upper()
        if effect and verdict == "FAIL":
            statuses[effect] = "supplemental_visual_fail"
        elif effect and verdict == "WARN":
            statuses[effect] = "supplemental_visual_warn"
    if statuses:
        return statuses

    per_effect_verdicts: dict[str, set[str]] = defaultdict(set)
    for review in supplemental_visual_review.get("per_image_reviews") or []:
        effect = str(review.get("effect") or "")
        verdict = str(review.get("verdict") or "").upper()
        if effect and verdict:
            per_effect_verdicts[effect].add(verdict)
    for effect, verdicts in per_effect_verdicts.items():
        if "FAIL" in verdicts:
            statuses[effect] = "supplemental_visual_fail"
        elif "WARN" in verdicts:
            statuses[effect] = "supplemental_visual_warn"
    return statuses


def _diagnostic_reason_by_effect_condition(
    supplemental_material_diagnostic: dict[str, Any] | None,
) -> dict[tuple[str, str], str]:
    reasons: dict[tuple[str, str], str] = {}
    if not supplemental_material_diagnostic:
        return reasons
    for case in supplemental_material_diagnostic.get("cases") or []:
        effect = str(case.get("effect") or "")
        for condition, record in (case.get("conditions") or {}).items():
            reason = str((record or {}).get("diagnostic_reason") or "")
            if effect and condition and reason:
                reasons[(effect, condition)] = reason
    return reasons


def _visual_risk_by_effect_condition(supplemental_visual_review: dict[str, Any] | None) -> dict[tuple[str, str], str]:
    risks: dict[tuple[str, str], str] = {}
    if not supplemental_visual_review:
        return risks
    for review in supplemental_visual_review.get("per_image_reviews") or []:
        effect = str(review.get("effect") or "")
        condition = str(review.get("condition") or "")
        verdict = str(review.get("verdict") or "").lower()
        main_risk = str(review.get("main_risk") or "")
        if effect and condition and verdict in {"warn", "fail"}:
            risks[(effect, condition)] = f"visual_{verdict}:{main_risk}"
    return risks


def _condition_has_failed_static_gate(samples: list[dict[str, Any]], condition: str) -> bool:
    for sample in samples:
        record = (sample.get("conditions") or {}).get(condition) or {}
        if str(record.get("status") or "") == "static_gate_failed" or record.get("static_gate_passed") is False:
            return True
    return False


def _risk_for_condition(
    *,
    effect: str,
    samples: list[dict[str, Any]],
    condition: str,
    qualitative_status: str,
    diagnostic_reasons: dict[tuple[str, str], str],
    visual_risks: dict[tuple[str, str], str],
) -> str:
    reason = diagnostic_reasons.get((effect, condition), "")
    visual_risk = visual_risks.get((effect, condition), "")
    if reason == "converted_stage_missing_target_prim":
        return "target_missing"
    if reason == "converted_preview_surface_lacks_checker_texture":
        return "checker_not_preserved"
    if reason == "clearcoat_approximated_by_preview_surface":
        return "; ".join(part for part in [reason, visual_risk] if part)
    if _condition_has_failed_static_gate(samples, condition):
        return "static_gate_failed"
    if visual_risk:
        return visual_risk
    if qualitative_status == "selected_panel_ready":
        return "bounded_visual_review_warn_or_pass"
    if not samples:
        return "no_sample"
    return "static_gate_only"


def _relative_interpretation(convertasset_risk: str, nvidia_risk: str, qualitative_status: str) -> str:
    if "target_missing" in nvidia_risk:
        return "selected_nvidia_failure_convertasset_target_retained"
    if convertasset_risk == "checker_not_preserved" and nvidia_risk == "checker_not_preserved":
        return "both_converted_conditions_risky_static_gate_insufficient"
    if qualitative_status == "selected_panel_ready":
        return "bounded_three_condition_static_and_qualitative_evidence"
    return "static_evidence_only"


def _claim_allowed(relative_interpretation: str, qualitative_status: str) -> str:
    if relative_interpretation == "selected_nvidia_failure_convertasset_target_retained":
        return "selected_nvidia_failure_case"
    if relative_interpretation == "both_converted_conditions_risky_static_gate_insufficient":
        return "diagnostic_limitation_case"
    if qualitative_status == "selected_panel_ready":
        return "bounded_static_and_selected_qualitative"
    return "static_readiness_only"


def _claim_forbidden(relative_interpretation: str, qualitative_status: str) -> str:
    if relative_interpretation == "selected_nvidia_failure_convertasset_target_retained":
        return "population_failure_rate; success_panel"
    if relative_interpretation == "both_converted_conditions_risky_static_gate_insufficient":
        return "procedural_preservation_success; success_panel; population_failure_rate"
    if qualitative_status == "selected_panel_ready":
        return "final_visual_quality_win"
    return "visual_success_claim"


def _evidence_sources(
    *,
    sample_source: str,
    qualitative_status: str,
    convertasset_risk: str,
    nvidia_risk: str,
) -> str:
    sources = ["baseline_conversion_manifest.json"]
    if sample_source != "GRScenes expanded30":
        sources.append("supplemental_conversion_manifest.json")
    if qualitative_status == "selected_panel_ready":
        sources.append("qualitative_render_manifest.json")
    has_supplemental_visual_risk = convertasset_risk.startswith("visual_") or nvidia_risk.startswith("visual_")
    if qualitative_status.startswith("supplemental_visual") or has_supplemental_visual_risk:
        sources.append("supplemental_clean_room_visual_review.json")
    if {
        convertasset_risk,
        nvidia_risk,
    } & {"target_missing", "checker_not_preserved"} or "clearcoat_approximated_by_preview_surface" in convertasset_risk:
        sources.append("supplemental_material_preservation_diagnostic.json")
    return "; ".join(dict.fromkeys(sources))


def build_risk_rows(
    conversion_manifest: dict[str, Any],
    *,
    supplemental_conversion_manifest: dict[str, Any] | None = None,
    qualitative_render_manifest: dict[str, Any] | None = None,
    supplemental_visual_review: dict[str, Any] | None = None,
    supplemental_material_diagnostic: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    samples = _merge_samples(conversion_manifest, supplemental_conversion_manifest)
    effects = {
        str(effect)
        for sample in samples
        for effect in (sample.get("present_effects") or [])
    }
    effects.update(EFFECT_ORDER)
    qualitative_statuses = _qualitative_status_by_effect(qualitative_render_manifest)
    supplemental_panel_statuses = _supplemental_panel_status_by_effect(supplemental_visual_review)
    diagnostic_reasons = _diagnostic_reason_by_effect_condition(supplemental_material_diagnostic)
    visual_risks = _visual_risk_by_effect_condition(supplemental_visual_review)

    rows: list[dict[str, Any]] = []
    for effect in _effect_order(effects):
        effect_samples = [
            sample
            for sample in samples
            if effect in (sample.get("present_effects") or [])
        ]
        qualitative_status = qualitative_statuses.get(effect) or supplemental_panel_statuses.get(effect) or "static_only"
        sample_source = _sample_source(effect_samples)
        convertasset_risk = _risk_for_condition(
            effect=effect,
            samples=effect_samples,
            condition=CONVERTASSET_CONDITION,
            qualitative_status=qualitative_status,
            diagnostic_reasons=diagnostic_reasons,
            visual_risks=visual_risks,
        )
        nvidia_risk = _risk_for_condition(
            effect=effect,
            samples=effect_samples,
            condition=NVIDIA_CONDITION,
            qualitative_status=qualitative_status,
            diagnostic_reasons=diagnostic_reasons,
            visual_risks=visual_risks,
        )
        relative = _relative_interpretation(convertasset_risk, nvidia_risk, qualitative_status)
        rows.append(
            {
                "effect": effect,
                "sample_source": sample_source,
                "sample_count": len(effect_samples),
                "static_gate_summary": _static_gate_summary(effect_samples),
                "qualitative_status": qualitative_status,
                "convertasset_risk": convertasset_risk,
                "nvidia_risk": nvidia_risk,
                "relative_interpretation": relative,
                "claim_allowed": _claim_allowed(relative, qualitative_status),
                "claim_forbidden": _claim_forbidden(relative, qualitative_status),
                "evidence_sources": _evidence_sources(
                    sample_source=sample_source,
                    qualitative_status=qualitative_status,
                    convertasset_risk=convertasset_risk,
                    nvidia_risk=nvidia_risk,
                ),
            }
        )
    return rows


def write_risk_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_risk_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Auto-generated by build_material_effect_risk_matrix.py",
        "\\begin{tabular}{llll}",
        "\\toprule",
        "Effect & Evidence status & Relative interpretation & Claim allowed \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(
                [
                    _latex_escape(row["effect"]),
                    _latex_escape(row["qualitative_status"]),
                    _latex_escape(row["relative_interpretation"]),
                    _latex_escape(row["claim_allowed"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    allowed_counts = Counter(str(row.get("claim_allowed") or "") for row in rows)
    status_counts = Counter(str(row.get("qualitative_status") or "") for row in rows)
    return {
        "effect_count": len(rows),
        "selected_panel_ready_count": status_counts["selected_panel_ready"],
        "supplemental_visual_fail_count": status_counts["supplemental_visual_fail"],
        "selected_nvidia_failure_case_count": allowed_counts["selected_nvidia_failure_case"],
        "diagnostic_limitation_case_count": allowed_counts["diagnostic_limitation_case"],
        "bounded_static_and_selected_qualitative_count": allowed_counts[
            "bounded_static_and_selected_qualitative"
        ],
    }


def write_risk_profile_json(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    generated_at_utc: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "status": "material_effect_risk_profile",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "summary": _summarize_rows(rows),
        "rows": rows,
        "claim_boundary": {
            "allowed": [
                "Use the matrix to separate static readiness, selected qualitative evidence, and selected failure/limitation evidence by effect bin.",
                "Use clearcoat as a selected NVIDIA failure case only when paired with the linked static and visual evidence.",
                "Use procedural texture as a limitation/investigation case until a checker-preserving conversion or baking path exists.",
            ],
            "forbidden": [
                "Do not treat the supplemental cases as population-level failure rates.",
                "Do not call the supplemental contact sheet a successful all-effects qualitative comparison.",
                "Do not use static-gate pass alone as proof of procedural texture preservation.",
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
        "--qualitative-render-manifest",
        type=Path,
        default=DEFAULT_QUALITATIVE_RENDER_MANIFEST,
    )
    parser.add_argument("--supplemental-visual-review", type=Path, default=DEFAULT_SUPPLEMENTAL_VISUAL_REVIEW)
    parser.add_argument(
        "--supplemental-material-diagnostic",
        type=Path,
        default=DEFAULT_SUPPLEMENTAL_MATERIAL_DIAGNOSTIC,
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = build_risk_rows(
        _load_json(args.conversion_manifest),
        supplemental_conversion_manifest=_load_json(args.supplemental_conversion_manifest)
        if args.supplemental_conversion_manifest.exists()
        else None,
        qualitative_render_manifest=_load_json(args.qualitative_render_manifest)
        if args.qualitative_render_manifest.exists()
        else None,
        supplemental_visual_review=_load_json(args.supplemental_visual_review)
        if args.supplemental_visual_review.exists()
        else None,
        supplemental_material_diagnostic=_load_json(args.supplemental_material_diagnostic)
        if args.supplemental_material_diagnostic.exists()
        else None,
    )
    write_risk_csv(args.csv, rows)
    write_risk_tex(args.tex, rows)
    write_risk_profile_json(args.profile, rows)
    print(f"Wrote {args.csv} rows={len(rows)}")
    print(f"Wrote {args.tex} rows={len(rows)}")
    print(f"Wrote {args.profile} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
