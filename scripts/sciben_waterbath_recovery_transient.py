"""Read-only actual-pose finite-difference evidence around a grasp transient."""
import json,argparse
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run)
poses={r['step']:r for r in map(json.loads,(run/'poses_each_step.jsonl').open())};events={}
for r in map(json.loads,(run/'contact_events_each_header.jsonl').open()):
    if r['action_step'] is None:continue
    if 140<=r['action_step']<=152 and any(x.endswith('/fl/link7') for x in r['actors']) and any(x.endswith('/obj_sample_tube') for x in r['actors']) and r['minimum_separation_m'] is not None:
        i=r['action_step']
        if i not in events or r['minimum_separation_m']<events[i]['minimum_separation_m']:events[i]=r
geom=json.loads((run/'grip_geometry_audit.json').read_text());raw={r['step']:r['max_raw_vertex_depth_m'] for r in geom['links']['link7']['records']};tube='/World/_scene/obj_sample_tube';finger='/World/_scene/lift2/lift2/lift2/fl/link7';rows=[]
for i,e in sorted(events.items()):
    point=np.array(e['worst_position']);normal=np.array(e['worst_normal']);v={};body={}
    for name,path in [('tube',tube),('finger7',finger)]:
        cur=poses[i]['poses'][path];old=poses[i-1]['poses'][path];linear=(np.array(cur['position'])-np.array(old['position']))*120;angular=(Rotation.from_quat(cur['orientation_xyzw'])*Rotation.from_quat(old['orientation_xyzw']).inv()).as_rotvec()*120;v[name]=linear+np.cross(angular,point-np.array(cur['position']));body[name]={'pose':cur,'linear_velocity_m_s':linear.tolist(),'angular_velocity_rad_s':angular.tolist()}
    relative=v['tube']-v['finger7'];rows.append({'action_step':i,'native_post_count':poses[i]['native_count'],'raw_depth_m':raw.get(i,0),'sdk_separation_m':e['minimum_separation_m'],'sdk_contact_point':point.tolist(),'sdk_normal':normal.tolist(),'sdk_actors':e['actors'],'sdk_colliders':e['colliders'],'relative_point_speed_m_s':float(np.linalg.norm(relative)),'relative_velocity_along_sdk_normal_m_s':float(relative@normal),'bodies':body})
result={'scope':'This run only, finite differences of actual native120 post-fetch poses, not commanded target velocities; SDK point/normal from same-frame contact event. Velocity estimates average one step and normal sign follows SDK actor ordering.','sdk_gt1mm_frames':[r['action_step'] for r in rows if r['sdk_separation_m']<-.001],'sdk_gt1mm_duration_s':sum(r['sdk_separation_m']<-.001 for r in rows)/120,'gt1mm_frames':[r['action_step'] for r in rows if r['raw_depth_m']>.001],'gt1mm_duration_s':sum(r['raw_depth_m']>.001 for r in rows)/120,'rows':rows};(run/'finger146_transient_audit.json').write_text(json.dumps(result,indent=2)+'\n');print([{k:r[k] for k in ['action_step','raw_depth_m','sdk_separation_m','relative_point_speed_m_s']} for r in rows])
