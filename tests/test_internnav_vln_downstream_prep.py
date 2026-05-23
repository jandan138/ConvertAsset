import gzip
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/prepare_minipair.py"
COLLECT_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/collect_results.py"


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


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_scene_usd(root: Path, scene_split: str, scene_id: str, usd_name: str) -> Path:
    scene_dir = root / "scenes/GRScenes-100" / scene_split / "scenes" / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)
    usd_path = scene_dir / usd_name
    usd_path.write_text("#usda 1.0\n", encoding="utf-8")
    return usd_path


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
