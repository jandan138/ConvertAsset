"""Report artifact-backed cohort readiness without treating queued jobs as results."""
import argparse,datetime,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
ready=json.loads((a.raw/'ready_scenes.json').read_text())['scenes'];records=[]
for row in ready:
 sid=row['scene_id'];item={'scene_id':sid,'family':row['family'],'selected_pair_count':0,'captured_conditions':{},'technical_audit_pass':False,'final_visual_accepted':False,'qualified_input_count':0}
 selected=a.assets/'formal_selected_views_v1'/sid/'selection_receipt.json'
 if selected.exists():item['selected_pair_count']=json.loads(selected.read_text())['pair_count']
 for condition in ['original','converted']:
  capture=a.assets/'formal_selected_captures_v1'/sid;progress=capture/condition/'progress.json';marker=capture/(condition+'.exit')
  if progress.exists():
   d=json.loads(progress.read_text());item['captured_conditions'][condition]={'frames':d['completed'],'planned':d['planned'],'exit_code':int(marker.read_text().strip()) if marker.exists() else None}
 audit=a.raw/('final_capture_audit_'+sid+'.json')
 if audit.exists():
  d=json.loads(audit.read_text());item['technical_audit_pass']=not d['errors'] and len(d['pairs'])==16
 review=a.raw/'final_visual_reviews'/(sid+'.json')
 if review.exists():item['final_visual_accepted']=json.loads(review.read_text())['status']=='ACCEPTED_FINAL_PAIRS'
 inputs=a.raw/'qualified_scene_inputs'/(sid+'.json')
 if inputs.exists():
  d=json.loads(inputs.read_text())
  if d['status']=='qualified_scene_inputs':item['qualified_input_count']=len(d['records'])
 records.append(item)
counts={'planned_scenes':30,'planned_pairs':480,'planned_predictions':5760,'scenes_with_selected_views':sum(r['selected_pair_count']==16 for r in records),'scenes_with_final_qualified_inputs':sum(r['qualified_input_count']==32 for r in records),'qualified_pairs':sum(r['qualified_input_count'] for r in records)//2}
result={'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts,'scenes':records,'scope':'Artifact existence/status snapshot, not a replacement for hash checks or goal completion audit.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(counts))
