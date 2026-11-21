"""Geometry-only formal view proposals with off-center framing and exact ray checks."""
import argparse,hashlib,itertools,json,math
from pathlib import Path
import numpy as np

def intersects_triangles(origin,end,triangles,limit):
 if not len(triangles):return False
 direction=end-origin;e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0];h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10
 inv=np.divide(1.,det,out=np.zeros_like(det),where=valid);s=origin-triangles[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*(q@direction);t=inv*np.einsum('ij,ij->i',e2,q)
 return bool(np.any(valid&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-6)&(t<limit-1e-6)))

def aabb_entry(origin,end,lo,hi):
 d=end-origin;tmin=0.;tmax=1.
 for k in range(3):
  if abs(d[k])<1e-12:
   if origin[k]<lo[k] or origin[k]>hi[k]:return None
  else:
   t0,t1=sorted(((lo[k]-origin[k])/d[k],(hi[k]-origin[k])/d[k]));tmin=max(tmin,t0);tmax=min(tmax,t1)
   if tmin>tmax:return None
 return tmin

def attach_base_layer(camera_file,base_scene):
 from pxr import Sdf
 layer=Sdf.Layer.FindOrOpen(str(camera_file))
 if not layer:raise ValueError('Camera layer missing after save')
 layer.subLayerPaths=[str(base_scene)];layer.Save()

def main():
 p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--candidate-views',type=int,choices=[2,4],default=2);p.add_argument('--target-count',type=int,choices=range(1,9),default=8);p.add_argument('--elevations',type=float,nargs='+',default=[.25,.5,.8]);p.add_argument('--view-prefix',default='v');a=p.parse_args();row=json.loads(a.scene.read_text());pool=json.loads(Path(row['target_pool']).read_text());a.out.mkdir(parents=True,exist_ok=False)
 if not a.view_prefix.replace('_','').replace('-','').isalnum() or not all(math.isfinite(e) for e in a.elevations):raise ValueError('Invalid camera proposal options')
 from pxr import Usd,UsdGeom,UsdLux,Gf
 stage=Usd.Stage.Open(row['original']);bounds=UsdGeom.BBoxCache(0,[UsdGeom.Tokens.default_,UsdGeom.Tokens.render]);xforms=UsdGeom.XformCache(0);obstacles=[];cache={}
 for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
  if not prim.IsA(UsdGeom.Mesh) or UsdGeom.Imageable(prim).ComputeVisibility()==UsdGeom.Tokens.invisible:continue
  box=bounds.ComputeWorldBound(prim).ComputeAlignedRange()
  if not box.IsEmpty():obstacles.append((prim,np.array(box.GetMin()),np.array(box.GetMax())))
 up=Gf.Vec3d(0,0,1) if pool['up_axis']=='Z' else Gf.Vec3d(0,1,0);units=pool['meters_per_unit'];selected=[];excluded=[];jobs=[]
 for target in pool['selected']+pool['reserve']:
  lo=Gf.Vec3d(*target['bbox_min']);hi=Gf.Vec3d(*target['bbox_max']);center=(lo+hi)*.5;target_path=target['prim'];chosen=[];attempts=0
  for view in range(a.candidate_views):
   u,v=[(.3,.4),(.7,.6)][view%2]
   found=None
   for factor,elevation,angle in itertools.product([1.,1.3,1.8,2.4,.8],a.elevations,range(0,360,30)):
    if any(min(abs(angle-c['angle']),360-abs(angle-c['angle']))<30 for c in chosen):continue
    attempts+=1;distance=max((hi-lo).GetLength()*factor,.5/units);theta=math.radians(angle)
    horizontal=Gf.Vec3d(math.cos(theta),math.sin(theta),0) if pool['up_axis']=='Z' else Gf.Vec3d(math.cos(theta),0,math.sin(theta))
    eye=center+horizontal*distance+up*distance*elevation;view_matrix=Gf.Matrix4d().SetLookAt(eye,center,up);points=[view_matrix.Transform(Gf.Vec3d(*xyz)) for xyz in itertools.product(*zip(lo,hi))]
    if any(q[2]>=-.001/units for q in points):continue
    pixels=[(u+q[0]/(-q[2])*24/36,v-q[1]/(-q[2])*24/27) for q in points];box=[min(q[0] for q in pixels),min(q[1] for q in pixels),max(q[0] for q in pixels),max(q[1] for q in pixels)];area=(box[2]-box[0])*(box[3]-box[1])
    if box[0]<.02 or box[1]<.02 or box[2]>.98 or box[3]>.98 or not .002<=area<=.5:continue
    start=np.asarray(eye);end=np.asarray(center);limit=aabb_entry(start,end,np.asarray(lo),np.asarray(hi));limit=1. if limit is None else limit;blocked=False
    for prim,blo,bhi in obstacles:
     key=str(prim.GetPath())
     if key==target_path or key.startswith(target_path+'/') or target_path.startswith(key+'/'):continue
     entry=aabb_entry(start,end,blo,bhi)
     if entry is None or entry>=limit-1e-6:continue
     if key not in cache:
      mesh=UsdGeom.Mesh(prim);pts=np.asarray(mesh.GetPointsAttr().Get(),dtype=float);matrix=np.asarray(xforms.GetLocalToWorldTransform(prim));world=(np.c_[pts,np.ones(len(pts))]@matrix)[:,:3];indices=np.asarray(mesh.GetFaceVertexIndicesAttr().Get());counts=mesh.GetFaceVertexCountsAttr().Get();tri=[];offset=0
      for count in counts:
       face=indices[offset:offset+count];offset+=count
       tri.extend((face[0],face[j],face[j+1]) for j in range(1,count-1))
      cache[key]=world[np.asarray(tri,dtype=int)] if tri else np.zeros((0,3,3))
     if intersects_triangles(start,end,cache[key],limit):blocked=True;break
    if not blocked:found={'matrix':view_matrix.GetInverse(),'angle':angle,'u':u,'v':v,'box':box};break
   if found is None:break
   chosen.append(found)
  if len(chosen)<2:
   excluded.append({'prim':target_path,'category':target['category'],'reason':'fewer_than_two_framed_clear_candidates','attempts':attempts});continue
  object_id=hashlib.sha256(target_path.encode()).hexdigest()[:16]
  for view,camera in enumerate(chosen):
   for condition in ['original','converted']:
    path=a.out/object_id/f'{a.view_prefix}{view}_{condition}.usda';path.parent.mkdir(parents=True,exist_ok=True);wrapper=Usd.Stage.CreateNew(str(path));UsdGeom.SetStageUpAxis(wrapper,pool['up_axis']);UsdGeom.SetStageMetersPerUnit(wrapper,units)
    cam=UsdGeom.Camera.Define(wrapper,'/DiagnosticCamera');cam.AddTransformOp().Set(camera['matrix']);cam.CreateFocalLengthAttr().Set(24);cam.CreateHorizontalApertureAttr().Set(36);cam.CreateVerticalApertureAttr().Set(27);cam.CreateHorizontalApertureOffsetAttr().Set((.5-camera['u'])*36);cam.CreateVerticalApertureOffsetAttr().Set((camera['v']-.5)*27);cam.CreateClippingRangeAttr().Set(Gf.Vec2f(.001/units,1000/units));UsdLux.DomeLight.Define(wrapper,'/DiagnosticLight').CreateIntensityAttr().Set(1000);wrapper.GetRootLayer().Save();del cam,wrapper;attach_base_layer(path,row[condition])
    jobs.append({'pair_id':f"{row['scene_id']}:{object_id}:{a.view_prefix}{view}",'scene_id':row['scene_id'],'target_prim':target_path,'category':target['category'],'condition':condition,'query':f"Point to the {target['category'].replace('_',' ')} in the image.",'stage':str(path),'resolution':[1024,768],'projected_bbox_normalized':camera['box'],'status':'geometry_proposal_requires_original_image_qa','requires_label_review':target.get('requires_label_review',False)})
  selected.append({'prim':target_path,'category':target['category'],'object_id':object_id,'attempts':attempts});print('selected',row['scene_id'],len(selected),target['category'],flush=True)
  if len(selected)==a.target_count:break
 result={'scene_id':row['scene_id'],'selected':selected,'excluded':excluded,'jobs':jobs,'candidate_views_requested':a.candidate_views,'target_count_requested':a.target_count,'camera_elevations':a.elevations,'view_prefix':a.view_prefix,'status':('proposed_16_pairs' if a.candidate_views==2 else 'proposed_candidate_views') if len(selected)==a.target_count else 'insufficient_geometry_candidates'}
 (a.out/'jobs.json').write_text(json.dumps(result,indent=2)+'\n')
 return int(len(selected)!=a.target_count)
if __name__=='__main__':raise SystemExit(main())
