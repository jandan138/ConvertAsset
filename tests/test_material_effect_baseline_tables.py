import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/08_material_effect_baseline/build_effect_tables.py"


def load_tables_module():
    spec = importlib.util.spec_from_file_location("material_effect_tables", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _condition(status: str, *, gate: bool, preview: int | None, active_mdl: int | None) -> dict:
    return {
        "status": status,
        "static_gate_passed": gate,
        "preview_surface_count": preview,
        "active_mdl_shader_count": active_mdl,
    }


def test_build_effect_summary_rows_counts_condition_status_by_effect() -> None:
    module = load_tables_module()
    manifest = {
        "samples": [
            {
                "sample_id": "cup.zoom_001",
                "target_category": "cup",
                "present_effects": ["normal_bump", "opacity_transparency"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True, preview=0, active_mdl=2),
                    "existing_noMDL": _condition("available", gate=True, preview=4, active_mdl=0),
                    "nvidia_asset_converter_preview_or_bake": _condition(
                        "planned_output_missing", gate=False, preview=None, active_mdl=None
                    ),
                },
            },
            {
                "sample_id": "lamp.zoom_002",
                "target_category": "lamp",
                "present_effects": ["emission"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True, preview=0, active_mdl=1),
                    "existing_noMDL": _condition("static_gate_failed", gate=False, preview=0, active_mdl=1),
                    "nvidia_asset_converter_preview_or_bake": _condition(
                        "available", gate=True, preview=3, active_mdl=0
                    ),
                },
            },
        ]
    }

    rows = module.build_effect_summary_rows(manifest)
    by_key = {(row["effect"], row["condition"]): row for row in rows}

    assert by_key[("clearcoat", "existing_noMDL")]["sample_count"] == 0
    assert by_key[("procedural_texture", "existing_noMDL")]["sample_count"] == 0
    normal_nvidia = by_key[("normal_bump", "nvidia_asset_converter_preview_or_bake")]
    assert normal_nvidia["sample_count"] == 1
    assert normal_nvidia["planned_output_missing_count"] == 1
    assert normal_nvidia["available_count"] == 0
    emission_nomdl = by_key[("emission", "existing_noMDL")]
    assert emission_nomdl["sample_count"] == 1
    assert emission_nomdl["static_gate_failed_count"] == 1
    assert emission_nomdl["available_count"] == 0


def test_merge_conversion_manifests_adds_supplemental_effect_samples() -> None:
    module = load_tables_module()
    base_manifest = {
        "samples": [
            {
                "sample_id": "cup.zoom_001",
                "target_category": "cup",
                "present_effects": ["normal_bump"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True, preview=0, active_mdl=1),
                    "existing_noMDL": _condition("available", gate=True, preview=1, active_mdl=0),
                    "nvidia_asset_converter_preview_or_bake": _condition(
                        "available", gate=True, preview=1, active_mdl=0
                    ),
                },
            }
        ]
    }
    supplemental_manifest = {
        "samples": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "target_category": "supplemental_material_fixture",
                "present_effects": ["clearcoat"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True, preview=0, active_mdl=1),
                    "existing_noMDL": _condition("available", gate=True, preview=1, active_mdl=0),
                    "nvidia_asset_converter_preview_or_bake": _condition(
                        "static_gate_failed", gate=False, preview=0, active_mdl=0
                    ),
                },
            },
            {
                "sample_id": "supplemental_procedural_checker",
                "target_category": "supplemental_material_fixture",
                "present_effects": ["procedural_texture"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True, preview=0, active_mdl=1),
                    "existing_noMDL": _condition("available", gate=True, preview=1, active_mdl=0),
                    "nvidia_asset_converter_preview_or_bake": _condition(
                        "available", gate=True, preview=1, active_mdl=0
                    ),
                },
            },
        ]
    }

    merged = module.merge_conversion_manifests(base_manifest, supplemental_manifest)
    rows = module.build_effect_summary_rows(merged)
    by_key = {(row["effect"], row["condition"]): row for row in rows}

    assert by_key[("clearcoat", "original_MDL")]["sample_count"] == 1
    assert by_key[("clearcoat", "existing_noMDL")]["available_count"] == 1
    clearcoat_nvidia = by_key[("clearcoat", "nvidia_asset_converter_preview_or_bake")]
    assert clearcoat_nvidia["sample_count"] == 1
    assert clearcoat_nvidia["available_count"] == 0
    assert clearcoat_nvidia["static_gate_failed_count"] == 1
    procedural_nvidia = by_key[("procedural_texture", "nvidia_asset_converter_preview_or_bake")]
    assert procedural_nvidia["sample_count"] == 1
    assert procedural_nvidia["available_count"] == 1


def test_build_case_records_attaches_rendered_visual_failure_evidence() -> None:
    module = load_tables_module()
    manifest = {
        "samples": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "target_category": "supplemental_material_fixture",
                "target_prim_path": "/World/ClearcoatTarget",
                "present_effects": ["clearcoat"],
                "conditions": {
                    "original_MDL": _condition("available", gate=True, preview=0, active_mdl=1),
                    "existing_noMDL": _condition("available", gate=True, preview=1, active_mdl=0),
                    "nvidia_asset_converter_preview_or_bake": {
                        **_condition("static_gate_failed", gate=False, preview=0, active_mdl=0),
                        "usd_path": "/external/clearcoat.usd",
                    },
                },
            }
        ]
    }
    visual_qa_manifest = {
        "failure_cases": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "condition": "nvidia_asset_converter_preview_or_bake",
                "reason": "near_black_render",
                "evidence": "Image is near black.",
                "image_path": "/repo/clearcoat/nvidia_0000.png",
                "source_condition_status": "static_gate_failed",
            }
        ]
    }

    cases = module.build_case_records(manifest, visual_qa_manifest=visual_qa_manifest)

    assert len(cases) == 1
    case = cases[0]
    assert case["reason"] == "static_gate_failed"
    assert case["rendered_failure_reason"] == "near_black_render"
    assert case["rendered_failure_image_path"] == "/repo/clearcoat/nvidia_0000.png"
    assert case["rendered_failure_evidence"] == "Image is near black."
    assert case["has_rendered_failure_evidence"] is True


def test_write_outputs_creates_csv_tex_and_case_manifest(tmp_path: Path) -> None:
    module = load_tables_module()
    rows = [
        {
            "effect": "normal_bump",
            "condition": "existing_noMDL",
            "sample_count": 2,
            "available_count": 2,
            "static_gate_failed_count": 0,
            "planned_output_missing_count": 0,
            "missing_count": 0,
        }
    ]
    cases = [
        {
            "case_id": "normal_bump:cup.zoom_001:nvidia_asset_converter_preview_or_bake",
            "effect": "normal_bump",
            "sample_id": "cup.zoom_001",
            "target_category": "cup",
            "condition": "nvidia_asset_converter_preview_or_bake",
            "status": "planned_output_missing",
            "reason": "planned_output_missing",
        }
    ]
    csv_path = tmp_path / "summary.csv"
    tex_path = tmp_path / "summary.tex"
    case_path = tmp_path / "cases.json"

    module.write_summary_csv(csv_path, rows)
    module.write_summary_tex(tex_path, rows)
    module.write_case_manifest(case_path, cases, generated_at_utc="2026-05-25T00:00:00Z")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        loaded = list(csv.DictReader(handle))
    assert loaded[0]["effect"] == "normal_bump"
    assert b"\r" not in csv_path.read_bytes()
    assert "normal\\_bump" in tex_path.read_text(encoding="utf-8")
    assert "planned_output_missing" in case_path.read_text(encoding="utf-8")
