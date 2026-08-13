from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_scientific_workbench_r7_assets.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("build_scientific_workbench_r7_assets", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rack_profile_declares_six_medium_sockets_at_source_scale(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "rack.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    facade = tmp_path / "facade.usda"
    facade.write_text("#usda 1.0\n", encoding="utf-8")

    profile = module._rack_interaction(facade)

    assert profile["rigid_root"]["motion_role"] == "kinematic"
    frames = profile["named_frames"]
    assert len([name for name in frames if name.startswith("medium_socket_") and name.endswith("_aperture")]) == 6
    assert frames["medium_socket_01_aperture"]["translation_body_local_usd"] == [
        -0.08303,
        0.0,
        0.06651,
    ]
    assert frames["medium_socket_03_inserted_bottom"]["translation_body_local_usd"] == [
        -0.016606,
        0.0,
        0.0012,
    ]
    assert frames["medium_socket_06_aperture"]["translation_body_local_usd"] == [
        0.08303,
        0.0,
        0.06651,
    ]
    collider_names = {Path(collider["relative_path"]).name for collider in profile["colliders"]}
    assert "medium_socket_01_bottom" in collider_names
    assert "medium_socket_01_wall_pos_x" in collider_names
    assert "medium_socket_06_bottom" in collider_names
    assert "medium_socket_06_wall_neg_y" in collider_names
    assert "socket_0_bottom" in collider_names


def test_open_tube_body_facade_references_only_non_animated_body(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "tube.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")

    text = module._open_tube_body_facade(source)

    assert "@</root/centrifuge_tube_15ml_red_cap_ROOT/Tube_Body_Hollow>" in text
    assert "Cap_Controller" not in text
    assert "timeSamples" not in text


def test_body_visual_profile_targets_rebased_body_mesh(tmp_path: Path) -> None:
    module = _module()
    sources = {}
    for name in module.REQUIRED_SOURCE_KEYS:
        path = tmp_path / f"{name}.usda"
        path.write_text(f"#usda 1.0\n# {name}\n", encoding="utf-8")
        sources[name] = path

    result = module.build(sources=sources, out=tmp_path / "out")
    profile = json.loads(result["centrifuge_tube_15ml_body_visual"].read_text())

    assert profile["override"]["binding_targets"] == [
        "/World/CentrifugeTube15mlBody/Visual/Source/Tube_Body_Hollow_Mesh"
    ]

    interaction = json.loads(result["centrifuge_tube_15ml_body_interaction"].read_text())
    assert interaction["open_top"]["required"] is False
    assert [collider["relative_path"] for collider in interaction["colliders"]] == [
        "__aan_collision_proxy/body"
    ]
    glass_tube = json.loads(result["glass_test_tube_150mm_interaction"].read_text())
    assert glass_tube["open_top"]["required"] is False


def test_closed_context_tube_facade_preserves_full_material_namespace_without_animation(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "tube.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")

    text = module._closed_tube_facade(source)

    assert 'def Xform "Cap_Controller"' not in text
    assert "@</root>" in text
    assert "timeSamples" not in text
    assert 'def Xform "CentrifugeTube15mlClosed"' in text


def test_manifest_records_exact_source_hashes(tmp_path: Path) -> None:
    module = _module()
    sources = {}
    for name in module.REQUIRED_SOURCE_KEYS:
        path = tmp_path / f"{name}.usda"
        path.write_text(f"#usda 1.0\n# {name}\n", encoding="utf-8")
        sources[name] = path

    out = tmp_path / "out"
    result = module.build(sources=sources, out=out)
    manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))

    assert set(manifest["sources"]) == set(module.REQUIRED_SOURCE_KEYS)
    assert all(record["sha256"] for record in manifest["sources"].values())
    assert manifest["rack_layout"]["selected_medium_socket_indices"] == [1, 3, 6]
