"""Run with Isaac Python: a copied scene must not retain source USD references."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/12_cviu_diagnostics/restore_pilot.py'
class RestoreGuardTests(unittest.TestCase):
 def test_relative_closure_and_absolute_escape(self):
  for absolute in [False,True]:
   with self.subTest(absolute=absolute),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);family=root/'source/home';scene=family/'scenes/S';scene.mkdir(parents=True)
    model=family/'models/object/instance.usda';model.parent.mkdir(parents=True);model.write_text('#usda 1.0\n(defaultPrim = "Asset")\ndef Xform "Asset" {}\n')
    (family/'Materials').mkdir()
    source=scene/'start_result_raw.usda';ref=str(model) if absolute else 'models/object/instance.usda'
    source.write_text('#usda 1.0\ndef Xform "Root" (prepend references = @'+ref+'@) {}\n')
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [model,source]}
    manifest=root/'manifest.json';manifest.write_text(json.dumps({'scenes':[{'scene_id':'S','original':str(source),'split':'train'}]}))
    out=root/'out';run=subprocess.run([sys.executable,str(SCRIPT),'--manifest',str(manifest),'--out',str(out),'--splits','train'],capture_output=True,text=True)
    self.assertEqual(run.returncode,1 if absolute else 0,run.stderr[-1000:])
    record=json.loads((out/'restore_report.json').read_text())['records'][0]
    self.assertEqual(bool(record['external_usd_layers']),absolute)
    self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in [model,source]})
if __name__=='__main__':unittest.main()
