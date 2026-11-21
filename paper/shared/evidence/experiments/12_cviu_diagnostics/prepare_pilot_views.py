"""Author candidate natural-scene cameras; projections remain unvalidated until visual QA."""
import json,itertools,argparse,math,importlib.util
import numpy as np
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 from pxr import Usd,UsdGeom,UsdLux,Gf
 a.out.mkdir(parents=True,exist_ok=False)
 legacy=Path(__file__).resolve().parent.parent/'06_grscenes_vlm_grounding/plan_visibility_aware_views.py'
 spec=importlib.util.spec_from_file_location('visibility',legacy);visibility=importlib.util.module_from_spec(spec);spec.loader.exec_module(visibility)
 visibility_records=[]
 rows=json.loads((a.workspace/'target_candidates.json').read_text())['records']; jobs=[]
 selections=[['couch','laptop'],['couch','microwave'],['stool','toy']]
 for row,categories in zip(rows,selections):
  targets=row['targets'];up=Gf.Vec3d(0,0,1) if row['up_axis']=='Z' else Gf.Vec3d(0,1,0)
  original=Usd.Stage.Open(row['stage']);bounds=UsdGeom.BBoxCache(0,[UsdGeom.Tokens.default_,UsdGeom.Tokens.render]);obstacles=[];triangle_cache={};xforms=UsdGeom.XformCache(0)
  for prim in Usd.PrimRange.Stage(original,Usd.TraverseInstanceProxies()):
   if not prim.IsA(UsdGeom.Mesh) or UsdGeom.Imageable(prim).ComputeVisibility()==UsdGeom.Tokens.invisible:continue
   box=bounds.ComputeWorldBound(prim).ComputeAlignedRange()
   if box.IsEmpty():continue
   obstacles.append({'prim':prim,'prim_path':str(prim.GetPath()),'bbox':{'min':list(box.GetMin()),'max':list(box.GetMax())}})
  for category in categories:
   matches=[x for x in targets if x['category']==category]
   if len(matches)!=1:raise ValueError((row['scene_id'],category,len(matches)))
   target=matches[0];lo=Gf.Vec3d(*target['bbox_min']);hi=Gf.Vec3d(*target['bbox_max']);c=(lo+hi)*.5
   blockers=[o for o in obstacles if not (o['prim_path'].startswith(target['prim']) or target['prim'].startswith(o['prim_path']))]
   candidates=[]
   for factor in [1.0,.8,.6,1.2,1.5]:
    distance=max((hi-lo).GetLength()*factor,.5/row['meters_per_unit'])
    for elevation in [.25,.5,.8]:
     for angle in range(0,360,30):
      theta=math.radians(angle)
      horizontal=Gf.Vec3d(math.cos(theta),math.sin(theta),0) if row['up_axis']=='Z' else Gf.Vec3d(math.cos(theta),0,math.sin(theta))
      eye=c+horizontal*distance+up*distance*elevation
      look=c+up*distance*.08
      interval=visibility.segment_aabb_interval(list(eye),list(c),{'min':list(lo),'max':list(hi)})
      limit=interval['t_enter'] if interval else 1.0
      check={'status':'centerline_clear','blocker_prim_path':None}
      for obstacle in blockers:
       coarse=visibility.segment_aabb_interval(list(eye),list(c),obstacle['bbox'])
       if coarse is None or coarse['t_enter']>=limit-1e-6:continue
       key=obstacle['prim_path']
       if key not in triangle_cache:
        mesh=UsdGeom.Mesh(obstacle['prim']);points=np.asarray(mesh.GetPointsAttr().Get(),dtype=float)
        matrix=np.asarray(xforms.GetLocalToWorldTransform(obstacle['prim']),dtype=float)
        world=(np.c_[points,np.ones(len(points))]@matrix)[:,:3]
        indices=np.asarray(mesh.GetFaceVertexIndicesAttr().Get(),dtype=int);counts=mesh.GetFaceVertexCountsAttr().Get();tris=[];offset=0
        for count in counts:
         face=indices[offset:offset+count];offset+=count
         for j in range(1,count-1):tris.append((face[0],face[j],face[j+1]))
        triangle_cache[key]=world[np.asarray(tris,dtype=int)] if tris else np.zeros((0,3,3))
       t=triangle_cache[key]
       if not len(t):continue
       origin=np.asarray(eye);direction=np.asarray(c-eye);edge1=t[:,1]-t[:,0];edge2=t[:,2]-t[:,0]
       h=np.cross(direction,edge2);det=np.einsum('ij,ij->i',edge1,h);valid=np.abs(det)>1e-10
       inv=np.divide(1.,det,out=np.zeros_like(det),where=valid);delta=origin-t[:,0]
       u=inv*np.einsum('ij,ij->i',delta,h);q=np.cross(delta,edge1);v=inv*(q@direction);distance_t=inv*np.einsum('ij,ij->i',edge2,q)
       if np.any(valid&(u>=0)&(v>=0)&(u+v<=1)&(distance_t>1e-6)&(distance_t<limit-1e-6)):
        check={'status':'blocked_triangle_centerline','blocker_prim_path':key};break
      visibility_records.append({'scene':row['scene_id'],'target':target['prim'],'factor':factor,'angle':angle,'elevation':elevation,**check})
      if check['status']=='centerline_clear':candidates.append((eye,look,angle,factor,elevation))
   chosen=[]
   for candidate in candidates:
    if not chosen or min(abs(candidate[2]-chosen[0][2]),360-abs(candidate[2]-chosen[0][2]))>=30:
     chosen.append(candidate)
    if len(chosen)==2:break
   if len(chosen)!=2:
    (a.out/'visibility.json').write_text(json.dumps(visibility_records,indent=2))
    raise ValueError(f'Insufficient unobstructed candidates: {row["scene_id"]} {category}')
   for view,(eye,look,angle,factor,elevation) in enumerate(chosen):
    matrix=Gf.Matrix4d().SetLookAt(eye,look,up).GetInverse()
    for condition in ['original','converted']:
     src=Path(row['stage']);src=src if condition=='original' else src.with_name('start_result_raw_noMDL.usd')
     output=a.out/row['scene_id']/category/f'v{view}_{condition}.usda';output.parent.mkdir(parents=True,exist_ok=True)
     stage=Usd.Stage.CreateNew(str(output));stage.GetRootLayer().subLayerPaths=[str(src)];UsdGeom.SetStageUpAxis(stage,row['up_axis']);UsdGeom.SetStageMetersPerUnit(stage,row['meters_per_unit'])
     cam=UsdGeom.Camera.Define(stage,'/DiagnosticCamera');cam.AddTransformOp().Set(matrix);cam.CreateFocalLengthAttr().Set(24);cam.CreateHorizontalApertureAttr().Set(36);cam.CreateVerticalApertureAttr().Set(27);cam.CreateClippingRangeAttr().Set(Gf.Vec2f(.001/row['meters_per_unit'],1000/row['meters_per_unit']))
     UsdLux.DomeLight.Define(stage,'/DiagnosticLight').CreateIntensityAttr().Set(1000)
     camera=cam.GetCamera(0);vp=camera.frustum.ComputeViewMatrix()*camera.frustum.ComputeProjectionMatrix()
     points=[vp.Transform(Gf.Vec3d(*v)) for v in itertools.product(*zip(lo,hi))]
     pixels=[((q[0]+1)*512,(1-q[1])*384) for q in points]
     box=[min(x[0] for x in pixels),min(x[1] for x in pixels),max(x[0] for x in pixels),max(x[1] for x in pixels)]
     stage.GetRootLayer().Save()
     jobs.append({'pair_id':f"{row['scene_id']}:{category}:v{view}",'condition':condition,'scene_id':row['scene_id'],'target_prim':target['prim'],'category':category,'query':f'Point to the {category} in the image.','stage':str(output),'camera':'/DiagnosticCamera','resolution':[1024,768],'projected_world_bbox':box,'status':'candidate_not_visibility_validated'})
 (a.out/'visibility.json').write_text(json.dumps(visibility_records,indent=2)+'\n')
 (a.out/'jobs.json').write_text(json.dumps({'jobs':jobs},indent=2)+'\n');print(len(jobs),'candidate images')
if __name__=='__main__':main()
