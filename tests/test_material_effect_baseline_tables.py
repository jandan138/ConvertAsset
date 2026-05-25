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
