import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/audit_episode_height_filter.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("internnav_episode_height_audit", AUDIT_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_max_adjacent_z_delta_detects_single_target_height_jump() -> None:
    module = load_audit_module()

    delta = module.max_adjacent_z_delta(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.89],
        ]
    )

    assert delta == 0.89


def test_episode_summary_matches_internnav_different_height_threshold() -> None:
    module = load_audit_module()
    episode = {
        "episode_id": 6,
        "trajectory_id": "scene_usd_bottle_model_hash_0_0",
        "instruction": {"instruction_text": "Navigate to bottle."},
        "reference_path": [
            [-1.0, 1.0, 0.0],
            [-2.0, 1.0, 0.0],
            [-2.0, 1.0, 0.8906290911956787],
        ],
        "source": {"object_instance_id": "bottle/model_hash_0"},
    }

    summary = module.episode_summary(episode, threshold=0.3, hang_path_keys={"scene_usd_bottle_model_hash_0_0_6"})

    assert summary["runtime_path_key"] == "scene_usd_bottle_model_hash_0_0_6"
    assert summary["max_adjacent_z_delta"] == 0.8906290911956787
    assert summary["would_filter_stairs"] is True
    assert summary["is_known_hang"] is True


def test_episode_summary_does_not_filter_flat_stair_instruction_without_height_jump() -> None:
    module = load_audit_module()
    episode = {
        "episode_id": 1,
        "trajectory_id": "scene_usd_floor_model_hash_0_0",
        "instruction": {"instruction_text": "Navigate near the stairs."},
        "reference_path": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
    }

    summary = module.episode_summary(episode, threshold=0.3)

    assert summary["instruction_mentions_stair"] is True
    assert summary["max_adjacent_z_delta"] == 0.0
    assert summary["would_filter_stairs"] is False


def test_audit_counts_known_hangs_that_official_filter_would_remove() -> None:
    module = load_audit_module()
    episodes = [
        {
            "episode_id": 1,
            "trajectory_id": "scene_usd_table_model_a_0_0",
            "instruction": {"instruction_text": "Navigate to table."},
            "reference_path": [[0, 0, 0.0], [1, 0, 0.0], [1, 0, 0.8]],
        },
        {
            "episode_id": 2,
            "trajectory_id": "scene_usd_floor_model_b_0_0",
            "instruction": {"instruction_text": "Navigate to floor."},
            "reference_path": [[0, 0, 0.0], [1, 0, 0.0], [2, 0, 0.1]],
        },
    ]

    audit = module.audit_episodes(
        episodes,
        threshold=0.3,
        hang_path_keys={"scene_usd_table_model_a_0_0_1"},
    )

    assert audit["episode_count"] == 2
    assert audit["would_filter_stairs_count"] == 1
    assert audit["known_hang_count"] == 1
    assert audit["known_hang_would_filter_stairs_count"] == 1


def test_combined_audit_counts_unique_known_hangs_removed_by_filter() -> None:
    module = load_audit_module()
    datasets = [
        [
            {
                "episode_id": 1,
                "trajectory_id": "scene_usd_table_model_a_0_0",
                "instruction": {"instruction_text": "Navigate to table."},
                "reference_path": [[0, 0, 0.0], [1, 0, 0.0], [1, 0, 0.8]],
            },
        ],
        [
            {
                "episode_id": 2,
                "trajectory_id": "scene_usd_floor_model_b_0_0",
                "instruction": {"instruction_text": "Navigate to floor."},
                "reference_path": [[0, 0, 0.0], [1, 0, 0.0], [2, 0, 0.1]],
            },
        ],
    ]

    payload = module.combined_audit_payload(
        datasets,
        dataset_names=["a.json.gz", "b.json.gz"],
        threshold=0.3,
        hang_path_keys={"scene_usd_table_model_a_0_0_1", "scene_usd_floor_model_b_0_0_2"},
    )

    assert payload["known_hang_count"] == 2
    assert payload["known_hang_covered_count"] == 2
    assert payload["known_hang_would_filter_stairs_covered_count"] == 1
