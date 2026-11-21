"""Build a preparation column, then persist settled grains as the r4 initial state."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_compact_powder_scene import build


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preparation_positions(floor,count,radius,seed):
    bound = radius*1.182056
    spacing = 2*bound+.00014
    limit = .024-bound-.00075-.00012
    if count<=0 or radius<=0 or limit<=0:
        raise ValueError('Invalid preparation count or grain radius')
    extent = math.ceil(.024/spacing)
    points = []
    rng = random.Random(seed)
    layer = 0
    while len(points)<count:
        z = floor+bound+.00015+layer*spacing*math.sqrt(2/3)
        for iy in range(-extent,extent+1):
            y = iy*spacing*math.sqrt(3)/2+(layer%2)*spacing*math.sqrt(3)/6
            for ix in range(-extent,extent+1):
                x = (ix+.5*(iy%2)+.5*(layer%2))*spacing
                if math.hypot(x,y)<limit and len(points)<count:
                    points.append(tuple(v+rng.uniform(-1e-5,1e-5) for v in (x,y,z)))
        layer += 1
    return points


def canonical_grains(points,orientations,bottle_pose,initial_xyz):
    import numpy as np
    # Records store body poses xyzw, but particle orientations wxyz.
    q = np.asarray([bottle_pose[6],*-np.asarray(bottle_pose[3:6])],dtype=float)
    q /= np.linalg.norm(q)
    v = points-np.asarray(bottle_pose[:3])
    cross = 2*np.cross(q[1:],v)
    positions = v+q[0]*cross+np.cross(q[1:],cross)+np.asarray(initial_xyz)
    rotations = np.empty_like(orientations,dtype=float)
    rotations[:,0] = q[0]*orientations[:,0]-orientations[:,1:]@q[1:]
    rotations[:,1:] = (q[0]*orientations[:,1:]+orientations[:,0,None]*q[1:]
                       +np.cross(q[1:],orientations[:,1:]))
    rotations /= np.linalg.norm(rotations,axis=1,keepdims=True)
    return positions,rotations


def prepare(base,model,out,count,radius,seed):
    data = json.loads(model.read_text())
    floor = data['metadata']['insert_top_m']
    build(base,model,out,count,radius,seed,240,positions=preparation_positions(floor,count,radius,seed))
    path = out/'scene_config.json'
    cfg = json.loads(path.read_text())
    cfg.update(schema_version='task09_full_powder.v4',revision='r4',initial_state='preparation_gravity_column',
               target_headspace_m=[.003,.007],powder_surface_target_m=.095,
               preparation_only=True)
    cfg.pop('qualified_runtime',None)
    path.write_text(json.dumps(cfg,indent=2))


def bake(source,run,out):
    import numpy as np
    from pxr import Usd,Sdf,Gf
    cfg = json.loads((source/'scene_config.json').read_text())
    report = json.loads((run/'report.json').read_text())
    if (report.get('status')!='passed' or report.get('mode')!='settle'
            or not report.get('runtime','').startswith('4.5')
            or report.get('scene_sha256')!=sha(source/'scene.usda')
            or report.get('engine_errors')!=[] or report.get('requested_seconds',0)<8
            or not report.get('checks',{}).get('retained')):
        raise ValueError('Complete healthy preparation settlement required')
    with np.load(run/'states.npz',allow_pickle=False) as states:
        paths = states['paths'].tolist()
        body_paths = states['body_paths'].tolist()
        bottle = states['body_poses'][-1,body_paths.index(cfg['paths']['bottle'])]
        points,quats = canonical_grains(states['positions'][-1],states['orientations'][-1],bottle,cfg['bottle_xyz'])
    expected = [f'/World/obj_powder_grain_{i:05d}' for i in range(cfg['count'])]
    if paths!=expected or not np.isfinite(points).all() or not np.isfinite(quats).all():
        raise ValueError('Incorrect or nonfinite preparation recording')
    shutil.copytree(source,out)
    stage = Usd.Stage.Open(str(out/'scene.usda'))
    with Sdf.ChangeBlock():
        for path,point,q in zip(paths,points,quats):
            spec = stage.GetRootLayer().GetPrimAtPath(path)
            spec.attributes['xformOp:translate'].default = Gf.Vec3d(*point)
            spec.attributes['xformOp:orient'].default = Gf.Quatf(float(q[0]),Gf.Vec3f(*map(float,q[1:])))
    stage.GetRootLayer().Save()
    cfg.update(initial_state='presettled',preparation_only=False,status='candidate',
               preparation_scene_sha256=sha(source/'scene.usda'),
               preparation_report_sha256=sha(run/'report.json'),
               preparation_states_sha256=sha(run/'states.npz'),
               presettled_seconds=report['requested_seconds'])
    cfg.pop('qualified_runtime',None)
    (out/'scene_config.json').write_text(json.dumps(cfg,indent=2))
    evidence = out/'preparation_evidence'
    evidence.mkdir()
    shutil.copy2(run/'report.json',evidence/'report.json')
    print(json.dumps({'out':str(out),'scene_sha256':sha(out/'scene.usda'),'count':len(points)}))


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command',required=True)
    prep = sub.add_parser('prepare')
    for name in ('base','model','out'):
        prep.add_argument('--'+name,type=Path,required=True)
    prep.add_argument('--count',type=int,default=10240)
    prep.add_argument('--radius',type=float,default=.0007)
    prep.add_argument('--seed',type=int,default=42)
    persist = sub.add_parser('bake')
    for name in ('source','run','out'):
        persist.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    if a.command=='prepare':
        prepare(a.base,a.model,a.out,a.count,a.radius,a.seed)
    else:
        bake(a.source,a.run,a.out)
