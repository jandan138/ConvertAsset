import importlib.util
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_full_nomdl_scratch.py"


def load_materializer_module():
    spec = importlib.util.spec_from_file_location("grscenes_full_scratch_materializer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_full_plan(
    tmp_path: Path,
    *,
    scratch_inside_source: bool = False,
    copy_mode: str = "hardlink",
) -> tuple[dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = source_root / "scratch" if scratch_inside_source else tmp_path / "scratch"
    split_root = source_root / "scenes/GRScenes-100/home_scenes"
    scene_dir = split_root / "scenes/scene_a_usd"
    model_root = split_root / "models/object/bottle/hash"
    materials_root = split_root / "Materials"
    scene_dir.mkdir(parents=True)
    model_root.mkdir(parents=True)
    materials_root.mkdir(parents=True)
    (scene_dir / "start_result_raw.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (scene_dir / "metadata.json").write_text("{}\n", encoding="utf-8")
    (scene_dir / "models").write_text("../../models", encoding="utf-8")
    (scene_dir / "Materials").write_text("../../Materials", encoding="utf-8")
    (model_root / "instance.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (materials_root / "material.mdl").write_text("mdl 1.0;\n", encoding="utf-8")

    scratch_split_root = scratch_root / split_root.relative_to(source_root)
    scratch_scene = scratch_root / scene_dir.relative_to(source_root)
    scratch_models = scratch_split_root / "models"
    scratch_materials = scratch_split_root / "Materials"
    scratch_input = scratch_scene / "start_result_raw.usd"
    expected_output = scratch_scene / "start_result_raw_noMDL.usd"
    actions = [
        {
            "kind": "resource_tree",
            "split": "home_scenes",
            "resource_name": "Materials",
            "src": str(materials_root),
            "dst": str(scratch_materials),
            "copy_mode": copy_mode,
            "exists_policy": "fail_if_different",
        },
        {
            "kind": "resource_tree",
            "split": "home_scenes",
            "resource_name": "models",
            "src": str(split_root / "models"),
            "dst": str(scratch_models),
            "copy_mode": copy_mode,
            "exists_policy": "fail_if_different",
        },
        {
            "kind": "scene_dir",
            "source_scene_id": "scene_a_usd",
            "source_scene_split": "home_scenes",
            "src": str(scene_dir),
            "dst": str(scratch_scene),
            "copy_mode": copy_mode,
            "exists_policy": "fail_if_different",
            "repairable_entry_names": ["models", "Materials"],
        },
        {
            "kind": "scene_entry_repair",
            "mode": "create_relative_symlink",
            "source_scene_id": "scene_a_usd",
            "source_scene_split": "home_scenes",
            "entry_name": "models",
            "dst": str(scratch_scene / "models"),
            "target_text": "../../models",
            "target_resolved": str(scratch_models),
            "source_entry": str(scene_dir / "models"),
            "source_entry_type": "file",
        },
        {
            "kind": "scene_entry_repair",
            "mode": "create_relative_symlink",
            "source_scene_id": "scene_a_usd",
            "source_scene_split": "home_scenes",
            "entry_name": "Materials",
            "dst": str(scratch_scene / "Materials"),
            "target_text": "../../Materials",
            "target_resolved": str(scratch_materials),
            "source_entry": str(scene_dir / "Materials"),
            "source_entry_type": "file",
        },
        {
            "kind": "convert_no_mdl",
            "conversion_job_id": "home_scenes:scene_a_usd:start_result_raw.usd",
            "source_usd": str(scene_dir / "start_result_raw.usd"),
            "scratch_input_usd": str(scratch_input),
            "expected_top_output_usd": str(expected_output),
        },
    ]
    plan = {
        "schema_version": 1,
        "status": "planned_full_grscenes_nomdl_scratch",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": {"conversion_job_count": 1},
        "actions": actions,
        "conversion_jobs": [actions[-1]],
    }
    paths = {
        "source_root": source_root,
        "scratch_root": scratch_root,
        "split_root": split_root,
        "scene_dir": scene_dir,
        "model_root": model_root,
        "materials_root": materials_root,
        "scratch_split_root": scratch_split_root,
        "scratch_scene": scratch_scene,
        "scratch_models": scratch_models,
        "scratch_materials": scratch_materials,
        "scratch_input": scratch_input,
    }
    return plan, paths


def test_module_imports_without_pxr() -> None:
    module = load_materializer_module()

    assert hasattr(module, "materialize_full_scratch_plan")


def test_materializer_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path)

    report = module.materialize_full_scratch_plan(plan, dry_run=True)

    assert report["dry_run"] is True
    assert report["summary"]["planned_tree_action_count"] == 3
    assert report["summary"]["planned_repair_action_count"] == 2
    assert report["summary"]["ignored_convert_action_count"] == 1
    assert report["summary"]["top_level_scratch_input_missing_count"] == 1
    assert not paths["scratch_scene"].exists()


def test_materializer_rejects_scratch_inside_source(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, _paths = make_full_plan(tmp_path, scratch_inside_source=True)

    with pytest.raises(ValueError, match="scratch_root must not be inside source_root"):
        module.materialize_full_scratch_plan(plan, dry_run=True)


def test_materializer_rejects_tree_destination_outside_scratch(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, _paths = make_full_plan(tmp_path)
    plan["actions"][0]["dst"] = str(tmp_path / "outside/Materials")

    with pytest.raises(ValueError, match="tree action dst must be inside scratch_root"):
        module.materialize_full_scratch_plan(plan, dry_run=True)


def test_materializer_rejects_repair_target_escaping_scratch(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, _paths = make_full_plan(tmp_path)
    plan["actions"][3]["target_text"] = "../../../../../../outside"

    with pytest.raises(ValueError, match="repair target would escape scratch_root"):
        module.materialize_full_scratch_plan(plan, dry_run=True)


def test_materializer_rejects_unsupported_repair_action_shape(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, _paths = make_full_plan(tmp_path / "entry-name")
    plan["actions"][3]["entry_name"] = "metadata.json"

    with pytest.raises(ValueError, match="repair entry_name must be one of"):
        module.materialize_full_scratch_plan(plan, dry_run=True)

    plan, _paths = make_full_plan(tmp_path / "source-entry-type")
    plan["actions"][3]["source_entry_type"] = "symlink"

    with pytest.raises(ValueError, match="repair source_entry_type must be file"):
        module.materialize_full_scratch_plan(plan, dry_run=True)

    plan, _paths = make_full_plan(tmp_path / "mode")
    plan["actions"][3]["mode"] = "copy_file"

    with pytest.raises(ValueError, match="repair mode must be create_relative_symlink"):
        module.materialize_full_scratch_plan(plan, dry_run=True)


def test_materializer_rejects_internal_symlink_escaping_scratch(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path)
    (paths["model_root"] / "Materials").symlink_to(paths["materials_root"], target_is_directory=True)

    with pytest.raises(ValueError, match="symlink target would escape scratch_root"):
        module.materialize_full_scratch_plan(plan, dry_run=False)


def test_materializer_rejects_existing_scratch_nomdl_outputs(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path)
    stale_output = paths["scratch_scene"] / "start_result_raw_noMDL.usd"
    stale_output.parent.mkdir(parents=True)
    stale_output.write_text("#usda 1.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="scratch contains existing no-MDL outputs"):
        module.materialize_full_scratch_plan(plan, dry_run=False)


def test_materializer_rejects_source_tree_nomdl_outputs_before_apply(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path)
    (paths["model_root"] / "instance_noMDL.usd").write_text("#usda 1.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="scratch contains existing no-MDL outputs"):
        module.materialize_full_scratch_plan(plan, dry_run=False)


def test_materializer_hardlinks_trees_and_repairs_scene_entries(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path)

    report = module.materialize_full_scratch_plan(plan, dry_run=False)

    assert report["summary"]["created_tree_count"] == 3
    assert report["summary"]["repaired_scene_entry_count"] == 2
    assert report["summary"]["top_level_scratch_input_exists_count"] == 1
    assert paths["scratch_input"].exists()
    assert paths["scratch_input"].stat().st_ino == (paths["scene_dir"] / "start_result_raw.usd").stat().st_ino
    assert (paths["scratch_scene"] / "models").is_symlink()
    assert os.readlink(paths["scratch_scene"] / "models") == "../../models"
    assert (paths["scratch_scene"] / "models").resolve() == paths["scratch_models"]
    assert (paths["scene_dir"] / "models").is_file()
    assert (paths["scene_dir"] / "models").read_text(encoding="utf-8") == "../../models"
    assert (paths["scratch_models"] / "object/bottle/hash/instance.usd").stat().st_ino == (
        paths["model_root"] / "instance.usd"
    ).stat().st_ino


def test_materializer_is_idempotent_after_repairs(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, _paths = make_full_plan(tmp_path)

    module.materialize_full_scratch_plan(plan, dry_run=False)
    second_report = module.materialize_full_scratch_plan(plan, dry_run=False)

    assert second_report["summary"]["existing_tree_count"] == 3
    assert second_report["summary"]["existing_scene_entry_count"] == 2
    assert second_report["summary"]["created_tree_count"] == 0
    assert second_report["summary"]["repaired_scene_entry_count"] == 0


def test_materializer_idempotency_skips_byte_compare_for_hardlinks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = load_materializer_module()
    plan, _paths = make_full_plan(tmp_path)
    module.materialize_full_scratch_plan(plan, dry_run=False)

    def forbidden_byte_compare(*args, **kwargs):
        raise AssertionError("hardlinked files should be validated by inode without byte compare")

    monkeypatch.setattr(module.filecmp, "cmp", forbidden_byte_compare)

    second_report = module.materialize_full_scratch_plan(plan, dry_run=False)

    assert second_report["summary"]["existing_tree_count"] == 3


def test_materializer_copy_mode_copies_files_instead_of_hardlinking(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path, copy_mode="copy")

    module.materialize_full_scratch_plan(plan, dry_run=False)

    assert paths["scratch_input"].exists()
    assert paths["scratch_input"].stat().st_ino != (paths["scene_dir"] / "start_result_raw.usd").stat().st_ino


def test_output_path_guard_rejects_source_and_scratch_outputs(tmp_path: Path) -> None:
    module = load_materializer_module()
    plan, paths = make_full_plan(tmp_path)

    with pytest.raises(ValueError, match="output path must not be inside source_root"):
        module.validate_output_path(paths["source_root"] / "report.json", plan=plan)

    with pytest.raises(ValueError, match="output path must not be inside scratch_root"):
        module.validate_output_path(paths["scratch_root"] / "report.json", plan=plan)

    assert module.validate_output_path(tmp_path / "reports/report.json", plan=plan) == (
        tmp_path / "reports/report.json"
    ).resolve(strict=False)
