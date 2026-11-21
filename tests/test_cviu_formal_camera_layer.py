"""Isaac Python regression for expired Sdf handles after releasing a staging Stage."""
import importlib.util,tempfile,unittest
from pathlib import Path
from pxr import Sdf,Usd,UsdGeom
p=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal/prepare_views.py';spec=importlib.util.spec_from_file_location('formal_views',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CameraLayerTest(unittest.TestCase):
 def test_reopen_layer_after_stage_release(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'camera.usda';stage=Usd.Stage.CreateNew(str(path));UsdGeom.Camera.Define(stage,'/DiagnosticCamera').CreateFocalLengthAttr().Set(24)
   layer=stage.GetRootLayer();layer.Save();del stage
   self.assertFalse(bool(layer))
   source=Path(tmp)/'not_loaded.usda';m.attach_base_layer(path,source)
   reopened=Sdf.Layer.FindOrOpen(str(path));self.assertEqual(list(reopened.subLayerPaths),[str(source)]);self.assertEqual(reopened.GetAttributeAtPath('/DiagnosticCamera.focalLength').default,24)
if __name__=='__main__':unittest.main()
