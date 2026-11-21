"""Wait for terminal primary batch, then rerender missing or visually failed pairs."""
import argparse,json,subprocess,time
import numpy as np
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--primary',type=Path,required=True);p.add_argument('--qa',type=Path,required=True);p.add_argument('--replacement-jobs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--reuse-progress',type=Path);a=p.parse_args()
while True:
 progress=a.primary/'progress.json'
 if progress.exists():
  data=json.loads(progress.read_text())
  if data['completed']==data['planned']:break
 time.sleep(30)
reuse={}
if a.reuse_progress:
 while True:
  if a.reuse_progress.exists():
   previous=json.loads(a.reuse_progress.read_text())
   if previous['completed']==previous['planned']:break
  time.sleep(30)
 for r in previous['records']:
  if r['capture_status']=='captured_unreviewed' and (Path(r['output'])/'target_mask.npy').exists() and np.load(Path(r['output'])/'target_mask.npy',allow_pickle=False).any():reuse[(r['pair_id'],r['condition'],r['stage'])]=r
qa=json.loads(a.qa.read_text())['reviews'];failed_pairs={r['pair_id'] for r in qa if r['verdict']=='FAIL'}
replacement={(r['pair_id'],r['condition']):r for r in json.loads(a.replacement_jobs.read_text())['jobs']}
# An absent/empty target mask is also a visibility failure requiring matched camera replacement.
import numpy as np
for r in data['records']:
 if r['capture_status']=='captured_unreviewed':
  mask=Path(r['output'])/'target_mask.npy'
  if not mask.exists() or not np.load(mask,allow_pickle=False).any():failed_pairs.add(r['pair_id'])
jobs=[]
for r in data['records']:
 if r['pair_id'] in failed_pairs:jobs.append(replacement[r['pair_id'],r['condition']])
 elif r['capture_status']!='captured_unreviewed':jobs.append(r)
jobs=[r for r in jobs if (r['pair_id'],r['condition'],r['stage']) not in reuse]
a.out.parent.mkdir(parents=True,exist_ok=True)
plan=a.out.with_name(a.out.name+'_jobs.json')
with plan.open('x') as f:json.dump({'jobs':jobs,'reason':'Technical capture failures and pre-inference visibility failures only','primary':str(a.primary)},f,indent=2)
if jobs:
 command=['python','-u',str(Path(__file__).with_name('render_pilot_batch.py')),'--jobs',str(plan),'--out',str(a.out),'--gpus','0','1','2','3','--timeout-seconds','3600']
 raise SystemExit(subprocess.call(command))
print('No technical repairs required',flush=True)
