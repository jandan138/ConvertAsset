import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/materialize_scratch.py"


def load_materialize_module():
    spec = importlib.util.spec_from_file_location("grscenes_materialize_scratch", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_source_manifest(tmp_path: Path, *, scratch_inside_source: bool = False) -> dict:
    source_root = tmp_path / "source"
    scratch_root = source_root / "scratch" if scratch_inside_source else tmp_path / "scratch"
    split_root = source_root / "scenes/GRScenes-100/home_scenes"
    scene_dir = split_root / "scenes/scene_a_usd"
    scene_dir.mkdir(parents=True)
    (scene_dir / "start_result_raw.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (scene_dir / "metadata.json").write_text("{}\n", encoding="utf-8")
    (scene_dir / "interactive_obj_list.json").write_text("[]\n", encoding="utf-8")
    (scene_dir / "models").write_text("../../models", encoding="utf-8")
    (scene_dir / "Materials").write_text("../../Materials", encoding="utf-8")
    (split_root / "models/object/bottle/hash").mkdir(parents=True)
    (split_root / "models/object/bottle/hash/instance.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (split_root / "Materials").mkdir(parents=True)
    (split_root / "Materials/material.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (split_root / "models/object/bottle/hash/Materials").symlink_to("../../../../Materials", target_is_directory=True)

    scratch_scene_root = scratch_root / "scenes/GRScenes-100/home_scenes/scenes/scene_a_usd"
    return {
        "schema_version": 1,
        "status": "planned_source_manifest",
        "dataset_roles": {
            "benchmark_source_dataset": {
                "local_root": str(source_root),
                "name": "GRScenes-100",
                "mutation_policy": "never_in_place",
            },
            "intervention_outputs": {
                "scratch_root": str(scratch_root),
                "retention_policy": "generated_outputs_may_be_deleted_and_regenerated",
            },
        },
        "scenes": [
            {
                "dataset_role": "benchmark_source_dataset",
                "source_dataset_root": str(source_root),
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "scene_dir": str(scene_dir),
                "source_usd": str(scene_dir / "start_result_raw.usd"),
                "source_usd_variant": "start_result_raw.usd",
                "scratch_scene_root": str(scratch_scene_root),
                "converted_usd": str(scratch_scene_root / "start_result_raw_noMDL.usd"),
                "conversion_command": f"./scripts/isaac_python.sh ./main.py no-mdl {scratch_scene_root / 'start_result_raw.usd'}",
                "material_conditions": ["original", "converted"],
            }
        ],
    }


def test_module_imports_without_pxr() -> None:
    module = load_materialize_module()

    assert hasattr(module, "build_materialization_plan")


def test_build_materialization_plan_rejects_scratch_inside_source(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path, scratch_inside_source=True)

    with pytest.raises(ValueError, match="scratch_root must not be inside source_root"):
        module.build_materialization_plan(manifest)


def test_build_materialization_plan_rejects_missing_dataset_roots(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    del manifest["dataset_roles"]["benchmark_source_dataset"]["local_root"]

    with pytest.raises(ValueError, match="manifest must define benchmark source_root"):
        module.build_materialization_plan(manifest)


def test_build_materialization_plan_rejects_derived_resource_dst_outside_scratch(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    manifest["scenes"][0]["scratch_scene_root"] = str(tmp_path / "scratch/scene_a_usd")
    manifest["scenes"][0]["converted_usd"] = str(tmp_path / "scratch/scene_a_usd/start_result_raw_noMDL.usd")

    with pytest.raises(ValueError, match="action dst must be inside scratch_root"):
        module.build_materialization_plan(manifest)


def test_build_materialization_plan_includes_split_resources_and_scene(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)

    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")

    assert plan["summary"]["scene_count"] == 1
    assert plan["summary"]["resource_tree_count"] == 2
    assert plan["summary"]["conversion_command_count"] == 1
    actions = plan["actions"]
    assert [action["kind"] for action in actions] == ["resource_tree", "resource_tree", "scene_dir"]
    assert actions[0]["resource_name"] == "Materials"
    assert actions[1]["resource_name"] == "models"
    assert actions[2]["source_scene_id"] == "scene_a_usd"
    assert actions[2]["dst"].endswith("/scratch/scenes/GRScenes-100/home_scenes/scenes/scene_a_usd")
    for action in actions:
        assert "/source/" not in action["dst"]
    assert plan["conversion_commands"] == [
        f"./scripts/isaac_python.sh ./main.py no-mdl {Path(manifest['scenes'][0]['scratch_scene_root']) / 'start_result_raw.usd'}"
    ]


def test_materialize_from_plan_hardlinks_resources_and_scene(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")

    report = module.materialize_from_plan(plan, dry_run=False)

    assert report["summary"]["created_count"] == 3
    assert report["summary"]["exists_count"] == 0
    scene_src = Path(manifest["scenes"][0]["scene_dir"])
    scene_dst = Path(manifest["scenes"][0]["scratch_scene_root"])
    assert (scene_dst / "start_result_raw.usd").exists()
    assert not (scene_dst / "start_result_raw.usd").is_symlink()
    assert (scene_src / "start_result_raw.usd").stat().st_ino == (scene_dst / "start_result_raw.usd").stat().st_ino

    source_material = scene_src.parent.parent / "Materials/material.mdl"
    scratch_material = scene_dst.parent.parent / "Materials/material.mdl"
    assert scratch_material.exists()
    assert not scratch_material.is_symlink()
    assert source_material.stat().st_ino == scratch_material.stat().st_ino

    scratch_materials_link = scene_dst.parent.parent / "models/object/bottle/hash/Materials"
    assert scratch_materials_link.is_symlink()
    assert scratch_materials_link.resolve() == scene_dst.parent.parent / "Materials"


def test_materialize_from_plan_skips_existing_destinations(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")

    module.materialize_from_plan(plan, dry_run=False)
    second_report = module.materialize_from_plan(plan, dry_run=False)

    assert second_report["summary"]["created_count"] == 0
    assert second_report["summary"]["exists_count"] == 3
    assert {result["status"] for result in second_report["results"]} == {"exists"}


def test_materialize_from_plan_rejects_existing_destination_symlink(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")
    materials_action = next(action for action in plan["actions"] if action["kind"] == "resource_tree" and action["resource_name"] == "Materials")
    dst = Path(materials_action["dst"])
    dst.parent.mkdir(parents=True)
    dst.symlink_to(Path(materials_action["src"]), target_is_directory=True)

    with pytest.raises(ValueError, match="destination must not be a symlink"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_from_plan_rejects_internal_symlink_escaping_scratch(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    scene_dir = Path(manifest["scenes"][0]["scene_dir"])
    split_root = scene_dir.parent.parent
    source_link = split_root / "models/object/bottle/hash/Materials"
    source_link.unlink()
    source_link.symlink_to(split_root / "Materials", target_is_directory=True)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")

    with pytest.raises(ValueError, match="symlink target would escape scratch_root"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_from_plan_rejects_incomplete_existing_destination(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")
    materials_action = next(
        action
        for action in plan["actions"]
        if action["kind"] == "resource_tree" and action["resource_name"] == "Materials"
    )
    dst = Path(materials_action["dst"])
    dst.mkdir(parents=True)

    with pytest.raises(ValueError, match="existing destination is incomplete"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_from_plan_rejects_existing_destination_with_wrong_relative_paths(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")
    module.materialize_from_plan(plan, dry_run=False)
    materials_action = next(
        action
        for action in plan["actions"]
        if action["kind"] == "resource_tree" and action["resource_name"] == "Materials"
    )
    dst = Path(materials_action["dst"])
    (dst / "material.mdl").unlink()
    (dst / "wrong_name.mdl").write_text("mdl 1.0;\n", encoding="utf-8")

    with pytest.raises(ValueError, match="differs from source tree"):
        module.materialize_from_plan(plan, dry_run=False)


def test_materialize_from_plan_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="hardlink")

    report = module.materialize_from_plan(plan, dry_run=True)

    assert report["summary"]["dry_run"] is True
    assert report["summary"]["planned_count"] == 3
    assert not Path(manifest["scenes"][0]["scratch_scene_root"]).exists()


def test_materialize_from_plan_copy_mode_copies_instead_of_hardlinking(tmp_path: Path) -> None:
    module = load_materialize_module()
    manifest = make_source_manifest(tmp_path)
    plan = module.build_materialization_plan(manifest, copy_mode="copy")

    module.materialize_from_plan(plan, dry_run=False)

    scene_src = Path(manifest["scenes"][0]["scene_dir"])
    scene_dst = Path(manifest["scenes"][0]["scratch_scene_root"])
    assert (scene_dst / "start_result_raw.usd").exists()
    assert (scene_src / "start_result_raw.usd").stat().st_ino != (scene_dst / "start_result_raw.usd").stat().st_ino
