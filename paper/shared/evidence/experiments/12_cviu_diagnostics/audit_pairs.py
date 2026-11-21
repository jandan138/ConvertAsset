"""Compare authored mesh geometry and world transforms in restored pilot pairs."""
import argparse,hashlib,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 from pxr import Usd,UsdGeom,UsdUtils
 results=[]
 for row in json.loads(a.report.read_text())['records']:
  entry={'scene_id':row['scene_id']}
  for side,key in [('original','source'),('converted','converted')]:
   stage=Usd.Stage.Open(row[key]);cache=UsdGeom.XformCache(0);meshes={}
   for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
    if not prim.IsA(UsdGeom.Mesh):continue
    m=UsdGeom.Mesh(prim)
    values=[str(m.GetPointsAttr().Get()),str(m.GetFaceVertexCountsAttr().Get()),str(m.GetFaceVertexIndicesAttr().Get()),str(cache.GetLocalToWorldTransform(prim))]
    meshes[str(prim.GetPath())]=hashlib.sha256(repr(values).encode()).hexdigest()
   _,_,missing=UsdUtils.ComputeAllDependencies(row[key])
   entry[side]={'meshes':meshes,'unresolved':missing}
  entry['geometry_equal']=entry['original']['meshes']==entry['converted']['meshes']
  results.append(entry);print(row['scene_id'],entry['geometry_equal'],len(entry['original']['meshes']),len(entry['converted']['unresolved']),flush=True)
 with a.out.open('x') as f:json.dump({'records':results},f,indent=2)
 return int(any(not x['geometry_equal'] or x['original']['unresolved'] or x['converted']['unresolved'] for x in results))
if __name__=='__main__':raise SystemExit(main())
