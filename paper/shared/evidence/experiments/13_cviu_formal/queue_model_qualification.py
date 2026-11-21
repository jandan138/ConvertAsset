"""Run held-out model qualification only after capture releases its GPUs."""
import argparse,json,os,shlex,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wait-pid',type=int,required=True);p.add_argument('--gpu',type=int,nargs='+',required=True);p.add_argument('--model',choices=['8b','32b'],required=True);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--download-receipt',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
while True:
 try:os.kill(a.wait_pid,0)
 except ProcessLookupError:break
 time.sleep(20)
if a.download_receipt:
 while not a.download_receipt.exists():time.sleep(20)
 if json.loads(a.download_receipt.read_text())['status']!='downloaded':raise RuntimeError('Checkpoint download did not complete')
while True:
 r=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090','nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits'],capture_output=True,text=True)
 if r.returncode==0:
  memory={int(line.split(',')[0]):int(line.split(',')[1]) for line in r.stdout.splitlines()}
  if all(memory.get(g,999999)<512 for g in a.gpu):break
 time.sleep(20)
root=Path(__file__).resolve().parents[5];a.out.parent.mkdir(parents=True,exist_ok=True)
python='/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python'
cmd=['env','CUDA_VISIBLE_DEVICES='+','.join(map(str,a.gpu)),'PYTHONUNBUFFERED=1','timeout','-k','20','3600',python,str(Path(__file__).with_name('formal_inference.py').resolve()),'--mode','qualification','--manifest',str(root/'paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/manifest.json'),'--protocol',str(root/'paper/shared/evidence/raw/cviu_formal/v1/protocol.json'),'--model',a.model,'--checkpoint',str(a.checkpoint),'--repeat','0','--out',str(a.out.resolve())]
log=a.out.with_suffix('.log');marker=a.out.with_suffix('.exit')
remote=shlex.join(cmd)+' > '+shlex.quote(str(log))+' 2>&1; result=$?; echo "$result" > '+shlex.quote(str(marker))+'; exit "$result"'
r=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',remote]);print('qualification exit',r.returncode,flush=True);raise SystemExit(r.returncode)
