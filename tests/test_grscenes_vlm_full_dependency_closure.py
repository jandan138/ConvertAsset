import builtins
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_dependency_closure.py"


def load_closure_module():
    spec = importlib.util.spec_from_file_location("grscenes_full_dependency_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_plan(tmp_path: Path, *, scratch_exists: bool = True) -> tuple[dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = tmp_path / "scratch"
    scene_dir = source_root / "scenes/GRScenes-100/home_scenes/scenes/scene_usd"
    scratch_scene_dir = scratch_root / "scenes/GRScenes-100/home_scenes/scenes/scene_usd"
    scene_dir.mkdir(parents=True)
    if scratch_exists:
        scratch_scene_dir.mkdir(parents=True)
    root_usd = scene_dir / "start_result_raw.usd"
    scratch_root_usd = scratch_scene_dir / "start_result_raw.usd"
    root_usd.write_text("#usda 1.0\n", encoding="utf-8")
    if scratch_exists:
        scratch_root_usd.write_text("#usda 1.0\n", encoding="utf-8")
    plan = {
        "schema_version": 1,
        "status": "planned_full_grscenes_nomdl_scratch",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "safety": {
            "apply_blockers": [
                "single_process_multi_root_runner_missing",
                "whole_scene_dependency_closure_not_scanned",
                "recursive_nomdl_output_collision_scan_missing",
                "scratch_cleanliness_not_verified",
            ],
        },
        "conversion_jobs": [
            {
                "kind": "convert_no_mdl",
                "conversion_job_id": "home_scenes:scene_usd:start_result_raw.usd",
                "source_usd": str(root_usd),
                "scratch_input_usd": str(scratch_root_usd),
                "expected_top_output_usd": str(scratch_scene_dir / "start_result_raw_noMDL.usd"),
                "blocked_by": [
                    "single_process_multi_root_runner_missing",
                    "whole_scene_dependency_closure_not_scanned",
                    "recursive_nomdl_output_collision_scan_missing",
                ],
                "safe_to_execute_now": False,
            }
        ],
    }
    return plan, {
        "source_root": source_root,
        "scratch_root": scratch_root,
        "scene_dir": scene_dir,
        "scratch_scene_dir": scratch_scene_dir,
        "root_usd": root_usd,
        "scratch_root_usd": scratch_root_usd,
    }


def ref(asset_path: str, *, layer_dir: Path, kind: str = "reference") -> dict:
    return {
        "kind": kind,
        "declaring_layer": str(layer_dir / "layer.usd"),
        "layer_dir": str(layer_dir),
        "asset_path": asset_path,
        "prim_path": "/Root",
    }


def test_module_imports_without_pxr(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__
    for module_name in list(sys.modules):
        if module_name == "pxr" or module_name.startswith("pxr."):
            sys.modules.pop(module_name)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pxr" or name.startswith("pxr."):
            raise AssertionError("full dependency closure module must not import pxr at module import time")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = load_closure_module()

    assert hasattr(module, "build_full_dependency_closure_report")


def test_report_recovers_split_level_scene_references_and_maps_recursive_outputs(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)
    model_usd = paths["source_root"] / "scenes/GRScenes-100/home_scenes/models/chair/asset/instance.usd"
    model_usd.parent.mkdir(parents=True)
    model_usd.write_text("#usda 1.0\n", encoding="utf-8")
    material = paths["source_root"] / "scenes/GRScenes-100/home_scenes/Materials/DayMaterial.mdl"
    material.parent.mkdir(parents=True)
    material.write_text("mdl", encoding="utf-8")
    dependency_records = {
        str(paths["root_usd"]): [
            ref("models/chair/asset/instance.usd", layer_dir=paths["scene_dir"]),
            ref("Materials/DayMaterial.mdl", layer_dir=paths["scene_dir"]),
        ],
        str(model_usd): [],
    }

    report = module.build_full_dependency_closure_report(plan, dependency_records_by_layer=dependency_records)

    assert report["status"] == "planned_full_grscenes_dependency_closure"
    assert report["summary"]["conversion_job_count"] == 1
    assert report["summary"]["missing_dependency_count"] == 0
    assert report["summary"]["outside_source_root_ref_count"] == 0
    assert report["summary"]["reachable_source_usd_count"] == 2
    assert report["summary"]["expected_recursive_nomdl_output_count"] == 1
    assert "whole_scene_dependency_closure_not_scanned" in report["safety"]["satisfied_apply_blockers"]
    assert "recursive_nomdl_output_collision_scan_missing" in report["safety"]["satisfied_apply_blockers"]
    assert any(item["resolution_status"] == "recovered_split_resource" for item in report["resolved_dependencies"])
    assert str(paths["scratch_root"] / model_usd.relative_to(paths["source_root"])).replace(
        "instance.usd", "instance_noMDL.usd"
    ) in {item["expected_output_usd"] for item in report["expected_recursive_nomdl_outputs"]}


def test_report_blocks_missing_and_outside_dependencies(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)
    outside = tmp_path / "outside/child.usd"
    outside.parent.mkdir()
    outside.write_text("#usda 1.0\n", encoding="utf-8")
    dependency_records = {
        str(paths["root_usd"]): [
            ref("missing/child.usd", layer_dir=paths["scene_dir"]),
            ref(str(outside), layer_dir=paths["scene_dir"]),
        ],
    }

    report = module.build_full_dependency_closure_report(plan, dependency_records_by_layer=dependency_records)

    assert report["summary"]["missing_dependency_count"] == 1
    assert report["summary"]["outside_source_root_ref_count"] == 1
    assert "dependency_closure_has_missing_dependencies" in report["safety"]["remaining_apply_blockers"]
    assert "dependency_closure_has_outside_source_refs" in report["safety"]["remaining_apply_blockers"]
    assert report["summary"]["safe_to_run_multi_root_nomdl"] is False


def test_report_dedupes_shared_dependencies(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)
    second_root = paths["scene_dir"] / "start_result_navigation.usd"
    second_scratch = paths["scratch_scene_dir"] / "start_result_navigation.usd"
    second_root.write_text("#usda 1.0\n", encoding="utf-8")
    second_scratch.write_text("#usda 1.0\n", encoding="utf-8")
    plan["conversion_jobs"].append(
        {
            **plan["conversion_jobs"][0],
            "conversion_job_id": "home_scenes:scene_usd:start_result_navigation.usd",
            "source_usd": str(second_root),
            "scratch_input_usd": str(second_scratch),
            "expected_top_output_usd": str(paths["scratch_scene_dir"] / "start_result_navigation_noMDL.usd"),
        }
    )
    shared = paths["source_root"] / "scenes/GRScenes-100/home_scenes/models/shared/instance.usd"
    shared.parent.mkdir(parents=True)
    shared.write_text("#usda 1.0\n", encoding="utf-8")
    dependency_records = {
        str(paths["root_usd"]): [ref("models/shared/instance.usd", layer_dir=paths["scene_dir"])],
        str(second_root): [ref("models/shared/instance.usd", layer_dir=paths["scene_dir"])],
        str(shared): [],
    }

    report = module.build_full_dependency_closure_report(plan, dependency_records_by_layer=dependency_records)

    assert report["summary"]["conversion_job_count"] == 2
    assert report["summary"]["reachable_source_usd_count"] == 3
    assert report["summary"]["expected_top_output_count"] == 2
    assert report["summary"]["expected_recursive_nomdl_output_count"] == 1
    assert report["summary"]["duplicate_expected_output_count"] == 0


def test_report_detects_recursive_output_collisions(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)
    child = paths["source_root"] / "scenes/GRScenes-100/home_scenes/models/chair/instance.usd"
    child.parent.mkdir(parents=True)
    child.write_text("#usda 1.0\n", encoding="utf-8")
    scratch_child = paths["scratch_root"] / child.relative_to(paths["source_root"])
    scratch_child.parent.mkdir(parents=True)
    scratch_child.write_text("#usda 1.0\n", encoding="utf-8")
    scratch_child.with_name("instance_noMDL.usd").write_text("#usda 1.0\n", encoding="utf-8")
    scratch_child.with_name("instance_noMDL_20260521_000000.usd").write_text("#usda 1.0\n", encoding="utf-8")
    dependency_records = {
        str(paths["root_usd"]): [ref("models/chair/instance.usd", layer_dir=paths["scene_dir"])],
        str(child): [],
    }

    report = module.build_full_dependency_closure_report(plan, dependency_records_by_layer=dependency_records)

    assert report["summary"]["existing_expected_output_count"] == 1
    assert report["summary"]["existing_timestamped_output_count"] == 1
    assert report["summary"]["output_collision_count"] == 2
    assert "recursive_nomdl_output_collisions_present" in report["safety"]["remaining_apply_blockers"]


def test_report_keeps_scan_blockers_when_layer_limit_is_reached(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)
    child = paths["source_root"] / "scenes/GRScenes-100/home_scenes/models/chair/instance.usd"
    child.parent.mkdir(parents=True)
    child.write_text("#usda 1.0\n", encoding="utf-8")
    dependency_records = {
        str(paths["root_usd"]): [ref("models/chair/instance.usd", layer_dir=paths["scene_dir"])],
        str(child): [],
    }

    report = module.build_full_dependency_closure_report(
        plan,
        dependency_records_by_layer=dependency_records,
        max_usd_layers=1,
    )

    assert report["summary"]["scan_truncated"] is True
    assert report["summary"]["usd_layer_scan_limit"] == 1
    assert "dependency_closure_scan_truncated" in report["safety"]["remaining_apply_blockers"]
    assert "whole_scene_dependency_closure_not_scanned" not in report["safety"]["satisfied_apply_blockers"]
    assert "recursive_nomdl_output_collision_scan_missing" not in report["safety"]["satisfied_apply_blockers"]


def test_report_blocks_missing_recursive_scratch_inputs(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)
    child = paths["source_root"] / "scenes/GRScenes-100/home_scenes/models/chair/instance.usd"
    child.parent.mkdir(parents=True)
    child.write_text("#usda 1.0\n", encoding="utf-8")
    dependency_records = {
        str(paths["root_usd"]): [ref("models/chair/instance.usd", layer_dir=paths["scene_dir"])],
        str(child): [],
    }

    report = module.build_full_dependency_closure_report(plan, dependency_records_by_layer=dependency_records)

    assert report["summary"]["top_level_scratch_input_missing_count"] == 0
    assert report["summary"]["recursive_scratch_input_missing_count"] == 1
    assert report["summary"]["scratch_input_missing_count"] == 1
    assert "scratch_inputs_missing" in report["safety"]["remaining_apply_blockers"]


def test_output_path_guard_rejects_source_and_scratch_outputs(tmp_path: Path) -> None:
    module = load_closure_module()
    plan, paths = make_plan(tmp_path)

    with pytest.raises(ValueError, match="output path must not be inside source_root"):
        module.validate_output_path(paths["source_root"] / "report.json", plan=plan)

    with pytest.raises(ValueError, match="output path must not be inside scratch_root"):
        module.validate_output_path(paths["scratch_root"] / "report.json", plan=plan)

    assert module.validate_output_path(tmp_path / "reports/report.json", plan=plan) == (
        tmp_path / "reports/report.json"
    ).resolve(strict=False)
