import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/prepare_source_manifest.py"


def load_manifest_module():
    spec = importlib.util.spec_from_file_location("grscenes_prepare_source_manifest", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_scene(scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True)
    for name in ("start_result_raw.usd", "start_result_navigation.usd", "start_result_interaction.usd"):
        (scene_dir / name).write_text("#usda 1.0\n", encoding="utf-8")
    metadata = {
        "models": [
            "models/object/others/cabinet/a/instance.usd",
            "models/object/others/chair/b/instance.usd",
        ]
    }
    (scene_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (scene_dir / "interactive_obj_list.json").write_text("{}", encoding="utf-8")
    (scene_dir / "Materials").write_text("../../Materials", encoding="utf-8")
    (scene_dir / "models").write_text("../../models", encoding="utf-8")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_grscenes_root(tmp_path: Path) -> Path:
    source_root = tmp_path / "zzh-grscenes"
    benchmark = source_root / "benchmark"
    scenes_root = source_root / "scenes/GRScenes-100"

    for scene_id in ("home_a_usd", "home_b_usd"):
        write_scene(scenes_root / "home_scenes/scenes" / scene_id)
    for scene_id in ("commercial_a_usd", "commercial_b_usd"):
        write_scene(scenes_root / "commercial_scenes/scenes" / scene_id)

    episode = {
        "test": {
            "home_a_usd": {
                "cabinet/model_a_0": [
                    {
                        "instruction": "find cabinet",
                        "condition": "visible",
                        "prompt": "Point to the cabinet.",
                        "candidates": ["cabinet/model_a_0"],
                    }
                ]
            }
        },
        "validate": {
            "home_b_usd": {
                "chair/model_b_0": [
                    {
                        "instruction": "find chair",
                        "condition": "visible",
                        "prompt": "Point to the chair.",
                        "candidates": ["chair/model_b_0"],
                    }
                ]
            }
        },
    }
    write_json(benchmark / "mm_episodes.json", episode)
    write_json(benchmark / "sn_episodes.json", episode)
    return source_root


def test_build_source_manifest_separates_episode_home_and_commercial_stress(tmp_path: Path) -> None:
    module = load_manifest_module()
    source_root = make_grscenes_root(tmp_path)
    scratch_root = tmp_path / "scratch"

    manifest = module.build_source_manifest(
        source_root=source_root,
        scratch_root=scratch_root,
        episode_home_scenes=1,
        metadata_commercial_scenes=1,
        targets_per_scene=2,
    )

    assert manifest["schema_version"] == 1
    assert manifest["protocol_path"].endswith("protocol.yaml")
    assert len(manifest["protocol_hash_sha256"]) == 64
    assert manifest["dataset_roles"]["benchmark_source_dataset"]["local_root"] == str(source_root)
    assert manifest["selection"]["episode_home_scenes"] == 1
    assert manifest["selection"]["metadata_commercial_scenes"] == 1
    assert manifest["selection"]["targets_per_scene"] == 2

    home_entry, commercial_entry = manifest["scenes"]
    assert home_entry["pilot_role"] == "episode_backed_home"
    assert home_entry["paper_claim_eligible"] is True
    assert home_entry["episode_sources"] == ["mm_episodes.json", "sn_episodes.json"]
    assert home_entry["source_scene_split"] == "home_scenes"
    assert "/scenes/GRScenes-100/home_scenes/scenes/home_a_usd" in home_entry["scratch_scene_root"]
    assert home_entry["source_usd"].endswith("/start_result_raw.usd")
    assert home_entry["converted_usd"].endswith("/start_result_raw_noMDL.usd")
    assert len(home_entry["source_usd_hash_sha256"]) == 64
    assert len(home_entry["metadata_hash_sha256"]) == 64

    assert commercial_entry["pilot_role"] == "metadata_driven_commercial_stress"
    assert commercial_entry["paper_claim_eligible"] is False
    assert commercial_entry["episode_sources"] == []
    assert commercial_entry["source_scene_split"] == "commercial_scenes"

    assert len(manifest["episode_records"]) == 2
    episode_record = manifest["episode_records"][0]
    assert episode_record["source_scene_id"] == "home_a_usd"
    assert episode_record["episode_json_pointer"].startswith("/test/home_a_usd/")
    assert episode_record["episode_file"] in {"mm_episodes.json", "sn_episodes.json"}
    assert len(episode_record["stable_episode_id"]) >= 16
    assert len(episode_record["episode_hash_sha256"]) == 64
    assert len(episode_record["episode_file_hash_sha256"]) == 64
    assert episode_record["mapping_status"] == "pending_metadata_to_prim"
    assert episode_record["target_prim_path"] is None
    assert episode_record["object_category"] == "cabinet"
    assert episode_record["model_hash"] == "a"
    assert episode_record["instance_index"] == 0
    assert episode_record["metadata_match_count"] == 1
    assert episode_record["metadata_model_paths"] == ["models/object/others/cabinet/a/instance.usd"]


def test_build_source_manifest_rejects_scratch_inside_source_root(tmp_path: Path) -> None:
    module = load_manifest_module()
    source_root = make_grscenes_root(tmp_path)

    with pytest.raises(ValueError, match="scratch_root must not be inside source_root"):
        module.build_source_manifest(
            source_root=source_root,
            scratch_root=source_root / "scratch",
            episode_home_scenes=1,
            metadata_commercial_scenes=0,
            targets_per_scene=1,
        )


def test_build_source_manifest_reports_missing_required_scene_files(tmp_path: Path) -> None:
    module = load_manifest_module()
    source_root = make_grscenes_root(tmp_path)
    missing_file = (
        source_root
        / "scenes/GRScenes-100/home_scenes/scenes/home_a_usd/start_result_interaction.usd"
    )
    missing_file.unlink()

    with pytest.raises(FileNotFoundError, match="start_result_interaction.usd"):
        module.build_source_manifest(
            source_root=source_root,
            scratch_root=tmp_path / "scratch",
            episode_home_scenes=1,
            metadata_commercial_scenes=0,
            targets_per_scene=1,
        )
