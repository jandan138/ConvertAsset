import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py"


def load_module():
    spec = importlib.util.spec_from_file_location("material_effect_risk_matrix", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _condition(status: str, *, gate: bool) -> dict:
    return {"status": status, "static_gate_passed": gate}


def _base_manifest() -> dict:
    return {
        "samples": [
            {
                "sample_id": "cup.zoom_001",
                "target_category": "cup",
                "present_effects": ["opacity_transparency"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True),
                    "existing_noMDL": _condition("available", gate=True),
                    "nvidia_asset_converter_preview_or_bake": _condition("available", gate=True),
                },
            }
        ]
    }


def _supplemental_manifest() -> dict:
    return {
        "samples": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "target_category": "supplemental_material_fixture",
                "present_effects": ["clearcoat"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True),
                    "existing_noMDL": _condition("available", gate=True),
                    "nvidia_asset_converter_preview_or_bake": _condition("static_gate_failed", gate=False),
                },
            },
            {
                "sample_id": "supplemental_procedural_checker",
                "target_category": "supplemental_material_fixture",
                "present_effects": ["procedural_texture"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True),
                    "existing_noMDL": _condition("available", gate=True),
                    "nvidia_asset_converter_preview_or_bake": _condition("available", gate=True),
                },
            },
        ]
    }


def _qualitative_manifest() -> dict:
    return {
        "summary": {
            "ready_for_contact_sheet": True,
            "ready_for_visual_quality_claim": False,
        },
        "selected_cases": [
            {
                "sample_id": "cup.zoom_001",
                "covered_effects": ["opacity_transparency"],
                "condition_statuses": {
                    "original_MDL": "image_ready",
                    "existing_noMDL": "image_ready",
                    "nvidia_asset_converter_preview_or_bake": "render_ready",
                },
            }
        ],
    }


def _supplemental_visual_review() -> dict:
    return {
        "summary": {"overall_verdict": "FAIL", "ready_for_paper_success_panel": False},
        "per_image_reviews": [
            {
                "effect": "clearcoat",
                "condition": "existing_noMDL",
                "verdict": "WARN",
                "main_risk": "Possible material fallback or loss of blue/clearcoat appearance.",
            },
            {
                "effect": "clearcoat",
                "condition": "nvidia_asset_converter_preview_or_bake",
                "verdict": "FAIL",
                "main_risk": "Missing target makes comparison invalid.",
            },
            {
                "effect": "procedural_texture",
                "condition": "existing_noMDL",
                "verdict": "FAIL",
                "main_risk": "Missing procedural texture/material fallback.",
            },
            {
                "effect": "procedural_texture",
                "condition": "nvidia_asset_converter_preview_or_bake",
                "verdict": "FAIL",
                "main_risk": "Missing procedural texture or baked result not visibly preserving the pattern.",
            },
        ],
    }


def _supplemental_diagnostic() -> dict:
    return {
        "summary": {
            "ready_for_success_panel": False,
            "ready_for_failure_case_writeup": True,
            "blockers": [
                "nvidia_clearcoat_target_missing",
                "procedural_checker_not_preserved_in_converted_conditions",
            ],
        },
        "cases": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "effect": "clearcoat",
                "case_verdict": "FAIL",
                "conditions": {
                    "existing_noMDL": {
                        "verdict": "WARN",
                        "diagnostic_reason": "clearcoat_approximated_by_preview_surface",
                    },
                    "nvidia_asset_converter_preview_or_bake": {
                        "verdict": "FAIL",
                        "diagnostic_reason": "converted_stage_missing_target_prim",
                    },
                },
            },
            {
                "sample_id": "supplemental_procedural_checker",
                "effect": "procedural_texture",
                "case_verdict": "FAIL",
                "source_checker_authored": True,
                "conditions": {
                    "existing_noMDL": {
                        "verdict": "FAIL",
                        "diagnostic_reason": "converted_preview_surface_lacks_checker_texture",
                    },
                    "nvidia_asset_converter_preview_or_bake": {
                        "verdict": "FAIL",
                        "diagnostic_reason": "converted_preview_surface_lacks_checker_texture",
                    },
                },
            },
        ],
    }


def test_build_risk_rows_separates_ready_covered_bins_from_supplemental_failures() -> None:
    module = load_module()

    rows = module.build_risk_rows(
        _base_manifest(),
        supplemental_conversion_manifest=_supplemental_manifest(),
        qualitative_render_manifest=_qualitative_manifest(),
        supplemental_visual_review=_supplemental_visual_review(),
        supplemental_material_diagnostic=_supplemental_diagnostic(),
    )
    by_effect = {row["effect"]: row for row in rows}

    opacity = by_effect["opacity_transparency"]
    assert opacity["sample_source"] == "GRScenes expanded30"
    assert opacity["qualitative_status"] == "selected_panel_ready"
    assert opacity["claim_allowed"] == "bounded_static_and_selected_qualitative"
    assert opacity["claim_forbidden"] == "final_visual_quality_win"
    assert "supplemental_clean_room_visual_review.json" not in opacity["evidence_sources"]

    clearcoat = by_effect["clearcoat"]
    assert clearcoat["sample_source"] == "supplemental_official_or_sample_wrapper"
    assert "clearcoat_approximated_by_preview_surface" in clearcoat["convertasset_risk"]
    assert "target_missing" in clearcoat["nvidia_risk"]
    assert clearcoat["relative_interpretation"] == "selected_nvidia_failure_convertasset_target_retained"
    assert clearcoat["claim_allowed"] == "selected_nvidia_failure_case"
    assert "population_failure_rate" in clearcoat["claim_forbidden"]

    procedural = by_effect["procedural_texture"]
    assert procedural["convertasset_risk"] == "checker_not_preserved"
    assert procedural["nvidia_risk"] == "checker_not_preserved"
    assert procedural["relative_interpretation"] == "both_converted_conditions_risky_static_gate_insufficient"
    assert "procedural_preservation_success" in procedural["claim_forbidden"]


def test_write_risk_outputs_creates_csv_tex_and_profile(tmp_path: Path) -> None:
    module = load_module()
    rows = [
        {
            "effect": "clearcoat",
            "sample_source": "supplemental_official_or_sample_wrapper",
            "sample_count": 1,
            "static_gate_summary": "original=1/1, convertasset=1/1, nvidia=0/1",
            "qualitative_status": "supplemental_visual_fail",
            "convertasset_risk": "clearcoat_approximated_by_preview_surface",
            "nvidia_risk": "target_missing",
            "relative_interpretation": "selected_nvidia_failure_convertasset_target_retained",
            "claim_allowed": "selected_nvidia_failure_case",
            "claim_forbidden": "population_failure_rate; success_panel",
            "evidence_sources": "supplemental_conversion_manifest.json; supplemental_material_preservation_diagnostic.json",
        }
    ]
    csv_path = tmp_path / "risk.csv"
    tex_path = tmp_path / "risk.tex"
    profile_path = tmp_path / "risk.json"

    module.write_risk_csv(csv_path, rows)
    module.write_risk_tex(tex_path, rows)
    module.write_risk_profile_json(profile_path, rows, generated_at_utc="2026-05-26T00:00:00Z")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        loaded = list(csv.DictReader(handle))
    assert loaded[0]["effect"] == "clearcoat"
    assert b"\r" not in csv_path.read_bytes()
    assert "selected\\_nvidia\\_failure" in tex_path.read_text(encoding="utf-8")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    assert profile["summary"]["effect_count"] == 1
    assert profile["summary"]["selected_nvidia_failure_case_count"] == 1
    assert profile["claim_boundary"]["forbidden"]
