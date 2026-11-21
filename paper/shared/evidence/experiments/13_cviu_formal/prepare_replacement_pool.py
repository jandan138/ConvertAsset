"""Preserve the frozen scene and reserve order when original-only QA fails."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ready',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--previous-jobs',type=Path,nargs='+',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
review=json.loads(a.review.read_text());sid=review['scene_id'];missing=[r for r in review['targets'] if not any(f.get('proposed_selected') for f in r['frames'])]
if not missing:raise ValueError('No failed targets to replace')
row=next(r for r in json.loads(a.ready.read_text())['scenes'] if r['scene_id']==sid);original_pool=Path(row['target_pool']);pool=json.loads(original_pool.read_text());seen=set()
for path in a.previous_jobs:
 data=json.loads(path.read_text());seen.update(r['prim'] for r in data['selected']);seen.update(r['prim'] for r in data['excluded'])
remaining=[r for r in pool['selected']+pool['reserve'] if r['prim'] not in seen]
if len(remaining)<len(missing):raise ValueError('Insufficient remaining reserves')
a.out.mkdir(parents=True,exist_ok=False);pool['selected']=[];pool['reserve']=remaining
(a.out/'target_pool.json').write_text(json.dumps(pool,indent=2)+'\n');row['target_pool']=str((a.out/'target_pool.json').resolve());(a.out/'scene.json').write_text(json.dumps(row,indent=2)+'\n')
(a.out/'selection_receipt.json').write_text(json.dumps({'scene_id':sid,'review':str(a.review),'review_sha256':hashlib.sha256(a.review.read_bytes()).hexdigest(),'source_pool':str(original_pool),'source_pool_sha256':hashlib.sha256(original_pool.read_bytes()).hexdigest(),'failed_target_prims':[r['target_prim'] for r in missing],'target_count':len(missing),'remaining_reserves':len(remaining),'rule':'Preserve prior reserve order; selection uses original images only.'},indent=2)+'\n')
print('Remaining reserves:',len(remaining),'requested replacements:',len(missing))
