"""Read-only cup-release trace attribution; independently estimated action alignment."""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np
from sciben_waterbath_recovery_trace_analysis import parse_log,contact_stats

ARM_DOF_INDICES=[10,12,14,16,18,20,9,11,13,15,17,19]
SOURCE_ARM_COLUMNS=[0,1,2,3,4,5,8,9,10,11,12,13]


def estimate_alignment(poses,commands,offsets=range(0,701)):
    rows=[r for r in poses if r['index']>=600 and r.get('joint_positions') is not None and len(r['joint_positions'])==25]
    if not rows:return {'status':'INSUFFICIENT_POSES'}
    indices=np.array([r['index'] for r in rows]);actual=np.array([r['joint_positions'] for r in rows])[:,ARM_DOF_INDICES];commands=np.asarray(commands)[:,SOURCE_ARM_COLUMNS];costs=[]
    for offset in offsets:
        source=indices-offset;mask=(source>=0)&(source<len(commands))
        if mask.sum()<min(8,len(rows)):continue
        error=actual[mask]-commands[source[mask]];costs.append({'native_minus_source_index':offset,'arm_mean_squared_error_rad2':float(np.mean(error**2)),'samples':int(mask.sum()),'max_abs_error_rad':float(np.abs(error).max())})
    costs.sort(key=lambda r:r['arm_mean_squared_error_rad2'])
    return {'status':'EMPIRICAL_TARGET_TO_ACTUAL_ALIGNMENT_ONLY','best':costs[0] if costs else None,'best_candidates':costs[:7],'scope':'Actual12 arm DOFs matched against source targets over this case; servo lag can shift the best index. Not an authoritative source-action timestamp; do not copy bad08 offset.','native_pose_count':len(rows)}


def region(path):
    if path.endswith('/RigidSolidBottom/SolidCap'):return 'solid_cap'
    if '/RigidSolidBottom/Upper_' in path:return 'upper_'+path.rsplit('/',1)[-1].rsplit('_',1)[0]
    if '/RigidWallProxy/Bottom_' in path:return path.rsplit('/',1)[-1].rsplit('_',1)[0]
    if '/RigidWallProxy/Wall_' in path:return path.rsplit('/',1)[-1].rsplit('_',1)[0]
    return path.rsplit('/',1)[-1]


def pair_group(row):
    actors=row['actors'];tube='/World/_scene/obj_sample_tube';bath='/World/_scene/obj_beaker'
    if tube in actors and bath in actors:
        tp=next((p for p in row['colliders'] if '/obj_sample_tube/' in p),tube+'/UNKNOWN_COLLIDER');bp=next((p for p in row['colliders'] if '/obj_beaker/' in p),bath+'/UNKNOWN_COLLIDER')
        return 'tube_bath | '+region(tp)+' | '+bp.split('/obj_beaker/',1)[1]
    if tube in actors or bath in actors:
        other=next((p for p in actors if '/lift2/' in p),None)
        if other:return ('robot_tube | ' if tube in actors else 'robot_bath | ')+other.split('/lift2/lift2/lift2/',1)[-1]
    return None


def summarize_window(contacts,low,high):
    selected=[r for r in contacts if low<=r['index']<=high];groups=collections.defaultdict(list)
    for r in selected:
        key=pair_group(r)
        if key:groups[key].append(r)
    summary={}
    for k,v in groups.items():
        summary[k]=contact_stats(v);summary[k].update(event_types=dict(collections.Counter(r['type'] for r in v)),positive_point_native_frames=len({r['index'] for r in v if r['points']>0}),LOST_native_indices=sorted({r['index'] for r in v if 'LOST' in r['type']}),FOUND_native_indices=sorted({r['index'] for r in v if 'FOUND' in r['type']}))
    return {'native_range':[low,high],'groups':summary,'PBD_only_rigid_header_hits':sum(any('/PBDBottomProxy/' in p or '/WaterbathCollision/' in p for p in r['colliders']) for r in selected),'total_report_headers':len(selected)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--log',required=True);p.add_argument('--actions',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False);raw=Path(a.log).read_bytes();lines=raw.decode(errors='replace').splitlines();first=next((i for i,l in enumerate(lines) if 'mArtiSolveBlockPartitionFunction' in l or 'CUDA error' in l),len(lines));data=parse_log(a.log,'\n'.join(lines[:first]));from sciben_silver_bad09_probe import load_pickle,normalize_action
    source=Path(a.actions);commands=np.array([normalize_action(v)[0] for v in load_pickle(source)['model_output']]);alignment=estimate_alignment(data['poses'],commands);last=max((r['index'] for r in data['poses']),default=-1);expected=1568+alignment['best']['native_minus_source_index'] if alignment.get('best') else None
    for key in ['poses','contacts']:
        with (out/(key+'.jsonl')).open('w') as f:
            for row in data[key]:f.write(json.dumps(row)+'\n')
    release_rows=[]
    if expected is not None:
        for r in data['poses']:
            if expected-10<=r['index']<=expected+12:
                release_rows.append({'native_index':r['index'],'left_finger_DOF23_24_m':r['joint_positions'][23:25],'actual_poses':r['poses']})
    result={'scope':'Native trace before first logged engine error. Configured/source targets and actual SDK state separated; not new physics qualification.','log':str(Path(a.log).resolve()),'log_snapshot_sha256':hashlib.sha256(raw).hexdigest(),'source_actions':str(source.resolve()),'source_actions_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_release_index':1568,'first_error_line':lines[first] if first<len(lines) else None,'last_native_index':last,'pose_rows':len(data['poses']),'contact_rows':len(data['contacts']),'diagnostic_errors':data['diagnostic_errors'],'alignment':alignment,'release_native_estimate':expected,'actual_release_neighborhood':release_rows,'last31':summarize_window(data['contacts'],last-30,last),'release_window':summarize_window(data['contacts'],expected-12,expected+12) if expected else None,'last_pose':data['poses'][-1] if data['poses'] else None};(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print({'last_native':last,'poses':len(data['poses']),'contacts':len(data['contacts']),'first_error':result['first_error_line'],'best_offset':alignment.get('best')})
if __name__=='__main__':main()
