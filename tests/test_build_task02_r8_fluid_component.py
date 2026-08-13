from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_task02_r8_fluid_component.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("build_task02_r8_fluid_component", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _asset_package(root: Path, name: str, entry: str) -> Path:
    package = root / name
    package.mkdir(parents=True)
    (package / "asset.usd").write_text(
        '#usda 1.0\n(defaultPrim="World")\ndef Xform "World" { def Xform "'
        + entry
        + '" {} }\n',
        encoding="utf-8",
    )
    (package / "evidence").mkdir()
    (package / "evidence/manifest.json").write_text(
        json.dumps({"overall_status": "pass", "asset_id": name}), encoding="utf-8"
    )
    return package


def test_builder_creates_deterministic_548_particle_component(tmp_path: Path) -> None:
    module = _module()
    cylinder = _asset_package(tmp_path, "cylinder", "GraduatedCylinder250ml")
    beaker = _asset_package(tmp_path, "beaker", "Beaker325ml")

    out = tmp_path / "out"
    result = module.build(cylinder_package=cylinder, beaker_package=beaker, out=out)

    points = json.loads((out / "authored_particle_points.json").read_text())
    profile = json.loads((out / "interactive_fluid_scene_profile.json").read_text())
    manifest = json.loads((out / "evidence/manifest.json").read_text())
    assert len(points) == 548
    assert profile["particles"]["count"] == 548
    assert profile["particles"]["authored_points_sha256"] == module._sha(
        out / "authored_particle_points.json"
    )
    assert profile["entrypoints"]["qualification_30hz"]["physics_hz"] == 30
    assert profile["entrypoints"]["consumer_60hz"]["physics_hz"] == 60
    assert manifest["overall_status"] == "candidate_pending_runtime"
    assert result["consumer"].is_file()


def test_component_uses_visual_mesh_convex_decomposition_and_disables_old_proxies(
    tmp_path: Path,
) -> None:
    module = _module()
    cylinder = _asset_package(tmp_path, "cylinder", "GraduatedCylinder250ml")
    beaker = _asset_package(tmp_path, "beaker", "Beaker325ml")
    out = tmp_path / "out"
    module.build(cylinder_package=cylinder, beaker_package=beaker, out=out)

    text = (out / "component.usda").read_text()
    assert 'token physics:approximation = "convexDecomposition"' in text
    assert "physxConvexDecompositionCollision:errorPercentage = 10" in text
    assert "physxConvexDecompositionCollision:maxConvexHulls = 32" in text
    assert 'over "__aan_collision_proxy"' in text
    assert text.count("bool physics:collisionEnabled = 0") == 12
    assert text.count('over "wall_pos_x"') == 2
    assert "Hollow_Body_Mesh_002" in text
    assert "Beaker_Hollow_Body_Mesh" in text


def test_component_closure_is_package_relative(tmp_path: Path) -> None:
    module = _module()
    cylinder = _asset_package(tmp_path, "cylinder", "GraduatedCylinder250ml")
    beaker = _asset_package(tmp_path, "beaker", "Beaker325ml")
    out = tmp_path / "out"
    module.build(cylinder_package=cylinder, beaker_package=beaker, out=out)

    for name in ("asset.usd", "component.usda", "qualification_30hz.usda", "consumer_60hz.usda"):
        text = (out / name).read_text()
        assert str(tmp_path) not in text
        assert "@/" not in text
    assert (out / "deps/source_container/asset.usd").is_file()
    assert (out / "deps/target_container/asset.usd").is_file()
