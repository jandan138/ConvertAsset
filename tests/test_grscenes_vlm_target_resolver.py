import importlib.util
import pytest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/resolve_target_prims.py"


def load_resolver_module():
    spec = importlib.util.spec_from_file_location("grscenes_resolve_target_prims", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_imports_without_pxr() -> None:
    module = load_resolver_module()

    assert hasattr(module, "resolve_episode_record")


def test_asset_path_matches_metadata_path_with_relative_prefixes() -> None:
    module = load_resolver_module()

    assert module.asset_path_matches_metadata_path(
        "../../models/object/others/cabinet/abc123/instance.usd",
        "models/object/others/cabinet/abc123/instance.usd",
    )
    assert not module.asset_path_matches_metadata_path(
        "../../models/object/others/chair/abc123/instance.usd",
        "models/object/others/cabinet/abc123/instance.usd",
    )


def test_resolve_episode_record_selects_candidate_by_instance_index() -> None:
    module = load_resolver_module()
    episode_record = {
        "object_instance_id": "cabinet/model_abc123_1",
        "object_category": "cabinet",
        "model_hash": "abc123",
        "instance_index": 1,
        "metadata_model_paths": ["models/object/others/cabinet/abc123/instance.usd"],
    }
    prim_records = [
        {
            "prim_path": "/World/Scene/cabinet_0",
            "asset_paths": ["../../models/object/others/cabinet/abc123/instance.usd"],
            "world_bbox": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
        },
        {
            "prim_path": "/World/Scene/cabinet_1",
            "asset_paths": ["../../models/object/others/cabinet/abc123/instance.usd"],
            "world_bbox": {"min": [2.0, 0.0, 0.0], "max": [3.0, 1.0, 1.0]},
        },
    ]

    resolved = module.resolve_episode_record(episode_record, prim_records)

    assert resolved["mapping_status"] == "resolved_metadata_reference_to_prim"
    assert resolved["mapping_method"] == "metadata_model_path_to_authored_reference"
    assert resolved["mapping_confidence"] == "medium_instance_index"
    assert resolved["target_prim_path"] == "/World/Scene/cabinet_1"
    assert resolved["candidate_prim_paths"] == ["/World/Scene/cabinet_0", "/World/Scene/cabinet_1"]
    assert resolved["world_bbox"]["min"] == [2.0, 0.0, 0.0]


def test_resolve_episode_record_prefers_exact_suffix_over_candidate_index() -> None:
    module = load_resolver_module()
    episode_record = {
        "object_instance_id": "cabinet/model_abc123_10",
        "object_category": "cabinet",
        "model_hash": "abc123",
        "instance_index": 10,
        "metadata_model_paths": ["models/object/others/cabinet/abc123/instance.usd"],
    }
    prim_records = [
        {
            "prim_path": "/Root/Meshes/Furnitures/cabinet/model_abc123_0",
            "asset_paths": ["models/object/others/cabinet/abc123/instance.usd"],
            "world_bbox": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
        },
        {
            "prim_path": "/Root/Meshes/Furnitures/cabinet/model_abc123_10",
            "asset_paths": ["models/object/others/cabinet/abc123/instance.usd"],
            "world_bbox": {"min": [10.0, 0.0, 0.0], "max": [11.0, 1.0, 1.0]},
        },
    ]

    resolved = module.resolve_episode_record(episode_record, prim_records)

    assert resolved["mapping_status"] == "resolved_metadata_reference_to_prim"
    assert resolved["target_prim_path"] == "/Root/Meshes/Furnitures/cabinet/model_abc123_10"
    assert resolved["world_bbox"]["min"] == [10.0, 0.0, 0.0]


def test_resolve_episode_record_falls_back_to_exact_prim_suffix() -> None:
    module = load_resolver_module()
    episode_record = {
        "object_instance_id": "pillow/model_fd19fbe9bc625e175917e78b747bd35b_0",
        "object_category": "pillow",
        "model_hash": "fd19fbe9bc625e175917e78b747bd35b",
        "instance_index": 0,
        "metadata_model_paths": ["models/object/others/pillow/fd19fbe9bc625e175917e78b747bd35b/instance.usd"],
    }
    prim_records = [
        {
            "prim_path": "/Root/Meshes/Furnitures/pillow/model_fd19fbe9bc625e175917e78b747bd35b_0",
            "asset_paths": [],
            "world_bbox": {"min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 1.0]},
        }
    ]

    resolved = module.resolve_episode_record(episode_record, prim_records)

    assert resolved["mapping_status"] == "resolved_prim_suffix_to_prim"
    assert resolved["mapping_method"] == "prim_suffix_exact"
    assert resolved["mapping_confidence"] == "medium"
    assert resolved["target_prim_path"] == "/Root/Meshes/Furnitures/pillow/model_fd19fbe9bc625e175917e78b747bd35b_0"


def test_resolve_episode_record_reports_missing_candidate_explicitly() -> None:
    module = load_resolver_module()
    episode_record = {
        "object_instance_id": "cabinet/model_abc123_0",
        "object_category": "cabinet",
        "model_hash": "abc123",
        "instance_index": 0,
        "metadata_model_paths": ["models/object/others/cabinet/abc123/instance.usd"],
    }

    resolved = module.resolve_episode_record(episode_record, [])

    assert resolved["mapping_status"] == "unresolved_no_matching_prim"
    assert resolved["mapping_method"] == "metadata_model_path_to_authored_reference"
    assert resolved["mapping_confidence"] == "none"
    assert resolved["target_prim_path"] is None
    assert resolved["candidate_prim_paths"] == []
    assert resolved["world_bbox"] is None


def test_resolve_model_path_uses_scene_split_level_model_root(tmp_path: Path) -> None:
    module = load_resolver_module()
    source_root = tmp_path / "zzh-grscenes"

    resolved = module.resolve_model_path(
        source_root,
        "home_scenes",
        "models/object/others/bottle/abc123/instance.usd",
    )

    assert resolved == (
        source_root
        / "scenes/GRScenes-100/home_scenes/models/object/others/bottle/abc123/instance.usd"
    ).resolve()


def test_resolution_summary_counts_unique_targets() -> None:
    module = load_resolver_module()
    records = [
        {
            "source_scene_id": "scene_a",
            "object_instance_id": "cup/model_a_0",
            "target_prim_path": "/Root/cup/model_a_0",
        },
        {
            "source_scene_id": "scene_a",
            "object_instance_id": "cup/model_a_0",
            "target_prim_path": "/Root/cup/model_a_0",
        },
        {
            "source_scene_id": "scene_a",
            "object_instance_id": "plate/model_b_0",
            "target_prim_path": "/Root/plate/model_b_0",
        },
    ]

    summary = module.target_uniqueness_summary(records)

    assert summary == {
        "unique_target_prim_count": 2,
        "duplicate_episode_target_count": 1,
        "max_episode_records_per_unique_target": 2,
    }


def test_validate_output_path_rejects_source_tree_destination(tmp_path: Path) -> None:
    module = load_resolver_module()
    source_root = tmp_path / "zzh-grscenes"
    source_root.mkdir()
    manifest = {"dataset_roles": {"benchmark_source_dataset": {"local_root": str(source_root)}}}

    with pytest.raises(ValueError, match="output path must not be inside benchmark source root"):
        module.validate_output_path(source_root / "target_manifest.json", manifest)
