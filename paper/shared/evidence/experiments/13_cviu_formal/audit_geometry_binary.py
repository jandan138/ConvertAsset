"""Hash complete numeric buffers at time zero; do not rely on formatted array strings."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--ready',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 from pxr import Usd,UsdGeom
 records=[]
 for row in json.loads(a.ready.read_text())['scenes']:
  signatures={}
  for side in ['original','converted']:
   stage=Usd.Stage.Open(row[side]);xf=UsdGeom.XformCache(0);meshes={}
   for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
    if not prim.IsA(UsdGeom.Mesh):continue
    mesh=UsdGeom.Mesh(prim);digest=hashlib.sha256()
    values=[mesh.GetPointsAttr().Get(0),mesh.GetFaceVertexCountsAttr().Get(0),mesh.GetFaceVertexIndicesAttr().Get(0),xf.GetLocalToWorldTransform(prim)]
    for value in values:
     if value is None:digest.update(b'NONE');continue
     data=np.ascontiguousarray(np.asarray(value));assert data.dtype!=object
     digest.update(str(data.dtype).encode());digest.update(str(data.shape).encode());digest.update(data.tobytes())
    meshes[str(prim.GetPath())]=digest.hexdigest()
   signatures[side]=meshes
  result={'scene_id':row['scene_id'],'equal':signatures['original']==signatures['converted'],'mesh_counts':{k:len(v) for k,v in signatures.items()},'mesh_signatures':signatures,'root_hashes':{k:hashlib.sha256(Path(row[k]).read_bytes()).hexdigest() for k in ['original','converted']}}
  (a.out/(row['scene_id']+'.json')).write_text(json.dumps(result,indent=2)+'\n');records.append({k:v for k,v in result.items() if k!='mesh_signatures'});(a.out/'summary.json').write_text(json.dumps({'records':records},indent=2)+'\n');print(row['scene_id'],result['equal'],flush=True)
 return int(any(not r['equal'] for r in records))
if __name__=='__main__':raise SystemExit(main())
