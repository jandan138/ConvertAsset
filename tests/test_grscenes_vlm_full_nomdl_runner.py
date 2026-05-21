import builtins
import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("grscenes_full_nomdl_runner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_plan(
    tmp_path: Path,
    *,
    scratch_inputs_exist: bool = True,
    create_expected_output: bool = False,
    create_timestamped_output: bool = False,
    duplicate_output: bool = False,
) -> tuple[dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = tmp_path / "scratch"
    source_scene = source_root / "scenes/GRScenes-100/home_scenes/scenes/home_scene_usd"
    scratch_scene = scratch_root / "scenes/GRScenes-100/home_scenes/scenes/home_scene_usd"
    source_scene.mkdir(parents=True)
    if scratch_inputs_exist:
        scratch_scene.mkdir(parents=True)

    jobs = []
    for name in ("start_result_raw.usd", "start_result_navigation.usd"):
        source_usd = source_scene / name
        scratch_input = scratch_scene / name
        expected_output = scratch_scene / f"{Path(name).stem}_noMDL.usd"
        source_usd.write_text("#usda 1.0\n", encoding="utf-8")
        if scratch_inputs_exist:
            scratch_input.write_text("#usda 1.0\n", encoding="utf-8")
        jobs.append(
            {
                "kind": "convert_no_mdl",
                "conversion_job_id": f"home_scenes:home_scene_usd:{name}",
                "source_scene_id": "home_scene_usd",
                "source_scene_split": "home_scenes",
                "source_usd_variant": name,
                "source_usd": str(source_usd),
                "scratch_input_usd": str(scratch_input),
                "expected_top_output_usd": str(expected_output),
                "argv": ["./scripts/isaac_python.sh", "./main.py", "no-mdl", "--only-new-usd", str(scratch_input)],
                "blocked_by": ["single_process_multi_root_runner_missing"],
                "safe_to_execute_now": False,
            }
        )

    if duplicate_output:
        jobs[1]["expected_top_output_usd"] = jobs[0]["expected_top_output_usd"]
    if create_expected_output:
        Path(jobs[0]["expected_top_output_usd"]).write_text("#usda 1.0\n", encoding="utf-8")
    if create_timestamped_output:
        timestamped = Path(jobs[1]["expected_top_output_usd"]).with_name("start_result_navigation_noMDL_20260521_000000.usd")
        timestamped.parent.mkdir(parents=True, exist_ok=True)
        timestamped.write_text("#usda 1.0\n", encoding="utf-8")

    plan = {
        "schema_version": 1,
        "status": "planned_full_grscenes_nomdl_scratch",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "safety": {
            "safe_to_apply": False,
            "apply_blockers": [
                "single_process_multi_root_runner_missing",
                "whole_scene_dependency_closure_not_scanned",
                "recursive_nomdl_output_collision_scan_missing",
                "scratch_cleanliness_not_verified",
            ],
        },
        "summary": {"conversion_job_count": len(jobs)},
        "conversion_jobs": jobs,
    }
    return plan, {"source_root": source_root, "scratch_root": scratch_root, "scratch_scene": scratch_scene}


def make_closure_report(
    plan: dict,
    *,
    scan_truncated: bool = False,
    scratch_input_missing_count: int = 0,
    missing_dependency_count: int = 0,
    outside_source_root_ref_count: int = 0,
    output_collision_count: int = 0,
    source_root: Path | None = None,
) -> dict:
    jobs = [
        {
            "conversion_job_id": job["conversion_job_id"],
            "scratch_input_usd": job["scratch_input_usd"],
            "expected_top_output_usd": job["expected_top_output_usd"],
        }
        for job in plan["conversion_jobs"]
    ]
    return {
        "schema_version": 1,
        "status": "planned_full_grscenes_dependency_closure",
        "source_root": str(source_root or plan["source_root"]),
        "scratch_root": plan["scratch_root"],
        "source_plan_status": plan["status"],
        "summary": {
            "conversion_job_count": len(jobs),
            "expected_top_output_count": len(jobs),
            "scan_truncated": scan_truncated,
            "unscanned_usd_queue_count": 1 if scan_truncated else 0,
            "missing_dependency_count": missing_dependency_count,
            "outside_source_root_ref_count": outside_source_root_ref_count,
            "output_collision_count": output_collision_count,
            "scratch_input_missing_count": scratch_input_missing_count,
        },
        "safety": {
            "remaining_apply_blockers": [
                "single_process_multi_root_runner_closure_report_not_consumed",
                "scratch_cleanliness_not_verified",
            ]
        },
        "jobs": jobs,
    }


def make_materialization_report(plan: dict, *, dry_run: bool = False, existing_nomdl_output_count: int = 0) -> dict:
    return {
        "schema_version": 1,
        "status": "full_grscenes_nomdl_scratch_materialization",
        "dry_run": dry_run,
        "source_root": plan["source_root"],
        "scratch_root": plan["scratch_root"],
        "source_plan_status": plan["status"],
        "summary": {
            "tree_action_count": 3,
            "repair_action_count": 2,
            "ignored_convert_action_count": len(plan["conversion_jobs"]),
            "dry_run": dry_run,
            "planned_tree_action_count": 0 if not dry_run else 3,
            "created_tree_count": 3 if not dry_run else 0,
            "existing_tree_count": 0,
            "planned_repair_action_count": 0 if not dry_run else 2,
            "repaired_scene_entry_count": 2 if not dry_run else 0,
            "existing_scene_entry_count": 0,
            "existing_nomdl_output_count": existing_nomdl_output_count,
            "top_level_scratch_input_exists_count": len(plan["conversion_jobs"]),
            "top_level_scratch_input_missing_count": 0,
        },
    }


def test_module_imports_without_pxr(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__
    for module_name in list(sys.modules):
        if module_name == "pxr" or module_name.startswith("pxr."):
            sys.modules.pop(module_name)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pxr" or name.startswith("pxr."):
            raise AssertionError("run_full_nomdl_multi_root.py must not import pxr during module import")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = load_runner_module()

    assert hasattr(module, "build_multi_root_run_report")


def test_build_report_satisfies_runner_blocker_but_keeps_remaining_blockers(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, paths = make_plan(tmp_path)

    report = module.build_multi_root_run_report(plan)

    assert report["status"] == "planned_full_grscenes_nomdl_multi_root_run"
    assert report["dry_run"] is True
    assert report["apply_ready"] is False
    assert report["runner_strategy"]["process_model"] == "single_python_process_one_processor_instance"
    assert report["summary"]["planned_job_count"] == 2
    assert report["summary"]["scratch_input_missing_count"] == 0
    assert report["summary"]["existing_expected_top_output_count"] == 0
    assert report["safety"]["satisfied_apply_blockers"] == ["single_process_multi_root_runner_missing"]
    assert "single_process_multi_root_runner_missing" not in report["safety"]["remaining_apply_blockers"]
    assert "whole_scene_dependency_closure_not_scanned" in report["safety"]["remaining_apply_blockers"]
    assert all(job["source_plan_blocked_by"] == ["single_process_multi_root_runner_missing"] for job in report["jobs"])
    assert all("single_process_multi_root_runner_missing" not in job["blocked_by"] for job in report["jobs"])
    assert all("whole_scene_dependency_closure_not_scanned" in job["blocked_by"] for job in report["jobs"])
    assert all(Path(job["scratch_input_usd"]).resolve().is_relative_to(paths["scratch_root"].resolve()) for job in report["jobs"])


def test_build_report_consumes_valid_closure_report_and_clears_scan_blockers(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)

    report = module.build_multi_root_run_report(plan, closure_report=closure)

    assert report["apply_ready"] is False
    assert "single_process_multi_root_runner_missing" in report["safety"]["satisfied_apply_blockers"]
    assert "single_process_multi_root_runner_closure_report_not_consumed" in report["safety"]["satisfied_apply_blockers"]
    assert "whole_scene_dependency_closure_not_scanned" not in report["safety"]["remaining_apply_blockers"]
    assert "recursive_nomdl_output_collision_scan_missing" not in report["safety"]["remaining_apply_blockers"]
    assert "single_process_multi_root_runner_closure_report_not_consumed" not in report["safety"]["remaining_apply_blockers"]
    assert "scratch_cleanliness_not_verified" in report["safety"]["remaining_apply_blockers"]


def test_build_report_consumes_materialization_report_and_can_be_apply_ready(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    materialization = make_materialization_report(plan)

    report = module.build_multi_root_run_report(
        plan,
        closure_report=closure,
        materialization_report=materialization,
    )

    assert report["apply_ready"] is True
    assert "scratch_cleanliness_not_verified" in report["safety"]["satisfied_apply_blockers"]
    assert report["safety"]["remaining_apply_blockers"] == []


def test_build_report_does_not_clear_cleanliness_from_dry_run_materialization_report(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    materialization = make_materialization_report(plan, dry_run=True)

    report = module.build_multi_root_run_report(
        plan,
        closure_report=closure,
        materialization_report=materialization,
    )

    assert report["apply_ready"] is False
    assert "scratch_cleanliness_not_verified" in report["safety"]["remaining_apply_blockers"]


def test_build_report_rejects_closure_report_root_mismatch(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan, source_root=tmp_path / "other-source")

    with pytest.raises(ValueError, match="closure report source_root must match plan"):
        module.build_multi_root_run_report(plan, closure_report=closure)


def test_build_report_rejects_closure_report_missing_required_summary_fields(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    del closure["summary"]["missing_dependency_count"]

    with pytest.raises(ValueError, match="closure report summary missing required fields"):
        module.build_multi_root_run_report(plan, closure_report=closure)


def test_build_report_rejects_closure_report_null_required_summary_fields(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    closure["summary"]["missing_dependency_count"] = None

    with pytest.raises(ValueError, match="closure report summary missing_dependency_count must be a non-negative integer"):
        module.build_multi_root_run_report(plan, closure_report=closure)


def test_build_report_rejects_materialization_report_null_required_summary_fields(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    materialization = make_materialization_report(plan)
    materialization["summary"]["existing_nomdl_output_count"] = None

    with pytest.raises(
        ValueError,
        match="materialization report summary existing_nomdl_output_count must be a non-negative integer",
    ):
        module.build_multi_root_run_report(
            plan,
            closure_report=closure,
            materialization_report=materialization,
        )


def test_build_report_keeps_closure_blockers_when_closure_scan_is_not_clean(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(
        plan,
        scan_truncated=True,
        scratch_input_missing_count=1,
        missing_dependency_count=2,
        outside_source_root_ref_count=3,
        output_collision_count=4,
    )

    report = module.build_multi_root_run_report(plan, closure_report=closure)

    assert "whole_scene_dependency_closure_not_scanned" in report["safety"]["remaining_apply_blockers"]
    assert "recursive_nomdl_output_collision_scan_missing" in report["safety"]["remaining_apply_blockers"]
    assert "dependency_closure_scan_truncated" in report["safety"]["remaining_apply_blockers"]
    assert "missing_dependencies_present" in report["safety"]["remaining_apply_blockers"]
    assert "outside_source_root_refs_present" in report["safety"]["remaining_apply_blockers"]
    assert "recursive_nomdl_output_collisions_present" in report["safety"]["remaining_apply_blockers"]
    assert "scratch_inputs_missing" in report["safety"]["remaining_apply_blockers"]


def test_apply_requires_closure_report_before_importing_nomdl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    plan["safety"]["apply_blockers"] = ["single_process_multi_root_runner_missing"]
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("convert_asset.no_mdl") or name == "pxr" or name.startswith("pxr."):
            raise AssertionError("apply without closure report must not import no_mdl or pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ValueError, match="closure report is required"):
        module.run_multi_root_conversion(plan)


def test_apply_adds_project_root_to_sys_path_before_importing_nomdl(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    materialization = make_materialization_report(plan)
    monkeypatch.setattr(sys, "path", [path for path in sys.path if path != str(ROOT)])
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("convert_asset.no_mdl"):
            assert str(ROOT) in sys.path
            raise RuntimeError("stop after project root path check")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(RuntimeError, match="stop after project root path check"):
        module.run_multi_root_conversion(
            plan,
            closure_report=closure,
            materialization_report=materialization,
        )


def test_apply_report_status_and_notes_reflect_completed_conversion(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    closure = make_closure_report(plan)
    materialization = make_materialization_report(plan)
    calls = []

    class FakeProcessor:
        def __init__(self):
            self.done = {}

        def process(self, path):
            self.done[path] = path
            calls.append(path)
            return str(Path(path).with_name(f"{Path(path).stem}_noMDL.usd"))

    fake_processor_module = type("FakeProcessorModule", (), {})()
    monkeypatch.setattr(module, "_ensure_project_root_on_sys_path", lambda: None)
    monkeypatch.setitem(sys.modules, "convert_asset.no_mdl", type("FakeNoMdlModule", (), {"processor": fake_processor_module})())
    monkeypatch.setitem(sys.modules, "convert_asset.no_mdl.processor", type("FakeProcessorModule", (), {"Processor": FakeProcessor})())

    report = module.run_multi_root_conversion(
        plan,
        closure_report=closure,
        materialization_report=materialization,
    )

    assert report["status"] == "completed_full_grscenes_nomdl_multi_root_run"
    assert report["dry_run"] is False
    assert "converted_at_utc" in report
    assert report["results"]
    assert "This report records a completed no-MDL apply run." in report["notes"]
    assert "This report does not convert assets." not in report["notes"]
    assert len(calls) == len(plan["conversion_jobs"])


def test_build_report_imports_no_nomdl_or_pxr(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("convert_asset.no_mdl") or name == "pxr" or name.startswith("pxr."):
            raise AssertionError("dry-run report must not import no_mdl or pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    report = module.build_multi_root_run_report(plan)

    assert report["dry_run"] is True
    assert report["runner_strategy"]["imports_no_mdl_on_dry_run"] is False


def test_report_marks_missing_scratch_inputs_on_each_job(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path, scratch_inputs_exist=False)

    report = module.build_multi_root_run_report(plan)

    assert report["summary"]["scratch_input_missing_count"] == 2
    assert "scratch_inputs_missing" in report["safety"]["remaining_apply_blockers"]
    assert all("scratch_inputs_missing" in job["blocked_by"] for job in report["jobs"])


def test_report_detects_existing_and_timestamped_top_outputs(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path, create_expected_output=True, create_timestamped_output=True)

    report = module.build_multi_root_run_report(plan)

    assert report["summary"]["existing_expected_top_output_count"] == 1
    assert report["summary"]["existing_timestamped_top_output_count"] == 1
    assert report["summary"]["top_level_output_collision_count"] == 2
    assert "top_level_output_collisions_present" in report["safety"]["remaining_apply_blockers"]
    assert "top_level_output_collisions_present" in report["jobs"][0]["blocked_by"]
    assert "top_level_output_collisions_present" in report["jobs"][1]["blocked_by"]


def test_report_detects_duplicate_planned_top_outputs(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path, duplicate_output=True)

    report = module.build_multi_root_run_report(plan)

    assert report["summary"]["duplicate_expected_top_output_count"] == 1
    assert "duplicate_top_level_outputs_planned" in report["safety"]["remaining_apply_blockers"]
    assert all("duplicate_top_level_outputs_planned" in job["blocked_by"] for job in report["jobs"])


def test_report_rejects_job_paths_outside_declared_roots(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    plan["conversion_jobs"][0]["scratch_input_usd"] = str(tmp_path / "outside.usd")

    with pytest.raises(ValueError, match="scratch_input_usd must be inside scratch_root"):
        module.build_multi_root_run_report(plan)


def test_output_path_guard_rejects_source_and_scratch_outputs(tmp_path: Path) -> None:
    module = load_runner_module()
    plan, paths = make_plan(tmp_path)

    with pytest.raises(ValueError, match="output path must not be inside source_root"):
        module.validate_output_path(paths["source_root"] / "report.json", plan=plan)

    with pytest.raises(ValueError, match="output path must not be inside scratch_root"):
        module.validate_output_path(paths["scratch_root"] / "report.json", plan=plan)

    allowed = module.validate_output_path(tmp_path / "reports/report.json", plan=plan)

    assert allowed == (tmp_path / "reports/report.json").resolve(strict=False)


def test_main_rejects_unsafe_output_before_apply(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = load_runner_module()
    plan, paths = make_plan(tmp_path)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    def forbidden_apply(*args, **kwargs):
        raise AssertionError("apply path must not run before output path validation")

    monkeypatch.setattr(module, "run_multi_root_conversion", forbidden_apply)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_full_nomdl_multi_root.py",
            "--plan",
            str(plan_path),
            "--out",
            str(paths["source_root"] / "report.json"),
            "--apply",
        ],
    )

    with pytest.raises(ValueError, match="output path must not be inside source_root"):
        module.main()


def test_apply_refuses_with_blockers_before_importing_nomdl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = load_runner_module()
    plan, _paths = make_plan(tmp_path)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("convert_asset.no_mdl") or name == "pxr" or name.startswith("pxr."):
            raise AssertionError("blocked apply must not import no_mdl or pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    with pytest.raises(ValueError, match="multi-root no-MDL apply is not ready"):
        module.run_multi_root_conversion(plan)
