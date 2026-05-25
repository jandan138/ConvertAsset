import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_conversion_manifest.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("material_effect_supplemental_conversion", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_supplemental_conversion_manifest_records_three_conditions_and_nvidia_failure(
    tmp_path: Path,
) -> None:
    module = load_module()
    clearcoat_original = tmp_path / "fixtures/supplemental_clearcoat_omnipbr.usda"
    clearcoat_nomdl = tmp_path / "fixtures/supplemental_clearcoat_omnipbr_noMDL.usda"
    clearcoat_nvidia = (
        tmp_path
        / "nvidia/clearcoat/supplemental_clearcoat_omnipbr_nvidia_usd_to_usd_preview.usd"
    )
    procedural_original = tmp_path / "fixtures/supplemental_procedural_checker.usda"
    procedural_nomdl = tmp_path / "fixtures/supplemental_procedural_checker_noMDL.usda"
    procedural_nvidia = (
        tmp_path
        / "nvidia/procedural_texture/supplemental_procedural_checker_nvidia_usd_to_usd_preview.usd"
    )
    for path in [
        clearcoat_original,
        clearcoat_nomdl,
        clearcoat_nvidia,
        procedural_original,
        procedural_nomdl,
        procedural_nvidia,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#usda 1.0\n", encoding="utf-8")

    wrapper_manifest = {
        "wrappers": [
            {
                "wrapper_id": "supplemental_clearcoat_omnipbr",
                "effect": "clearcoat",
                "wrapper_stage": str(clearcoat_original),
                "material_path": "/World/Looks/OmniPBR_ClearCoat_Opacity",
                "target_prim_path": "/World/ClearcoatTarget",
            },
            {
                "wrapper_id": "supplemental_procedural_checker",
                "effect": "procedural_texture",
                "wrapper_stage": str(procedural_original),
                "material_path": "/World/Looks/ProceduralChecker",
                "target_prim_path": "/World/ProceduralTarget",
            },
        ]
    }

    def inspect(path: Path) -> dict:
        if path in {clearcoat_original, procedural_original}:
            return {
                "inspection_status": "ok",
                "stage_opened": True,
                "shader_count": 1,
                "preview_surface_count": 0,
                "active_mdl_shader_count": 1,
            }
        if path in {clearcoat_nomdl, procedural_nomdl, procedural_nvidia}:
            return {
                "inspection_status": "ok",
                "stage_opened": True,
                "shader_count": 4,
                "preview_surface_count": 1,
                "active_mdl_shader_count": 0,
            }
        return {
            "inspection_status": "ok",
            "stage_opened": True,
            "shader_count": 0,
            "preview_surface_count": 0,
            "active_mdl_shader_count": 0,
        }

    manifest = module.build_supplemental_conversion_manifest(
        wrapper_manifest,
        nvidia_output_root=tmp_path / "nvidia",
        stage_inspector=inspect,
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["sample_count"] == 2
    assert manifest["summary"]["original_available_count"] == 2
    assert manifest["summary"]["convertasset_available_count"] == 2
    assert manifest["summary"]["nvidia_available_count"] == 1
    assert manifest["summary"]["nvidia_static_gate_failed_count"] == 1
    assert manifest["summary"]["ready_for_effect_table_regeneration"] is True
    assert manifest["summary"]["ready_for_full_claim"] is False
    assert "supplemental_nvidia_static_gate_failed" in manifest["summary"]["blockers"]

    clearcoat = manifest["samples"][0]
    assert clearcoat["sample_id"] == "supplemental_clearcoat_omnipbr"
    assert clearcoat["present_effects"] == ["clearcoat"]
    assert clearcoat["conditions"]["original_MDL"]["status"] == "available"
    assert clearcoat["conditions"]["existing_noMDL"]["status"] == "available"
    assert clearcoat["conditions"]["nvidia_asset_converter_preview_or_bake"]["status"] == "static_gate_failed"

    failure_cases = manifest["failure_cases"]
    assert failure_cases == [
        {
            "sample_id": "supplemental_clearcoat_omnipbr",
            "effect": "clearcoat",
            "condition": "nvidia_asset_converter_preview_or_bake",
            "status": "static_gate_failed",
            "reason": "supplemental_condition_static_gate_failed",
        }
    ]


def test_build_supplemental_conversion_manifest_blocks_when_outputs_missing(tmp_path: Path) -> None:
    module = load_module()
    original = tmp_path / "fixtures/supplemental_clearcoat_omnipbr.usda"
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text("#usda 1.0\n", encoding="utf-8")
    wrapper_manifest = {
        "wrappers": [
            {
                "wrapper_id": "supplemental_clearcoat_omnipbr",
                "effect": "clearcoat",
                "wrapper_stage": str(original),
                "material_path": "/World/Looks/OmniPBR_ClearCoat_Opacity",
                "target_prim_path": "/World/ClearcoatTarget",
            }
        ]
    }

    manifest = module.build_supplemental_conversion_manifest(
        wrapper_manifest,
        nvidia_output_root=tmp_path / "nvidia",
        stage_inspector=lambda _path: {
            "inspection_status": "ok",
            "stage_opened": True,
            "shader_count": 1,
            "preview_surface_count": 0,
            "active_mdl_shader_count": 1,
        },
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["convertasset_available_count"] == 0
    assert manifest["summary"]["nvidia_available_count"] == 0
    assert manifest["summary"]["ready_for_effect_table_regeneration"] is False
    assert "supplemental_condition_outputs_missing" in manifest["summary"]["blockers"]
