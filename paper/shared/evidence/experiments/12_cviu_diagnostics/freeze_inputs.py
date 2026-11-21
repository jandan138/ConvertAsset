"""Freeze reviewed paired RGB/semantic masks; no automatic visual acceptance."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--progress',type=Path,required=True);p.add_argument('--qa',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 import numpy as np
 from PIL import Image
 progress=json.loads(a.progress.read_text());qa=json.loads(a.qa.read_text());accepted={}
 for q in qa['reviews']:
  key=(q['pair_id'],q['condition'])
  if key in accepted:raise ValueError('Duplicate QA key')
  accepted[key]=q
 overrides={}
 for q in qa['reviews']:
  if q.get('query_override'):
   key=q['pair_id']
   if key in overrides and overrides[key]!=q['query_override']:raise ValueError('Conflicting query overrides')
   overrides[key]=q['query_override']
 records=[]
 for r in progress['records']:
  q=accepted.get((r['pair_id'],r['condition']))
  if q is None or q['verdict']!='PASS':raise ValueError('Missing visual acceptance')
  folder=Path(r['output']);image=folder/'rgb.png';mask=folder/'target_mask.npy'
  if sha(image)!=q['image_sha256']:raise ValueError('QA does not cover current RGB')
  if sha(mask)!=q['mask_sha256']:raise ValueError('QA does not cover current mask')
  with Image.open(image) as im:w,h=im.size
  arr=np.load(mask,allow_pickle=False)
  if arr.dtype!=np.bool_ or arr.shape!=(h,w) or not arr.any():raise ValueError('Invalid visible target mask')
  receipt=json.loads((folder/'receipt.json').read_text())
  if receipt['target_prim']!=r['target_prim'] or Path(receipt['stage'])!=Path(r['stage']):raise ValueError('Capture provenance mismatch')
  cache=json.loads((folder/'cache_receipt.json').read_text())
  if not Path(cache['omni_global_cache']).is_relative_to(folder):raise ValueError('Cache isolation absent')
  ys,xs=np.where(arr)
  records.append({'pair_id':r['pair_id'],'condition':r['condition'],'scene_id':r['scene_id'],'target_prim':r['target_prim'],'view_id':r['pair_id'].rsplit(':',1)[1],'query':overrides.get(r['pair_id'],r['query']),'source_category':r['category'],'visual_qa':'PASS','image':{'path':str(image),'sha256':sha(image),'width':w,'height':h},'mask':{'path':str(mask),'sha256':sha(mask),'pixels':int(arr.sum())},'center_baseline_hit':bool(arr[h//2,w//2]),'uniform_pixel_baseline_probability':float(arr.mean()),'visible_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'camera_stage_sha256':sha(r['stage']),'capture_receipt':str(folder/'receipt.json'),'capture_receipt_sha256':sha(folder/'receipt.json')})
 from pilot_inference import validate_manifest
 result={'schema_version':1,'records':records,'qa_sha256':sha(a.qa),'progress_sha256':sha(a.progress)}
 validate_manifest(result)
 with a.out.open('x') as f:json.dump(result,f,indent=2)
 print('Frozen',len(records),'images')
if __name__=='__main__':main()
