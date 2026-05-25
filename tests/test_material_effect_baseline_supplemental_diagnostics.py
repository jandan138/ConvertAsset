import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/diagnose_supplemental_material_preservation.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("supplemental_material_diagnostics", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_supplemental_material_diagnostics_flags_target_and_checker_loss(tmp_path: Path) -> None:
    module = load_module()
    clearcoat_original = tmp_path / "fixtures/supplemental_clearcoat_omnipbr.usda"
    clearcoat_nomdl = tmp_path / "fixtures/supplemental_clearcoat_omnipbr_noMDL.usda"
    clearcoat_nvidia = tmp_path / "nvidia/clearcoat.usd"
    procedural_original = tmp_path / "fixtures/supplemental_procedural_checker.usda"
    procedural_nomdl = tmp_path / "fixtures/supplemental_procedural_checker_noMDL.usda"
    procedural_nvidia = tmp_path / "nvidia/procedural.usd"

    conversion_manifest = {
        "samples": [
            {
                "sample_id": "supplemental_clearcoat_omnipbr",
                "present_effects": ["clearcoat"],
                "target_prim_path": "/World/ClearcoatTarget",
                "conditions": {
                    "original_MDL": {"status": "available", "usd_path": str(clearcoat_original)},
                    "existing_noMDL": {"status": "available", "usd_path": str(clearcoat_nomdl)},
                    "nvidia_asset_converter_preview_or_bake": {
                        "status": "static_gate_failed",
                        "usd_path": str(clearcoat_nvidia),
                    },
                },
            },
            {
                "sample_id": "supplemental_procedural_checker",
                "present_effects": ["procedural_texture"],
                "target_prim_path": "/World/ProceduralTarget",
                "conditions": {
                    "original_MDL": {"status": "available", "usd_path": str(procedural_original)},
                    "existing_noMDL": {"status": "available", "usd_path": str(procedural_nomdl)},
                    "nvidia_asset_converter_preview_or_bake": {
                        "status": "available",
                        "usd_path": str(procedural_nvidia),
                    },
                },
            },
        ]
    }

    def inspect(path: Path, target_prim_path: str) -> dict:
        if path == clearcoat_nvidia:
            return {
                "inspection_status": "ok",
                "target_exists": False,
                "preview_surface_count": 0,
                "basecolor_texture_file_count": 0,
                "diffuse_color_connected": False,
            }
        if path == procedural_original:
            return {
                "inspection_status": "ok",
                "target_exists": True,
                "active_mdl_shader_count": 1,
                "mdl_checker_enabled": True,
                "mdl_checker_scale": 8.0,
                "mdl_texture_inputs": ["tex"],
            }
        if path in {procedural_nomdl, procedural_nvidia}:
            return {
                "inspection_status": "ok",
                "target_exists": True,
                "preview_surface_count": 1,
                "basecolor_texture_file_count": 0,
                "diffuse_color_connected": False,
                "diffuse_color_value": [1.0, 1.0, 1.0],
            }
        return {
            "inspection_status": "ok",
            "target_exists": True,
            "preview_surface_count": 1,
            "basecolor_texture_file_count": 0,
            "diffuse_color_connected": False,
        }

    report = module.build_supplemental_material_diagnostics(
        conversion_manifest,
        stage_inspector=inspect,
        generated_at_utc="2026-05-26T00:00:00Z",
        generator_git_commit="test",
    )

    assert report["summary"]["case_count"] == 2
    assert report["summary"]["nvidia_target_missing_count"] == 1
    assert report["summary"]["converted_procedural_checker_loss_count"] == 2
    assert report["summary"]["ready_for_success_panel"] is False
    assert report["summary"]["ready_for_failure_case_writeup"] is True
    assert "nvidia_clearcoat_target_missing" in report["summary"]["blockers"]
    assert "procedural_checker_not_preserved_in_converted_conditions" in report["summary"]["blockers"]

    clearcoat = report["cases"][0]
    assert clearcoat["case_verdict"] == "FAIL"
    assert clearcoat["conditions"]["nvidia_asset_converter_preview_or_bake"]["diagnostic_reason"] == (
        "converted_stage_missing_target_prim"
    )
    assert clearcoat["conditions"]["nvidia_asset_converter_preview_or_bake"]["retake_action"] == (
        "camera_retake_insufficient_rerun_or_treat_as_failure"
    )

    procedural = report["cases"][1]
    assert procedural["case_verdict"] == "FAIL"
    assert procedural["conditions"]["original_MDL"]["diagnostic_reason"] == "source_checker_authored"
    assert procedural["conditions"]["existing_noMDL"]["diagnostic_reason"] == (
        "converted_preview_surface_lacks_checker_texture"
    )
    assert procedural["conditions"]["nvidia_asset_converter_preview_or_bake"]["diagnostic_reason"] == (
        "converted_preview_surface_lacks_checker_texture"
    )
