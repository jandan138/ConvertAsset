import csv
import importlib.util
from pathlib import Path


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
