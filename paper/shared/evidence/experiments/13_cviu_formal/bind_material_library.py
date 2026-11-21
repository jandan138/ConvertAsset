"""Rebind completed experiment copies to a qualified isolated MDL library."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path


def main():
 p=argparse.ArgumentParser();p.add_argument('--ready',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--captures',type=Path,required=True);p.add_argument('--sources',type=Path,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 receipt=json.loads((a.library/'repair_receipt.json').read_text());source=Path(receipt['source']).resolve();library=a.library.resolve();sources=a.sources.resolve()
 if library.is_relative_to(source) or sources.is_relative_to(source):raise ValueError('Experiment paths must be separate from source library')
 audit=json.loads(a.audit.read_text());failed={r['scene_id'] for r in audit['records'] if any('KooPbr' in e['text'] for e in r['material_errors'])};rows=[r for r in json.loads(a.ready.read_text())['scenes'] if r['scene_id'] in failed]
 complete={r['scene_id'] for r in json.loads((a.captures/'progress.json').read_text())['records']}
 running=subprocess.run(['ssh','-o','BatchMode=yes','dsw-4090','ps -eo args'],capture_output=True,text=True,check=True).stdout
 for row in rows:
  if row['scene_id'] not in complete:raise ValueError('Scene capture not finished')
  if any(row['scene_id'] in line and ('render_scene_views.py' in line or 'renderer_snapshot.py' in line) for line in running.splitlines()):raise ValueError('Scene currently rendering')
  root=sources/row['scene_id']
  if not root.is_dir() or not root.resolve().is_relative_to(sources):raise ValueError('Workspace escape')
 for file in receipt['files']:
  if hashlib.sha256(Path(file['source']).read_bytes()).hexdigest()!=file['source_sha256']:raise ValueError('Source MDL changed')
 a.out.mkdir(parents=True,exist_ok=False);changes=[]
 for row in rows:
  scene_changes=[]
  for folder,dirs,files in os.walk(sources/row['scene_id'],followlinks=False):
   for name in dirs+files:
    link=Path(folder)/name
    if link.is_symlink() and link.resolve()==source:
     before=str(link.readlink());temp=link.with_name(link.name+'.formal_library_new');temp.symlink_to(library,target_is_directory=True);temp.replace(link)
     scene_changes.append({'path':str(link),'before':before,'after':str(library)})
  changes.append({'scene_id':row['scene_id'],'changes':scene_changes})
  (a.out/'bindings.json').write_text(json.dumps({'library':str(library),'records':changes,'status':'rebound_requires_scene_recapture'},indent=2)+'\n')
 for file in receipt['files']:
  if hashlib.sha256(Path(file['source']).read_bytes()).hexdigest()!=file['source_sha256']:raise ValueError('Source MDL changed')
 (a.out/'ready_scenes.json').write_text(json.dumps({'scenes':rows,'selection':'Only scenes with runtime KooPbr errors; frozen scene IDs unchanged'},indent=2)+'\n')
 print('Scenes rebound:',len(rows),'links changed:',sum(len(r['changes']) for r in changes),flush=True)

if __name__=='__main__':main()
