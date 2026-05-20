import builtins
import importlib.util
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py"
)


def load_closure_module():
    spec = importlib.util.spec_from_file_location("grscenes_material_dependency_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_reference_plan(
    tmp_path: Path,
    *,
    duplicate_model: bool = False,
    missing_texture: bool = False,
    materials_entry: str = "missing",
) -> tuple[dict, dict[str, Path]]:
    source_root = tmp_path / "source"
    scratch_root = tmp_path / "scratch"
    split_root = source_root / "scenes/GRScenes-100/home_scenes"
    materials_root = split_root / "Materials"
    model_root = split_root / "models/object/others/cup/hash_a"
    model_b_root = split_root / "models/object/others/cup/hash_b"

    materials_root.joinpath("Textures").mkdir(parents=True)
    model_root.mkdir(parents=True)
    if duplicate_model:
        model_b_root.mkdir(parents=True)
    if materials_entry == "pointer_file":
        (model_root / "Materials").write_text("../../../../../Materials\n", encoding="utf-8")
    elif materials_entry != "missing":
        raise ValueError(materials_entry)

    (model_root / "instance.usd").write_text(
        '#usda 1.0\nasset inputs:sourceAsset = @./Materials/cup.mdl@\n',
        encoding="utf-8",
    )
    if duplicate_model:
        (model_b_root / "instance.usd").write_text(
            '#usda 1.0\nasset inputs:sourceAsset = @./Materials/cup.mdl@\n',
            encoding="utf-8",
        )

    texture_name = "missing.png" if missing_texture else "cup.png"
    (materials_root / "cup.mdl").write_text(
        f"mdl 1.0;\ntexture_2d('{texture_name}', @./Textures/{texture_name}@);\n",
        encoding="utf-8",
    )
    if not missing_texture:
        (materials_root / "Textures/cup.png").write_bytes(b"png")

    def action_for(root: Path, scene_id: str) -> dict:
        return {
            "kind": "target_model_root",
            "src": str(root),
            "dst": str(scratch_root / root.relative_to(source_root)),
            "copy_mode": "hardlink",
            "split_root": str(split_root),
            "source_relative_path": root.relative_to(source_root).as_posix(),
            "scratch_relative_path": (root.relative_to(source_root)).as_posix(),
            "materials_entry": {
                "path": str(root / "Materials"),
                "type": materials_entry,
                "resolved_path": str(materials_root),
                "target_scope": "inside_split_root_outside_model_root",
            },
            "targets": [
                {
                    "source_scene_id": scene_id,
                    "object_instance_id": f"cup/{root.name}_0",
                    "target_prim_path": f"/Root/Meshes/Furnitures/cup/{root.name}_0",
                    "resolved_model_path": str(root / "instance.usd"),
                }
            ],
        }

    actions = [action_for(model_root, "scene_a_usd")]
    if duplicate_model:
        actions.append(action_for(model_b_root, "scene_b_usd"))

    reference_plan = {
        "schema_version": 1,
        "status": "planned_reference_closure",
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "actions": actions,
    }
    paths = {
        "source_root": source_root,
        "scratch_root": scratch_root,
        "split_root": split_root,
        "materials_root": materials_root,
        "model_root": model_root,
        "model_b_root": model_b_root,
    }
    return reference_plan, paths


def test_module_imports_without_pxr(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    for module_name in list(sys.modules):
        if module_name == "pxr" or module_name.startswith("pxr."):
            sys.modules.pop(module_name)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pxr" or name.startswith("pxr."):
            raise AssertionError("plan_material_dependency_closure.py must not import pxr")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = load_closure_module()

    assert hasattr(module, "build_material_dependency_closure_plan")
    assert not any(module_name == "pxr" or module_name.startswith("pxr.") for module_name in sys.modules)


def test_text_backend_recovers_material_subset_without_copying_full_materials_root(tmp_path: Path) -> None:
    module = load_closure_module()
    reference_plan, paths = make_reference_plan(tmp_path)

    plan = module.build_material_dependency_closure_plan(reference_plan, dependency_backend="text")

    assert plan["summary"]["model_root_count"] == 1
    assert plan["summary"]["required_material_asset_count"] == 2
    assert plan["summary"]["missing_material_asset_count"] == 0
    assert plan["summary"]["safe_to_materialize_selected_materials"] is True
    assert plan["summary"]["requires_materials_entry_repair_before_nomdl"] is True
    assert plan["summary"]["ready_for_nomdl_after_material_file_actions"] is False
    assert plan["summary"]["materials_entry_repair_action_count"] == 1
    assert plan["summary"]["material_closure_status"] == "selected_material_dependencies_resolved_with_entry_repairs_required"
    assert plan["summary"]["warning_counts"]["scratch_materials_entry_repair_required"] == 1
    assert plan["summary"]["warning_counts"]["usd_dependency_unresolved"] == 1
    assert [action["kind"] for action in plan["material_file_actions"]] == [
        "material_asset_file",
        "material_asset_file",
    ]
    assert {Path(action["src"]).name for action in plan["material_file_actions"]} == {
        "cup.mdl",
        "cup.png",
    }
    assert not any(action["src"] == str(paths["materials_root"]) for action in plan["material_file_actions"])
    assert all(action["dst"].startswith(str(paths["scratch_root"])) for action in plan["material_file_actions"])
    assert plan["materials_entry_repair_actions"] == [
        {
            "kind": "model_materials_entry_repair",
            "mode": "create_relative_symlink",
            "dst": str(paths["scratch_root"] / paths["model_root"].relative_to(paths["source_root"]) / "Materials"),
            "target_text": "../../../../../Materials",
            "model_root": str(paths["model_root"].resolve()),
            "scratch_model_root": str(
                (paths["scratch_root"] / paths["model_root"].relative_to(paths["source_root"])).resolve()
            ),
            "scratch_split_materials_root": str(
                (paths["scratch_root"] / paths["materials_root"].relative_to(paths["source_root"])).resolve()
            ),
            "source_entry_type": "missing",
            "reason": "model_materials_entry_must_resolve_to_split_materials_in_scratch",
        }
    ]


def test_material_dependency_closure_deduplicates_shared_material_files(tmp_path: Path) -> None:
    module = load_closure_module()
    reference_plan, _paths = make_reference_plan(tmp_path, duplicate_model=True)

    plan = module.build_material_dependency_closure_plan(reference_plan, dependency_backend="text")

    assert plan["summary"]["model_root_count"] == 2
    assert plan["summary"]["required_material_asset_count"] == 2
    assert plan["summary"]["materials_entry_repair_action_count"] == 2
    mdl_action = next(action for action in plan["material_file_actions"] if action["src"].endswith("cup.mdl"))
    assert mdl_action["referenced_by_model_root_count"] == 2
    assert plan["summary"]["safe_to_materialize_selected_materials"] is True


def test_material_dependency_closure_plans_pointer_file_repair_mode(tmp_path: Path) -> None:
    module = load_closure_module()
    reference_plan, paths = make_reference_plan(tmp_path, materials_entry="pointer_file")

    plan = module.build_material_dependency_closure_plan(reference_plan, dependency_backend="text")

    assert plan["summary"]["materials_entry_repair_action_count"] == 1
    assert plan["materials_entry_repair_actions"][0]["mode"] == "replace_pointer_file_with_relative_symlink"
    assert plan["materials_entry_repair_actions"][0]["dst"] == str(
        paths["scratch_root"] / paths["model_root"].relative_to(paths["source_root"]) / "Materials"
    )
    assert "materials_pointer_file_not_usd_resolvable" in plan["models"][0]["warnings"]


def test_material_dependency_closure_reports_missing_recovered_textures(tmp_path: Path) -> None:
    module = load_closure_module()
    reference_plan, _paths = make_reference_plan(tmp_path, missing_texture=True)

    plan = module.build_material_dependency_closure_plan(reference_plan, dependency_backend="text")

    assert plan["summary"]["required_material_asset_count"] == 1
    assert plan["summary"]["missing_material_asset_count"] == 1
    assert plan["summary"]["safe_to_materialize_selected_materials"] is False
    model = plan["models"][0]
    assert model["missing_material_assets"][0]["recovered_source_path"].endswith("Materials/Textures/missing.png")
    assert "missing_material_dependency_after_split_recovery" in model["warnings"]
    assert "scratch_materials_entry_repair_required" in model["warnings"]


def test_material_dependency_closure_rejects_unrelated_materials_tail_recovery(tmp_path: Path) -> None:
    module = load_closure_module()
    reference_plan, paths = make_reference_plan(tmp_path)
    outside_material = tmp_path / "outside/Materials/cup.mdl"
    (paths["model_root"] / "instance.usd").write_text(
        f"#usda 1.0\nasset inputs:sourceAsset = @{outside_material}@\n",
        encoding="utf-8",
    )

    plan = module.build_material_dependency_closure_plan(reference_plan, dependency_backend="text")

    assert plan["summary"]["required_material_asset_count"] == 0
    assert plan["summary"]["unresolved_non_material_asset_count"] == 1
    assert plan["summary"]["safe_to_materialize_selected_materials"] is False
    assert "unresolved_non_material_dependency" in plan["models"][0]["warnings"]


def test_pxr_backend_anchors_relative_unresolved_paths_to_root_asset_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_closure_module()
    reference_plan, paths = make_reference_plan(tmp_path)

    class FakeUsdUtils:
        @staticmethod
        def ComputeAllDependencies(_root_asset: str):
            return ([], [], ["./Materials/cup.mdl"])

    fake_pxr = types.ModuleType("pxr")
    fake_pxr.UsdUtils = FakeUsdUtils
    monkeypatch.setitem(sys.modules, "pxr", fake_pxr)

    plan = module.build_material_dependency_closure_plan(reference_plan, dependency_backend="pxr")

    model_asset = next(
        asset for asset in plan["models"][0]["required_material_assets"] if asset["source_path"].endswith("cup.mdl")
    )
    assert model_asset["computed_asset_path"] == str(
        (paths["model_root"] / "Materials/cup.mdl").resolve(strict=False)
    )
    assert model_asset["source_path"] == str((paths["materials_root"] / "cup.mdl").resolve())


def test_material_dependency_closure_rejects_model_action_outside_source_root(tmp_path: Path) -> None:
    module = load_closure_module()
    reference_plan, _paths = make_reference_plan(tmp_path)
    outside_root = tmp_path / "outside/model"
    outside_root.mkdir(parents=True)
    (outside_root / "instance.usd").write_text("#usda 1.0\n", encoding="utf-8")
    reference_plan["actions"][0]["src"] = str(outside_root)
    reference_plan["actions"][0]["targets"][0]["resolved_model_path"] = str(outside_root / "instance.usd")

    with pytest.raises(ValueError, match="model action src must be inside source_root"):
        module.build_material_dependency_closure_plan(reference_plan, dependency_backend="text")
