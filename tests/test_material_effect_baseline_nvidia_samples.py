import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/08_material_effect_baseline/run_nvidia_sample_conversions.py"
)


def load_sample_module():
    spec = importlib.util.spec_from_file_location("material_effect_nvidia_samples", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample(scene_id: str, sample_id: str, input_path: Path, output_path: Path) -> dict:
    return {
        "sample_id": sample_id,
        "source_scene_id": scene_id,
        "present_effects": ["normal_bump"],
        "conditions": {
            "original_MDL": {
                "status": "available",
                "usd_path": str(input_path),
                "static_gate_passed": True,
            },
            "nvidia_asset_converter_preview_or_bake": {
                "status": "planned_output_missing",
                "usd_path": str(output_path),
                "preferred_smoke_attempt": "usd_to_usd_preview",
                "context_flags": {"export_preview_surface": True, "keep_all_materials": True},
            },
        },
    }


def test_build_scene_conversion_jobs_deduplicates_by_source_scene(tmp_path: Path) -> None:
    module = load_sample_module()
    input_path = tmp_path / "scene_a/start_result_raw.usd"
    output_path = tmp_path / "out/scene_a/start_result_raw_nvidia.usd"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("#usda 1.0\n", encoding="utf-8")
    manifest = {
        "samples": [
            _sample("scene_a_usd", "sample_1", input_path, output_path),
            _sample("scene_a_usd", "sample_2", input_path, output_path),
        ]
    }

    jobs = module.build_scene_conversion_jobs(manifest)

    assert len(jobs) == 1
    assert jobs[0]["source_scene_id"] == "scene_a_usd"
    assert jobs[0]["sample_ids"] == ["sample_1", "sample_2"]
    assert jobs[0]["input_usd"] == str(input_path)
    assert jobs[0]["output_usd"] == str(output_path)
    assert jobs[0]["context_flags"]["export_preview_surface"] is True
    assert jobs[0]["skip_reason"] is None


def test_build_scene_conversion_jobs_skips_existing_output_without_force(tmp_path: Path) -> None:
    module = load_sample_module()
    input_path = tmp_path / "scene_a/start_result_raw.usd"
    output_path = tmp_path / "out/scene_a/start_result_raw_nvidia.usd"
    input_path.parent.mkdir(parents=True)
    output_path.parent.mkdir(parents=True)
    input_path.write_text("#usda 1.0\n", encoding="utf-8")
    output_path.write_text("#usda 1.0\n", encoding="utf-8")
    manifest = {"samples": [_sample("scene_a_usd", "sample_1", input_path, output_path)]}

    skipped = module.build_scene_conversion_jobs(manifest)
    forced = module.build_scene_conversion_jobs(manifest, force=True)

    assert skipped[0]["skip_reason"] == "output_exists"
    assert forced[0]["skip_reason"] is None


def test_build_sample_conversion_manifest_counts_attempts(tmp_path: Path) -> None:
    module = load_sample_module()
    output_path = tmp_path / "out.usd"
    output_path.write_text("#usda 1.0\n", encoding="utf-8")
    jobs = [
        {
            "source_scene_id": "scene_a_usd",
            "sample_ids": ["sample_1"],
            "input_usd": str(tmp_path / "in.usd"),
            "output_usd": str(output_path),
            "skip_reason": None,
            "context_flags": {"export_preview_surface": True},
        }
    ]
    attempts = [
        module.build_attempt_record(
            jobs[0],
            conversion_success=True,
            error_message=None,
            started_at_utc="2026-05-25T00:00:00Z",
            finished_at_utc="2026-05-25T00:01:00Z",
        )
    ]

    manifest = module.build_sample_conversion_manifest(
        jobs=jobs,
        attempts=attempts,
        generated_at_utc="2026-05-25T00:02:00Z",
        generator_git_commit="test",
    )

    assert manifest["status"] == "nvidia_sample_conversion_manifest"
    assert manifest["summary"]["scene_job_count"] == 1
    assert manifest["summary"]["attempted_scene_count"] == 1
    assert manifest["summary"]["successful_scene_count"] == 1
    assert manifest["summary"]["output_exists_count"] == 1
    assert manifest["summary"]["ready_for_baseline_manifest_regeneration"] is True


def test_build_sample_conversion_manifest_treats_existing_output_skip_as_ready(
    tmp_path: Path,
) -> None:
    module = load_sample_module()
    output_path = tmp_path / "out.usd"
    output_path.write_text("#usda 1.0\n", encoding="utf-8")
    jobs = [
        {
            "source_scene_id": "scene_a_usd",
            "sample_ids": ["sample_1"],
            "input_usd": str(tmp_path / "in.usd"),
            "output_usd": str(output_path),
            "skip_reason": "output_exists",
            "context_flags": {"export_preview_surface": True},
        }
    ]

    manifest = module.build_sample_conversion_manifest(
        jobs=jobs,
        attempts=[],
        generated_at_utc="2026-05-25T00:02:00Z",
        generator_git_commit="test",
    )

    assert manifest["summary"]["attempted_scene_count"] == 0
    assert manifest["summary"]["skipped_scene_count"] == 1
    assert manifest["summary"]["reusable_existing_output_count"] == 1
    assert manifest["summary"]["output_exists_count"] == 1
    assert manifest["summary"]["ready_for_baseline_manifest_regeneration"] is True
