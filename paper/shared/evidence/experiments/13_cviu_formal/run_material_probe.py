"""Queue a repair qualification after the active capture controller finishes."""
import argparse,json,os,shlex,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wait-pid',type=int,required=True);p.add_argument('--jobs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--gpu',type=int,default=0);a=p.parse_args()
while True:
 try:os.kill(a.wait_pid,0)
 except ProcessLookupError:break
 time.sleep(20)
while True:
 r=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',f'nvidia-smi --id={a.gpu} --query-gpu=memory.used --format=csv,noheader,nounits'],capture_output=True,text=True)
 if r.returncode==0 and r.stdout.strip().isdigit() and int(r.stdout.strip())<512:break
 time.sleep(20)
python='/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/bin/python'
cmd=['env',f'CUDA_VISIBLE_DEVICES={a.gpu}','OMNI_KIT_ACCEPT_EULA=YES','PYTHONUNBUFFERED=1','timeout','-k','15','1800',python,str(Path(__file__).resolve().with_name('render_scene_views.py')),'--jobs',str(a.jobs.resolve()),'--out',str(a.out.resolve()),'--gpu',str(a.gpu)]
log=a.out.with_suffix('.log');exit_file=a.out.with_suffix('.exit')
remote=shlex.join(cmd)+' > '+shlex.quote(str(log))+' 2>&1; result=$?; echo "$result" > '+shlex.quote(str(exit_file))+'; exit "$result"'
r=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',remote]);print(json.dumps({'exit_code':r.returncode,'output':str(a.out),'log':str(log)}),flush=True)

raise SystemExit(r.returncode)
