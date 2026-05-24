import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATCHDOG_SCRIPT = ROOT / "paper/shared/evidence/experiments/07_internnav_vln_downstream/runtime_watchdog.py"


def load_watchdog_module():
    spec = importlib.util.spec_from_file_location("internnav_vln_runtime_watchdog", WATCHDOG_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_triage_detects_stale_warmup_hang_without_actions(tmp_path: Path) -> None:
    module = load_watchdog_module()
    progress_log = tmp_path / "progress.log"
    progress_log.write_text(
        "\n".join(
            [
                "[2026-05-24 17:06:25,632][INFO] start eval dataset: split, total_path: 30",
                "[2026-05-24 18:31:05,859][INFO] [12/30][step_index:951] finish: "
                "[trajectory_id:scene_usd_plant_model_hash_0_0_11][duration:839.24 s]"
                "[step_count:951][fps:1.13][result:not_reach_goal]",
                "[2026-05-24 18:31:23,125][INFO] start sampling trajectory_id: "
                "scene_usd_bottle_model_hash_0_0_6",
            ]
        ),
        encoding="utf-8",
    )
    common_log = tmp_path / "common.log"
    common_log.write_text(
        "\n".join(
            [
                "[2026-05-24 18:31:23,125][INFO] env[0]: states switch to WARM UP.",
                "[2026-05-24 18:31:23,125][INFO] [TIME] Env Reset time: 17.69s",
                "[2026-05-24 18:31:23,125][INFO] [TIME] agent step time: 0.0s",
            ]
        ),
        encoding="utf-8",
    )
    result_path = tmp_path / "result.json"
    write_json(result_path, {"split": {"Count": 12, "SR": 0.0, "SPL": 0.0}})

    triage = module.triage_run(
        log_paths=[progress_log, common_log],
        result_path=result_path,
        now_epoch=1_779_619_500,
        stale_seconds=300,
        log_mtime_epoch=1_779_618_683,
    )

    assert triage["status"] == "runtime_hang"
    assert triage["reason"] == "warmup_reset_without_first_action_or_terminal_metric"
    assert triage["trajectory_id"] == "scene_usd_bottle_model_hash_0_0_6"
    assert triage["exclude_path_key"] == "scene_usd_bottle_model_hash_0_0_6"
    assert triage["last_finish_index"] == 12
    assert triage["result_count"] == 12
    assert triage["evidence"]["saw_warmup_after_latest_start"] is True
    assert triage["evidence"]["saw_env_reset_after_latest_start"] is True
    assert triage["evidence"]["saw_action_after_latest_start"] is False


def test_triage_keeps_episode_active_after_first_action(tmp_path: Path) -> None:
    module = load_watchdog_module()
    log_path = tmp_path / "combined.log"
    log_path.write_text(
        "\n".join(
            [
                "[2026-05-24 18:31:23,125][INFO] [12/30][step_index:951] finish: "
                "[trajectory_id:scene_usd_plant_model_hash_0_0_11][result:not_reach_goal]",
                "[2026-05-24 18:31:23,125][INFO] start sampling trajectory_id: "
                "scene_usd_bottle_model_hash_0_0_6",
                "[2026-05-24 18:31:23,125][INFO] env[0]: states switch to WARM UP.",
                "[2026-05-24 18:31:23,125][INFO] [TIME] Env Reset time: 17.69s",
                "[2026-05-24 18:32:01,000][INFO] now action: move_forward",
            ]
        ),
        encoding="utf-8",
    )
    result_path = tmp_path / "result.json"
    write_json(result_path, {"split": {"Count": 12}})

    triage = module.triage_run(
        log_paths=[log_path],
        result_path=result_path,
        now_epoch=1_779_619_500,
        stale_seconds=300,
        log_mtime_epoch=1_779_618_683,
    )

    assert triage["status"] == "active"
    assert triage["reason"] == "latest_episode_has_started_actions_or_steps"
    assert triage["exclude_path_key"] is None


def test_triage_reports_terminal_latest_episode(tmp_path: Path) -> None:
    module = load_watchdog_module()
    log_path = tmp_path / "progress.log"
    log_path.write_text(
        "\n".join(
            [
                "[2026-05-24 18:31:23,125][INFO] start sampling trajectory_id: "
                "scene_usd_bottle_model_hash_0_0_6",
                "[2026-05-24 18:40:00,000][INFO] [13/30][step_index:333] finish: "
                "[trajectory_id:scene_usd_bottle_model_hash_0_0_6][result:not_reach_goal]",
            ]
        ),
        encoding="utf-8",
    )
    result_path = tmp_path / "result.json"
    write_json(result_path, {"split": {"Count": 13}})

    triage = module.triage_run(
        log_paths=[log_path],
        result_path=result_path,
        now_epoch=1_779_619_500,
        stale_seconds=300,
        log_mtime_epoch=1_779_619_000,
    )

    assert triage["status"] == "terminal"
    assert triage["reason"] == "latest_episode_has_terminal_finish"
    assert triage["exclude_path_key"] is None


def test_triage_groups_duplicate_latest_start_events_across_logs(tmp_path: Path) -> None:
    module = load_watchdog_module()
    progress_log = tmp_path / "progress.log"
    progress_log.write_text(
        "\n".join(
            [
                "[2026-05-24 18:31:05,859][INFO] [12/30][step_index:951] finish: "
                "[trajectory_id:scene_usd_plant_model_hash_0_0_11][result:not_reach_goal]",
                "[2026-05-24 18:31:23,125][INFO] start sampling trajectory_id: "
                "scene_usd_bottle_model_hash_0_0_6",
            ]
        ),
        encoding="utf-8",
    )
    common_log = tmp_path / "common.log"
    common_log.write_text(
        "\n".join(
            [
                "[2026-05-24 18:31:23,125][INFO] env[0]: states switch to WARM UP.",
                "[2026-05-24 18:31:23,125][INFO] [TIME] Env Reset time: 17.69s",
            ]
        ),
        encoding="utf-8",
    )
    stdout_log = tmp_path / "stdout.log"
    stdout_log.write_text(
        "[2026-05-24 18:31:23,125][INFO] /path/progress_log_multi_util.py[line:107] -: "
        "start sampling trajectory_id: scene_usd_bottle_model_hash_0_0_6\n",
        encoding="utf-8",
    )
    result_path = tmp_path / "result.json"
    write_json(result_path, {"split": {"Count": 12}})

    triage = module.triage_run(
        log_paths=[progress_log, common_log, stdout_log],
        result_path=result_path,
        now_epoch=1_779_619_500,
        stale_seconds=300,
        log_mtime_epoch=1_779_618_683,
    )

    assert triage["status"] == "runtime_hang"
    assert triage["evidence"]["saw_warmup_after_latest_start"] is True
    assert triage["evidence"]["saw_env_reset_after_latest_start"] is True


def test_triage_detects_stale_reset_hang_when_warmup_precedes_start_by_millisecond(tmp_path: Path) -> None:
    module = load_watchdog_module()
    log_path = tmp_path / "stdout.log"
    log_path.write_text(
        "\n".join(
            [
                "[2026-05-24 15:17:36,449][INFO] [12/30][step_index:427] finish: "
                "[trajectory_id:scene_usd_clock_model_hash_0_0_2][result:not_reach_goal]",
                "[2026-05-24 15:17:55,210][INFO] env[0]: states switch to WARM UP.",
                "[2026-05-24 15:17:55,211][INFO] start sampling trajectory_id: "
                "scene_usd_washingmachine_model_hash_0_0_29",
                "[2026-05-24 15:17:55,211][INFO] [TIME] Env Reset time: 18.78s",
                "[2026-05-24 15:17:55,211][INFO] [TIME] agent step time: 0.0s",
            ]
        ),
        encoding="utf-8",
    )
    result_path = tmp_path / "result.json"
    write_json(result_path, {"split": {"Count": 12}})

    triage = module.triage_run(
        log_paths=[log_path],
        result_path=result_path,
        now_epoch=1_779_619_500,
        stale_seconds=300,
        log_mtime_epoch=1_779_618_683,
    )

    assert triage["status"] == "runtime_hang"
    assert triage["reason"] == "reset_without_first_action_or_terminal_metric"
    assert triage["trajectory_id"] == "scene_usd_washingmachine_model_hash_0_0_29"
    assert triage["exclude_path_key"] == "scene_usd_washingmachine_model_hash_0_0_29"
    assert triage["evidence"]["saw_warmup_after_latest_start"] is False
    assert triage["evidence"]["saw_env_reset_after_latest_start"] is True
    assert triage["evidence"]["saw_action_after_latest_start"] is False
