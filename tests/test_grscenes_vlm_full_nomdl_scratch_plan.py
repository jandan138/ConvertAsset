import builtins
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py"


def load_planner_module():
    spec = importlib.util.spec_from_file_location("grscenes_full_nomdl_scratch_planner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_dataset(tmp_path: Path, *, existing_source_sidecar: bool = False) -> tuple[Path, Path, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = tmp_path / "scratch"
    grscenes_root = source_root / "scenes/GRScenes-100"

    paths: dict[str, Path] = {"source_root": source_root, "scratch_root": scratch_root}
    for split, scene_id, entry_mode in (
        ("home_scenes", "home_scene_usd", "pointer_file"),
        ("commercial_scenes", "commercial_scene_usd", "symlink"),
    ):
        split_root = grscenes_root / split
        scene_dir = split_root / "scenes" / scene_id
        models_root = split_root / "models"
        materials_root = split_root / "Materials"
        scene_dir.mkdir(parents=True)
        models_root.mkdir(parents=True)
        materials_root.mkdir(parents=True)

        for usd_name in (
            "start_result_raw.usd",
            "start_result_navigation.usd",
            "start_result_interaction.usd",
        ):
            (scene_dir / usd_name).write_text(f"#usda 1.0\n# {scene_id} {usd_name}\n", encoding="utf-8")

        if existing_source_sidecar and split == "home_scenes":
            (scene_dir / "start_result_raw_noMDL.usd").write_text("#usda 1.0\n", encoding="utf-8")

        if entry_mode == "pointer_file":
            (scene_dir / "models").write_text("../../models\n", encoding="utf-8")
            (scene_dir / "Materials").write_text("../../Materials\n", encoding="utf-8")
        else:
            (scene_dir / "models").symlink_to("../../models")
            (scene_dir / "Materials").symlink_to("../../Materials")

        paths[f"{split}_scene_dir"] = scene_dir
        paths[f"{split}_models_root"] = models_root
        paths[f"{split}_materials_root"] = materials_root

    return source_root, scratch_root, paths


def test_module_imports_without_pxr(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__
    for module_name in list(sys.modules):
        if module_name == "pxr" or module_name.startswith("pxr."):
            sys.modules.pop(module_name)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pxr" or name.startswith("pxr."):
            raise AssertionError("plan_full_nomdl_scratch.py must not import pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = load_planner_module()

    assert hasattr(module, "build_full_nomdl_scratch_plan")


def test_build_full_plan_inventory_actions_and_commands(tmp_path: Path) -> None:
    module = load_planner_module()
    source_root, scratch_root, paths = make_dataset(tmp_path)

    plan = module.build_full_nomdl_scratch_plan(
        source_root=source_root,
        scratch_root=scratch_root,
        source_usd_variants=("start_result_raw.usd", "start_result_navigation.usd"),
    )

    assert plan["status"] == "planned_full_grscenes_nomdl_scratch"
    assert plan["config"]["source_usd_variants"] == ["start_result_raw.usd", "start_result_navigation.usd"]
    assert plan["summary"]["scene_count"] == 2
    assert plan["summary"]["scene_dir_action_count"] == 2
    assert plan["summary"]["resource_tree_action_count"] == 4
    assert plan["summary"]["scene_entry_repair_count"] == 2
    assert plan["summary"]["scene_entry_symlink_projectable_count"] == 2
    assert plan["summary"]["input_usd_count"] == 4
    assert plan["summary"]["conversion_job_count"] == 4
    assert plan["summary"]["existing_source_nomdl_sidecar_count"] == 0
    assert plan["inventory"]["splits"]["home_scenes"]["scene_count"] == 1
    assert plan["inventory"]["splits"]["commercial_scenes"]["scene_count"] == 1

    assert plan["safety"]["source_root_immutable"] is True
    assert plan["safety"]["scratch_outside_source_root"] is True
    assert plan["safety"]["source_outside_scratch_root"] is True
    assert plan["safety"]["safe_to_apply"] is False
    assert "single_process_multi_root_runner_missing" in plan["safety"]["apply_blockers"]
    assert "whole_scene_dependency_closure_not_scanned" in plan["safety"]["apply_blockers"]

    resource_actions = [action for action in plan["actions"] if action["kind"] == "resource_tree"]
    assert {Path(action["src"]).name for action in resource_actions} == {"models", "Materials"}
    assert {action["split"] for action in resource_actions} == {"home_scenes", "commercial_scenes"}

    repairs = [action for action in plan["actions"] if action["kind"] == "scene_entry_repair"]
    assert {action["entry_name"] for action in repairs} == {"models", "Materials"}
    assert all(action["source_entry_type"] == "file" for action in repairs)

    jobs = plan["conversion_jobs"]
    assert len(jobs) == 4
    assert all("--only-new-usd" in job["command"] for job in jobs)
    assert all(job["argv"][:4] == ["./scripts/isaac_python.sh", "./main.py", "no-mdl", "--only-new-usd"] for job in jobs)
    for job in jobs:
        Path(job["scratch_input_usd"]).resolve(strict=False).relative_to(scratch_root.resolve(strict=False))
        with pytest.raises(ValueError):
            Path(job["scratch_input_usd"]).resolve(strict=False).relative_to(source_root.resolve(strict=False))
    assert {
        Path(job["expected_top_output_usd"]).name for job in jobs
    } == {"start_result_raw_noMDL.usd", "start_result_navigation_noMDL.usd"}
    assert jobs[0]["scratch_input_usd"].startswith(str(scratch_root))
    assert str(paths["home_scenes_scene_dir"]) in {scene["source_scene_dir"] for scene in plan["scenes"]}


def test_default_variant_is_raw_only(tmp_path: Path) -> None:
    module = load_planner_module()
    source_root, scratch_root, _paths = make_dataset(tmp_path)

    plan = module.build_full_nomdl_scratch_plan(source_root=source_root, scratch_root=scratch_root)

    assert plan["config"]["source_usd_variants"] == ["start_result_raw.usd"]
    assert plan["summary"]["scene_count"] == 2
    assert plan["summary"]["input_usd_count"] == 2
    assert plan["summary"]["conversion_job_count"] == 2


def test_full_plan_detects_existing_source_nomdl_sidecars(tmp_path: Path) -> None:
    module = load_planner_module()
    source_root, scratch_root, _paths = make_dataset(tmp_path, existing_source_sidecar=True)

    plan = module.build_full_nomdl_scratch_plan(source_root=source_root, scratch_root=scratch_root)

    assert plan["summary"]["existing_source_nomdl_sidecar_count"] == 1
    assert len(plan["inventory"]["existing_source_nomdl_sidecars"]) == 1
    assert plan["inventory"]["existing_source_nomdl_sidecars"][0].endswith("start_result_raw_noMDL.usd")
    assert "source_tree_has_existing_nomdl_sidecars" in plan["safety"]["warnings"]


def test_full_plan_rejects_scratch_inside_source(tmp_path: Path) -> None:
    module = load_planner_module()
    source_root, _scratch_root, _paths = make_dataset(tmp_path)

    with pytest.raises(ValueError, match="scratch_root must not be inside source_root"):
        module.build_full_nomdl_scratch_plan(source_root=source_root, scratch_root=source_root / "scratch")


def test_full_plan_rejects_source_inside_scratch(tmp_path: Path) -> None:
    module = load_planner_module()
    source_root, _scratch_root, _paths = make_dataset(tmp_path)

    with pytest.raises(ValueError, match="source_root must not be inside scratch_root"):
        module.build_full_nomdl_scratch_plan(source_root=source_root, scratch_root=tmp_path)


def test_output_path_guard_rejects_source_and_scratch_outputs(tmp_path: Path) -> None:
    module = load_planner_module()
    source_root, scratch_root, _paths = make_dataset(tmp_path)

    with pytest.raises(ValueError, match="output path must not be inside source_root"):
        module.validate_output_path(source_root / "plan.json", source_root=source_root, scratch_root=scratch_root)

    with pytest.raises(ValueError, match="output path must not be inside scratch_root"):
        module.validate_output_path(scratch_root / "plan.json", source_root=source_root, scratch_root=scratch_root)

    allowed = module.validate_output_path(tmp_path / "reports/plan.json", source_root=source_root, scratch_root=scratch_root)

    assert allowed == (tmp_path / "reports/plan.json").resolve(strict=False)
