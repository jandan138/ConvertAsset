"""Isolated render-product probe; progress is unbuffered and stack dumps expose hangs."""
import argparse,faulthandler,json,time,hashlib,sys,os
from pathlib import Path
SCRIPT_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--stage',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gpu',type=int,default=0);p.add_argument('--anti-aliasing',type=int,choices=range(5),default=3);p.add_argument('--sync-loads',action='store_true');p.add_argument('--capture-mode',choices=['step','updates'],default='updates');a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)
cache=a.out/'cache'
cache.mkdir(parents=True,exist_ok=True)
os.environ['XDG_CACHE_HOME']=str(cache/'xdg')
kit_args=['--portable','--portable-root',str(cache),'--/app/tokens/omni_global_cache='+str(cache/'global'),'--/rtx-transient/resourcemanager/localTextureCachePath='+str(cache/'global/texturecache')]
# Isaac 4.1 forwards sys.argv; it does not support the 4.5 extra_args config key.
sys.argv=[sys.argv[0],*kit_args]
from isaacsim import SimulationApp
print('before SimulationApp',flush=True)
app=SimulationApp({'headless':True,'create_new_stage':False,'sync_loads':a.sync_loads,'fast_shutdown':True,'active_gpu':a.gpu,'physics_gpu':0,'multi_gpu':False,'renderer':'RayTracedLighting','anti_aliasing':a.anti_aliasing})
print('after SimulationApp',flush=True)
import carb.tokens,carb.settings
tokens=carb.tokens.get_tokens_interface()
receipt={'omni_global_cache':tokens.resolve('${omni_global_cache}'),'texture_cache':carb.settings.get_settings().get('/rtx-transient/resourcemanager/localTextureCachePath')}
(a.out/'cache_receipt.json').write_text(json.dumps(receipt,indent=2))
if not Path(receipt['omni_global_cache']).is_relative_to(a.out):raise RuntimeError('Global cache not isolated')
try:
 import omni.usd
 import omni.replicator.core as rep
 import numpy as np
 from PIL import Image
 manager=app._app.get_extension_manager()
 manager.set_extension_enabled_immediate('isaacsim.gui.menu',False)
 print('GUI menu disabled',flush=True)
 context=omni.usd.get_context()
 context.open_stage(a.stage)
 from pxr import UsdGeom
 import math
 camera=UsdGeom.Camera(context.get_stage().GetPrimAtPath('/DiagnosticCamera'))
 values=[float(v) for row in camera.GetCamera(0).transform for v in row]+list(camera.GetClippingRangeAttr().Get())
 if not all(math.isfinite(v) and abs(v)<1e12 for v in values):raise ValueError('Invalid camera transform or clip range')
 if not context.get_attached_hydra_engine_names():
  hydra_engine=omni.usd.add_hydra_engine('rtx',context)
  omni.usd.attach_all_hydra_engines(context)
 target_prim=None
 jobs_file=Path(a.stage).parents[2]/'jobs.json'
 if jobs_file.is_file():
  job=next(x for x in json.loads(jobs_file.read_text())['jobs'] if Path(x['stage'])==Path(a.stage))
  target_prim=job['target_prim']
  from pxr import Usd,Semantics
  stage=context.get_stage()
  with Usd.EditContext(stage,stage.GetSessionLayer()):
   target=stage.GetPrimAtPath(target_prim)
   if not target:raise ValueError('Missing target prim')
   semantic=Semantics.SemanticsAPI.Apply(target,'CVIUTarget')
   semantic.CreateSemanticTypeAttr().Set('class')
   semantic.CreateSemanticDataAttr().Set('cviu_target')
 print('stage opened',flush=True)
 print('hydra engines',omni.usd.get_context().get_attached_hydra_engine_names(),flush=True)
 product=rep.create.render_product('/DiagnosticCamera',(1024,768))
 rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product])
 instance_ids=rep.AnnotatorRegistry.get_annotator('instance_id_segmentation');instance_ids.attach([product])
 semantic_mask=rep.AnnotatorRegistry.get_annotator('semantic_segmentation');semantic_mask.attach([product])
 app.reset_render_settings()
 if a.capture_mode == 'step':
  rep.orchestrator.step(rt_subframes=8,delta_time=0.0,pause_timeline=True)
 else:
  import omni.timeline
  rep.orchestrator.set_capture_on_play(True)
  omni.timeline.get_timeline_interface().play()
 deadline=time.monotonic()+90
 i=0
 data=None
 while time.monotonic()<deadline:
  app.update()
  data=rgb.get_data()
  if i%100==0:print('update',i,'loading',omni.usd.get_context().get_stage_loading_status(),'rgb',getattr(data,'shape',None),flush=True)
  if isinstance(data,np.ndarray) and data.size and i>100:break
  time.sleep(.01)
  i+=1
 print('shape',getattr(data,'shape',None),flush=True)
 if not isinstance(data,np.ndarray) or data.size==0:raise RuntimeError('RGB empty')
 if float(data[:,:,:3].std())<1:raise RuntimeError('Blank or near-constant RGB; reject capture')
 Image.fromarray(data[:,:,:3]).save(a.out/'rgb.png')
 segmentation=instance_ids.get_data()
 if isinstance(segmentation,dict) and isinstance(segmentation.get('data'),np.ndarray):
  np.save(a.out/'instance_ids.npy',segmentation['data'],allow_pickle=False)
  (a.out/'instance_ids_info.json').write_text(json.dumps(segmentation.get('info',{}),default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x),indent=2))
 sem=semantic_mask.get_data()
 if target_prim and isinstance(sem,dict):
  info=sem.get('info',{});labels=info.get('idToLabels',{})
  ids=[int(k) for k,v in labels.items() if isinstance(v,dict) and v.get('class')=='cviu_target']
  if ids:
   mask=np.isin(sem['data'],ids);np.save(a.out/'target_mask.npy',mask,allow_pickle=False)
  (a.out/'semantic_info.json').write_text(json.dumps(info,default=str,indent=2))
 (a.out/'receipt.json').write_text(json.dumps({'stage':a.stage,'gpu':a.gpu,'shape':list(data.shape),'cache':str(cache),'status':'captured_unreviewed','target_prim':target_prim,'script_sha256':SCRIPT_SHA256}))
except Exception as exc:
 (a.out/'failure.json').write_text(json.dumps({'error':repr(exc)}))
 print('CAPTURE_FAILED',repr(exc),flush=True)
 raise
finally:
 app.close(wait_for_replicator=False)
