from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/build_task02_r82_fluid_component.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("build_task02_r82", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _asset(root: Path, name: str, entry: str, *, topology: bool = False) -> Path:
    package = root / name
    package.mkdir()
    (package / "asset.usd").write_text(
        '#usda 1.0\n(defaultPrim="World")\ndef Xform "World" { def Xform "'
        + entry
        + '" {} }\n',
        encoding="utf-8",
    )
    (package / "evidence").mkdir()
    (package / "evidence/manifest.json").write_text(
        json.dumps({"overall_status": "pass"}), encoding="utf-8"
    )
    if topology:
        (package / "evidence/container_topology.json").write_text(
            json.dumps({"result": {"boundary_edge_count": 0}}), encoding="utf-8"
        )
    return package


def test_r82_uses_v3_closed_wall_contract(tmp_path: Path) -> None:
    module = _module()
    cylinder = _asset(tmp_path, "cylinder", "GraduatedCylinder250ml", topology=True)
    beaker = _asset(tmp_path, "beaker", "Beaker325ml")

    result = module.build(
        cylinder_package=cylinder, beaker_package=beaker, out=tmp_path / "out"
    )

    profile = json.loads(result["profile"].read_text(encoding="utf-8"))
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
    assert profile["schema_version"] == "aan.interactive_fluid_scene_profile.v3"
    assert profile["container_collision"]["strategy"] == (
        "visual_mesh_closed_wall_convex_decomposition"
    )
    assert all(
        mesh["render_visible"] for mesh in profile["container_collision"]["meshes"]
    )
    assert profile["qualification"]["required_cold_runs"] == 3
    assert manifest["package_id"].endswith("r82")
    assert (tmp_path / "out/evidence/source_container_topology.json").is_file()
    assert "voxelResolution = 500000" in result["component"].read_text()
    assert "PhysxSceneAPI" in result["qualification"].read_text()
