"""Capture original-condition proposals for QA; these are not frozen model inputs."""
import argparse,concurrent.futures,json,shlex,shutil,subprocess,threading,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--views',type=Path,required=True);p.add_argument('--ready',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--limit-scenes',type=int);p.add_argument('--gpus',type=int,nargs='+',default=[0,1,2,3]);a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
rows=json.loads(a.ready.read_text())['scenes'][:a.limit_scenes];snapshot=a.out/'renderer_snapshot.py';shutil.copy2(Path(__file__).with_name('render_scene_views.py'),snapshot);lock=threading.Lock();results=[]
python='/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/bin/python'
def lane(slot):
 index,gpu=slot
 for row in rows[index::len(a.gpus)]:
  while True:
   check=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',f'nvidia-smi --id={gpu} --query-gpu=memory.used --format=csv,noheader,nounits'],capture_output=True,text=True)
   if check.returncode==0 and check.stdout.strip().isdigit() and int(check.stdout.strip())<512:break
   time.sleep(30)
  sid=row['scene_id'];proposal=json.loads((a.views/sid/'jobs.json').read_text())
  if proposal['status'] not in ['proposed_16_pairs','proposed_candidate_views']:raise ValueError('Incomplete proposals '+sid)
  jobs=[r for r in proposal['jobs'] if r['condition']=='original'];assert 16<=len(jobs)<=32
  spec=a.out/(sid+'.json');spec.write_text(json.dumps({'jobs':jobs,'purpose':'original-view qualification only'},indent=2));folder=a.out/sid;log=a.out/(sid+'.log');exit_file=a.out/(sid+'.exit')
  cmd=['env',f'CUDA_VISIBLE_DEVICES={gpu}','OMNI_KIT_ACCEPT_EULA=YES','PYTHONUNBUFFERED=1','timeout','-k','15','3600',python,str(snapshot),'--jobs',str(spec),'--out',str(folder),'--gpu',str(gpu),'--anti-aliasing','3']
  remote=shlex.join(cmd)+' > '+shlex.quote(str(log))+' 2>&1; result=$?; echo "$result" > '+shlex.quote(str(exit_file))+'; exit "$result"'
  r=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',remote]);result={'scene_id':sid,'gpu':gpu,'exit_code':r.returncode,'output':str(folder),'log':str(log),'qa_status':'pending'}
  with lock:
   results.append(result);tmp=a.out/'progress.tmp';tmp.write_text(json.dumps({'planned_scenes':len(rows),'completed_scenes':len(results),'records':results},indent=2));tmp.replace(a.out/'progress.json');print(result,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=len(a.gpus)) as pool:list(pool.map(lane,enumerate(a.gpus)))
