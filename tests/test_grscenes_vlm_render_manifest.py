import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_render_manifest.py"


def load_render_module():
    spec = importlib.util.spec_from_file_location("grscenes_prepare_render_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_target_manifest(tmp_path: Path, *, converted_exists: bool) -> dict:
    source_usd = tmp_path / "source/scene_a/start_result_raw.usd"
    converted_usd = tmp_path / "scratch/scene_a/start_result_raw_noMDL.usd"
    source_usd.parent.mkdir(parents=True)
    source_usd.write_text("#usda 1.0\n", encoding="utf-8")
    if converted_exists:
        converted_usd.parent.mkdir(parents=True)
        converted_usd.write_text("#usda 1.0\n", encoding="utf-8")

    scene = {
        "dataset_role": "benchmark_source_dataset",
        "source_dataset_root": str(tmp_path / "source"),
        "source_scene_id": "scene_a_usd",
        "source_scene_split": "home_scenes",
        "source_usd": str(source_usd),
        "source_usd_variant": "start_result_raw.usd",
        "scratch_scene_root": str(tmp_path / "scratch/scene_a"),
        "converted_usd": str(converted_usd),
        "conversion_command": f"./scripts/isaac_python.sh ./main.py no-mdl {tmp_path / 'scratch/scene_a/start_result_raw.usd'}",
        "material_conditions": ["original", "converted"],
        "pilot_role": "episode_backed_home",
        "paper_claim_eligible": True,
    }
    base_record = {
        "episode_family": "mm",
        "episode_file": "mm_episodes.json",
        "source_scene_id": "scene_a_usd",
        "object_instance_id": "bottle/model_hash_0",
        "object_category": "bottle",
        "target_prim_path": "/Root/Meshes/Furnitures/bottle/model_hash_0",
        "mapping_status": "resolved_metadata_reference_to_prim",
        "mapping_confidence": "high_exact_suffix",
        "instruction": "Pick the bottle from the bedroom.",
        "prompt": "Point to the bottle.",
        "world_bbox": {
            "min": [1.0, 2.0, 0.0],
            "max": [2.0, 4.0, 1.0],
            "center": [1.5, 3.0, 0.5],
            "size": [1.0, 2.0, 1.0],
            "diagonal": 2.44948974278,
        },
        "resolved_model_path": str(tmp_path / "source/models/object/others/bottle/hash/instance.usd"),
        "reference_asset_path": "models/object/others/bottle/hash/instance.usd",
        "bbox_method": "model_local_bbox_x_scene_xform",
        "paper_claim_eligible": True,
    }
    second_record = {
        **base_record,
        "stable_episode_id": "episode_b",
        "episode_family": "sn",
        "episode_file": "sn_episodes.json",
        "instruction": "Find the same bottle.",
    }
    return {
        "schema_version": 1,
        "status": "target_resolved_manifest",
        "generated_by": "target_script",
        "generator_git_commit": "abc123",
        "dataset_roles": {
            "benchmark_source_dataset": {
                "local_root": str(tmp_path / "source"),
                "name": "GRScenes-100",
                "mutation_policy": "never_in_place",
            },
            "intervention_outputs": {
                "scratch_root": str(tmp_path / "scratch"),
                "retention_policy": "generated_outputs_may_be_deleted_and_regenerated",
            },
        },
        "selection": {"source_usd_variant": "start_result_raw.usd"},
        "paper_claim_gate": {"source_root_required": str(tmp_path / "source")},
        "resolution_summary": {
            "scenes_attempted": 1,
            "episode_records_attempted": 2,
            "unique_target_prim_count": 1,
        },
        "scenes": [scene],
        "episode_records": [
            {**base_record, "stable_episode_id": "episode_a"},
            second_record,
        ],
    }


def test_module_imports_without_pxr() -> None:
    module = load_render_module()

    assert hasattr(module, "build_render_manifest")


def test_build_render_manifest_collapses_duplicates_and_pairs_conditions(tmp_path: Path) -> None:
    module = load_render_module()
    target_manifest = make_target_manifest(tmp_path, converted_exists=True)

    manifest = module.build_render_manifest(
        target_manifest,
        render_root=tmp_path / "renders",
        view_azimuths=[0.0, 90.0],
        image_width=640,
        image_height=480,
    )

    assert manifest["schema_version"] == 1
    assert manifest["status"] == "planned_render_manifest"
    assert manifest["render_summary"]["episode_records_input"] == 2
    assert manifest["render_summary"]["unique_render_targets"] == 1
    assert manifest["render_summary"]["views_per_target"] == 2
    assert manifest["render_summary"]["render_pairs"] == 2
    assert manifest["render_summary"]["render_jobs"] == 4
    assert manifest["render_summary"]["render_jobs_missing_input_count"] == 0
    assert manifest["render_summary"]["camera_stage_missing_count"] == 4
    assert manifest["render_summary"]["render_jobs_ready_to_run"] == 0

    target = manifest["render_targets"][0]
    assert target["linked_episode_ids"] == ["episode_a", "episode_b"]
    assert target["linked_episode_count"] == 2
    assert target["target_category"] == "bottle"
    assert target["world_bbox"]["center"] == [1.5, 3.0, 0.5]

    pair = manifest["render_pairs"][0]
    assert pair["view"]["azimuth_deg"] == 0.0
    assert pair["view"]["camera"]["look_at"] == [1.5, 3.0, 0.5]
    assert len(pair["conditions"]) == 2
    original, converted = pair["conditions"]
    assert original["material_condition"] == "original"
    assert converted["material_condition"] == "converted"
    assert original["usd_path"].endswith("start_result_raw.usd")
    assert converted["usd_path"].endswith("start_result_raw_noMDL.usd")
    assert original["camera"] == converted["camera"] == pair["view"]["camera"]
    assert original["camera_stage_status"] == "pending_authoring"
    assert converted["camera_stage_status"] == "pending_authoring"
    assert original["render_status"] == "planned_camera_stage_pending"
    assert converted["render_status"] == "planned_camera_stage_pending"
    assert original["output_image"].endswith("/original_0000.png")
    assert converted["output_image"].endswith("/converted_0000.png")
    assert "--wait-frames" in original["render_command"]
    assert original["render_command"][original["render_command"].index("--wait-frames") + 1] == "8"
    assert len(manifest["records"]) == 4
    assert manifest["records"][0]["target"]["bbox_source"] == "pending_projection_from_world_bbox"
    assert manifest["records"][0]["target"]["bbox_xyxy"] is None
    assert manifest["records"][0]["image"]["hash_sha256"] is None
    assert manifest["records"][0]["prompt_text"] == "Point to the bottle."
    assert manifest["records"][0]["source_episode_instructions"] == [
        "Pick the bottle from the bedroom.",
        "Find the same bottle.",
    ]


def test_build_render_manifest_tracks_missing_converted_inputs(tmp_path: Path) -> None:
    module = load_render_module()
    target_manifest = make_target_manifest(tmp_path, converted_exists=False)

    manifest = module.build_render_manifest(
        target_manifest,
        render_root=tmp_path / "renders",
        view_azimuths=[0.0],
        require_converted=False,
    )

    assert manifest["render_summary"]["render_jobs"] == 2
    assert manifest["render_summary"]["render_jobs_missing_input_count"] == 1
    converted = manifest["render_pairs"][0]["conditions"][1]
    assert converted["material_condition"] == "converted"
    assert converted["input_exists"] is False
    assert converted["render_status"] == "blocked_missing_material_input"

    with pytest.raises(FileNotFoundError, match="converted USD is missing"):
        module.build_render_manifest(
            target_manifest,
            render_root=tmp_path / "renders",
            view_azimuths=[0.0],
            require_converted=True,
        )


def test_build_render_manifest_keeps_planned_image_hashes_empty(tmp_path: Path) -> None:
    module = load_render_module()
    target_manifest = make_target_manifest(tmp_path, converted_exists=True)
    first = module.build_render_manifest(
        target_manifest,
        render_root=tmp_path / "renders",
        view_azimuths=[0.0],
    )
    image_path = Path(first["records"][0]["output_image"])
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"already rendered")

    manifest = module.build_render_manifest(
        target_manifest,
        render_root=tmp_path / "renders",
        view_azimuths=[0.0],
    )

    assert manifest["records"][0]["image"]["hash_sha256"] is None


def test_build_render_manifest_can_overlay_completed_full_nomdl_run_report(tmp_path: Path) -> None:
    module = load_render_module()
    target_manifest = make_target_manifest(tmp_path, converted_exists=False)
    full_scratch_scene = tmp_path / "full_scratch/scenes/scene_a"
    scratch_input = full_scratch_scene / "start_result_raw.usd"
    converted_output = full_scratch_scene / "start_result_raw_noMDL.usd"
    scratch_input.parent.mkdir(parents=True)
    scratch_input.write_text("#usda 1.0\n", encoding="utf-8")
    converted_output.write_text("#usda 1.0\n", encoding="utf-8")
    run_report = {
        "status": "completed_full_grscenes_nomdl_multi_root_run",
        "dry_run": False,
        "apply_ready": True,
        "results": [
            {
                "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
                "scratch_input_usd": str(scratch_input),
                "top_output_usd": str(converted_output),
            }
        ],
        "jobs": [
            {
                "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "source_usd_variant": "start_result_raw.usd",
                "scratch_input_usd": str(scratch_input),
                "expected_top_output_usd": str(converted_output),
            }
        ],
    }

    manifest = module.build_render_manifest(
        target_manifest,
        render_root=tmp_path / "renders",
        view_azimuths=[0.0],
        require_converted=True,
        nomdl_run_report=run_report,
    )

    original = manifest["render_pairs"][0]["conditions"][0]
    converted = manifest["render_pairs"][0]["conditions"][1]
    assert original["input_exists"] is True
    assert original["usd_path"] == str(scratch_input)
    assert original["source_usd"] == target_manifest["scenes"][0]["source_usd"]
    assert original["scratch_input_usd"] == str(scratch_input)
    assert converted["input_exists"] is True
    assert converted["converted_usd"] == str(converted_output)
    assert converted["scratch_input_usd"] == str(scratch_input)
    assert converted["scratch_scene_root"] == str(full_scratch_scene)
    assert manifest["render_summary"]["converted_jobs_missing_input_count"] == 0


def test_build_render_manifest_rejects_inconsistent_duplicate_targets(tmp_path: Path) -> None:
    module = load_render_module()
    target_manifest = make_target_manifest(tmp_path, converted_exists=True)
    target_manifest["episode_records"][1]["world_bbox"] = {
        **target_manifest["episode_records"][1]["world_bbox"],
        "center": [99.0, 3.0, 0.5],
    }

    with pytest.raises(ValueError, match="inconsistent duplicate target metadata"):
        module.build_render_manifest(
            target_manifest,
            render_root=tmp_path / "renders",
            view_azimuths=[0.0],
        )


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        (("object_category",), "cup"),
        (("bbox_method",), "scene_composed_bbox_fallback"),
        (("resolved_model_path",), "/different/model.usd"),
    ],
)
def test_build_render_manifest_rejects_other_duplicate_metadata_divergence(
    tmp_path: Path, field_path: tuple[str, ...], value: object
) -> None:
    module = load_render_module()
    target_manifest = make_target_manifest(tmp_path, converted_exists=True)
    target_manifest["episode_records"][1][field_path[0]] = value

    with pytest.raises(ValueError, match="inconsistent duplicate target metadata"):
        module.build_render_manifest(
            target_manifest,
            render_root=tmp_path / "renders",
            view_azimuths=[0.0],
        )
