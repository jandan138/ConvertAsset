import importlib.util
import builtins
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_reference_closure.py"


def load_closure_module():
    spec = importlib.util.spec_from_file_location("grscenes_reference_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_manifests(
    tmp_path: Path,
    *,
    outside_model: bool = False,
    materials_entry: str = "symlink",
) -> tuple[dict, dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = tmp_path / "scratch"
    split_root = source_root / "scenes/GRScenes-100/home_scenes"
    scene_dir = split_root / "scenes/scene_a_usd"
    model_root = split_root / "models/object/others/bottle/hash_a"
    materials_root = split_root / "Materials"

    scene_dir.mkdir(parents=True)
    model_root.mkdir(parents=True)
    materials_root.mkdir(parents=True)
    (scene_dir / "start_result_raw.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (scene_dir / "metadata.json").write_text("{}\n", encoding="utf-8")
    (scene_dir / "interactive_obj_list.json").write_text("[]\n", encoding="utf-8")
    (scene_dir / "models").write_text("../../models", encoding="utf-8")
    (scene_dir / "Materials").write_text("../../Materials", encoding="utf-8")
    (model_root / "instance.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (model_root / "mesh.usd").write_text("#usda 1.0\n", encoding="utf-8")
    (model_root / "textures").mkdir()
    (model_root / "textures/albedo.png").write_bytes(b"png")
    if materials_entry == "symlink":
        (model_root / "Materials").symlink_to("../../../../../Materials", target_is_directory=True)
    elif materials_entry == "pointer_file":
        (model_root / "Materials").write_text("../../../../../Materials\n", encoding="utf-8")
    elif materials_entry == "missing":
        pass
    else:
        raise ValueError(materials_entry)
    (materials_root / "bottle.mdl").write_text("mdl 1.0;\n", encoding="utf-8")

    outside_root = tmp_path / "outside/object"
    outside_root.mkdir(parents=True)
    outside_model_path = outside_root / "instance.usd"
    outside_model_path.write_text("#usda 1.0\n", encoding="utf-8")
    resolved_model_path = outside_model_path if outside_model else model_root / "instance.usd"

    scratch_scene_root = scratch_root / "scenes/GRScenes-100/home_scenes/scenes/scene_a_usd"
    source_manifest = {
        "schema_version": 1,
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
                "source_dataset_root": str(source_root),
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "scene_dir": str(scene_dir),
                "source_usd": str(scene_dir / "start_result_raw.usd"),
                "source_usd_variant": "start_result_raw.usd",
                "scratch_scene_root": str(scratch_scene_root),
                "converted_usd": str(scratch_scene_root / "start_result_raw_noMDL.usd"),
                "conversion_command": f"./scripts/isaac_python.sh ./main.py no-mdl {scratch_scene_root / 'start_result_raw.usd'}",
            }
        ],
    }
    target_manifest = {
        "schema_version": 1,
        "episode_records": [
            {
                "mapping_status": "resolved_metadata_reference_to_prim",
                "source_dataset_root": str(source_root),
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "stable_episode_id": "episode_a",
                "object_category": "bottle",
                "object_instance_id": "bottle/model_hash_a_0",
                "target_prim_path": "/Root/Meshes/Furnitures/bottle/model_hash_a_0",
                "reference_asset_path": "models/object/others/bottle/hash_a/instance.usd",
                "resolved_model_path": str(resolved_model_path),
            },
            {
                "mapping_status": "resolved_metadata_reference_to_prim",
                "source_dataset_root": str(source_root),
                "source_scene_id": "scene_a_usd",
                "source_scene_split": "home_scenes",
                "stable_episode_id": "episode_b",
                "object_category": "bottle",
                "object_instance_id": "bottle/model_hash_a_0",
                "target_prim_path": "/Root/Meshes/Furnitures/bottle/model_hash_a_0",
                "reference_asset_path": "models/object/others/bottle/hash_a/instance.usd",
                "resolved_model_path": str(resolved_model_path),
            },
        ],
    }
    paths = {
        "source_root": source_root,
        "scratch_root": scratch_root,
        "scene_dir": scene_dir,
        "model_root": model_root,
        "materials_root": materials_root,
        "scratch_scene_root": scratch_scene_root,
    }
    return source_manifest, target_manifest, paths


def test_module_imports_without_pxr(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    for module_name in list(sys.modules):
        if module_name == "pxr" or module_name.startswith("pxr."):
            sys.modules.pop(module_name)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pxr" or name.startswith("pxr."):
            raise AssertionError("plan_reference_closure.py must not import pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = load_closure_module()

    assert hasattr(module, "build_reference_closure_plan")
    assert not any(module_name == "pxr" or module_name.startswith("pxr.") for module_name in sys.modules)


def test_reference_closure_plan_deduplicates_targets_and_models(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, paths = make_manifests(tmp_path)

    plan = module.build_reference_closure_plan(source_manifest, target_manifest)

    assert plan["summary"]["episode_record_count"] == 2
    assert plan["summary"]["resolved_episode_record_count"] == 2
    assert plan["summary"]["unique_target_count"] == 1
    assert plan["summary"]["duplicate_episode_target_count"] == 1
    assert plan["summary"]["unique_model_root_count"] == 1
    assert [action["kind"] for action in plan["actions"]] == ["scene_dir", "target_model_root"]
    model_action = plan["actions"][1]
    assert model_action["src"] == str(paths["model_root"].resolve())
    assert model_action["dst"] == str((paths["scratch_root"] / paths["model_root"].relative_to(paths["source_root"])).resolve())
    assert plan["conversion_commands"] == [
        f"./scripts/isaac_python.sh ./main.py no-mdl {paths['scratch_scene_root'] / 'start_result_raw.usd'}"
    ]


def test_reference_closure_plan_reports_uncovered_split_material_symlink(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path)

    plan = module.build_reference_closure_plan(source_manifest, target_manifest)

    assert plan["summary"]["uncovered_symlink_target_count"] == 1
    assert plan["summary"]["material_closure_status"] == "requires_material_dependency_resolution"
    gap = plan["uncovered_symlink_targets"][0]
    assert gap["link_relative_path"].endswith("models/object/others/bottle/hash_a/Materials")
    assert gap["projected_target_relative_path"].endswith("home_scenes/Materials")
    assert gap["target_inside_scratch_root"] is True
    assert gap["target_covered_by_planned_actions"] is False


@pytest.mark.parametrize(
    ("materials_entry", "expected_warning"),
    [
        ("symlink", "materials_symlink_escapes_selected_root"),
        ("pointer_file", "materials_pointer_file_not_usd_resolvable"),
        ("missing", "materials_entry_missing_requires_usd_dependency_scan"),
    ],
)
def test_reference_closure_plan_classifies_model_materials_entry(
    tmp_path: Path, materials_entry: str, expected_warning: str
) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path, materials_entry=materials_entry)

    plan = module.build_reference_closure_plan(source_manifest, target_manifest)

    assert plan["summary"]["model_root_only_materialization_safe"] is False
    assert plan["summary"]["materials_entry_counts"][materials_entry] == 1
    action = next(action for action in plan["actions"] if action["kind"] == "target_model_root")
    assert action["materials_entry"]["type"] == materials_entry
    assert expected_warning in action["warnings"]
    assert "unresolved_split_level_material_closure" in action["warnings"]
    assert action["required_external_resource_roots"][0]["resource_name"] == "Materials"


def test_reference_closure_plan_rejects_model_paths_outside_source_root(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path, outside_model=True)

    with pytest.raises(ValueError, match="resolved_model_path must be inside source_root"):
        module.build_reference_closure_plan(source_manifest, target_manifest)


def test_reference_closure_plan_rejects_scene_source_usd_outside_source_root(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path)
    source_manifest["scenes"][0]["source_usd"] = str(tmp_path / "outside_source.usd")

    with pytest.raises(ValueError, match="source_usd must be inside source_root"):
        module.build_reference_closure_plan(source_manifest, target_manifest)


def test_reference_closure_plan_rejects_converted_usd_outside_scratch_root(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path)
    source_manifest["scenes"][0]["converted_usd"] = str(tmp_path / "converted_noMDL.usd")

    with pytest.raises(ValueError, match="converted_usd must be inside scratch_root"):
        module.build_reference_closure_plan(source_manifest, target_manifest)


def test_reference_closure_plan_rejects_source_usd_variant_path_traversal(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path)
    source_manifest["scenes"][0]["source_usd_variant"] = "../escape.usd"

    with pytest.raises(ValueError, match="source_usd_variant must be a relative file name"):
        module.build_reference_closure_plan(source_manifest, target_manifest)


def test_reference_closure_plan_derives_conversion_command_from_scratch_input(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, paths = make_manifests(tmp_path)
    source_manifest["scenes"][0]["conversion_command"] = "./scripts/isaac_python.sh ./main.py no-mdl /source/bad.usd"

    plan = module.build_reference_closure_plan(source_manifest, target_manifest)

    assert plan["conversion_commands"] == [
        f"./scripts/isaac_python.sh ./main.py no-mdl {paths['scratch_scene_root'] / 'start_result_raw.usd'}"
    ]


def test_reference_closure_plan_rejects_target_record_source_root_mismatch(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path)
    target_manifest["episode_records"][0]["source_dataset_root"] = str(tmp_path / "other-source")

    with pytest.raises(ValueError, match="target record source_dataset_root must match source_root"):
        module.build_reference_closure_plan(source_manifest, target_manifest)


def test_reference_closure_plan_rejects_target_manifest_dataset_role_mismatch(tmp_path: Path) -> None:
    module = load_closure_module()
    source_manifest, target_manifest, _paths = make_manifests(tmp_path)
    target_manifest["dataset_roles"] = {
        "benchmark_source_dataset": {"local_root": str(tmp_path / "other-source")},
    }

    with pytest.raises(ValueError, match="target_manifest benchmark source root must match source_manifest"):
        module.build_reference_closure_plan(source_manifest, target_manifest)
