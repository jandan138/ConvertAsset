import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py"
)


def load_conversion_module():
    spec = importlib.util.spec_from_file_location("material_effect_conversion_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _smoke_manifest() -> dict:
    return {
        "schema_version": 1,
        "status": "nvidia_asset_converter_smoke",
        "summary": {
            "ready_for_sample_baseline": True,
            "usable_usd_baseline_attempts": ["usd_to_usd_preview"],
        },
        "attempts": [
            {
                "name": "usd_to_usd_preview",
                "context_flags": {"export_preview_surface": True, "keep_all_materials": True},
                "claimable_as_baseline": True,
            }
        ],
    }


def test_build_baseline_conversion_manifest_records_three_conditions_and_missing_nvidia(
    tmp_path: Path,
) -> None:
    module = load_conversion_module()
    source_usd = tmp_path / "source.usd"
    scratch_input_usd = tmp_path / "scratch/source.usd"
    nomdl_usd = tmp_path / "scratch/source_noMDL.usd"
    for path in [source_usd, scratch_input_usd, nomdl_usd]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#usda 1.0\n", encoding="utf-8")

    effect_manifest = {
        "schema_version": 1,
        "summary": {"effect_gaps": ["clearcoat"]},
        "samples": [
            {
                "sample_id": "cup.zoom_001",
                "source_scene_id": "scene_a_usd",
                "target_category": "cup",
                "present_effects": ["opacity_transparency", "normal_bump"],
                "material_model": {"target_prim_path": "/Root/Cup"},
            }
        ],
    }
    run_report = {
        "schema_version": 1,
        "status": "completed_full_grscenes_nomdl_multi_root_run",
        "jobs": [
            {
                "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "source_usd": str(source_usd),
                "scratch_input_usd": str(scratch_input_usd),
                "expected_top_output_usd": str(nomdl_usd),
            }
        ],
        "results": [
            {
                "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
                "scratch_input_usd": str(scratch_input_usd),
                "top_output_usd": str(nomdl_usd),
            }
        ],
    }

    def inspect(path: Path) -> dict:
        if path == scratch_input_usd:
            return {
                "inspection_status": "ok",
                "stage_opened": True,
                "shader_count": 2,
                "preview_surface_count": 0,
                "active_mdl_shader_count": 2,
            }
        return {
            "inspection_status": "ok",
            "stage_opened": True,
            "shader_count": 3,
            "preview_surface_count": 3,
            "active_mdl_shader_count": 0,
        }

    manifest = module.build_baseline_conversion_manifest(
        effect_manifest,
        run_report,
        _smoke_manifest(),
        nvidia_output_root=tmp_path / "nvidia",
        stage_inspector=inspect,
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["status"] == "baseline_conversion_manifest_ready"
    assert manifest["summary"]["sample_count"] == 1
    assert manifest["summary"]["original_available_count"] == 1
    assert manifest["summary"]["convertasset_available_count"] == 1
    assert manifest["summary"]["nvidia_available_count"] == 0
    assert manifest["summary"]["nvidia_missing_count"] == 1
    assert manifest["summary"]["ready_for_full_claim"] is False
    assert "nvidia_sample_outputs_missing" in manifest["summary"]["blockers"]
    sample = manifest["samples"][0]
    assert set(sample["conditions"]) == {
        "original_MDL",
        "existing_noMDL",
        "nvidia_asset_converter_preview_or_bake",
    }
    assert sample["conditions"]["original_MDL"]["usd_path"] == str(scratch_input_usd)
    assert sample["conditions"]["original_MDL"]["provenance"]["source_usd"] == str(source_usd)
    assert sample["conditions"]["original_MDL"]["active_mdl_shader_count"] == 2
    assert sample["conditions"]["existing_noMDL"]["preview_surface_count"] == 3
    nvidia = sample["conditions"]["nvidia_asset_converter_preview_or_bake"]
    assert nvidia["status"] == "planned_output_missing"
    assert nvidia["preferred_smoke_attempt"] == "usd_to_usd_preview"


def test_build_baseline_conversion_manifest_marks_nvidia_available_when_output_passes_gate(
    tmp_path: Path,
) -> None:
    module = load_conversion_module()
    source_usd = tmp_path / "source.usd"
    nomdl_usd = tmp_path / "source_noMDL.usd"
    nvidia_usd = tmp_path / "nvidia/scene_a_usd/start_result_raw_nvidia_usd_to_usd_preview.usd"
    for path in [source_usd, nomdl_usd, nvidia_usd]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#usda 1.0\n", encoding="utf-8")

    effect_manifest = {
        "schema_version": 1,
        "summary": {"effect_gaps": []},
        "samples": [
            {
                "sample_id": "cup.zoom_001",
                "source_scene_id": "scene_a_usd",
                "target_category": "cup",
                "present_effects": ["normal_bump"],
            }
        ],
    }
    run_report = {
        "jobs": [
            {
                "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
                "source_scene_id": "scene_a_usd",
                "source_usd": str(source_usd),
                "scratch_input_usd": str(source_usd),
                "expected_top_output_usd": str(nomdl_usd),
            }
        ],
        "results": [
            {
                "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
                "top_output_usd": str(nomdl_usd),
            }
        ],
    }

    def inspect(_path: Path) -> dict:
        return {
            "inspection_status": "ok",
            "stage_opened": True,
            "shader_count": 4,
            "preview_surface_count": 4,
            "active_mdl_shader_count": 0,
        }

    manifest = module.build_baseline_conversion_manifest(
        effect_manifest,
        run_report,
        _smoke_manifest(),
        nvidia_output_root=tmp_path / "nvidia",
        stage_inspector=inspect,
        generated_at_utc="2026-05-25T00:00:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["nvidia_available_count"] == 1
    assert manifest["summary"]["nvidia_missing_count"] == 0
    nvidia = manifest["samples"][0]["conditions"]["nvidia_asset_converter_preview_or_bake"]
    assert nvidia["status"] == "available"
    assert nvidia["static_gate_passed"] is True
