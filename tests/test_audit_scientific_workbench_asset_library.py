from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/audit_scientific_workbench_asset_library.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("audit_workbench_assets", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_catalog_has_29_unique_single_assets_and_locked_role_split() -> None:
    module = _module()
    catalog = module.CATALOG

    assert len(catalog) == 29
    assert len({item.asset_id for item in catalog}) == 29
    assert len({item.source for item in catalog}) == 29
    assert sum(item.phase == 1 for item in catalog) == 13
    assert sum(item.phase == 2 for item in catalog) == 16
    assert sum(item.role == "liquid_container" for item in catalog) == 12
    assert sum(item.role == "liquid_conduit" for item in catalog) == 1
    assert all(not item.source.startswith("07_组合场景与视频/") for item in catalog)


def test_primary_mesh_selector_uses_explicit_suffix_or_largest_mesh() -> None:
    module = _module()
    meshes = [
        {"prim_path": "/root/Body", "face_count": 12, "point_count": 20},
        {"prim_path": "/root/Label", "face_count": 200, "point_count": 220},
    ]

    assert module._select_primary(meshes, "/Body")["prim_path"] == "/root/Body"
    assert module._select_primary(meshes, None)["prim_path"] == "/root/Label"
