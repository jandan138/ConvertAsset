"""Four isolated render lanes; receipts indicate capture, never automatic visual acceptance."""
import argparse,concurrent.futures,json,os,shlex,subprocess,threading,time,shutil,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--jobs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gpus',type=int,nargs='+',default=[0,1,2,3]);p.add_argument('--resume',action='store_true');p.add_argument('--timeout-seconds',type=int,default=900);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=a.resume)
rows=json.loads(a.jobs.read_text())['jobs'];lock=threading.Lock();results=json.loads((a.out/'progress.json').read_text())['records'] if a.resume and (a.out/'progress.json').exists() else []
completed={r['job_index'] for r in results}
root=Path(__file__).resolve().parents[5];python='/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/bin/python';renderer=a.out/'render_probe_snapshot.py'
if not a.resume:shutil.copy2(Path(__file__).with_name('render_probe.py'),renderer)
(a.out/'batch_config.json').write_text(json.dumps({'renderer_sha256':hashlib.sha256(renderer.read_bytes()).hexdigest(),'jobs_sha256':hashlib.sha256(a.jobs.read_bytes()).hexdigest(),'jobs':str(a.jobs)},indent=2))
def lane(slot):
 lane_index,gpu=slot
 for i in range(lane_index,len(rows),len(a.gpus)):
  if i in completed:continue
  row=rows[i];folder=a.out/f'{i:02d}';log=a.out/f'{i:02d}.log'
  cmd=['env',f'CUDA_VISIBLE_DEVICES={gpu}','OMNI_KIT_ACCEPT_EULA=YES','PYTHONUNBUFFERED=1','timeout','-k','15',str(a.timeout_seconds),python,str(renderer),'--stage',row['stage'],'--out',str(folder),'--gpu',str(gpu),'--capture-mode','step']
  start=time.time()
  if folder.exists():
   probe="import os,sys; from pathlib import Path; target=sys.argv[1].encode(); active=False\nfor p in Path('/proc').glob('[0-9]*/cmdline'):\n try:\n  args=p.read_bytes().split(bytes([0])); active=active or (target in args and any(x.endswith(b'/render_probe_snapshot.py') for x in args))\n except OSError:pass\nprint(active)"
   while True:
    observed=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',shlex.join(['python','-c',probe,str(folder)])],capture_output=True,text=True)
    if observed.returncode:time.sleep(30);continue
    if observed.stdout.strip()=='False':break
    time.sleep(30)
   code=None
  else:
   remote=shlex.join(cmd)+' > '+shlex.quote(str(log))+' 2>&1; result=$?; echo "$result" > '+shlex.quote(str(a.out/f'{i:02d}.exit'))+'; exit "$result"'
   done=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',remote]);code=done.returncode
  record={**row,'job_index':i,'gpu':gpu,'exit_code':code,'elapsed_s':time.time()-start,'output':str(folder),'log':str(log),'capture_status':'captured_unreviewed' if (folder/'rgb.png').exists() and (folder/'receipt.json').exists() else 'failed','visual_qa':'PENDING'}
  with lock:
   results.append(record);tmp=a.out/'progress.tmp';tmp.write_text(json.dumps({'planned':len(rows),'completed':len(results),'records':sorted(results,key=lambda x:x['job_index'])},indent=2));os.replace(tmp,a.out/'progress.json');print('finished',i,record['capture_status'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=len(a.gpus)) as pool:list(pool.map(lane,enumerate(a.gpus)))
print('batch terminal',flush=True)
