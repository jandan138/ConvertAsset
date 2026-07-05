from pathlib import Path

import pytest


pytest.importorskip("pxr")


def test_no_mdl_prunes_missing_mdl_pin_texture(tmp_path: Path) -> None:
    from pxr import Usd, UsdShade

    from convert_asset.no_mdl.processor import Processor

    scene = tmp_path / "scene.usda"
    scene.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Scope "Looks"
    {
        def Material "Soap"
        {
            token outputs:surface.connect = </World/Looks/Soap/OmniPBR.outputs:surface>
            token outputs:surface:mdl.connect = </World/Looks/Soap/OmniPBR.outputs:surface>

            def Shader "OmniPBR"
            {
                uniform token info:id = "OmniPBR"
                uniform asset info:mdl:sourceAsset = @./Materials/O.mdl@
                asset inputs:BaseColor_Tex = @./textures/missing.jpg@
                token outputs:surface
            }
        }
    }
}
""",
        encoding="utf-8",
    )

    out_path = Path(Processor().process(str(scene)))
    assert out_path.name == "scene_noMDL.usda"

    out_text = out_path.read_text(encoding="utf-8")
    assert "missing.jpg" not in out_text
    assert "inputs:file" not in out_text

    stage = Usd.Stage.Open(str(out_path))
    preview = UsdShade.Shader.Get(stage, "/World/Looks/Soap/PreviewNetwork/Tex_BaseColor")
    assert preview
    assert not preview.GetInput("file")

    surface = UsdShade.Shader.Get(stage, "/World/Looks/Soap/PreviewNetwork/PreviewSurface")
    diffuse = surface.GetInput("diffuseColor")
    assert diffuse
    assert diffuse.Get() is not None


def test_no_mdl_preserves_existing_mdl_pin_texture(tmp_path: Path) -> None:
    from pxr import Usd, UsdShade

    from convert_asset.no_mdl.processor import Processor

    texture = tmp_path / "textures" / "albedo.jpg"
    texture.parent.mkdir()
    texture.write_bytes(b"jpg")
    scene = tmp_path / "scene.usda"
    scene.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Scope "Looks"
    {
        def Material "Soap"
        {
            token outputs:surface.connect = </World/Looks/Soap/OmniPBR.outputs:surface>
            token outputs:surface:mdl.connect = </World/Looks/Soap/OmniPBR.outputs:surface>

            def Shader "OmniPBR"
            {
                uniform token info:id = "OmniPBR"
                uniform asset info:mdl:sourceAsset = @./Materials/O.mdl@
                asset inputs:BaseColor_Tex = @./textures/albedo.jpg@
                token outputs:surface
            }
        }
    }
}
""",
        encoding="utf-8",
    )

    out_path = Path(Processor().process(str(scene)))
    out_text = out_path.read_text(encoding="utf-8")
    assert "textures/albedo.jpg" in out_text

    stage = Usd.Stage.Open(str(out_path))
    preview = UsdShade.Shader.Get(stage, "/World/Looks/Soap/PreviewNetwork/Tex_BaseColor")
    assert preview.GetInput("file").Get().path == "textures/albedo.jpg"


def test_no_mdl_preserves_existing_mdl_text_texture_relative_to_mdl_file(tmp_path: Path) -> None:
    from pxr import Usd, UsdShade

    from convert_asset.no_mdl.processor import Processor

    materials = tmp_path / "Materials"
    textures = tmp_path / "textures"
    materials.mkdir()
    textures.mkdir()
    (textures / "albedo_color.png").write_bytes(b"png")
    (materials / "Root.mdl").write_text(
        'mdl 1.0;\ntexture_2d("../textures/albedo_color.png");\n',
        encoding="utf-8",
    )
    scene = tmp_path / "scene.usda"
    scene.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Scope "Looks"
    {
        def Material "Soap"
        {
            token outputs:surface.connect = </World/Looks/Soap/OmniPBR.outputs:surface>
            token outputs:surface:mdl.connect = </World/Looks/Soap/OmniPBR.outputs:surface>

            def Shader "OmniPBR"
            {
                uniform token info:id = "OmniPBR"
                uniform asset info:mdl:sourceAsset = @./Materials/Root.mdl@
                token outputs:surface
            }
        }
    }
}
""",
        encoding="utf-8",
    )

    out_path = Path(Processor().process(str(scene)))
    out_text = out_path.read_text(encoding="utf-8")
    assert "textures/albedo_color.png" in out_text

    stage = Usd.Stage.Open(str(out_path))
    preview = UsdShade.Shader.Get(stage, "/World/Looks/Soap/PreviewNetwork/Tex_BaseColor")
    assert preview.GetInput("file").Get().path == "textures/albedo_color.png"


def test_no_mdl_prunes_missing_texture_catalog_asset_attr(tmp_path: Path) -> None:
    from pxr import Usd

    from convert_asset.no_mdl.processor import Processor

    kept = tmp_path / "textures" / "kept.jpg"
    kept.parent.mkdir()
    kept.write_bytes(b"jpg")
    scene = tmp_path / "scene.usda"
    scene.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Scope "TextureCatalog"
    {
        asset texture_0 = @./textures/missing.jpg@
        asset texture_1 = @./textures/kept.jpg@
    }
}
""",
        encoding="utf-8",
    )

    out_path = Path(Processor().process(str(scene)))
    out_text = out_path.read_text(encoding="utf-8")
    assert "missing.jpg" not in out_text
    assert "textures/kept.jpg" in out_text

    stage = Usd.Stage.Open(str(out_path))
    catalog = stage.GetPrimAtPath("/World/TextureCatalog")
    assert not catalog.HasAttribute("texture_0")
    assert catalog.GetAttribute("texture_1").Get().path.endswith("textures/kept.jpg")


def test_no_mdl_prunes_missing_tx_texture_catalog_asset_attr(tmp_path: Path) -> None:
    from pxr import Usd

    from convert_asset.no_mdl.processor import Processor

    scene = tmp_path / "scene.usda"
    scene.write_text(
        """#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Scope "TextureCatalog"
    {
        asset texture_0 = @./textures/missing.tx@
    }
}
""",
        encoding="utf-8",
    )

    out_path = Path(Processor().process(str(scene)))
    out_text = out_path.read_text(encoding="utf-8")
    assert "missing.tx" not in out_text

    stage = Usd.Stage.Open(str(out_path))
    catalog = stage.GetPrimAtPath("/World/TextureCatalog")
    assert not catalog.HasAttribute("texture_0")
