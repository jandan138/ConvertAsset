"""Bounded recorded-pose geometry audit that never fabricates an engine report."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom,Gf
p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--last-step',type=int,default=300);a=p.parse_args();run=Path(a.run)
rows=[]
for line in (run/'poses_each_step.jsonl').open():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 if 0<=r['step']<=a.last_step:rows.append(r)
s=Usd.Stage.Open(str(run/'fixture.usda'));root='/World/_scene';tube=root+'/obj_sample_tube';cache=UsdGeom.XformCache()
def local_vertices(mesh,body):
 m=cache.GetLocalToWorldTransform(s.GetPrimAtPath(mesh))*cache.GetLocalToWorldTransform(s.GetPrimAtPath(body)).GetInverse()
 return np.asarray([m.Transform(Gf.Vec3d(*v)) for v in s.GetPrimAtPath(mesh).GetAttribute('points').Get()])
v=local_vertices(tube+'/Visual/GlassShell',tube);tube_scale=np.linalg.norm(np.asarray(cache.GetLocalToWorldTransform(s.GetPrimAtPath(tube)))[:3,:3],axis=1)
def mat(p,scale=None):
 m=np.eye(4);m[:3,:3]=Rotation.from_quat(p['orientation_xyzw']).as_matrix().T
 if scale is not None:m[:3,:3]*=scale[:,None]
 m[3,:3]=p['position'];return m
result={'scope':'Read-only recorded native post-step geometry, not an engine completion result; no cross-run frame substitution.','run':str(run.resolve()),'first_step':rows[0]['step'],'last_step':rows[-1]['step'],'links':{}}
for link in ['link7','link8']:
 path=root+'/lift2/lift2/lift2/fl/'+link;points=local_vertices(path+'/mesh',path);h=ConvexHull(points);minimum=points.min(0);maximum=points.max(0);records=[]
 for r in rows:
  m=mat(r['poses'][tube],tube_scale)@np.linalg.inv(mat(r['poses'][path]));xyz=v@m[:3,:3]+m[3,:3];xyz=xyz[np.all((xyz>=minimum)&(xyz<=maximum),axis=1)]
  depth=max(0.,float(-np.max(xyz@h.equations[:,:3].T+h.equations[:,3],axis=1).min())) if len(xyz) else 0.
  records.append({'step':r['step'],'depth_m':depth})
 result['links'][link]={'max':max(records,key=lambda r:r['depth_m']),'gt1mm_frames':[r['step'] for r in records if r['depth_m']>.001],'records':records}
(run/('grip_recorded_prefix_'+str(a.last_step)+'.json')).write_text(json.dumps(result,indent=2)+'\n');print({k:{'max':v['max'],'gt1mm_frames':v['gt1mm_frames']} for k,v in result['links'].items()})
