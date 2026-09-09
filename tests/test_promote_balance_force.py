import hashlib
import json

import pytest

from scripts.promote_balance_force import promote


def test_measurement_reports_cannot_promote_a_device_without_its_load_cell(tmp_path):
    candidate=tmp_path/'candidate'
    candidate.mkdir()
    source='''#usda 1.0
def Xform "World" {
 def Xform "obj_analytical_balance" {
  def Xform "Instance" {
'''
    for name in ['Body','RightTare','WeighingPan']:
        source+=f'''   def Xform "{name}" (prepend apiSchemas = ["PhysicsRigidBodyAPI"]) {{
    float physics:mass = 0.05
   }}
'''
    source+='  }\n }\n}\n'
    asset=candidate/'asset.usda'
    asset.write_text(source)
    digest=hashlib.sha256(asset.read_bytes()).hexdigest()
    (candidate/'manifest.json').write_text(json.dumps({'configuration':{'resolution_g':.1}}))
    reports=[]
    for i,(runtime,mode) in enumerate((v,m) for v in ['4.1.0','4.5.0'] for m in ['zero','omitted','pressed']):
        path=tmp_path/f'report{i}.json'
        path.write_text(json.dumps(dict(pid=i+1,runtime=runtime,initialization=mode,
            asset_sha256=digest,status='measured',gpu=True,
            cases=[dict(error_g=0,range_g=0)]*11)))
        reports.append(path)
    with pytest.raises(ValueError,match='load.cell|articulation|topology'):
        promote(candidate,reports,tmp_path/'published')
    assert not (tmp_path/'published').exists()
