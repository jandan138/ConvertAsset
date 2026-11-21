"""Bind all frozen formal IDs to audited scene copies and provisional target pools."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[]
 for source in json.loads(a.inventory.read_text())['scenes']:
  folder=a.workspace/source['scene_id'];repair=folder/'remote_material_repair'
  receipt=repair/'receipt.json' if (repair/'receipt.json').exists() else folder/'receipt.json'
  result=json.loads(receipt.read_text());assert result['status']=='ready_for_target_selection'
  audit=receipt.parent/'geometry_audit.json';record=json.loads(audit.read_text())['records'][0]
  assert record['geometry_equal'] and record['original']['meshes']==record['converted']['meshes'] and not record['original']['unresolved'] and not record['converted']['unresolved']
  targets=receipt.parent/'target_pool.json';pool=json.loads(targets.read_text());assert len(pool['selected'])==8
  assert sha(source['original'])==source['original_sha256']
  rows.append({'scene_id':source['scene_id'],'family':source['family'],'split':source['split'],'original':result['restored'],'converted':result['converted'],'original_sha256':sha(result['restored']),'converted_sha256':sha(result['converted']),'scene_receipt':str(receipt),'scene_receipt_sha256':sha(receipt),'geometry_audit':str(audit),'geometry_audit_sha256':sha(audit),'target_pool':str(targets),'target_pool_sha256':sha(targets),'status':'assets_audited_targets_provisional'})
 assert len(rows)==30 and len({r['scene_id'] for r in rows})==30
 with a.out.open('x') as f:json.dump({'scene_count':30,'provisional_target_count':240,'inventory_sha256':sha(a.inventory),'scenes':rows},f,indent=2)
 print('30 audited scenes; 240 provisional targets; no image QA claimed')
if __name__=='__main__':main()
