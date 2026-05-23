import gzip
import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py"
COLLECT_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py"
RUN_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py"
EXTRACT_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/extract_episode_metrics.py"
ANALYZE_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/analyze_paired_metrics.py"
VIDEO_SELECT_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/select_video_cases.py"


def load_prep_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_prepare_minipair", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_collect_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_collect_results", COLLECT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_run_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_run_eval", RUN_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_extract_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_extract_episode_metrics", EXTRACT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_analyze_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_analyze_paired_metrics", ANALYZE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_video_select_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_select_video_cases", VIDEO_SELECT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_scene_usd(root: Path, scene_split: str, scene_id: str, usd_name: str) -> Path:
    scene_dir = root / "scenes/GRScenes-100" / scene_split / "scenes" / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    usd_path = scene_dir / usd_name
    usd_path.write_text("#usda 1.0\n", encoding="utf-8")
    return usd_path


def write_grscene_sidecar_entries(root: Path, scene_split: str, scene_id: str) -> dict[str, Path]:
    split_root = root / "scenes/GRScenes-100" / scene_split
    models_root = split_root / "models"
    materials_root = split_root / "Materials"
    models_root.mkdir(parents=True, exist_ok=True)
    materials_root.mkdir(parents=True, exist_ok=True)
    scene_dir = split_root / "scenes" / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "models").write_text("../../models", encoding="utf-8")
    (scene_dir / "Materials").write_text("../../Materials", encoding="utf-8")
    return {"models": models_root, "Materials": materials_root}


def make_source_root(tmp_path: Path) -> Path:
    source_root = tmp_path / "zzh-grscenes"
    episode = {
        "test": {
            "scene_a_usd": {
                "chair/model_hash_0": [
                    {
                        "start_point": [1.0, 2.0],
                        "target_point": [3.0, 2.0, 0.0],
                        "distance": 2.5,
                        "path": [[1.0, 2.0], [2.0, 2.0], [3.0, 2.0]],
                        "candidates": ["chair/model_hash_0"],
                        "dialogue": [
                            {"role": "human", "content": "Find the chair beside the sofa."}
                        ],
                    }
                ]
            }
        },
        "validate": {},
    }
    write_json(source_root / "benchmark/sn_episodes.json", episode)
    write_scene_usd(source_root, "home_scenes", "scene_a_usd", "start_result_navigation.usd")
    return source_root


def test_prepare_minipair_writes_internnav_dataset_scene_links_and_manifest(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    converted_usd = write_scene_usd(
        nomdl_root,
        "home_scenes",
        "scene_a_usd",
        "start_result_navigation_noMDL.usd",
    )
    work_root = tmp_path / "internnav_work"
    manifest_path = tmp_path / "prep_manifest.json"

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=work_root,
        repo_manifest_path=manifest_path,
        max_episodes=1,
        split_name="mini",
        link_mode="copy",
    )

    dataset_path = Path(manifest["dataset"]["path"])
    assert dataset_path == work_root / "datasets/grscene_sn_mini/mini/mini.json.gz"
    with gzip.open(dataset_path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert list(payload) == ["episodes"]
    assert len(payload["episodes"]) == 1

    episode = payload["episodes"][0]
    assert episode["scan"] == "scene_a_usd"
    assert episode["trajectory_id"] == "scene_a_usd_chair_model_hash_0_0"
    assert episode["episode_id"] == 0
    assert episode["start_position"] == [1.0, 2.0, 0.0]
    assert episode["start_rotation"] == [1.0, 0.0, 0.0, 0.0]
    assert episode["reference_path"] == [[1.0, 2.0, 0.0], [2.0, 2.0, 0.0], [3.0, 2.0, 0.0]]
    assert episode["instruction"]["instruction_text"] == "Find the chair beside the sofa."
    assert episode["instruction"]["instruction_tokens"] == []
    assert episode["info"]["geodesic_distance"] == 2.5
    assert episode["source"]["object_instance_id"] == "chair/model_hash_0"

    original_fixed = work_root / "scene_data/original/scene_a_usd/fixed.usd"
    converted_fixed = work_root / "scene_data/converted/scene_a_usd/fixed.usd"
    assert original_fixed.read_text(encoding="utf-8") == "#usda 1.0\n"
    assert converted_fixed.read_text(encoding="utf-8") == converted_usd.read_text(encoding="utf-8")

    assert manifest_path.exists()
    persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert persisted["schema_version"] == 1
    assert persisted["scene_records"][0]["pair_status"] == "ready"
    assert persisted["scene_records"][0]["original_fixed_usd"] == str(original_fixed)
    assert persisted["scene_records"][0]["converted_fixed_usd"] == str(converted_fixed)
    assert Path(persisted["internnav_eval_configs"]["original"]).exists()
    assert Path(persisted["internnav_eval_configs"]["converted"]).exists()
    original_eval_cfg = Path(persisted["internnav_eval_configs"]["original"]).read_text(encoding="utf-8")
    assert '"vis_debug": False' in original_eval_cfg
    assert '"vis_output": False' in original_eval_cfg
    original_command = persisted["internnav_eval_commands"]["original"]
    converted_command = persisted["internnav_eval_commands"]["converted"]
    assert "run_internnav_eval.py" in original_command
    assert "scripts/eval/eval.py" not in original_command
    assert "--config" in original_command
    assert persisted["internnav_eval_configs"]["original"] in original_command
    assert "run_internnav_eval.py" in converted_command
    assert "scripts/eval/eval.py" not in converted_command
    assert persisted["internnav_eval_configs"]["converted"] in converted_command
    runtime = persisted["internnav_runtime"]
    assert runtime["wrapper_path"].endswith(
        "paper/shared/evidence/experiments/07_internnav_vln_downstream/run_internnav_eval.py"
    )
    assert runtime["runtime_deps_root"] == "/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523"
    assert runtime["hf_home"] == "/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523/hf_cache"
    assert runtime["hf_hub_disable_xet"] == "1"
    assert runtime["attn_fallback"] == "sdpa"
    assert runtime["nextdit_checkpoint_ffn_multiplier"] == 2 / 3
    assert "hard_blockers_before_metrics" not in persisted["runtime_requirements"]
    assert "required_for_real_metrics" in persisted["runtime_requirements"]


def test_prepare_minipair_installs_grscene_dependency_sidecar_links(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    original_sidecars = write_grscene_sidecar_entries(source_root, "home_scenes", "scene_a_usd")
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    write_scene_usd(
        nomdl_root,
        "home_scenes",
        "scene_a_usd",
        "start_result_navigation_noMDL.usd",
    )
    converted_sidecars = write_grscene_sidecar_entries(nomdl_root, "home_scenes", "scene_a_usd")
    work_root = tmp_path / "internnav_work"

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=work_root,
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=1,
        split_name="mini",
        link_mode="symlink",
    )

    original_scene_dir = work_root / "scene_data/original/scene_a_usd"
    converted_scene_dir = work_root / "scene_data/converted/scene_a_usd"
    for sidecar_name, target in original_sidecars.items():
        installed = original_scene_dir / sidecar_name
        assert installed.is_symlink()
        assert installed.resolve() == target
        assert manifest["scene_records"][0]["original_dependency_sidecars"][sidecar_name] == str(target)
    for sidecar_name, target in converted_sidecars.items():
        installed = converted_scene_dir / sidecar_name
        assert installed.is_symlink()
        assert installed.resolve() == target
        assert manifest["scene_records"][0]["converted_dependency_sidecars"][sidecar_name] == str(target)


def test_prepare_minipair_reports_missing_converted_navigation_usd(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work",
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=1,
        split_name="mini",
        link_mode="copy",
    )

    assert manifest["scene_records"][0]["pair_status"] == "missing_converted_navigation_usd"
    assert manifest["claim_gate"]["can_run_paired_eval"] is False
    assert manifest["claim_gate"]["blocked_by"] == ["missing_converted_navigation_usd"]


def test_prepare_minipair_filters_to_requested_scene_ids(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    write_scene_usd(source_root, "home_scenes", "scene_b_usd", "start_result_navigation.usd")
    write_scene_usd(nomdl_root, "home_scenes", "scene_b_usd", "start_result_navigation_noMDL.usd")
    sn_path = source_root / "benchmark/sn_episodes.json"
    data = json.loads(sn_path.read_text(encoding="utf-8"))
    data["test"]["scene_b_usd"] = {
        "table/model_hash_0": [
            {
                "start_point": [0.0, 0.0],
                "target_point": [0.0, 1.0, 0.0],
                "distance": 1.0,
                "path": [[0.0, 0.0], [0.0, 1.0]],
                "dialogue": [{"role": "human", "content": "Find the table."}],
            }
        ]
    }
    sn_path.write_text(json.dumps(data), encoding="utf-8")

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work",
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=1,
        split_name="mini",
        link_mode="copy",
        scene_ids=["scene_b_usd"],
    )

    assert manifest["episode_records"][0]["scan"] == "scene_b_usd"
    assert manifest["scene_records"][0]["scene_id"] == "scene_b_usd"
    assert manifest["source"]["requested_scene_ids"] == ["scene_b_usd"]
    assert manifest["source"]["selected_scene_ids"] == ["scene_b_usd"]


def test_prepare_minipair_uses_dynamic_task_names_for_acl_batch(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    write_scene_usd(
        nomdl_root,
        "home_scenes",
        "scene_a_usd",
        "start_result_navigation_noMDL.usd",
    )
    write_scene_usd(source_root, "home_scenes", "scene_b_usd", "start_result_navigation.usd")
    write_scene_usd(
        nomdl_root,
        "home_scenes",
        "scene_b_usd",
        "start_result_navigation_noMDL.usd",
    )
    sn_path = source_root / "benchmark/sn_episodes.json"
    data = json.loads(sn_path.read_text(encoding="utf-8"))
    data["test"]["scene_b_usd"] = {
        "table/model_hash_0": [
            {
                "start_point": [0.0, 0.0],
                "target_point": [0.0, 1.0, 0.0],
                "distance": 1.0,
                "path": [[0.0, 0.0], [0.0, 1.0]],
                "dialogue": [{"role": "human", "content": "Find the table."}],
            }
        ]
    }
    sn_path.write_text(json.dumps(data), encoding="utf-8")

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work",
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=2,
        split_name="acl_main_050",
        link_mode="copy",
    )

    assert manifest["dataset"]["split"] == "acl_main_050"
    assert manifest["dataset"]["episode_count"] == 2
    assert "convertasset_grscene_sn_original_acl_main_050" in manifest["internnav_eval_commands"]["original"]
    assert "convertasset_grscene_sn_modified_acl_main_050" in manifest["internnav_eval_commands"]["converted"]
    assert manifest["internnav_eval_commands"]["expected_result_jsons"] == [
        "logs/convertasset_grscene_sn_original_acl_main_050/result.json",
        "logs/convertasset_grscene_sn_modified_acl_main_050/result.json",
    ]
    converted_cfg = Path(manifest["internnav_eval_configs"]["converted"]).read_text(encoding="utf-8")
    assert 'task_name="convertasset_grscene_sn_modified_acl_main_050"' in converted_cfg


def test_prepare_minipair_preserves_legacy_mini_nomdl_result_paths(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    write_scene_usd(
        nomdl_root,
        "home_scenes",
        "scene_a_usd",
        "start_result_navigation_noMDL.usd",
    )

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work",
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=1,
        split_name="mini",
        link_mode="copy",
    )

    assert manifest["internnav_eval_commands"]["expected_result_jsons"] == [
        "logs/convertasset_grscene_sn_original_mini/result.json",
        "logs/convertasset_grscene_sn_nomdl_mini/result.json",
    ]
    assert Path(manifest["internnav_eval_configs"]["original"]).name == "original_eval_cfg.py"
    assert Path(manifest["internnav_eval_configs"]["converted"]).name == "converted_eval_cfg.py"
    converted_cfg = Path(manifest["internnav_eval_configs"]["converted"]).read_text(encoding="utf-8")
    assert 'task_name="convertasset_grscene_sn_nomdl_mini"' in converted_cfg


def test_prepare_minipair_ready_only_round_robins_ready_scenes_and_reports_gate(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    sn_path = source_root / "benchmark/sn_episodes.json"
    data = json.loads(sn_path.read_text(encoding="utf-8"))
    data["test"]["scene_a_usd"]["chair/model_hash_0"].append(
        {
            "start_point": [2.0, 2.0],
            "target_point": [4.0, 2.0, 0.0],
            "distance": 2.0,
            "path": [[2.0, 2.0], [4.0, 2.0]],
            "dialogue": [{"role": "human", "content": "Find another chair."}],
        }
    )
    for scene_id, object_id in (
        ("scene_b_usd", "table/model_hash_0"),
        ("scene_c_usd", "lamp/model_hash_0"),
        ("scene_d_usd", "sofa/model_hash_0"),
    ):
        write_scene_usd(source_root, "home_scenes", scene_id, "start_result_navigation.usd")
        data["test"][scene_id] = {
            object_id: [
                {
                    "start_point": [0.0, 0.0],
                    "target_point": [0.0, 1.0, 0.0],
                    "distance": 1.0,
                    "path": [[0.0, 0.0], [0.0, 1.0]],
                    "dialogue": [{"role": "human", "content": f"Find {object_id.split('/')[0]}."}],
                },
                {
                    "start_point": [1.0, 0.0],
                    "target_point": [1.0, 1.0, 0.0],
                    "distance": 1.0,
                    "path": [[1.0, 0.0], [1.0, 1.0]],
                    "dialogue": [{"role": "human", "content": f"Find another {object_id.split('/')[0]}."}],
                },
            ]
        }
    sn_path.write_text(json.dumps(data), encoding="utf-8")
    for scene_id in ("scene_a_usd", "scene_b_usd", "scene_d_usd"):
        write_scene_usd(nomdl_root, "home_scenes", scene_id, "start_result_navigation_noMDL.usd")

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work",
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=3,
        split_name="acl_main_ready3",
        link_mode="copy",
        ready_only=True,
        min_scenes=3,
        selection_strategy="round_robin_scenes",
    )

    assert manifest["claim_gate"]["can_run_paired_eval"] is True
    assert manifest["claim_gate"]["selected_scene_count"] == 3
    assert manifest["source"]["selected_scene_ids"] == ["scene_a_usd", "scene_b_usd", "scene_d_usd"]
    assert [record["scan"] for record in manifest["episode_records"]] == [
        "scene_a_usd",
        "scene_b_usd",
        "scene_d_usd",
    ]
    assert manifest["selection"]["ready_only"] is True
    assert manifest["selection"]["selection_strategy"] == "round_robin_scenes"
    assert manifest["selection"]["skipped_scene_count"] == 1
    assert manifest["selection"]["skipped_scene_records"][0]["scene_id"] == "scene_c_usd"
    assert manifest["selection"]["skipped_scene_records"][0]["blocked_by"] == ["missing_converted_navigation_usd"]

    blocked_manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work_blocked",
        repo_manifest_path=tmp_path / "prep_manifest_blocked.json",
        max_episodes=2,
        split_name="acl_main_ready2",
        link_mode="copy",
        ready_only=True,
        min_scenes=3,
        selection_strategy="round_robin_scenes",
    )

    assert blocked_manifest["claim_gate"]["can_run_paired_eval"] is False
    assert blocked_manifest["claim_gate"]["blocked_by"] == ["insufficient_ready_scenes"]
    assert blocked_manifest["claim_gate"]["selected_scene_count"] == 2


def test_prepare_minipair_excludes_path_key_and_replaces_from_selection_order(tmp_path: Path) -> None:
    module = load_prep_module()
    source_root = make_source_root(tmp_path)
    nomdl_root = tmp_path / "zzh-grscenes_nomdl"
    sn_path = source_root / "benchmark/sn_episodes.json"
    data = json.loads(sn_path.read_text(encoding="utf-8"))
    for index, scene_id in enumerate(("scene_a_usd", "scene_b_usd", "scene_c_usd")):
        write_scene_usd(source_root, "home_scenes", scene_id, "start_result_navigation.usd")
        write_scene_usd(nomdl_root, "home_scenes", scene_id, "start_result_navigation_noMDL.usd")
        data["test"][scene_id] = {
            f"object{index}/model_hash_0": [
                {
                    "start_point": [0.0, 0.0],
                    "target_point": [0.0, 1.0, 0.0],
                    "distance": 1.0,
                    "path": [[0.0, 0.0], [0.0, 1.0]],
                    "dialogue": [{"role": "human", "content": f"Find object {index}."}],
                },
                {
                    "start_point": [1.0, 0.0],
                    "target_point": [1.0, 1.0, 0.0],
                    "distance": 1.0,
                    "path": [[1.0, 0.0], [1.0, 1.0]],
                    "dialogue": [{"role": "human", "content": f"Find another object {index}."}],
                },
            ]
        }
    sn_path.write_text(json.dumps(data), encoding="utf-8")
    superseded_manifest = tmp_path / "acl_main_pilot30_prep_manifest.json"
    superseded_manifest.write_text('{"dataset":{"split":"acl_main_pilot30"}}\n', encoding="utf-8")

    manifest = module.prepare_minipair(
        source_root=source_root,
        nomdl_root=nomdl_root,
        work_root=tmp_path / "internnav_work",
        repo_manifest_path=tmp_path / "prep_manifest.json",
        max_episodes=3,
        split_name="acl_main_exclusion",
        link_mode="copy",
        ready_only=True,
        min_scenes=2,
        selection_strategy="round_robin_scenes",
        excluded_path_keys=["scene_b_usd_object1_model_hash_0_0_1"],
        exclusion_reason="simulator_hang_reset_warmup_no_terminal_metrics",
        supersedes_manifest_path=superseded_manifest,
    )

    assert manifest["claim_gate"]["can_run_paired_eval"] is True
    assert manifest["dataset"]["episode_count"] == 3
    assert manifest["selection"]["requested_excluded_path_keys"] == ["scene_b_usd_object1_model_hash_0_0_1"]
    assert manifest["selection"]["unmatched_excluded_path_keys"] == []
    assert manifest["selection"]["excluded_episode_count"] == 1
    assert manifest["selection"]["excluded_episode_records"] == [
        {
            "path_key": "scene_b_usd_object1_model_hash_0_0_1",
            "reason": "simulator_hang_reset_warmup_no_terminal_metrics",
            "scan": "scene_b_usd",
            "source_selection_rank": 1,
            "trajectory_id": "scene_b_usd_object1_model_hash_0_0",
        }
    ]
    assert [record["scan"] for record in manifest["episode_records"]] == [
        "scene_a_usd",
        "scene_c_usd",
        "scene_a_usd",
    ]
    assert manifest["selection"]["replacement_episode_count"] == 1
    assert manifest["selection"]["replacement_episode_records"][0]["source_selection_rank"] == 3
    assert manifest["selection"]["replacement_episode_records"][0]["scan"] == "scene_a_usd"
    assert manifest["episode_records"][2]["source_path_key"] == "scene_a_usd_object0_model_hash_0_1_3"
    assert manifest["selection"]["supersedes_manifest"]["path"] == str(superseded_manifest)
    assert len(manifest["selection"]["supersedes_manifest"]["hash_sha256"]) == 64


def test_collect_results_writes_metric_deltas(tmp_path: Path) -> None:
    module = load_collect_module()
    manifest_path = tmp_path / "prep_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "dataset": {"split": "mini", "episode_count": 2},
            "scene_records": [{"scene_id": "scene_a_usd", "pair_status": "ready"}],
            "internnav_eval_commands": {
                "expected_result_jsons": [
                    "logs/convertasset_grscene_sn_original_mini/result.json",
                    "logs/convertasset_grscene_sn_nomdl_mini/result.json",
                ]
            },
        },
    )
    original_result = tmp_path / "InternNav/logs/convertasset_grscene_sn_original_mini/result.json"
    converted_result = tmp_path / "InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json"
    write_json(
        original_result,
        {"mini": {"TL": 10.0, "NE": 1.2, "FR": 0.0, "StR": 0.5, "OS": 0.6, "SR": 0.5, "SPL": 0.4, "Count": 2}},
    )
    write_json(
        converted_result,
        {"mini": {"TL": 11.0, "NE": 1.4, "FR": 0.0, "StR": 0.4, "OS": 0.5, "SR": 0.4, "SPL": 0.3, "Count": 2}},
    )
    output_path = tmp_path / "internnav_vln_results.json"

    summary = module.collect_results(
        prep_manifest_path=manifest_path,
        original_result_path=original_result,
        converted_result_path=converted_result,
        output_path=output_path,
    )

    assert summary["schema_version"] == 1
    assert summary["claim_boundary"] == "actual_internnav_metrics_from_supplied_result_jsons"
    assert summary["split"] == "mini"
    assert summary["metrics"]["original"]["SR"] == 0.5
    assert summary["metrics"]["converted"]["SPL"] == 0.3
    assert summary["metric_deltas"]["SR"] == -0.1
    assert summary["metric_deltas"]["SPL"] == -0.1
    assert summary["metric_deltas"]["NE"] == 0.2
    assert json.loads(output_path.read_text(encoding="utf-8")) == summary


def test_collect_results_rejects_unexpected_result_paths(tmp_path: Path) -> None:
    module = load_collect_module()
    manifest_path = tmp_path / "prep_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "dataset": {"split": "mini", "episode_count": 1},
            "internnav_eval_commands": {
                "expected_result_jsons": [
                    "logs/convertasset_grscene_sn_original_mini/result.json",
                    "logs/convertasset_grscene_sn_nomdl_mini/result.json",
                ]
            },
        },
    )
    wrong_original = tmp_path / "InternNav/logs/old_original/result.json"
    converted_result = tmp_path / "InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json"
    result_payload = {"mini": {"TL": 1.0, "NE": 1.0, "FR": 0.0, "StR": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 1.0, "Count": 1}}
    write_json(wrong_original, result_payload)
    write_json(converted_result, result_payload)

    try:
        module.collect_results(
            prep_manifest_path=manifest_path,
            original_result_path=wrong_original,
            converted_result_path=converted_result,
            output_path=tmp_path / "internnav_vln_results.json",
        )
    except ValueError as exc:
        assert "does not match expected InternNav result suffix" in str(exc)
    else:
        raise AssertionError("collect_results accepted a mismatched original result path")


def test_collect_results_rejects_count_mismatch(tmp_path: Path) -> None:
    module = load_collect_module()
    manifest_path = tmp_path / "prep_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "dataset": {"split": "mini", "episode_count": 2},
            "internnav_eval_commands": {
                "expected_result_jsons": [
                    "logs/convertasset_grscene_sn_original_mini/result.json",
                    "logs/convertasset_grscene_sn_nomdl_mini/result.json",
                ]
            },
        },
    )
    original_result = tmp_path / "InternNav/logs/convertasset_grscene_sn_original_mini/result.json"
    converted_result = tmp_path / "InternNav/logs/convertasset_grscene_sn_nomdl_mini/result.json"
    wrong_count = {"mini": {"TL": 1.0, "NE": 1.0, "FR": 0.0, "StR": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 1.0, "Count": 1}}
    write_json(original_result, wrong_count)
    write_json(converted_result, wrong_count)

    try:
        module.collect_results(
            prep_manifest_path=manifest_path,
            original_result_path=original_result,
            converted_result_path=converted_result,
            output_path=tmp_path / "internnav_vln_results.json",
        )
    except ValueError as exc:
        assert "Count does not match prep manifest episode_count" in str(exc)
    else:
        raise AssertionError("collect_results accepted mismatched Count")


def test_extract_episode_metrics_normalizes_internnav_lmdb_record() -> None:
    module = load_extract_module()

    row = module.record_to_episode_row(
        condition="original",
        path_key="scene_obj_0_0",
        record={
            "info": {
                "TL": 10.0,
                "NE": 1.0,
                "osr": 1.0,
                "success": 0.0,
                "spl": 0.0,
                "steps": 200,
            },
            "finish_status": "fail",
            "fail_reason": "exceed_total_max_step",
        },
    )

    assert row == {
        "condition": "original",
        "path_key": "scene_obj_0_0",
        "finish_status": "fail",
        "failure_reason": "exceed_total_max_step",
        "metrics": {
            "TL": 10.0,
            "NE": 1.0,
            "OS": 1.0,
            "SR": 0.0,
            "SPL": 0.0,
            "steps": 200,
        },
    }


def test_extract_episode_metrics_requires_expected_metric_keys_and_normalizes_sentinels() -> None:
    module = load_extract_module()

    row = module.record_to_episode_row(
        condition="modified",
        path_key="episode_0",
        record={
            "info": {
                "TL": 1.0,
                "NE": -1.0,
                "osr": -1.0,
                "success": 0.0,
                "spl": 0.0,
                "steps": 10,
            },
            "finish_status": "fail",
            "fail_reason": "not_reach_goal",
        },
    )

    assert row["metrics"]["NE"] == 0.0
    assert row["metrics"]["OS"] == 0.0

    try:
        module.record_to_episode_row(
            condition="original",
            path_key="episode_1",
            record={
                "info": {"TL": 1.0, "NE": 1.0, "success": 0.0, "spl": 0.0, "steps": 10},
                "finish_status": "fail",
                "fail_reason": "not_reach_goal",
            },
        )
    except KeyError as exc:
        assert "missing InternNav metric keys" in str(exc)
    else:
        raise AssertionError("extractor accepted a record missing osr")


def test_analyze_paired_metrics_computes_paper_summary() -> None:
    module = load_analyze_module()
    rows = [
        {
            "condition": "original",
            "path_key": "episode_0",
            "failure_reason": "success",
            "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5, "steps": 100},
        },
        {
            "condition": "modified",
            "path_key": "episode_0",
            "failure_reason": "not_reach_goal",
            "metrics": {"TL": 12.0, "NE": 3.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 120},
        },
        {
            "condition": "original",
            "path_key": "episode_1",
            "failure_reason": "exceed_total_max_step",
            "metrics": {"TL": 5.0, "NE": 4.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 80},
        },
        {
            "condition": "modified",
            "path_key": "episode_1",
            "failure_reason": "exceed_total_max_step",
            "metrics": {"TL": 7.0, "NE": 5.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 90},
        },
    ]

    summary = module.analyze_paired_rows(rows)

    assert summary["schema_version"] == 1
    assert summary["episode_count"] == 2
    assert summary["metrics"]["NE"]["original_mean"] == 2.5
    assert summary["metrics"]["NE"]["modified_mean"] == 4.0
    assert summary["metrics"]["NE"]["mean_delta_modified_minus_original"] == 1.5
    assert summary["metrics"]["NE"]["cohen_dz"] == 2.1213
    assert summary["metrics"]["Count"]["original_mean"] == 1.0
    assert summary["metrics"]["FR"]["original_mean"] == 0.0
    assert summary["metrics"]["StR"]["original_mean"] == 0.0
    assert summary["paired_outcomes"]["SR"] == {
        "modified_better": 0,
        "original_better": 1,
        "tie": 1,
    }
    assert summary["paired_outcomes"]["NE"] == {
        "modified_better": 0,
        "original_better": 2,
        "tie": 0,
    }
    assert summary["failure_pairs"]["original_success__modified_not_reach_goal"] == 1
    assert summary["claim_gate"]["has_paired_episode_metrics"] is True
    assert summary["claim_gate"]["acl_main_result_ready"] is False


def test_analyze_paired_metrics_does_not_claim_acl_ready_from_counts_alone() -> None:
    module = load_analyze_module()
    rows = []
    for scene_idx in range(10):
        for episode_idx in range(10):
            path_key = f"scene_{scene_idx}_usd_obj_{episode_idx}"
            rows.append(
                {
                    "condition": "original",
                    "path_key": path_key,
                    "failure_reason": "success",
                    "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5, "steps": 100},
                }
            )
            rows.append(
                {
                    "condition": "modified",
                    "path_key": path_key,
                    "failure_reason": "success",
                    "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5, "steps": 100},
                }
            )

    summary = module.analyze_paired_rows(rows)

    assert summary["episode_count"] == 100
    assert summary["scene_count"] == 10
    assert summary["claim_gate"]["row_count_acl_ready"] is True
    assert summary["claim_gate"]["has_video_manifest"] is False
    assert summary["claim_gate"]["has_aggregate_result_json"] is False
    assert summary["claim_gate"]["acl_main_result_ready"] is False


def test_analyze_paired_metrics_rejects_missing_metric_rows() -> None:
    module = load_analyze_module()

    try:
        module.analyze_paired_rows(
            [
                {
                    "condition": "original",
                    "path_key": "episode_0",
                    "failure_reason": "success",
                    "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5},
                },
                {
                    "condition": "modified",
                    "path_key": "episode_0",
                    "failure_reason": "success",
                    "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5, "steps": 100},
                },
            ]
        )
    except KeyError as exc:
        assert "missing metric steps" in str(exc)
    else:
        raise AssertionError("analyzer accepted a row missing steps")


def test_select_video_cases_builds_storage_bounded_manifest() -> None:
    module = load_video_select_module()
    rows = [
        {
            "condition": "original",
            "path_key": "scene_a_usd_obj_0_0",
            "failure_reason": "success",
            "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5, "steps": 100},
        },
        {
            "condition": "modified",
            "path_key": "scene_a_usd_obj_0_0",
            "failure_reason": "not_reach_goal",
            "metrics": {"TL": 12.0, "NE": 3.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 120},
        },
        {
            "condition": "original",
            "path_key": "scene_b_usd_obj_0_0",
            "failure_reason": "not_reach_goal",
            "metrics": {"TL": 9.0, "NE": 2.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 90},
        },
        {
            "condition": "modified",
            "path_key": "scene_b_usd_obj_0_0",
            "failure_reason": "success",
            "metrics": {"TL": 7.0, "NE": 0.5, "OS": 1.0, "SR": 1.0, "SPL": 0.6, "steps": 70},
        },
        {
            "condition": "original",
            "path_key": "scene_c_usd_obj_0_0",
            "failure_reason": "exceed_total_max_step",
            "metrics": {"TL": 20.0, "NE": 4.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 200},
        },
        {
            "condition": "modified",
            "path_key": "scene_c_usd_obj_0_0",
            "failure_reason": "exceed_total_max_step",
            "metrics": {"TL": 50.0, "NE": 20.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 250},
        },
    ]

    manifest = module.select_video_cases(rows, max_cases=8)

    assert manifest["storage_policy"]["metric_runs_keep_video_disabled"] is True
    assert manifest["case_quota"]["max_cases"] == 8
    assert manifest["case_quota"]["selected_count"] == 3
    assert {case["case_type"] for case in manifest["selected_cases"]} == {
        "original_only_success",
        "modified_only_success",
        "both_failure_divergent",
    }
    assert manifest["selected_cases"][0]["rerun_profile"] == "video_selected_only"


def test_select_video_cases_reserves_diverse_case_types_when_over_quota() -> None:
    module = load_video_select_module()
    rows = []
    for idx in range(4):
        rows.extend(
            [
                {
                    "condition": "original",
                    "path_key": f"original_only_{idx}",
                    "failure_reason": "success",
                    "metrics": {"TL": 10.0, "NE": 1.0, "OS": 1.0, "SR": 1.0, "SPL": 0.5, "steps": 100},
                },
                {
                    "condition": "modified",
                    "path_key": f"original_only_{idx}",
                    "failure_reason": "not_reach_goal",
                    "metrics": {"TL": 20.0, "NE": 10.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 200},
                },
            ]
        )
    rows.extend(
        [
            {
                "condition": "original",
                "path_key": "modified_only_0",
                "failure_reason": "not_reach_goal",
                "metrics": {"TL": 20.0, "NE": 10.0, "OS": 0.0, "SR": 0.0, "SPL": 0.0, "steps": 200},
            },
            {
                "condition": "modified",
                "path_key": "modified_only_0",
                "failure_reason": "success",
                "metrics": {"TL": 8.0, "NE": 0.5, "OS": 1.0, "SR": 1.0, "SPL": 0.6, "steps": 80},
            },
        ]
    )

    manifest = module.select_video_cases(rows, max_cases=2)

    assert {case["case_type"] for case in manifest["selected_cases"]} == {
        "original_only_success",
        "modified_only_success",
    }


def test_select_video_cases_rejects_non_positive_case_quota() -> None:
    module = load_video_select_module()

    try:
        module.select_video_cases([], max_cases=0)
    except ValueError as exc:
        assert "max_cases must be positive" in str(exc)
    else:
        raise AssertionError("selector accepted max_cases=0")


def test_run_internnav_eval_builds_runtime_env_without_dropping_existing_pythonpath(tmp_path: Path) -> None:
    module = load_run_module()
    deps_root = tmp_path / "runtime_deps"
    internnav_root = tmp_path / "InternNav"

    env = module.build_runtime_env(
        runtime_deps_root=deps_root,
        internnav_root=internnav_root,
        base_env={"PYTHONPATH": "/already/there"},
    )

    entries = env["PYTHONPATH"].split(":")
    assert entries[:3] == [
        str(deps_root / "python_target"),
        str(deps_root / "internutopia_probe"),
        str(internnav_root),
    ]
    assert entries[3] == "/already/there"
    assert env["HF_HOME"] == str(deps_root / "hf_cache")
    assert env["HF_HUB_DISABLE_XET"] == "1"


def test_run_internnav_eval_forces_xet_disabled_even_if_parent_env_enables_it(tmp_path: Path) -> None:
    module = load_run_module()
    deps_root = tmp_path / "runtime_deps"
    internnav_root = tmp_path / "InternNav"

    env = module.build_runtime_env(
        runtime_deps_root=deps_root,
        internnav_root=internnav_root,
        base_env={"HF_HUB_DISABLE_XET": "0"},
    )

    assert env["HF_HUB_DISABLE_XET"] == "1"


def test_run_internnav_eval_dry_run_reports_wrapper_configuration(tmp_path: Path, capsys) -> None:
    module = load_run_module()
    deps_root = tmp_path / "runtime_deps"
    internnav_root = tmp_path / "InternNav"
    config_path = tmp_path / "original_eval_cfg.py"
    config_path.write_text("eval_cfg = None\n", encoding="utf-8")

    exit_code = module.main(
        [
            "--config",
            str(config_path),
            "--runtime-deps-root",
            str(deps_root),
            "--internnav-root",
            str(internnav_root),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["config_path"] == str(config_path)
    assert payload["internnav_root"] == str(internnav_root)
    assert payload["runtime_deps_root"] == str(deps_root)
    assert payload["preload_internvla_policy"] is True


def test_run_internnav_eval_selects_sdpa_when_flash_attention_is_missing() -> None:
    module = load_run_module()

    assert (
        module.select_attn_implementation(
            requested="flash_attention_2",
            fallback="sdpa",
            flash_attention_available=False,
        )
        == "sdpa"
    )
    assert (
        module.select_attn_implementation(
            requested="flash_attention_2",
            fallback="sdpa",
            flash_attention_available=True,
        )
        == "flash_attention_2"
    )
    assert (
        module.select_attn_implementation(
            requested="eager",
            fallback="sdpa",
            flash_attention_available=False,
        )
        == "eager"
    )


def test_run_internnav_eval_sets_gradient_checkpointing_on_nested_modules() -> None:
    module = load_run_module()

    class Child:
        gradient_checkpointing = False

    child = Child()

    class Parent:
        gradient_checkpointing = False

        def modules(self):
            return [self, child]

    parent = Parent()
    module.set_gradient_checkpointing_compat(parent, enable=True)

    assert parent.gradient_checkpointing is True
    assert child.gradient_checkpointing is True


def test_run_internnav_eval_exposes_packaging_on_pkg_resources(monkeypatch) -> None:
    module = load_run_module()
    fake_pkg_resources = types.SimpleNamespace()
    fake_packaging = types.SimpleNamespace(version="fake")
    monkeypatch.setitem(sys.modules, "pkg_resources", fake_pkg_resources)
    monkeypatch.setitem(sys.modules, "packaging", fake_packaging)

    module.patch_pkg_resources_packaging()

    assert fake_pkg_resources.packaging is fake_packaging


def test_run_internnav_eval_patches_nextdit_config_default_ffn_multiplier() -> None:
    module = load_run_module()

    class FakeNextDiTConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    module.patch_nextdit_config_default_ffn_multiplier(FakeNextDiTConfig)

    default_cfg = FakeNextDiTConfig(latent_embedding_size=768)
    explicit_cfg = FakeNextDiTConfig(ffn_dim_multiplier=0.5)

    assert default_cfg.kwargs["ffn_dim_multiplier"] == 2 / 3
    assert explicit_cfg.kwargs["ffn_dim_multiplier"] == 0.5
