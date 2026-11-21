"""Launch three fresh model processes on isolated GPUs and retain terminal receipts."""
import argparse,concurrent.futures,json,shlex,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
python='/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.venv_dlc/bin/python'
runner=Path(__file__).resolve().with_name('pilot_inference.py')
def run(i):
 folder=a.out/f'repeat{i}';log=a.out/f'repeat{i}.log';terminal=a.out/f'repeat{i}.exit'
 cmd=['env',f'CUDA_VISIBLE_DEVICES={i}','PYTHONUNBUFFERED=1','HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1',python,str(runner),'--manifest',str(a.manifest.resolve()),'--repeat',str(i),'--out',str(folder.resolve())]
 shell=shlex.join(cmd)+' > '+shlex.quote(str(log.resolve()))+' 2>&1; result=$?; echo "$result" > '+shlex.quote(str(terminal.resolve()))+'; exit "$result"'
 start=time.time();r=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090',shell]);result={'repeat':i,'gpu':i,'exit_code':r.returncode,'seconds':time.time()-start,'output':str(folder),'log':str(log)}
 (a.out/f'repeat{i}_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,range(3)))
(a.out/'campaign.json').write_text(json.dumps({'runs':results,'manifest':str(a.manifest)},indent=2)+'\n')
raise SystemExit(int(any(r['exit_code'] for r in results)))
