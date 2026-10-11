"""Offline, read-only native trace comparison; never opens simulator or runtime writes."""
import argparse,collections,hashlib,json,math
from pathlib import Path


def parse_log(path, text=None):
    result={'poses':[],'contacts':[],'diagnostic_errors':[],'engine_error_lines':[]}
    for line in (Path(path).read_text(errors='replace') if text is None else text).splitlines():
        for marker,key in [('[WB_NATIVE_POSE] ','poses'),('[WB_NATIVE_CONTACT] ','contacts'),('[WB_NATIVE_DIAG_ERROR] ','diagnostic_errors')]:
            if marker in line:
                try:result[key].append(json.loads(line.split(marker,1)[1]))
                except ValueError:pass  # May be a partial last line in a running log.
        if any(s in line for s in ['CUDA error','mArtiSolveBlockPartitionFunction','artiPropagateImpulses2','PxgCudaUtils.h']):result['engine_error_lines'].append(line)
    return result


def rack_region(row):
    paths=row['colliders'];tube=next((p for p in paths if '/obj_sample_tube/' in p),None);rack=next((p for p in paths if '/obj_tube_rack/' in p),None)
    if not tube or not rack:return None
    surface='Cube_015' if rack.endswith('/Cube_015') else rack.rsplit('/',1)[-1]
    region='solid_cap' if tube.endswith('/SolidCap') else 'upper_remainder' if '/RigidSolidBottom/Upper_' in tube else 'old_bottom' if '/RigidWallProxy/Bottom_' in tube else 'straight_lip' if '/RigidWallProxy/Wall_' in tube else 'other'
    return surface+' | '+region


def contact_stats(rows):
    rows=list(rows);frames=collections.Counter();negative_frames=collections.Counter();shapes=set();negative_bearing=0;negative_upper=0;known_nonnegative=0;all_exact=all('negative_points' in r for r in rows);minimum=None;worst=None;negative_sum=0
    for r in rows:
        frames[r['index']]+=r['points'];shapes.update(p for p in r['colliders'] if '/obj_sample_tube/' in p);sep=r.get('minimum_separation_m')
        if sep is not None and (minimum is None or sep<minimum):minimum=sep;worst=r
        if sep is not None and sep<0:negative_bearing+=1;negative_upper+=r['points']
        elif sep is not None:known_nonnegative+=r['points']
        if 'negative_points' in r:
            assert r['negative_points']+r['nonnegative_points']==r['points']
            negative_sum+=r['negative_points'];negative_frames[r['index']]+=r['negative_points']
    return {'headers':len(rows),'points':sum(frames.values()),'contact_native_frames':len(frames),'max_points_per_frame':max(frames.values(),default=0),'negative_bearing_headers':negative_bearing,'negative_points_exact':negative_sum if all_exact else None,'negative_point_bounds':[negative_bearing,negative_upper],'certain_nonnegative_points_from_minimum':known_nonnegative,'max_negative_points_per_frame':max(negative_frames.values(),default=0) if all_exact else None,'minimum_separation_m':minimum,'tube_shape_count':len(shapes),'worst':worst}


def summarize(contacts,low,high):
    selected=[r for r in contacts if low<=r['index']<=high];groups=collections.defaultdict(list);rigid_pbd=[];finger_rack=[]
    for r in selected:
        key=rack_region(r)
        if key:groups[key].append(r)
        if any('/PBDBottomProxy/' in p or '/WaterbathCollision/' in p for p in r['colliders']):rigid_pbd.append(r)
        if any('/obj_tube_rack/' in p for p in r['colliders']) and any('/lift2/' in p for p in r['colliders']):finger_rack.append(r)
    return {'native_index_range':[low,high],'tube_rack':contact_stats(r for r in selected if rack_region(r)),'regions':{k:contact_stats(v) for k,v in groups.items()},'robot_rack':contact_stats(finger_rack),'pbd_named_rigid_headers':len(rigid_pbd),'pbd_scope':'Exact PBD-only scope names PBDBottomProxy and WaterbathCollision; full static filtered membership receipt remains authoritative.'}


def compare_poses(new,old):
    before={(r['epoch'],r['index']):r for r in old};rows=[]
    for r in new:
        prev=before.get((r['epoch'],r['index']))
        if not prev:continue
        path='/World/_scene/obj_sample_tube'
        if path not in r['poses'] or path not in prev['poses']:continue
        a=r['poses'][path]['position'];b=prev['poses'][path]['position'];j=r.get('joint_positions');k=prev.get('joint_positions')
        rows.append({'native_index':r['index'],'tube_position_difference_m':math.dist(a,b),'maximum_joint_difference_mixed_units':max(abs(x-y) for x,y in zip(j,k)) if j and k else None,'scope':'Same native index only; compare actual joints before inferring equal source-action mapping.'})
    return rows


def local_worst_geometry(contacts,poses,low=3200):
    import numpy as np
    from scipy.spatial.transform import Rotation
    lookup={(r['epoch'],r['index']):r for r in poses};groups=collections.defaultdict(list);path='/World/_scene/obj_sample_tube'
    for r in contacts:
        key=rack_region(r);pose=lookup.get((r['epoch'],r['index']))
        if not key or r['index']<low or r.get('minimum_separation_m') is None or r['minimum_separation_m']>=0 or not pose or 'worst_position' not in r:continue
        p=pose['poses'][path];local=Rotation.from_quat(p['orientation_xyzw']).inv().apply(np.asarray(r['worst_position'])-np.asarray(p['position']))
        groups[key].append({'native_index':r['index'],'local_position_m':local.tolist(),'minimum_separation_m':r['minimum_separation_m'],'negative_points':r.get('negative_points')})
    return {'scope':'Only deepest header point projected with same-call pose; solver-phase difference can invalidate surface interpretation during fast motion. Not a penetration measurement. Tube unit scale must be verified separately.','regions':{k:{'negative_bearing_headers':len(v),'local_z_range_m':[min(x['local_position_m'][2] for x in v),max(x['local_position_m'][2] for x in v)],'worst_points_within10um_cut':sum(abs(x['local_position_m'][2]-.0009999)<.00001 for x in v),'worst':min(v,key=lambda x:x['minimum_separation_m'])} for k,v in groups.items()}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--log',required=True);p.add_argument('--old',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False);raw=Path(a.log).read_bytes();data=parse_log(a.log,raw.decode(errors='replace'));old=Path(a.old);old_contacts=[json.loads(x) for x in (old/'contacts.jsonl').read_text().splitlines()];old_poses=[json.loads(x) for x in (old/'poses.jsonl').read_text().splitlines()];last=max((r['index'] for r in data['poses']),default=-1)
    for key in ['poses','contacts']:
        with (out/(key+'.jsonl')).open('w') as f:
            for row in data[key]:f.write(json.dumps(row)+'\n')
    result={'scope':'Snapshot of read-only native log; completion must be established by original-core receipt, not trace extent. V1 negative counts are bounds only; V2 reports exact sign counts.','log':str(Path(a.log).resolve()),'snapshot_log_bytes':len(raw),'snapshot_log_sha256':hashlib.sha256(raw).hexdigest(),'pose_rows':len(data['poses']),'contact_rows':len(data['contacts']),'last_native_index':last,'diagnostic_errors':data['diagnostic_errors'],'engine_error_lines':data['engine_error_lines'][:16],'old_failure_window':{'old':summarize(old_contacts,3302,3332),'new':summarize(data['contacts'],3302,3332)},'new_return_window':summarize(data['contacts'],3200,last),'last_pose':data['poses'][-1] if data['poses'] else None,'same_index_pose_comparison':compare_poses(data['poses'],old_poses),'new_negative_header_local_geometry':local_worst_geometry(data['contacts'],data['poses'])};(out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['pose_rows','contact_rows','last_native_index','diagnostic_errors','engine_error_lines']}))
if __name__=='__main__':main()
