"""Resume only URI-dependency failures after the official material closure is complete."""
import argparse,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--closure',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[5];helpers=Path(__file__).parent;pilot=helpers.parent/'12_cviu_diagnostics';isaac=root/'scripts/isaac_python.sh'
while not a.closure.exists():time.sleep(15)
if json.loads(a.closure.read_text())['status']!='complete':raise SystemExit('Dependency download incomplete')
while True:
 progress=json.loads((a.workspace/'progress.json').read_text())
 if progress['completed']==progress['planned']:break
 time.sleep(15)
results=[]
for row in progress['records']:
 if row['status']!='failed':continue
 folder=a.workspace/row['scene_id'];repair=folder/'remote_material_repair';repair.mkdir(exist_ok=False);result={**row,'status':'repairing','commands':[]}
 def run(name,argv):
  with (repair/(name+'.log')).open('x') as log:r=subprocess.run([str(isaac),*map(str,argv)],cwd=root,stdout=log,stderr=subprocess.STDOUT)
  result['commands'].append({'step':name,'exit_code':r.returncode,'log':str(repair/(name+'.log'))})
  if r.returncode:raise RuntimeError(name+' failed')
 try:
  restored=json.loads((folder/'assets/restore_report.json').read_text())['records'][0];source=Path(restored['restored'])
  if any(not x.startswith('http') for x in restored['unresolved']):raise ValueError('Non-URI failure needs separate repair')
  run('localize',[helpers/'localize_remote_materials.py','--scene',source,'--workspace',folder/'assets','--closure',a.closure,'--out',repair/'localization.json'])
  run('convert',[root/'main.py','no-mdl',source]);converted=source.with_name('start_result_raw_noMDL.usd')
  conversion=repair/'conversion.json';conversion.write_text(json.dumps({'records':[{'scene_id':row['scene_id'],'source':str(source),'converted':str(converted)}]},indent=2))
  run('audit',[pilot/'audit_pairs.py','--report',conversion,'--out',repair/'geometry_audit.json'])
  result.update(status='ready_for_target_selection',restored=str(source),converted=str(converted));result.pop('error',None)
  (repair/'receipt.json').write_text(json.dumps(result,indent=2))
  run('targets',[helpers/'extract_target_pool.py','--receipt',repair/'receipt.json','--out',repair/'target_pool.json'])
 except Exception as e:result.update(status='failed',error=repr(e))
 (repair/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
 (a.workspace/'remote_repair_progress.json').write_text(json.dumps({'records':results},indent=2)+'\n');print(row['scene_id'],result['status'],flush=True)
