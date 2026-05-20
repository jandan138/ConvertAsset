import builtins
import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_targeted_closure.py"


def load_materializer_module():
    spec = importlib.util.spec_from_file_location("grscenes_targeted_materializer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_closure_plans(tmp_path: Path, *, scratch_inside_source: bool = False) -> tuple[dict, dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = source_root / "scratch" if scratch_inside_source else tmp_path / "scratch"
    split_root = source_root / "scenes/GRScenes-100/home_scenes"
    scene_dir = split_root / "scenes/scene_a_usd"
    model_root = split_root / "models/object/others/cup/hash_a"
    materials_root = split_root / "Materials"

    scene_dir.mkdir(parents=True)
    model_root.mkdir(parents=True)
    (materials_root / "Textures").mkdir(parents=True)

    (scene_dir / "start_result_raw.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (scene_dir / "models").write_text("../../models\n", encoding="utf-8")
    (scene_dir / "Materials").write_text("../../Materials\n", encoding="utf-8")
    (model_root / "instance.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (model_root / "mesh.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (materials_root / "cup.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (materials_root / "Textures/cup.png").write_bytes(b"png")

    scratch_split_root = scratch_root / split_root.relative_to(source_root)
    scratch_scene_root = scratch_root / scene_dir.relative_to(source_root)
    scratch_model_root = scratch_root / model_root.relative_to(source_root)
    scratch_materials_root = scratch_root / materials_root.relative_to(source_root)

    reference_plan = {
        "schema_version": 1,
        "status": "planned_reference_closure",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "actions": [
            {
                "kind": "scene_dir",
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "src": str(scene_dir),
                "dst": str(scratch_scene_root),
                "source_usd_variant": "start_result_raw.usd",
                "scratch_input_usd": str(scratch_scene_root / "start_result_raw.usd"),
                "converted_usd": str(scratch_scene_root / "start_result_raw_noMDL.usd"),
                "conversion_command": f"./scripts/isaac_python.sh ./main.py no-mdl {scratch_scene_root / 'start_result_raw.usd'}",
                "copy_mode": "hardlink",
            },
            {
                "kind": "target_model_root",
                "src": str(model_root),
                "dst": str(scratch_model_root),
                "split_root": str(split_root),
                "source_relative_path": model_root.relative_to(source_root).as_posix(),
                "scratch_relative_path": model_root.relative_to(source_root).as_posix(),
                "copy_mode": "hardlink",
                "materials_entry": {
                    "type": "missing",
                    "path": str(model_root / "Materials"),
                    "resolved_path": str(materials_root),
                },
                "targets": [],
            },
        ],
        "conversion_commands": [
            f"./scripts/isaac_python.sh ./main.py no-mdl {scratch_scene_root / 'start_result_raw.usd'}"
        ],
    }

    material_plan = {
        "schema_version": 1,
        "status": "planned_material_dependency_closure",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "summary": {
            "required_material_asset_count": 2,
            "materials_entry_repair_action_count": 1,
            "ready_for_nomdl_after_material_file_actions": False,
        },
        "material_file_actions": [
            {
                "kind": "material_asset_file",
                "src": str(materials_root / "cup.mdl"),
                "dst": str(scratch_materials_root / "cup.mdl"),
                "source_relative_path": (materials_root / "cup.mdl").relative_to(source_root).as_posix(),
                "scratch_relative_path": (materials_root / "cup.mdl").relative_to(source_root).as_posix(),
                "copy_mode": "hardlink",
                "size_bytes": 9,
                "referenced_by_model_roots": [str(model_root)],
            },
            {
                "kind": "material_asset_file",
                "src": str(materials_root / "Textures/cup.png"),
                "dst": str(scratch_materials_root / "Textures/cup.png"),
                "source_relative_path": (materials_root / "Textures/cup.png").relative_to(source_root).as_posix(),
                "scratch_relative_path": (materials_root / "Textures/cup.png").relative_to(source_root).as_posix(),
                "copy_mode": "hardlink",
                "size_bytes": 3,
                "referenced_by_model_roots": [str(model_root)],
            },
        ],
        "materials_entry_repair_actions": [
            {
                "kind": "model_materials_entry_repair",
                "mode": "create_relative_symlink",
                "dst": str(scratch_model_root / "Materials"),
                "target_text": "../../../../../Materials",
                "model_root": str(model_root),
                "scratch_model_root": str(scratch_model_root),
                "scratch_split_materials_root": str(scratch_materials_root),
                "source_entry_type": "missing",
                "reason": "model_materials_entry_must_resolve_to_split_materials_in_scratch",
            }
        ],
    }
    paths = {
        "source_root": source_root,
        "scratch_root": scratch_root,
        "split_root": split_root,
        "scene_dir": scene_dir,
        "model_root": model_root,
        "materials_root": materials_root,
        "scratch_split_root": scratch_split_root,
        "scratch_scene_root": scratch_scene_root,
        "scratch_model_root": scratch_model_root,
        "scratch_materials_root": scratch_materials_root,
    }
    return reference_plan, material_plan, paths


def test_module_imports_without_pxr(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__
    for module_name in list(sys.modules):
        if module_name == "pxr" or module_name.startswith("pxr."):
            sys.modules.pop(module_name)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pxr" or name.startswith("pxr."):
            raise AssertionError("materialize_targeted_closure.py must not import pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = load_materializer_module()

    assert hasattr(module, "build_targeted_materialization_plan")


def test_build_targeted_plan_uses_file_level_materials_and_entry_repairs(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, _paths = make_closure_plans(tmp_path)

    plan = module.build_targeted_materialization_plan(reference_plan, material_plan, copy_mode="hardlink")

    assert plan["summary"]["scene_dir_count"] == 1
    assert plan["summary"]["target_model_root_count"] == 1
    assert plan["summary"]["material_file_count"] == 2
    assert plan["summary"]["entry_repair_count"] == 3
    assert plan["summary"]["resource_tree_count"] == 0
    assert [action["kind"] for action in plan["actions"]] == [
        "scene_dir",
        "target_model_root",
        "material_asset_file",
        "material_asset_file",
        "scene_entry_repair",
        "scene_entry_repair",
        "model_materials_entry_repair",
    ]
    assert {action["entry_name"] for action in plan["actions"] if action["kind"] == "scene_entry_repair"} == {
        "Materials",
        "models",
    }


def test_materialize_targeted_plan_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, paths = make_closure_plans(tmp_path)
    plan = module.build_targeted_materialization_plan(reference_plan, material_plan)

    report = module.materialize_from_plan(plan, dry_run=True)

    assert report["summary"]["planned_count"] == 7
    assert "reported_at_utc" in report
    assert "materialized_at_utc" not in report
    assert not paths["scratch_scene_root"].exists()
    assert paths["scene_dir"].joinpath("models").is_file()


def test_materialize_targeted_plan_hardlinks_subset_and_repairs_entries(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, paths = make_closure_plans(tmp_path)
    plan = module.build_targeted_materialization_plan(reference_plan, material_plan, copy_mode="hardlink")

    report = module.materialize_from_plan(plan, dry_run=False)

    assert report["summary"]["created_count"] == 7
    assert (paths["scratch_scene_root"] / "start_result_raw.usd").exists()
    assert (paths["scratch_model_root"] / "instance.usd").exists()
    assert (paths["scratch_materials_root"] / "cup.mdl").exists()
    assert (paths["scratch_materials_root"] / "Textures/cup.png").exists()
    assert (paths["scratch_scene_root"] / "models").is_symlink()
    assert (paths["scratch_scene_root"] / "models").resolve() == paths["scratch_split_root"] / "models"
    assert (paths["scratch_scene_root"] / "Materials").is_symlink()
    assert (paths["scratch_scene_root"] / "Materials").resolve() == paths["scratch_materials_root"]
    assert (paths["scratch_model_root"] / "Materials").is_symlink()
    assert (paths["scratch_model_root"] / "Materials").resolve() == paths["scratch_materials_root"]
    assert (paths["materials_root"] / "cup.mdl").stat().st_ino == (paths["scratch_materials_root"] / "cup.mdl").stat().st_ino
    assert paths["scene_dir"].joinpath("models").is_file()
    assert not (paths["scratch_split_root"] / "models/object/others/cup/hash_b").exists()


def test_materialize_targeted_plan_rejects_tree_symlink_escape_before_apply(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, paths = make_closure_plans(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (paths["model_root"] / "bad_link").symlink_to(outside)
    plan = module.build_targeted_materialization_plan(reference_plan, material_plan, copy_mode="hardlink")

    with pytest.raises(ValueError, match="symlink target would escape scratch_root"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_targeted_plan_rejects_incomplete_existing_tree(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, paths = make_closure_plans(tmp_path)
    plan = module.build_targeted_materialization_plan(reference_plan, material_plan, copy_mode="hardlink")
    paths["scratch_scene_root"].mkdir(parents=True)
    (paths["scratch_scene_root"] / "stale.usd").write_text("#usda 1.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="existing destination is incomplete or differs from source tree"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_targeted_plan_rejects_same_size_stale_material_file(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, paths = make_closure_plans(tmp_path)
    plan = module.build_targeted_materialization_plan(reference_plan, material_plan, copy_mode="hardlink")
    stale = paths["scratch_materials_root"] / "cup.mdl"
    stale.parent.mkdir(parents=True)
    stale.write_text("bad 1.0;\n", encoding="utf-8")
    assert stale.stat().st_size == (paths["materials_root"] / "cup.mdl").stat().st_size

    with pytest.raises(ValueError, match="existing material destination differs from source"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_targeted_plan_rejects_scratch_inside_source(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, _paths = make_closure_plans(tmp_path, scratch_inside_source=True)

    with pytest.raises(ValueError, match="scratch_root must not be inside source_root"):
        module.build_targeted_materialization_plan(reference_plan, material_plan)


def test_materialize_targeted_plan_rejects_material_file_outside_source(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, _paths = make_closure_plans(tmp_path)
    material_plan["material_file_actions"][0]["src"] = str(tmp_path / "outside/cup.mdl")

    with pytest.raises(ValueError, match="material action src must be inside source_root"):
        module.build_targeted_materialization_plan(reference_plan, material_plan)


def test_materialize_targeted_plan_rejects_action_destination_outside_scratch(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, _paths = make_closure_plans(tmp_path)
    reference_plan["actions"][0]["dst"] = str(tmp_path / "outside/scene")

    with pytest.raises(ValueError, match="scene_dir dst must be inside scratch_root"):
        module.build_targeted_materialization_plan(reference_plan, material_plan)


def test_materialize_targeted_plan_rejects_repair_target_escape(tmp_path: Path) -> None:
    module = load_materializer_module()
    reference_plan, material_plan, _paths = make_closure_plans(tmp_path)
    material_plan["materials_entry_repair_actions"][0]["target_text"] = "../" * 20 + "outside"

    with pytest.raises(ValueError, match="model_materials_entry_repair target would escape scratch_root"):
        module.build_targeted_materialization_plan(reference_plan, material_plan)
