# -*- coding: utf-8 -*-
from __future__ import annotations

from convert_asset.capture.targets import TargetConfig, list_scene_targets, resolve_target_scope


class _FakePath:
    def __init__(self, path: str) -> None:
        self.pathString = path

    def __str__(self) -> str:
        return self.pathString


class _FakePrim:
    def __init__(
        self,
        path: str,
        type_name: str = "Xform",
        *,
        active: bool = True,
        instance_proxy: bool = False,
    ) -> None:
        self._path = path
        self._type_name = type_name
        self._active = active
        self._instance_proxy = instance_proxy
        self._children: list[_FakePrim] = []

    def add(self, name: str, type_name: str = "Xform", **kwargs) -> "_FakePrim":
        child = _FakePrim(f"{self._path}/{name}", type_name, **kwargs)
        self._children.append(child)
        return child

    def GetPath(self) -> _FakePath:
        return _FakePath(self._path)

    def GetName(self) -> str:
        return self._path.rstrip("/").rsplit("/", 1)[-1]

    def GetTypeName(self) -> str:
        return self._type_name

    def GetChildren(self) -> list["_FakePrim"]:
        return list(self._children)

    def IsActive(self) -> bool:
        return self._active

    def IsInstanceProxy(self) -> bool:
        return self._instance_proxy

    def IsValid(self) -> bool:
        return True


class _InvalidPrim:
    def IsValid(self) -> bool:
        return False


class _FakeStage:
    def __init__(self, root: _FakePrim) -> None:
        self.root = root
        self._index: dict[str, _FakePrim] = {}
        self._index_prim(root)

    def _index_prim(self, prim: _FakePrim) -> None:
        self._index[str(prim.GetPath())] = prim
        for child in prim.GetChildren():
            self._index_prim(child)

    def GetPrimAtPath(self, path) -> _FakePrim | _InvalidPrim:
        return self._index.get(str(path), _InvalidPrim())

    def GetDefaultPrim(self) -> _FakePrim:
        return self.root


def fake_grscenes_stage() -> _FakeStage:
    root = _FakePrim("/Root")
    meshes = root.add("Meshes", "Scope")
    furniture = meshes.add("Furnitures", "Scope")

    chair = furniture.add("chair", "Scope")
    chair_model = chair.add("model_chairhash_0", "Xform")
    chair_inst = chair_model.add("Instance", "Scope")
    chair_inst.add("seat_mesh", "Mesh")
    chair_inst.add("back_mesh", "Mesh")
    chair.add("model_empty_1", "Xform")

    table = furniture.add("table", "Scope")
    table_model = table.add("model_tablehash_0", "Xform")
    table_model.add("SM_table", "Mesh")

    furniture.add("inactive_category", "Scope", active=False)

    base = meshes.add("Base", "Scope")
    base.add("wall", "Mesh")
    root.add("lights", "Scope").add("KeyLight", "RectLight")
    root.add("__default_setting", "Scope").add("HDR_Sphere", "Mesh")
    return _FakeStage(root)


def fake_mixed_category_stage() -> _FakeStage:
    root = _FakePrim("/Root")
    furniture = root.add("Meshes", "Scope").add("Furnitures", "Scope")
    chair_model = furniture.add("chair", "Scope").add("model_chairhash_0", "Xform")
    chair_model.add("SM_chair", "Mesh")
    direct = furniture.add("direct_object", "Xform")
    direct.add("SM_direct", "Mesh")
    return _FakeStage(root)


def fake_collision_stage() -> _FakeStage:
    root = _FakePrim("/Root")
    furniture = root.add("Meshes", "Scope").add("Furnitures", "Scope")
    a = furniture.add("a_b", "Scope").add("model_c", "Xform")
    a.add("mesh", "Mesh")
    b = furniture.add("a", "Scope").add("b_model_c", "Xform")
    b.add("mesh", "Mesh")
    return _FakeStage(root)


def test_auto_scope_prefers_direct_grscenes_furniture() -> None:
    stage = fake_grscenes_stage()

    assert resolve_target_scope(stage, "auto") == "/Root/Meshes/Furnitures"


def test_explicit_relative_scope_resolves_under_default_prim() -> None:
    stage = fake_grscenes_stage()

    assert resolve_target_scope(stage, "Meshes/Furnitures") == "/Root/Meshes/Furnitures"


def test_object_level_lists_non_empty_model_roots_only() -> None:
    stage = fake_grscenes_stage()

    targets = list_scene_targets(
        stage,
        TargetConfig(target_scope="auto", target_level="object"),
    )

    assert [target.category for target in targets] == ["chair", "table"]
    assert [target.mesh_count for target in targets] == [2, 1]
    assert all("/model_" in target.prim_path for target in targets)
    assert targets[0].target_id.endswith("chair_model_chairhash_0")


def test_mesh_level_returns_mesh_leaves_under_scope() -> None:
    stage = fake_grscenes_stage()

    targets = list_scene_targets(
        stage,
        TargetConfig(target_scope="auto", target_level="mesh"),
    )

    assert [target.level for target in targets] == ["mesh", "mesh", "mesh"]
    assert [target.name for target in targets] == ["seat_mesh", "back_mesh", "SM_table"]


def test_category_level_returns_non_empty_direct_categories() -> None:
    stage = fake_grscenes_stage()

    targets = list_scene_targets(
        stage,
        TargetConfig(target_scope="auto", target_level="category"),
    )

    assert [target.category for target in targets] == ["chair", "table"]
    assert [target.mesh_count for target in targets] == [2, 1]


def test_explicit_structural_scope_overrides_default_exclusions() -> None:
    stage = fake_grscenes_stage()

    targets = list_scene_targets(
        stage,
        TargetConfig(target_scope="/Root/Meshes/Base", target_level="mesh"),
    )

    assert [target.name for target in targets] == ["wall"]


def test_object_level_keeps_fallback_categories_when_other_categories_have_model_roots() -> None:
    stage = fake_mixed_category_stage()

    targets = list_scene_targets(
        stage,
        TargetConfig(target_scope="auto", target_level="object"),
    )

    assert [target.name for target in targets] == ["model_chairhash_0", "direct_object"]


def test_target_ids_are_deduped_after_sanitization_collision() -> None:
    stage = fake_collision_stage()

    targets = list_scene_targets(
        stage,
        TargetConfig(target_scope="auto", target_level="object"),
    )

    target_ids = [target.target_id for target in targets]
    assert len(target_ids) == len(set(target_ids))
