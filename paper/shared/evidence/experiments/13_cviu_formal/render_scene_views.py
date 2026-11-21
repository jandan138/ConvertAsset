"""Load one scene/condition once; switch only session-layer cameras between views."""
import argparse,hashlib,json,os,sys,time,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_jobs(jobs):
 if not jobs:raise ValueError('Empty view batch')
 if len({(r['scene_id'],r['condition']) for r in jobs})!=1:raise ValueError('Batch must share one scene and material condition')
 if any(r['resolution']!=[1024,768] for r in jobs):raise ValueError('Expected 1024x768 inputs')

def main():
 p=argparse.ArgumentParser();p.add_argument('--jobs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gpu',type=int,required=True);p.add_argument('--anti-aliasing',type=int,choices=range(5),default=3);p.add_argument('--sync-loads',action='store_true');p.add_argument('--reload-stage-per-view',action='store_true');a=p.parse_args();jobs=json.loads(a.jobs.read_text())['jobs'];validate_jobs(jobs)
 a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);snapshot=a.out/'renderer_snapshot.py';shutil.copy2(__file__,snapshot);cache=a.out/'cache';cache.mkdir();os.environ['XDG_CACHE_HOME']=str(cache/'xdg')
 sys.argv=[sys.argv[0],'--portable','--portable-root',str(cache),'--/app/tokens/omni_global_cache='+str(cache/'global'),'--/rtx-transient/resourcemanager/localTextureCachePath='+str(cache/'global/texturecache')]
 from isaacsim import SimulationApp
 app=SimulationApp({'headless':True,'create_new_stage':False,'sync_loads':a.sync_loads,'fast_shutdown':True,'active_gpu':a.gpu,'physics_gpu':0,'multi_gpu':False,'renderer':'RayTracedLighting','anti_aliasing':a.anti_aliasing})
 try:
  import carb.tokens,carb.settings,omni.usd
  import omni.replicator.core as rep
  import numpy as np
  from PIL import Image
  from pxr import Sdf,Usd,Semantics
  tokens=carb.tokens.get_tokens_interface();cache_receipt={'global':tokens.resolve('${omni_global_cache}'),'texture':carb.settings.get_settings().get('/rtx-transient/resourcemanager/localTextureCachePath')}
  if not all(Path(v).is_relative_to(cache) for v in cache_receipt.values()):raise ValueError('Caches not isolated')
  (a.out/'cache_receipt.json').write_text(json.dumps(cache_receipt,indent=2))
  app._app.get_extension_manager().set_extension_enabled_immediate('isaacsim.gui.menu',False)
  layers=[Sdf.Layer.FindOrOpen(r['stage']) for r in jobs]
  if any(l is None for l in layers):raise ValueError('Missing camera layer')
  if any(list(l.subLayerPaths)!=list(layers[0].subLayerPaths) for l in layers):raise ValueError('Views refer to different scene assets')
  light=lambda l:{a.name:str(a.default) for a in l.GetPrimAtPath('/DiagnosticLight').attributes.values()}
  if any(light(l)!=light(layers[0]) for l in layers):raise ValueError('Lighting varies between views')
  context=omni.usd.get_context();context.open_stage(jobs[0]['stage']);stage=context.get_stage()
  if not context.get_attached_hydra_engine_names():engine=omni.usd.add_hydra_engine('rtx',context);omni.usd.attach_all_hydra_engines(context)
  labels={target:f'cviu_target_{i}' for i,target in enumerate(sorted({r['target_prim'] for r in jobs}))}
  with Usd.EditContext(stage,stage.GetSessionLayer()):
   for target,label in labels.items():
    prim=stage.GetPrimAtPath(target)
    if not prim:raise ValueError('Missing target '+target)
    sem=Semantics.SemanticsAPI.Apply(prim,'CVIUTarget');sem.CreateSemanticTypeAttr().Set('class');sem.CreateSemanticDataAttr().Set(label)
  app.reset_render_settings()
  results=[]
  for i,(job,layer) in enumerate(zip(jobs,layers)):
   begin=time.monotonic()
   if i and a.reload_stage_per_view:
    rep.orchestrator.stop();context.close_stage();context.open_stage(job['stage']);stage=context.get_stage()
    if not context.get_attached_hydra_engine_names():engine=omni.usd.add_hydra_engine('rtx',context);omni.usd.attach_all_hydra_engines(context)
    with Usd.EditContext(stage,stage.GetSessionLayer()):
     for target,label in labels.items():
      sem=Semantics.SemanticsAPI.Apply(stage.GetPrimAtPath(target),'CVIUTarget');sem.CreateSemanticTypeAttr().Set('class');sem.CreateSemanticDataAttr().Set(label)
    app.reset_render_settings()
   folder=a.out/f'{i:03d}';folder.mkdir()
   expected={}
   with Usd.EditContext(stage,stage.GetSessionLayer()):
    camera=stage.GetPrimAtPath('/DiagnosticCamera')
    for spec in layer.GetPrimAtPath('/DiagnosticCamera').attributes.values():
     camera.CreateAttribute(spec.name,spec.typeName).Set(spec.default);expected[spec.name]=str(spec.default)
   actual={k:str(camera.GetAttribute(k).Get()) for k in expected}
   if actual!=expected:raise ValueError('Camera override mismatch')
   product=rep.create.render_product('/DiagnosticCamera',(1024,768),name=f'cviu_view_{i}');rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product]);semantic=rep.AnnotatorRegistry.get_annotator('semantic_segmentation');semantic.attach([product])
   rep.orchestrator.step(rt_subframes=8,delta_time=0.0,pause_timeline=True)
   for _ in range(102):app.update()
   image=rgb.get_data();seg=semantic.get_data()
   if image.shape!=(768,1024,4):raise ValueError('Invalid RGB buffer')
   rgb_blank=bool(image[:,:,:3].std()<1)
   info=seg.get('info',{});ids=[int(k) for k,v in info.get('idToLabels',{}).items() if isinstance(v,dict) and v.get('class')==labels[job['target_prim']]]
   mask=np.isin(seg['data'],ids)
   Image.fromarray(image[:,:,:3]).save(folder/'rgb.png');np.save(folder/'target_mask.npy',mask,allow_pickle=False)
   (folder/'semantic_info.json').write_text(json.dumps(info,default=str,indent=2))
   receipt={**job,'output':str(folder),'camera_parameters':actual,'target_label':labels[job['target_prim']],'mask_pixels':int(mask.sum()),'elapsed_s':time.monotonic()-begin,'rgb_blank':rgb_blank,'status':'blank_rgb_requires_review' if rgb_blank else ('captured_unreviewed' if mask.any() else 'invisible_target'),'image_sha256':sha(folder/'rgb.png'),'mask_sha256':sha(folder/'target_mask.npy')}
   (folder/'receipt.json').write_text(json.dumps(receipt,indent=2));results.append(receipt)
   (a.out/'progress.json').write_text(json.dumps({'stage_open_count':(i+1 if a.reload_stage_per_view else 1),'process_start_count':1,'planned':len(jobs),'completed':len(results),'script_sha256':sha(snapshot),'gpu':a.gpu,'jobs_sha256':sha(a.jobs),'records':results},indent=2))
   print('captured',i,job['pair_id'],receipt['status'],flush=True)
   rgb.detach([product.path]);semantic.detach([product.path]);product.destroy()
 except Exception as exc:
  (a.out/'failure.json').write_text(json.dumps({'error':repr(exc)}));print('FAILED',repr(exc),flush=True);raise
 finally:app.close(wait_for_replicator=False)
if __name__=='__main__':main()
