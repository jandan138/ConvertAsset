"""Materialize source pilot layer closures without editing dataset or historic outputs."""
import argparse,json,shutil,hashlib
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--splits',nargs='+',default=['pilot']);a=p.parse_args()
 from pxr import Usd,UsdUtils
 a.out.mkdir(parents=True,exist_ok=False)
 records=[]
 for row in json.loads(a.manifest.read_text())['scenes']:
  if row['split'] not in a.splits:continue
  source=Path(row['original']).resolve();family=source.parent.parent.parent
  root=a.out/row['scene_id']; scene=root/'scenes'/row['scene_id'];scene.mkdir(parents=True)
  target=scene/source.name;shutil.copy2(source,target)
  # Read through source links only during dependency discovery.
  (scene/'models').symlink_to(family/'models',target_is_directory=True)
  (scene/'Materials').symlink_to(family/'Materials',target_is_directory=True)
  layers,_,_=UsdUtils.ComputeAllDependencies(str(target))
  copies=[]
  for layer in layers:
   src=Path(layer.realPath).resolve()
   if src==target.resolve():continue
   try: rel=src.relative_to(family.resolve())
   except ValueError: raise ValueError(f'External layer requires explicit mapping: {src}')
   copies.append((src,root/rel))
  (scene/'models').unlink()
  for src,dst in copies:
   dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  if not (root/'models').exists():raise RuntimeError('No model layers discovered')
  (scene/'models').symlink_to(root/'models',target_is_directory=True)
  (root/'Materials').symlink_to(family/'Materials',target_is_directory=True)
  # Shared Materials directory is the source dataset contract. Never substitute basenames.
  parents={dst.parent for _,dst in copies}
  for parent in parents:
   m=parent/'Materials'
   if not m.exists():m.symlink_to(family/'Materials',target_is_directory=True)
  stage=Usd.Stage.Open(str(target)); restored_layers,_,missing=UsdUtils.ComputeAllDependencies(str(target))
  outside=[l.realPath for l in restored_layers if l.realPath and not Path(l.realPath).resolve().is_relative_to(a.out.resolve())]
  record={'scene_id':row['scene_id'],'source':str(source),'restored':str(target),'copied_layers':len(copies),'prim_count':sum(1 for _ in stage.Traverse()),'unresolved':missing,'external_usd_layers':outside,'split':row['split'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
  records.append(record)
  (a.out/'restore_report.json').write_text(json.dumps({'records':records},indent=2)+'\n')
  print(row['scene_id'],len(copies),len(missing),flush=True)
 return int(any(r['unresolved'] or r['external_usd_layers'] for r in records))
if __name__=='__main__':raise SystemExit(main())
