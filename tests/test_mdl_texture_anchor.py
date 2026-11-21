"""Real USD regression; run with scripts/isaac_python.sh (no renderer required)."""
import tempfile
import unittest
from pathlib import Path
from pxr import Usd, UsdShade, Sdf
from convert_asset.no_mdl.materials import ensure_preview, copy_textures

class TextureAnchorTest(unittest.TestCase):
    def test_mdl_relative_and_absolute_texture_paths(self):
        for absolute in [False, True]:
            with self.subTest(absolute=absolute), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); materials=root/'Materials'; materials.mkdir()
                texture=materials/'Textures'/'normal.png'; texture.parent.mkdir(); texture.write_bytes(b'texture fixture')
                # A same-named wrong-directory texture must never win.
                wrong=root/'Textures'/'normal.png'; wrong.parent.mkdir(); wrong.write_bytes(b'wrong')
                texpath=str(texture) if absolute else './Textures/normal.png'
                mdl=materials/'material.mdl'
                mdl.write_text('float4 normal = tex::lookup_float4(texture_2d("'+texpath+'"));')
                stage=Usd.Stage.CreateNew(str(root/'scene.usda'))
                mat=UsdShade.Material.Define(stage,'/Material')
                shader=UsdShade.Shader.Define(stage,'/Material/MDL')
                shader.GetPrim().CreateAttribute('info:mdl:sourceAsset',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath('./Materials/material.mdl'))
                ensure_preview(stage,mat)
                filled,*_=copy_textures(stage,shader,mat,dst_layer_dir=str(root))
                self.assertTrue(filled.get('Normal'))
                attr=stage.GetPrimAtPath('/Material/PreviewNetwork/Tex_Normal').GetAttribute('inputs:file')
                value=attr.Get().path
                self.assertEqual((root/value).resolve(),texture.resolve())
                self.assertEqual(Path(value).is_absolute(),absolute)

if __name__=='__main__':unittest.main()
