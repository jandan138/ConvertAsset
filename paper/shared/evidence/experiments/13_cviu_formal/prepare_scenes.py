"""Restore, convert and audit every frozen formal scene; retain per-scene failures."""
import argparse,concurrent.futures,hashlib,json,subprocess,threading,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=2);a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[5];helpers=root/'paper/shared/evidence/experiments/12_cviu_diagnostics';isaac=str(root/'scripts/isaac_python.sh');rows=json.loads(a.manifest.read_text())['scenes'];lock=threading.Lock();results=[]
def run(row):
 begin=time.time();folder=a.out/row['scene_id'];folder.mkdir();one=folder/'source_manifest.json';one.write_text(json.dumps({'scenes':[row]},indent=2))
 result={'scene_id':row['scene_id'],'split':row['split'],'source':row['original'],'status':'preparing','commands':[]}
 def command(stage,cmd):
  log=folder/(stage+'.log')
  with log.open('x') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
  result['commands'].append({'stage':stage,'argv':cmd,'exit_code':r.returncode,'log':str(log)})
  if r.returncode:raise RuntimeError(f'{stage} exit {r.returncode}')
 try:
  assert hashlib.sha256(Path(row['original']).read_bytes()).hexdigest()==row['original_sha256'],'source revision changed'
  command('restore',[isaac,str(helpers/'restore_pilot.py'),'--manifest',str(one),'--out',str(folder/'assets'),'--splits',row['split']])
  restored=json.loads((folder/'assets/restore_report.json').read_text())['records'][0];source=Path(restored['restored'])
  assert (source.parent/'models').resolve().is_relative_to(folder/'assets')
  result['restored']=str(source)
  command('convert',[isaac,str(root/'main.py'),'no-mdl',str(source)])
  converted=source.with_name('start_result_raw_noMDL.usd');result['converted']=str(converted)
  conversion=folder/'conversion.json';conversion.write_text(json.dumps({'records':[{'scene_id':row['scene_id'],'source':str(source),'converted':str(converted)}]},indent=2))
  command('audit',[isaac,str(helpers/'audit_pairs.py'),'--report',str(conversion),'--out',str(folder/'geometry_audit.json')])
  result['status']='ready_for_target_selection'
 except Exception as exc:result.update(status='failed',error=repr(exc))
 result['elapsed_s']=time.time()-begin
 (folder/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 with lock:
  results.append(result);temp=a.out/'progress.tmp';temp.write_text(json.dumps({'planned':len(rows),'completed':len(results),'records':sorted(results,key=lambda r:r['scene_id'])},indent=2)+'\n');temp.replace(a.out/'progress.json');print(row['scene_id'],result['status'],flush=True)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(run,rows))
print('preparation terminal',flush=True)
