"""Consume completed scene receipts without waiting for all other scenes."""
import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[5];completed=set();records=[]
while True:
 progress=a.workspace/'progress.json'
 if not progress.exists():time.sleep(15);continue
 data=json.loads(progress.read_text())
 for row in data['records']:
  sid=row['scene_id']
  if sid in completed or row['status']!='ready_for_target_selection':continue
  folder=a.workspace/sid;out=folder/'target_pool.json'
  with (folder/'target_pool.log').open('x') as log:
   result=subprocess.run([str(root/'scripts/isaac_python.sh'),str(Path(__file__).with_name('extract_target_pool.py')),'--receipt',str(folder/'receipt.json'),'--out',str(out)],cwd=root,stdout=log,stderr=subprocess.STDOUT)
  record={'scene_id':sid,'exit_code':result.returncode,'output':str(out)}
  if out.exists():
   pool=json.loads(out.read_text());record.update(status=pool['status'],candidate_count=pool['candidate_count'],selected_count=len(pool['selected']))
  else:record['status']='failed'
  records.append(record);completed.add(sid);(a.workspace/'target_pool_progress.json').write_text(json.dumps({'records':records},indent=2)+'\n');print(record,flush=True)
 if data['completed']==data['planned']:break
 time.sleep(15)
print('target pool collection terminal',flush=True)
