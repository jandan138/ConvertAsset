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
