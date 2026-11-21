"""Localize known official material URLs in independent USD copies only."""
import argparse,hashlib,json
from pathlib import Path
from fetch_material_closure import normalize

def main():
 p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--closure',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 from pxr import UsdUtils
 closure=json.loads(a.closure.read_text())
 if closure['status']!='complete':raise ValueError('Material closure incomplete')
 mapping={r['url']:r for r in closure['files']}
 for r in mapping.values():assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256']
 layers,_,before=UsdUtils.ComputeAllDependencies(str(a.scene));records=[]
 for layer in layers:
  path=Path(layer.realPath).resolve()
  if not path.is_relative_to(a.workspace.resolve()):raise ValueError('Refuse writing external USD '+str(path))
  changes=[];old_hash=hashlib.sha256(path.read_bytes()).hexdigest()
  def rewrite(asset):
   url=normalize(asset)
   if url in mapping:
    new=mapping[url]['path'];changes.append({'old':asset,'new':new,'url':url});return new
   return asset
  UsdUtils.ModifyAssetPaths(layer,rewrite)
  if changes:
   layer.Save();records.append({'layer':str(path),'before_sha256':old_hash,'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'changes':changes})
 _,_,after=UsdUtils.ComputeAllDependencies(str(a.scene))
 with a.out.open('x') as f:json.dump({'scene':str(a.scene),'before_unresolved':before,'after_unresolved':after,'layers':records,'status':'localized' if not after else 'unresolved'},f,indent=2)
 print('localized layers',len(records),'remaining dependencies',len(after),flush=True)
 return int(bool(after))
if __name__=='__main__':raise SystemExit(main())
