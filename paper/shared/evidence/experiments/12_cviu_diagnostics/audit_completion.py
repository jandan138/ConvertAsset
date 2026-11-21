"""Audit the full three-scene goal against saved inputs, runs, labels and reports."""
import argparse,hashlib,json,re
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root
 import numpy as np
 from PIL import Image
 manifest=json.loads((root/'manifest.json').read_text());rows=manifest['records'];pairs={r['pair_id'] for r in rows};scenes={r['scene_id'] for r in rows}
 assert len(rows)==24 and len(pairs)==12 and len(scenes)==3
 lookup={(r['pair_id'],r['condition']):r for r in rows};assert len(lookup)==24
 qa=json.loads((root/'selected_qa.json').read_text())['reviews'];qa_index={(q['pair_id'],q['condition']):q for q in qa};assert len(qa_index)==24
 for scene in scenes:
  targets={r['target_prim'] for r in rows if r['scene_id']==scene};assert len(targets)==2
  for target in targets:assert len({r['view_id'] for r in rows if r['scene_id']==scene and r['target_prim']==target})==2
 for r in rows:
  for kind in ['image','mask']:assert sha(r[kind]['path'])==r[kind]['sha256']
  with Image.open(r['image']['path']) as im:assert im.size==(1024,768)
  mask=np.load(r['mask']['path'],allow_pickle=False);assert mask.dtype==np.bool_ and mask.shape==(768,1024) and mask.any()
  q=qa_index[r['pair_id'],r['condition']];assert q['verdict']=='PASS' and q['image_sha256']==r['image']['sha256'] and q['mask_sha256']==r['mask']['sha256']
  assert sha(r['capture_receipt'])==r['capture_receipt_sha256']
  receipt=json.loads(Path(r['capture_receipt']).read_text());assert receipt['target_prim']==r['target_prim'];assert sha(receipt['stage'])==r['camera_stage_sha256']
 for pair in pairs:
  o,c=lookup[pair,'original'],lookup[pair,'converted'];assert o['query']==c['query'] and o['target_prim']==c['target_prim'] and o['scene_id']==c['scene_id']
  signatures=[]
  for r in [o,c]:
   rec=json.loads(Path(r['capture_receipt']).read_text());m=re.search(r'def Camera "DiagnosticCamera"\s*\{(.*?)\n\}',Path(rec['stage']).read_text(),re.S);assert m;signatures.append(' '.join(m[1].split()))
  assert signatures[0]==signatures[1]
 stage_audit=json.loads((root/'completion_stage_audit.json').read_text());assert len(stage_audit['records'])==3
 for r in stage_audit['records']:assert r['geometry_equal'] and r['original']['meshes']==r['converted']['meshes'] and not r['original']['unresolved'] and not r['converted']['unresolved']
 campaign=json.loads((root/'inference/campaign.json').read_text());assert len(campaign['runs'])==3 and all(r['exit_code']==0 for r in campaign['runs'])
 predictions=[]
 for i in range(3):
  folder=root/'inference'/f'repeat{i}';meta=json.loads((folder/'metadata.json').read_text());assert meta['repeat']==i and meta['manifest_sha256']==sha(root/'manifest.json')
  assert sha(folder/'engine_snapshot.py')==meta['engine_sha256'];assert sha(folder/'pilot_inference_snapshot.py')==meta['runner_sha256']
  for name,digest in meta['checkpoint_config_hashes'].items():assert sha(folder/name)==digest
  run=[json.loads(l) for l in (folder/'predictions.jsonl').read_text().splitlines()];assert len(run)==24 and {(r['pair_id'],r['condition']) for r in run}==set(lookup)
  for r in run:
   assert r['status']=='ok' and r['repeat']==i
   base=lookup[r['pair_id'],r['condition']];assert r['query']==base['query'] and r['image']['sha256']==base['image']['sha256']
   m=re.fullmatch(r'\s*Point:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*',r['raw_response']);assert m
   point=[float(m[1]),float(m[2])];assert point==r['point_normalized'] and all(0<=v<1000 for v in point)
   mask=np.load(base['mask']['path'],allow_pickle=False);h,w=mask.shape
   assert bool(mask[int(point[1]*h/1000),int(point[0]*w/1000)])==r['hit']
  predictions+=run
 from analyze_pilot import summarize
 computed=summarize(predictions);saved=json.loads((root/'analysis/results.json').read_text())
 assert computed['by_repeat']==saved['by_repeat'] and computed['within_condition']==saved['within_condition'] and len(saved['cases'])==12
 assert (root/'analysis/report.md').is_file()
 repo=Path(__file__).resolve().parents[5]
 report=repo/'docs/records/2026-11-14-cviu-three-scene-pilot-results.md';tracker=repo/'paper/venues/cviu/REVIEW_RESPONSE_TRACKER.md'
 assert report.is_file() and 'E8' in tracker.read_text() and '72' in report.read_text()
 audit={'status':'PASS','scope':'Three-scene pilot goal only; full CVIU revision remains pending','requirements':{'three_restored_scene_pairs_and_geometry_audit':'PASS','two_targets_two_views_per_scene':'PASS','12_same_camera_pairs_visually_reviewed':'PASS','24_images_masks_and_hashes_verified':'PASS','72_real_predictions_three_independent_runs':'PASS','raw_responses_configs_and_script_snapshots':'PASS','independent_rescoring_matches_report':'PASS','hit_rates_directional_flips_repeat_differences_cases':'PASS','experiment_record_and_review_tracker_updated':'PASS'},'counts':{'scenes':3,'objects':6,'pairs':12,'images':24,'predictions':72},'evidence':{str(p.relative_to(root)):sha(p) for p in [root/'manifest.json',root/'selected_qa.json',root/'completion_stage_audit.json',root/'inference/campaign.json',root/'analysis/results.json',root/'analysis/report.md']},'documentation':{str(report.relative_to(repo)):sha(report),str(tracker.relative_to(repo)):sha(tracker)}}
 (root/'completion_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit['counts']),'PASS')
if __name__=='__main__':main()
