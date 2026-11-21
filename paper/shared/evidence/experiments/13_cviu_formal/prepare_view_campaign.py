"""Generate original-geometry view proposals for the frozen 30-scene cohort."""
import argparse,concurrent.futures,json,subprocess,threading
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ready',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--candidate-views',type=int,choices=[2,4],default=2);a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);root=Path(__file__).resolve().parents[5];rows=json.loads(a.ready.read_text())['scenes'];lock=threading.Lock();results=[]
def run(row):
 spec=a.out/(row['scene_id']+'.json');spec.write_text(json.dumps(row,indent=2));directory=a.out/row['scene_id'];log=a.out/(row['scene_id']+'.log')
 with log.open('x') as f:r=subprocess.run([str(root/'scripts/isaac_python.sh'),str(Path(__file__).with_name('prepare_views.py')),'--scene',str(spec),'--out',str(directory),'--candidate-views',str(a.candidate_views)],cwd=root,stdout=f,stderr=subprocess.STDOUT)
 item={'scene_id':row['scene_id'],'exit_code':r.returncode,'jobs':str(directory/'jobs.json'),'log':str(log)}
 if (directory/'jobs.json').exists():d=json.loads((directory/'jobs.json').read_text());item.update(status=d['status'],objects=len(d['selected']),jobs_count=len(d['jobs']))
 else:item['status']='failed'
 with lock:
  results.append(item);tmp=a.out/'progress.tmp';tmp.write_text(json.dumps({'planned':len(rows),'completed':len(results),'records':results},indent=2));tmp.replace(a.out/'progress.json');print(item,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,rows))
