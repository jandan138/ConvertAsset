from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.build_scientific_workbench_standard_table import (
    TABLETOP_DIFFUSE_COLOR,
    TABLETOP_ROUGHNESS,
    author_workbench_table_visual,
    build,
    workbench_table_visual_overlay_text,
)


def test_workbench_table_visual_overlay_hides_body_and_binds_opaque_gray() -> None:
    text = workbench_table_visual_overlay_text()

    assert 'over "Body" (active = false)' in text
    assert 'def Material "WorkbenchTableTop"' in text
    assert 'uniform token info:id = "UsdPreviewSurface"' in text
    assert "color3f inputs:diffuseColor = (0.70, 0.72, 0.74)" in text
    assert "float inputs:metallic = 0" in text
    assert "float inputs:opacity = 1" in text
    assert "float inputs:roughness = 0.40" in text
    assert 'over "mesh"' in text
    assert "rel material:binding = </World/table/WorkbenchTableTop>" in text
    assert 'bindMaterialAs = "strongerThanDescendants"' in text
    assert "Plastic_Thick_Translucent" not in text
    assert "__aan_static_support_proxy" not in text
    assert TABLETOP_DIFFUSE_COLOR == (0.70, 0.72, 0.74)
    assert TABLETOP_ROUGHNESS == 0.40


def test_author_workbench_table_visual_composes_over_facade(tmp_path: Path) -> None:
    facade = tmp_path / "facade" / "facade.usda"
    facade.parent.mkdir(parents=True)
    facade.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{
    def Xform "table"
    {
        def Xform "Body" {}
        def Xform "Surface"
        {
            def Xform "Source"
            {
                def Mesh "mesh" {}
            }
        }
    }
}
""",
        encoding="utf-8",
    )

    overlay, source = author_workbench_table_visual(facade_path=facade, out=tmp_path)

    assert overlay == tmp_path / "overlays" / "workbench_table_visual.usda"
    assert source == tmp_path / "source.usda"
    source_text = source.read_text(encoding="utf-8")
    assert "@overlays/workbench_table_visual.usda@" in source_text
    assert "@facade/facade.usda@" in source_text

    from pxr import Usd, UsdShade  # type: ignore

    stage = Usd.Stage.Open(str(source))
    assert stage is not None
    assert not stage.GetPrimAtPath("/World/table/Body").IsActive()
    shader = stage.GetPrimAtPath("/World/table/WorkbenchTableTop/Preview")
    assert shader.GetAttribute("info:id").Get() == "UsdPreviewSurface"
    assert tuple(shader.GetAttribute("inputs:diffuseColor").Get()) == pytest.approx(
        (0.70, 0.72, 0.74)
    )
    mesh = stage.GetPrimAtPath("/World/table/Surface/Source/mesh")
    binding = UsdShade.MaterialBindingAPI(mesh)
    assert str(binding.GetDirectBinding().GetMaterialPath()) == "/World/table/WorkbenchTableTop"


def test_build_rebinds_static_support_profile_to_composed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "lab.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    profile = tmp_path / "facade.json"
    profile.write_text("{}\n", encoding="utf-8")
    facade = tmp_path / "out" / "facade" / "facade.usda"
    facade.parent.mkdir(parents=True)
    facade.write_text(
        '#usda 1.0\n(defaultPrim = "World")\ndef Xform "World" { def Xform "table" {} }\n',
        encoding="utf-8",
    )

    class _Result:
        facade_path = facade

    monkeypatch.setattr(
        "scripts.build_scientific_workbench_standard_table.build_component_facade",
        lambda *_args, **_kwargs: _Result(),
    )

    composed, support = build(source, profile, tmp_path / "out")

    payload = json.loads(support.read_text(encoding="utf-8"))
    assert composed == tmp_path / "out" / "source.usda"
    assert payload["source_binding"]["sha256"] == sha256(composed.read_bytes()).hexdigest()
    assert payload["revision"] == "r2"
    assert payload["source_collider_prim"] is None
