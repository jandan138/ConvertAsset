import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/verify_full_nomdl_apply.py"


def load_verifier_module():
    spec = importlib.util.spec_from_file_location("grscenes_full_nomdl_apply_verifier", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_apply_fixture(
    tmp_path: Path,
    *,
    dry_run: bool = False,
    job_count: int = 1,
) -> tuple[dict, dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = tmp_path / "scratch"
    source_scene = source_root / "scenes/scene_a"
    scratch_scene = scratch_root / "scenes/scene_a"
    source_scene.mkdir(parents=True)
    scratch_scene.mkdir(parents=True)

    jobs = []
    results = []
    top_outputs = []
    variants = ["start_result_raw.usd", "start_result_navigation.usd", "start_result_interaction.usd"]
    for name in variants[:job_count]:
        source_usd = source_scene / name
        scratch_input = scratch_scene / name
        top_output = scratch_scene / f"{Path(name).stem}_noMDL.usd"
        source_usd.write_text("#usda 1.0\n", encoding="utf-8")
        scratch_input.write_text("#usda 1.0\n", encoding="utf-8")
        top_output.write_text("#usda 1.0\n", encoding="utf-8")
        job = {
            "kind": "convert_no_mdl",
            "conversion_job_id": f"scene_a:{name}",
            "source_usd": str(source_usd),
            "scratch_input_usd": str(scratch_input),
            "expected_top_output_usd": str(top_output),
        }
        jobs.append(job)
        top_outputs.append(top_output)
        results.append(
            {
                "conversion_job_id": job["conversion_job_id"],
                "scratch_input_usd": str(scratch_input),
                "top_output_usd": str(top_output),
                "processor_done_count": len(results) + 1,
            }
        )

    plan = {
        "schema_version": 1,
        "status": "planned_full_grscenes_nomdl_scratch",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "conversion_jobs": jobs,
    }
    run_report = {
        "schema_version": 1,
        "status": "completed_full_grscenes_nomdl_multi_root_run",
        "dry_run": dry_run,
        "apply_ready": True,
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": {"planned_job_count": len(jobs)},
        "safety": {"remaining_apply_blockers": []},
        "jobs": [dict(job) for job in jobs],
        "results": results,
        "processor_done_count": len(jobs),
    }
    return plan, run_report, {"source_root": source_root, "scratch_root": scratch_root, "top_output": top_outputs[0]}


def test_completed_apply_report_passes_with_clean_source(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, paths = make_apply_fixture(tmp_path)

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is True
    assert report["summary"]["expected_top_output_count"] == 1
    assert report["summary"]["existing_top_output_count"] == 1
    assert report["summary"]["source_pollution_count"] == 0
    assert report["source_root"] == str(paths["source_root"])


def test_dry_run_report_is_not_completed_apply_evidence(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, _paths = make_apply_fixture(tmp_path, dry_run=True)

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "run_report_is_dry_run" in report["blockers"]


def test_planned_status_is_not_completed_apply_evidence(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, _paths = make_apply_fixture(tmp_path)
    run_report["status"] = "planned_full_grscenes_nomdl_multi_root_run"

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "run_report_status_not_completed" in report["blockers"]


def test_missing_top_output_is_reported(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, paths = make_apply_fixture(tmp_path)
    paths["top_output"].unlink()

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "top_outputs_missing" in report["blockers"]
    assert report["missing_top_outputs"] == [str(paths["top_output"])]


def test_empty_top_output_is_reported(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, paths = make_apply_fixture(tmp_path)
    paths["top_output"].write_text("", encoding="utf-8")

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "top_outputs_empty" in report["blockers"]
    assert report["empty_top_outputs"] == [str(paths["top_output"])]


def test_source_sidecar_pollution_is_reported(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, paths = make_apply_fixture(tmp_path)
    polluted = paths["source_root"] / "scenes/scene_a/start_result_raw_noMDL.usd"
    polluted.write_text("#usda 1.0\n", encoding="utf-8")

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "source_nomdl_sidecars_present" in report["blockers"]
    assert report["source_pollution"] == [str(polluted)]


def test_partial_limited_run_cannot_pass_full_plan(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, _paths = make_apply_fixture(tmp_path, job_count=2)
    run_report["jobs"] = run_report["jobs"][:1]
    run_report["results"] = run_report["results"][:1]
    run_report["summary"]["planned_job_count"] = 1

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "run_report_job_set_mismatch" in report["blockers"]
    assert "result_job_set_mismatch" in report["blockers"]


def test_missing_source_root_is_reported(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, paths = make_apply_fixture(tmp_path)
    for child in paths["source_root"].rglob("*"):
        if child.is_file() or child.is_symlink():
            child.unlink()
    for child in sorted(paths["source_root"].rglob("*"), reverse=True):
        if child.is_dir():
            child.rmdir()
    paths["source_root"].rmdir()

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "source_root_missing" in report["blockers"]


def test_job_input_paths_must_stay_inside_expected_roots(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, _paths = make_apply_fixture(tmp_path)
    outside = tmp_path / "outside.usd"
    outside.write_text("#usda 1.0\n", encoding="utf-8")
    for job in plan["conversion_jobs"]:
        job["source_usd"] = str(outside)
        job["scratch_input_usd"] = str(outside)
    for job in run_report["jobs"]:
        job["source_usd"] = str(outside)
        job["scratch_input_usd"] = str(outside)
    run_report["results"][0]["scratch_input_usd"] = str(outside)

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "source_usds_outside_source_root" in report["blockers"]
    assert "scratch_inputs_outside_scratch_root" in report["blockers"]
    assert "result_scratch_inputs_outside_scratch_root" in report["blockers"]


def test_result_scratch_input_must_match_expected_input(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, paths = make_apply_fixture(tmp_path)
    mismatched = paths["scratch_root"] / "scenes/scene_a/other.usd"
    mismatched.write_text("#usda 1.0\n", encoding="utf-8")
    run_report["results"][0]["scratch_input_usd"] = str(mismatched)

    report = module.build_verification_report(plan, run_report)

    assert report["passed"] is False
    assert "result_scratch_inputs_mismatch_expected" in report["blockers"]


def test_main_writes_report_and_returns_failure_for_blockers(tmp_path: Path) -> None:
    module = load_verifier_module()
    plan, run_report, _paths = make_apply_fixture(tmp_path, dry_run=True)
    plan_path = tmp_path / "plan.json"
    run_report_path = tmp_path / "run_report.json"
    out_path = tmp_path / "verify.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    run_report_path.write_text(json.dumps(run_report), encoding="utf-8")

    status = module.main(["--plan", str(plan_path), "--run-report", str(run_report_path), "--out", str(out_path)])

    assert status == 1
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert "run_report_is_dry_run" in written["blockers"]
