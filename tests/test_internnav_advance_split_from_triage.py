import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADVANCE_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/advance_split_from_triage.py"


def load_advance_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_advance_split", ADVANCE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def previous_manifest_payload(work_root: Path) -> dict:
    return {
        "source": {
            "grscenes_root": "/source/grscenes",
            "nomdl_work_root": "/source/grscenes_nomdl",
        },
        "selection": {
            "ready_only": True,
            "selection_strategy": "round_robin_scenes",
            "min_scenes": 5,
            "requested_excluded_path_keys": ["scene_usd_clock_model_hash_0_0_2"],
        },
        "work_root": str(work_root),
        "dataset": {
            "split": "acl_main_pilot30_v10",
            "episode_count": 30,
        },
    }


def test_advance_from_runtime_hang_triage_derives_v11_paths_and_merges_excludes(tmp_path: Path) -> None:
    module = load_advance_module()
    previous_manifest = tmp_path / "acl_main_pilot30_v10_prep_manifest.json"
    previous_work_root = tmp_path / "internnav_vln_downstream_work_20260523_pilot30_v10"
    write_json(previous_manifest, previous_manifest_payload(previous_work_root))
    triage_path = tmp_path / "acl_main_pilot30_v10_runtime_hang_triage.json"
    write_json(
        triage_path,
        {
            "status": "runtime_hang",
            "reason": "warmup_reset_without_first_action_or_terminal_metric",
            "exclude_path_key": "scene_usd_bottle_model_hash_0_0_6",
            "trajectory_id": "scene_usd_bottle_model_hash_0_0_6",
        },
    )
    calls = []

    def fake_prepare_minipair(**kwargs):
        calls.append(kwargs)
        return {
            "selection": {
                "requested_excluded_path_keys": kwargs["excluded_path_keys"],
                "unmatched_excluded_path_keys": [],
            },
            "dataset": {
                "split": kwargs["split_name"],
                "episode_count": kwargs["max_episodes"],
            },
            "work_root": str(kwargs["work_root"]),
        }

    manifest = module.advance_from_triage(
        previous_manifest_path=previous_manifest,
        triage_path=triage_path,
        prepare_func=fake_prepare_minipair,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call["source_root"] == Path("/source/grscenes")
    assert call["nomdl_root"] == Path("/source/grscenes_nomdl")
    assert call["work_root"] == tmp_path / "internnav_vln_downstream_work_20260523_pilot30_v11"
    assert call["repo_manifest_path"] == tmp_path / "acl_main_pilot30_v11_prep_manifest.json"
    assert call["max_episodes"] == 30
    assert call["split_name"] == "acl_main_pilot30_v11"
    assert call["ready_only"] is True
    assert call["min_scenes"] == 5
    assert call["selection_strategy"] == "round_robin_scenes"
    assert call["excluded_path_keys"] == [
        "scene_usd_clock_model_hash_0_0_2",
        "scene_usd_bottle_model_hash_0_0_6",
    ]
    assert call["exclusion_reason"] == "warmup_reset_without_first_action_or_terminal_metric"
    assert call["supersedes_manifest_path"] == previous_manifest
    assert manifest["selection"]["runtime_triage_source"]["path"] == str(triage_path.resolve())
    assert manifest["selection"]["runtime_triage_source"]["exclude_path_key"] == "scene_usd_bottle_model_hash_0_0_6"
    persisted = json.loads((tmp_path / "acl_main_pilot30_v11_prep_manifest.json").read_text(encoding="utf-8"))
    assert persisted["selection"]["runtime_triage_source"]["status"] == "runtime_hang"


def test_advance_from_triage_does_not_duplicate_existing_exclusion(tmp_path: Path) -> None:
    module = load_advance_module()
    previous_manifest = tmp_path / "acl_main_pilot30_v10_prep_manifest.json"
    previous = previous_manifest_payload(tmp_path / "work_v10")
    previous["selection"]["requested_excluded_path_keys"].append("scene_usd_bottle_model_hash_0_0_6")
    write_json(previous_manifest, previous)
    triage_path = tmp_path / "triage.json"
    write_json(
        triage_path,
        {
            "status": "runtime_hang",
            "reason": "warmup_reset_without_first_action_or_terminal_metric",
            "exclude_path_key": "scene_usd_bottle_model_hash_0_0_6",
        },
    )

    def fake_prepare_minipair(**kwargs):
        return {
            "selection": {"requested_excluded_path_keys": kwargs["excluded_path_keys"]},
            "dataset": {"split": kwargs["split_name"], "episode_count": kwargs["max_episodes"]},
        }

    manifest = module.advance_from_triage(
        previous_manifest_path=previous_manifest,
        triage_path=triage_path,
        prepare_func=fake_prepare_minipair,
    )

    assert manifest["selection"]["requested_excluded_path_keys"].count("scene_usd_bottle_model_hash_0_0_6") == 1


def test_advance_from_triage_rejects_non_runtime_hang_status(tmp_path: Path) -> None:
    module = load_advance_module()
    previous_manifest = tmp_path / "acl_main_pilot30_v10_prep_manifest.json"
    write_json(previous_manifest, previous_manifest_payload(tmp_path / "work_v10"))
    triage_path = tmp_path / "triage.json"
    write_json(
        triage_path,
        {
            "status": "active",
            "reason": "latest_episode_has_started_actions_or_steps",
            "exclude_path_key": None,
        },
    )

    try:
        module.advance_from_triage(
            previous_manifest_path=previous_manifest,
            triage_path=triage_path,
            prepare_func=lambda **kwargs: {},
        )
    except ValueError as exc:
        assert "status=runtime_hang" in str(exc)
    else:
        raise AssertionError("expected ValueError")
