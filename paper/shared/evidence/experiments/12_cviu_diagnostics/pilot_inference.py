"""Run one independent Qwen3-VL-8B repeat on a visually accepted pilot manifest."""
import argparse,hashlib,importlib.util,json,random,re,time,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse_point(text):
 m=re.fullmatch(r'\s*Point:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*',text)
 return [float(m[1]),float(m[2])] if m else None

def validate_manifest(manifest):
 rows=manifest['records']; ids=set(); pairs={}
 for r in rows:
  key=(r['pair_id'],r['condition'])
  if key in ids:raise ValueError('duplicate input')
  ids.add(key);pairs.setdefault(r['pair_id'],set()).add(r['condition'])
  if r['visual_qa']!='PASS':raise ValueError('Unaccepted image')
  for kind in ['image','mask']:
   if sha(r[kind]['path'])!=r[kind]['sha256']:raise ValueError(f'{kind} hash mismatch')
  if not r['query'].strip():raise ValueError('Missing query')
 for pair in pairs:
  members=[r for r in rows if r['pair_id']==pair]
  for field in ['scene_id','target_prim','view_id','query']:
   if len({r[field] for r in members})!=1:raise ValueError(f'Paired {field} mismatch')
 if len(pairs)<12 or any(v!={'original','converted'} for v in pairs.values()):raise ValueError('Incomplete paired pilot')
 scenes={r['scene_id'] for r in rows}
 if len(scenes)!=3:raise ValueError('Expected three scenes')
 for scene in scenes:
  targets={r['target_prim'] for r in rows if r['scene_id']==scene}
  if len(targets)<2:raise ValueError('Need two distinct targets per scene')
  for target in targets:
   views={r['view_id'] for r in rows if r['scene_id']==scene and r['target_prim']==target}
   if len(views)<2:raise ValueError('Need two views per target')
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--repeat',type=int,choices=[0,1,2],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--validate-only',action='store_true');a=p.parse_args()
 rows=validate_manifest(json.loads(a.manifest.read_text()))
 if a.validate_only:print('validated',len(rows));return
 a.out.mkdir(parents=True,exist_ok=False)
 import torch,numpy as np
 from PIL import Image
 seed=20261114+a.repeat;random.seed(seed);torch.manual_seed(seed)
 root=Path(__file__).resolve().parent.parent
 source=root/'06_grscenes_vlm_grounding/run_vlm_predictions.py'
 snapshot=a.out/'engine_snapshot.py';shutil.copy2(source,snapshot);shutil.copy2(__file__,a.out/'pilot_inference_snapshot.py')
 spec=importlib.util.spec_from_file_location('vlm_engine',snapshot);engine_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine_module)
 config=json.loads((root/'11_iclr_model_behavior/models.json').read_text())['models']['qwen3vl8b']
 engine=engine_module.LocalHFGenericEngine(model_path=config['path'],model_class=config['model_class'],temperature=0.0,max_new_tokens=128,dtype='bfloat16',attn_implementation='sdpa')
 metadata={'repeat':a.repeat,'seed':seed,'checkpoint':config['path'],'engine_sha256':sha(source),'runner_sha256':sha(__file__),'manifest_sha256':sha(a.manifest),'torch':torch.__version__,'decoding':{'do_sample':False,'max_new_tokens':128,'dtype':'bfloat16'}}
 metadata['checkpoint_config_hashes']={}
 for name in ['config.json','generation_config.json','preprocessor_config.json','processor_config.json','tokenizer_config.json']:
  config_file=Path(config['path'])/name
  if config_file.is_file():
   shutil.copy2(config_file,a.out/name);metadata['checkpoint_config_hashes'][name]=sha(config_file)
 (a.out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
 with (a.out/'predictions.jsonl').open('x') as f:
  for r in rows:
   prompt=r['query']+' Use normalized 0-1000 coordinates: (0,0) top left, (1000,1000) bottom right. Return exactly one line: Point: x, y'
   result={**r,'repeat':a.repeat,'seed':seed,'prompt':prompt,'checkpoint':config['path']};t=time.monotonic()
   try:
    raw=engine.generate(engine_module.build_messages({'image':{'path':r['image']['path']}},prompt));point=parse_point(raw)
    mask=np.load(r['mask']['path'],allow_pickle=False)
    with Image.open(r['image']['path']) as im:w,h=im.size
    if mask.shape!=(h,w):raise ValueError('Mask shape mismatch')
    valid=point is not None and all(0<=v<1000 for v in point)
    hit=bool(mask[int(point[1]*h/1000),int(point[0]*w/1000)]) if valid else False
    ys,xs=np.where(mask)
    bbox_hit=bool(xs.min()<=point[0]*w/1000<xs.max()+1 and ys.min()<=point[1]*h/1000<ys.max()+1) if valid and len(xs) else False
    result.update(status='ok',raw_response=raw,point_normalized=point,valid_point=valid,hit=hit,visible_bbox_hit=bbox_hit)
   except Exception as exc:result.update(status='runtime_error',error=repr(exc),hit=None)
   result['elapsed_seconds']=time.monotonic()-t
   f.write(json.dumps(result)+'\n');f.flush()
 print('finished repeat',a.repeat,flush=True)
if __name__=='__main__':main()
