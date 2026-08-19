from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from convert_asset.asset_application_normalizer.visual_material_profile import (
    apply_visual_material_profile,
    load_visual_material_profile,
)
from convert_asset.asset_application_normalizer.package_layout import TargetPackageLayout


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_profile(path: Path, source: Path, mdl: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "aan.visual_material_profile.v1",
                "profile_id": "scientific_workbench.beaker.transparent_glass",
                "revision": "r1",
                "source_binding": {"sha256": _sha256(source)},
                "override": {
                    "kind": "mdl_glass",
                    "source_mdl": str(mdl),
                    "source_sub_identifier": "OmniGlass",
                    "material_name": "TransparentGlass",
                    "binding_targets": ["/World/Beaker/Visual/Source/mesh"],
                    "claim_boundary": "Intentional visual compatibility override; physics is unchanged.",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_preview_surface_profile(path: Path, source: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "aan.visual_material_profile.v1",
                "profile_id": "scientific_workbench.centrifuge_tube_cap.red",
                "revision": "r1",
                "source_binding": {"sha256": _sha256(source)},
                "override": {
                    "kind": "usd_preview_surface",
                    "material_name": "RedPolypropylene",
                    "binding_targets": ["/World/Cap/Visual/Source/mesh"],
                    "diffuse_color": [0.65, 0.02, 0.02],
                    "opacity": 1.0,
                    "roughness": 0.35,
                    "metallic": 0.0,
                    "claim_boundary": "Visual color override only; physics is unchanged.",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_parameterized_glass_profile(
    path: Path, source: Path, mdl: Path, mdl_dependency: Path | None = None
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "aan.visual_material_profile.v2",
                "profile_id": "scientific_workbench.glass.render_change.v1",
                "revision": "glass_v1",
                "source_binding": {"sha256": _sha256(source)},
                "override": {
                    "kind": "mdl_glass",
                    "source_mdl": str(mdl),
                    "source_mdl_dependencies": (
                        [str(mdl_dependency)] if mdl_dependency is not None else []
                    ),
                    "source_sub_identifier": "OmniGlass",
                    "material_name": "OmniGlassRenderChangeV1",
                    "binding_targets": ["/World/Beaker/Visual/Source/mesh"],
                    "mdl_inputs": {
                        "reflection_color": {
                            "type": "color3f",
                            "value": [0.86629593, 0.97533488, 0.98841697],
                        },
                        "frosting_roughness": {"type": "float", "value": 0.0},
                        "roughness_texture_influence": {"type": "float", "value": 1.0},
                        "enable_opacity": {"type": "bool", "value": False},
                        "cutout_opacity": {"type": "float", "value": 0.0},
                    },
                    "claim_boundary": "Visual material override only; physics is unchanged.",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_loads_source_bound_transparent_glass_profile(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass.json"
    _write_profile(profile, source, mdl)

    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "pass"
    assert resolution.profile_id == "scientific_workbench.beaker.transparent_glass"
    assert resolution.source_mdl == mdl
    assert resolution.material_name == "TransparentGlass"
    assert resolution.binding_targets == ("/World/Beaker/Visual/Source/mesh",)
    assert resolution.profile_sha256 == _sha256(profile)


def test_rejects_visual_profile_when_source_binding_is_stale(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass.json"
    _write_profile(profile, source, mdl)
    source.write_text("#usda 1.0\n# changed\n", encoding="utf-8")

    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "blocked"
    assert "source sha256" in resolution.reason.lower()


def test_profile_writes_a_package_local_mdl_overlay_and_mesh_binding(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\nexport material OmniGlass() = material();\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass.json"
    _write_profile(profile, source, mdl)

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir()
    (layout.root / "base.usda").write_text(
        """#usda 1.0
def Xform \"World\"
{
    def Xform \"Beaker\"
    {
        def Xform \"Visual\"
        {
            def Xform \"Source\"
            {
                def Mesh \"mesh\" {}
            }
        }
    }
}
""",
        encoding="utf-8",
    )
    layout.root_usd.write_text(
        "#usda 1.0\n( subLayers = [ @overlays/visual_material.usda@, @base.usda@ ] )\n",
        encoding="utf-8",
    )

    result = apply_visual_material_profile(
        layout,
        profile,
        source,
        ["/World/Beaker"],
    )

    assert result.overall_status == "pass"
    assert layout.visual_material_mdl("OmniGlass.mdl").is_file()
    assert layout.visual_material_profile_json.is_file()
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(layout.root_usd))
    assert stage is not None
    mesh = stage.GetPrimAtPath("/World/Beaker/Visual/Source/mesh")
    assert mesh.GetRelationship("material:binding").GetTargets() == [
        "/World/Beaker/__aan_visual_materials/TransparentGlass"
    ]


def test_v2_profile_authors_typed_mdl_inputs_and_records_them(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\nexport material OmniGlass() = material();\n", encoding="utf-8")
    mdl_dependency = tmp_path / "OmniGlass_Opacity.mdl"
    mdl_dependency.write_text(
        "mdl 1.6;\nexport material OmniGlass_Opacity() = material();\n",
        encoding="utf-8",
    )
    profile = tmp_path / "transparent_glass_v2.json"
    _write_parameterized_glass_profile(profile, source, mdl, mdl_dependency)

    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "pass"
    assert resolution.schema_version == "aan.visual_material_profile.v2"
    assert resolution.mdl_inputs == {
        "cutout_opacity": {"type": "float", "value": 0.0},
        "enable_opacity": {"type": "bool", "value": False},
        "frosting_roughness": {"type": "float", "value": 0.0},
        "reflection_color": {
            "type": "color3f",
            "value": [0.86629593, 0.97533488, 0.98841697],
        },
        "roughness_texture_influence": {"type": "float", "value": 1.0},
    }

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir()
    (layout.root / "base.usda").write_text(
        """#usda 1.0
def Xform "World"
{
    def Xform "Beaker"
    {
        def Xform "Visual"
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
    layout.root_usd.write_text(
        "#usda 1.0\n( subLayers = [ @overlays/visual_material.usda@, @base.usda@ ] )\n",
        encoding="utf-8",
    )

    result = apply_visual_material_profile(layout, profile, source, ["/World/Beaker"])

    assert result.overall_status == "pass"
    assert layout.visual_material_mdl("OmniGlass_Opacity.mdl").is_file()
    assert result.profile_record["schema_version"] == "aan.visual_material_profile.v2"
    assert result.profile_record["mdl_inputs"] == resolution.mdl_inputs
    assert result.profile_record["package_mdl_dependencies"] == [
        {
            "package_path": "deps/mdl/OmniGlass_Opacity.mdl",
            "package_sha256": _sha256(mdl_dependency),
            "source_mdl": str(mdl_dependency),
            "source_sha256": _sha256(mdl_dependency),
        }
    ]
    from pxr import Gf, Usd, UsdShade  # type: ignore

    stage = Usd.Stage.Open(str(layout.root_usd))
    shader = UsdShade.Shader.Get(
        stage,
        "/World/Beaker/__aan_visual_materials/OmniGlassRenderChangeV1/Shader",
    )
    assert shader.GetInput("reflection_color").Get() == Gf.Vec3f(
        0.86629593, 0.97533488, 0.98841697
    )
    assert shader.GetInput("frosting_roughness").Get() == pytest.approx(0.0)
    assert shader.GetInput("roughness_texture_influence").Get() == pytest.approx(1.0)
    assert shader.GetInput("enable_opacity").Get() is False
    assert shader.GetInput("cutout_opacity").Get() == pytest.approx(0.0)


def test_v2_profile_can_bind_a_geometry_subset_without_overriding_sibling_subset(
    tmp_path: Path,
) -> None:
    source = tmp_path / "vessel.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\nexport material OmniGlass() = material();\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass_v2.json"
    _write_parameterized_glass_profile(profile, source, mdl)
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["override"]["binding_targets"] = [
        "/World/Vessel/Visual/Source/mesh/ClearGlass"
    ]
    profile.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir()
    (layout.root / "base.usda").write_text(
        '''#usda 1.0
def Xform "World"
{
    def Xform "Vessel"
    {
        def Xform "Visual"
        {
            def Xform "Source"
            {
                def Mesh "mesh"
                {
                    def GeomSubset "ClearGlass" {}
                    def GeomSubset "GroundGlass" {}
                }
            }
        }
    }
}
''',
        encoding="utf-8",
    )
    layout.root_usd.write_text(
        "#usda 1.0\n( subLayers = [ @overlays/visual_material.usda@, @base.usda@ ] )\n",
        encoding="utf-8",
    )

    result = apply_visual_material_profile(layout, profile, source, ["/World/Vessel"])

    assert result.overall_status == "pass"
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(layout.root_usd))
    clear = stage.GetPrimAtPath("/World/Vessel/Visual/Source/mesh/ClearGlass")
    ground = stage.GetPrimAtPath("/World/Vessel/Visual/Source/mesh/GroundGlass")
    assert clear.GetRelationship("material:binding").GetTargets() == [
        "/World/Vessel/__aan_visual_materials/OmniGlassRenderChangeV1"
    ]
    assert not ground.GetRelationship("material:binding").HasAuthoredTargets()


def test_v2_profile_rejects_unknown_mdl_input_type(tmp_path: Path) -> None:
    source = tmp_path / "beaker.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    mdl = tmp_path / "OmniGlass.mdl"
    mdl.write_text("mdl 1.6;\n", encoding="utf-8")
    profile = tmp_path / "transparent_glass_v2.json"
    _write_parameterized_glass_profile(profile, source, mdl)
    payload = json.loads(profile.read_text(encoding="utf-8"))
    payload["override"]["mdl_inputs"]["reflection_color"]["type"] = "vector3f"
    profile.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "blocked"
    assert "mdl_inputs.reflection_color.type" in resolution.reason


def test_profile_authors_package_local_usd_preview_surface(tmp_path: Path) -> None:
    source = tmp_path / "cap.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    profile = tmp_path / "red_cap.json"
    _write_preview_surface_profile(profile, source)
    resolution = load_visual_material_profile(profile, source)

    assert resolution.status == "pass"
    assert resolution.override_kind == "usd_preview_surface"
    assert resolution.diffuse_color == (0.65, 0.02, 0.02)

    layout = TargetPackageLayout(tmp_path / "package")
    layout.root.mkdir()
    (layout.root / "base.usda").write_text(
        """#usda 1.0
def Xform "World"
{
    def Xform "Cap"
    {
        def Xform "Visual"
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
    layout.root_usd.write_text(
        "#usda 1.0\n( subLayers = [ @overlays/visual_material.usda@, @base.usda@ ] )\n",
        encoding="utf-8",
    )

    result = apply_visual_material_profile(layout, profile, source, ["/World/Cap"])

    assert result.overall_status == "pass"
    assert result.profile_record["override_kind"] == "usd_preview_surface"
    assert "package_mdl_path" not in result.profile_record
    from pxr import Gf, Usd, UsdShade  # type: ignore

    stage = Usd.Stage.Open(str(layout.root_usd))
    material = UsdShade.Material.Get(
        stage, "/World/Cap/__aan_visual_materials/RedPolypropylene"
    )
    shader = UsdShade.Shader.Get(stage, material.GetPath().AppendChild("Shader"))
    assert shader.GetIdAttr().Get() == "UsdPreviewSurface"
    assert shader.GetInput("diffuseColor").Get() == Gf.Vec3f(0.65, 0.02, 0.02)
    assert shader.GetInput("roughness").Get() == pytest.approx(0.35)
    assert shader.GetInput("metallic").Get() == pytest.approx(0.0)
