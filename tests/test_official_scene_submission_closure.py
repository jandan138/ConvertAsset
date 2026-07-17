import csv
import importlib.util
import json
import sys
import types
from argparse import Namespace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/10_official_scene_submission_closure/"
    "build_submission_closure_package.py"
)
RUNNER = (
    ROOT
    / "paper/shared/evidence/experiments/10_official_scene_submission_closure/"
    "run_official_scene_performance.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("official_scene_submission_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location("official_scene_performance_runner", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_video_summary_marks_existing_repo_package_as_complete() -> None:
    module = load_module()
    package_index = {
        "claim_boundary": "repo_resident_selected_qualitative_media_only_full_metric_runs_remain_authoritative",
        "file_counts_excluding_package_index": {
            "mp4": 24,
            "png": 76,
            "json": 12,
            "total_files": 113,
        },
        "groups": [
            {
                "group_id": "kujiale0031",
                "video_count": 12,
                "qa_pass_count": 12,
                "all_videos_pass_basic_nonblank_check": True,
            },
            {
                "group_id": "kujiale0036_0066",
                "video_count": 12,
                "qa_pass_count": 12,
                "all_videos_pass_basic_nonblank_check": True,
            },
        ],
        "size_bytes_excluding_package_index": 124258279,
    }

    summary = module.build_video_evidence_summary(package_index)

    assert summary["video_package_complete"] is True
    assert summary["mp4_count"] == 24
    assert summary["png_count"] == 76
    assert summary["qa_pass_count"] == 24
    assert summary["group_count"] == 2
    assert summary["claim_boundary"] == "selected_qualitative_only_full_metric_runs_authoritative"


def test_scene_inventory_uses_official_scenes_and_marks_nvidia_unavailable() -> None:
    module = load_module()
    per_scene = {
        "scene_order": ["kujiale_0031", "kujiale_0036", "kujiale_0066"],
        "per_scene": {
            "kujiale_0031": {"episode_count": 33},
            "kujiale_0036": {"episode_count": 33},
            "kujiale_0066": {"episode_count": 33},
        },
    }
    static_gate = {
        "results": [
            {"scene_usd": "/tmp/scene_data_nomdl/kujiale_0036/kujiale_0036.usda", "static_gate_pass": True},
            {"scene_usd": "/tmp/scene_data_nomdl/kujiale_0066/kujiale_0066.usda", "static_gate_pass": True},
        ]
    }

    inventory = module.build_scene_inventory(
        per_scene_summary=per_scene,
        static_gate_0036_0066=static_gate,
        path_overrides={
            "kujiale_0031": {
                "original_mdl": "/tmp/original/kujiale_0031/kujiale_0031.usda",
                "convertasset_nomdl": "/tmp/nomdl/kujiale_0031/kujiale_0031.usda",
            }
        },
    )

    assert [row["scene_id"] for row in inventory] == ["kujiale_0031", "kujiale_0036", "kujiale_0066"]
    assert inventory[0]["episode_count"] == 33
    assert inventory[0]["conditions"]["original_mdl"]["status"] == "planned"
    assert inventory[0]["conditions"]["convertasset_nomdl"]["status"] == "planned"
    assert inventory[1]["conditions"]["convertasset_nomdl"]["static_gate_pass"] is True
    assert inventory[2]["conditions"]["nvidia_baseline"]["status"] == "not_available"
    assert inventory[2]["conditions"]["nvidia_baseline"]["reason"] == "no_official_scene_nvidia_conversion_yet"


def test_performance_summary_counts_failures_and_ci() -> None:
    module = load_module()
    rows = [
        {
            "scene_id": "kujiale_0031",
            "condition": "original_mdl",
            "run_id": "1",
            "status": "success",
            "open_ready_s": "2.0",
            "warmup_s": "10.0",
            "total_ready_s": "12.0",
            "gpu_memory_mb": "5000",
            "warmup_updates": "30",
        },
        {
            "scene_id": "kujiale_0031",
            "condition": "original_mdl",
            "run_id": "2",
            "status": "success",
            "open_ready_s": "4.0",
            "warmup_s": "15.0",
            "total_ready_s": "19.0",
            "gpu_memory_mb": "5100",
            "warmup_updates": "30",
        },
        {
            "scene_id": "kujiale_0031",
            "condition": "convertasset_nomdl",
            "run_id": "1",
            "status": "failed",
            "open_ready_s": "",
            "warmup_s": "",
            "total_ready_s": "",
            "gpu_memory_mb": "",
            "warmup_updates": "30",
        },
    ]

    summary = module.summarize_performance_rows(rows, ci_rounds=200)
    by_condition = {(row["scene_id"], row["condition"]): row for row in summary["rows"]}

    original = by_condition[("kujiale_0031", "original_mdl")]
    assert original["success_count"] == 2
    assert original["failure_count"] == 0
    assert original["open_ready_s_mean"] == 3.0
    assert original["warmup_fps_mean"] == 2.5
    assert original["open_ready_s_ci95_low"] <= 3.0 <= original["open_ready_s_ci95_high"]

    nomdl = by_condition[("kujiale_0031", "convertasset_nomdl")]
    assert nomdl["success_count"] == 0
    assert nomdl["failure_count"] == 1
    assert nomdl["open_ready_s_mean"] is None
    assert summary["performance_complete"] is False


def test_performance_summary_includes_condition_aggregates() -> None:
    module = load_module()
    rows = []
    for scene_id, base in (("kujiale_0031", 1.0), ("kujiale_0036", 2.0)):
        for condition in ("original_mdl", "convertasset_nomdl"):
            for run_id in range(1, 4):
                rows.append(
                    {
                        "scene_id": scene_id,
                        "condition": condition,
                        "run_id": str(run_id),
                        "status": "success",
                        "open_ready_s": str(base + run_id),
                        "warmup_s": "10.0",
                        "total_ready_s": str(base + run_id + 10),
                        "gpu_memory_mb": "4000",
                        "warmup_updates": "30",
                    }
                )

    summary = module.summarize_performance_rows(rows, planned_scene_count=2, ci_rounds=200)
    aggregate = {row["condition"]: row for row in summary["condition_summary_rows"]}

    assert summary["performance_complete"] is True
    assert aggregate["original_mdl"]["scene_count"] == 2
    assert aggregate["original_mdl"]["success_count"] == 6
    assert aggregate["original_mdl"]["failure_count"] == 0
    assert aggregate["convertasset_nomdl"]["complete_for_condition"] is True


def test_completion_gates_require_performance_video_and_claim_audit() -> None:
    module = load_module()
    gates = module.build_completion_gates(
        scene_inventory=[
            {
                "scene_id": "kujiale_0031",
                "conditions": {
                    "original_mdl": {"status": "planned"},
                    "convertasset_nomdl": {"status": "planned"},
                    "nvidia_baseline": {"status": "not_available"},
                },
            },
            {
                "scene_id": "kujiale_0036",
                "conditions": {
                    "original_mdl": {"status": "planned"},
                    "convertasset_nomdl": {"status": "planned"},
                    "nvidia_baseline": {"status": "not_available"},
                },
            },
            {
                "scene_id": "kujiale_0066",
                "conditions": {
                    "original_mdl": {"status": "planned"},
                    "convertasset_nomdl": {"status": "planned"},
                    "nvidia_baseline": {"status": "not_available"},
                },
            },
        ],
        performance_summary={"performance_complete": False, "planned_scene_count": 3},
        video_summary={"video_package_complete": True},
        claim_audit={"claim_audit_complete": False},
    )

    assert gates["official_scene_scope"] == "ready"
    assert gates["selected_video_package"] == "ready"
    assert gates["multi_run_performance_statistics"] == "missing"
    assert gates["final_claim_citation_audit"] == "missing"
    assert gates["submission_closure_complete"] is False


def test_write_status_table(tmp_path: Path) -> None:
    module = load_module()
    rows = [
        {
            "requirement": "selected_video_package",
            "status": "ready",
            "evidence": "package_index.json",
            "claim_boundary": "qualitative only",
        }
    ]
    csv_path = tmp_path / "status.csv"
    tex_path = tmp_path / "status.tex"

    module.write_status_table(csv_path, tex_path, rows)

    assert b"\r" not in csv_path.read_bytes()
    csv_text = csv_path.read_text(encoding="utf-8")
    loaded = list(csv.DictReader(csv_text.splitlines()))
    assert loaded[0]["requirement"] == "selected_video_package"
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\label{tab:official_scene_submission_closure_status}" in tex
    assert "official-scene submission closure" in tex.lower()


def test_write_performance_summary_table_includes_failure_counts(tmp_path: Path) -> None:
    module = load_module()
    performance_summary = {
        "condition_summary_rows": [
            {
                "condition": "original_mdl",
                "scene_count": 3,
                "success_count": 9,
                "failure_count": 0,
                "total_ready_s_mean": 13.9471,
                "total_ready_s_ci95_low": 10.0,
                "total_ready_s_ci95_high": 18.0,
                "warmup_fps_mean": 2.3647,
                "warmup_fps_ci95_low": 1.6,
                "warmup_fps_ci95_high": 2.9,
                "gpu_memory_mb_mean": 3807.0,
                "gpu_memory_mb_ci95_low": 3700.0,
                "gpu_memory_mb_ci95_high": 3900.0,
            },
            {
                "condition": "convertasset_nomdl",
                "scene_count": 3,
                "success_count": 9,
                "failure_count": 0,
                "total_ready_s_mean": 14.1234,
                "total_ready_s_ci95_low": 11.0,
                "total_ready_s_ci95_high": 19.0,
                "warmup_fps_mean": 2.4242,
                "warmup_fps_ci95_low": 1.7,
                "warmup_fps_ci95_high": 3.0,
                "gpu_memory_mb_mean": 3829.0,
                "gpu_memory_mb_ci95_low": 3650.0,
                "gpu_memory_mb_ci95_high": 4000.0,
            }
        ],
        "rows": [],
    }
    csv_path = tmp_path / "perf.csv"
    tex_path = tmp_path / "perf.tex"

    module.write_performance_summary_table(csv_path, tex_path, performance_summary)

    assert b"\r" not in csv_path.read_bytes()
    loaded = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    assert loaded[0]["row_type"] == "aggregate"
    assert loaded[0]["failure_count"] == "0"
    tex = tex_path.read_text(encoding="utf-8")
    assert "\\label{tab:official_scene_performance_summary}" in tex
    assert "Metric & Original MDL & noMDL" in tex
    assert "Scenes" in tex
    assert "Scenes & 3 & 3" in tex
    assert "Successful runs & 9; 0 fail & 9; 0 fail" in tex
    assert "kujiale\\_0031" not in tex
    assert "original\\_mdl" not in tex
    assert "convertasset\\_nomdl" not in tex


def test_performance_summary_caption_stays_compact_for_main_pdf(tmp_path: Path) -> None:
    module = load_module()
    performance_summary = {
        "condition_summary_rows": [
            {
                "condition": "original_mdl",
                "scene_count": 3,
                "success_count": 9,
                "failure_count": 0,
                "total_ready_s_mean": 13.9471,
                "total_ready_s_ci95_low": 10.0,
                "total_ready_s_ci95_high": 18.0,
                "warmup_fps_mean": 2.3647,
                "warmup_fps_ci95_low": 1.6,
                "warmup_fps_ci95_high": 2.9,
                "gpu_memory_mb_mean": 3807.0,
                "gpu_memory_mb_ci95_low": 3700.0,
                "gpu_memory_mb_ci95_high": 3900.0,
            },
            {
                "condition": "convertasset_nomdl",
                "scene_count": 3,
                "success_count": 9,
                "failure_count": 0,
                "total_ready_s_mean": 14.1234,
                "total_ready_s_ci95_low": 11.0,
                "total_ready_s_ci95_high": 19.0,
                "warmup_fps_mean": 2.4242,
                "warmup_fps_ci95_low": 1.7,
                "warmup_fps_ci95_high": 3.0,
                "gpu_memory_mb_mean": 3829.0,
                "gpu_memory_mb_ci95_low": 3650.0,
                "gpu_memory_mb_ci95_high": 4000.0,
            },
        ],
        "rows": [],
    }
    tex_path = tmp_path / "perf.tex"

    module.write_performance_summary_table(tmp_path / "perf.csv", tex_path, performance_summary)

    tex = tex_path.read_text(encoding="utf-8")
    caption = tex.split("\\caption{", 1)[1].split("}", 1)[0]
    assert len(caption.split()) <= 30
    assert "NVIDIA official-scene row is omitted" in caption
    assert "per-scene rows remain" not in caption


def test_claim_audit_decision_marks_audit_complete() -> None:
    module = load_module()
    required_ids = [
        "official_scene_scope",
        "performance_scope",
        "video_scope",
        "nvidia_scope",
        "material_effect_scope",
        "citation_provenance",
    ]
    audit = module.build_claim_audit_checklist(
        claim_audit_decision={
            "claim_audit_complete": True,
            "checks": [{"id": check_id, "status": "passed"} for check_id in required_ids],
        }
    )

    assert audit["claim_audit_complete"] is True
    assert {check["status"] for check in audit["checks"]} == {"passed"}


def test_claim_audit_decision_requires_all_required_checks() -> None:
    module = load_module()
    audit = module.build_claim_audit_checklist(
        claim_audit_decision={
            "claim_audit_complete": True,
            "checks": [
                {"id": "official_scene_scope", "status": "passed"},
                {"id": "performance_scope", "status": "passed"},
            ],
        }
    )

    assert audit["claim_audit_complete"] is False
    assert audit["claim_boundary"] == "audit_decision_present_but_not_complete"


def test_runner_builds_required_condition_tasks_and_skips_unavailable_nvidia() -> None:
    runner = load_runner()
    plan = {
        "scene_inventory": [
            {
                "scene_id": "kujiale_0031",
                "conditions": {
                    "original_mdl": {"status": "planned", "stage_path": "/tmp/original.usda"},
                    "convertasset_nomdl": {"status": "planned", "stage_path": "/tmp/nomdl.usda"},
                    "nvidia_baseline": {"status": "not_available"},
                },
            }
        ]
    }

    tasks = runner.build_batch_tasks(plan, runs=2, include_optional=False)

    assert [(task["condition"], task["run_id"]) for task in tasks] == [
        ("original_mdl", 1),
        ("original_mdl", 2),
        ("convertasset_nomdl", 1),
        ("convertasset_nomdl", 2),
    ]
    assert all(task["scene_id"] == "kujiale_0031" for task in tasks)


def test_runner_writes_lf_csv(tmp_path: Path) -> None:
    runner = load_runner()
    output_csv = tmp_path / "runs.csv"

    runner.write_result_rows(
        output_csv,
        [
            {
                "scene_id": "kujiale_0031",
                "condition": "original_mdl",
                "run_id": 1,
                "status": "success",
            }
        ],
    )

    assert b"\r" not in output_csv.read_bytes()
    loaded = list(csv.DictReader(output_csv.read_text(encoding="utf-8").splitlines()))
    assert loaded[0]["status"] == "success"


def test_runner_prints_result_json_before_simulation_close_can_exit(monkeypatch, capsys) -> None:
    runner = load_runner()

    class FakeSimulationApp:
        def __init__(self, config):
            self.config = config

        def update(self):
            return None

        def close(self):
            raise SystemExit(0)

    class FakeContext:
        def open_stage(self, stage):
            self.stage = stage

        def is_standby(self):
            return False

        def is_stage_loading(self):
            return False

        def close_stage(self):
            return None

    app_module = types.ModuleType("omni.kit.app")
    app_module.get_app = lambda: FakeSimulationApp({})
    usd_module = types.ModuleType("omni.usd")
    usd_module.get_context = lambda: FakeContext()
    kit_module = types.ModuleType("omni.kit")
    kit_module.app = app_module
    omni_module = types.ModuleType("omni")
    omni_module.kit = kit_module
    omni_module.usd = usd_module
    isaacsim_module = types.ModuleType("isaacsim")
    isaacsim_module.SimulationApp = FakeSimulationApp

    monkeypatch.setitem(sys.modules, "isaacsim", isaacsim_module)
    monkeypatch.setitem(sys.modules, "omni", omni_module)
    monkeypatch.setitem(sys.modules, "omni.kit", kit_module)
    monkeypatch.setitem(sys.modules, "omni.kit.app", app_module)
    monkeypatch.setitem(sys.modules, "omni.usd", usd_module)
    monkeypatch.setattr(runner, "_gpu_memory_mb", lambda: 123)

    args = Namespace(
        scene_id="kujiale_0031",
        condition="original_mdl",
        run_id=1,
        stage="/tmp/scene.usda",
        warmup_updates=1,
    )

    with pytest.raises(SystemExit):
        runner._run_once(args)

    captured = capsys.readouterr()
    result_line = next(line for line in captured.out.splitlines() if line.startswith(runner.RESULT_PREFIX))
    result = json.loads(result_line[len(runner.RESULT_PREFIX) :])
    assert result["status"] == "success"
    assert result["scene_id"] == "kujiale_0031"
