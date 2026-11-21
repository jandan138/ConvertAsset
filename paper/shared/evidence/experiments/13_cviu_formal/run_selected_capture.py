"""Capture selected original and converted views in separate matched batches."""
import argparse,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--selected',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--wait-pid',type=int,required=True);p.add_argument('--gpu',type=int,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
runner=Path(__file__).with_name('run_material_probe.py')
for condition in ['original','converted']:
 result=subprocess.run([sys.executable,str(runner),'--wait-pid',str(a.wait_pid),'--jobs',str(a.selected/(condition+'.json')),'--out',str(a.out/condition),'--gpu',str(a.gpu)])
 marker=a.out/(condition+'.exit')
 if result.returncode or not marker.exists() or marker.read_text().strip()!='0':raise RuntimeError('Capture process failed: '+condition)
 progress=a.out/condition/'progress.json'
 if not progress.exists():raise RuntimeError('Capture missing: '+condition)
 d=json.loads(progress.read_text())
 if d['completed']!=16:raise RuntimeError('Incomplete final capture: '+condition)
 print(condition,'captured',d['completed'],flush=True)
(a.out/'capture_complete.json').write_text(json.dumps({'status':'captured_requires_final_QA','selected':str(a.selected),'images':32},indent=2)+'\n')
