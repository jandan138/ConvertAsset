"""Pure offline summary of exact per-native containment telemetry."""
import argparse,collections,hashlib,json
from pathlib import Path


def intervals(ticks):
    result=[]
    for tick in sorted(set(ticks)):
        if result and tick==result[-1][1]+1:result[-1][1]=tick
        else:result.append([tick,tick])
    return [{'first_native_tick':a,'last_native_tick':b,'sample_count':b-a+1,'sample_duration_s':(b-a+1)/120} for a,b in result]


def summarize(rows):
    ticks=[r['native_tick'] for r in rows];bad=collections.defaultdict(list);history=collections.defaultdict(list)
    for r in rows:
        for i in r['bad_indices']:bad[i].append(r['native_tick'])
        for p in r['selected_particles']:history[p['index']].append({'native_tick':r['native_tick'],'particle':p,'container_position':r['container_position'],'container_orientation_xyzw':r['container_orientation_xyzw']})
    per={}
    for i,ts in bad.items():
        first=ts[0];around=[r for r in history[i] if first-6<=r['native_tick']<=first+6];per[str(i)]={'intervals':intervals(ts),'first_crossing_neighborhood':around,'last_observation':history[i][-1]}
    return {'sample_count':len(rows),'native_tick_range':[min(ticks),max(ticks)] if ticks else None,'all_callback_ticks_consecutive':all(b==a+1 for a,b in zip(ticks,ticks[1:])),'outside_native_steps':sum(r['outside_count']>0 for r in rows),'max_outside_count':max((r['outside_count'] for r in rows),default=0),'outside_intervals':intervals(r['native_tick'] for r in rows if r['outside_count']),'bad_particle_ids':sorted(bad),'per_particle':per,'pose_first':rows[0]['container_position'] if rows else None,'pose_last':rows[-1]['container_position'] if rows else None,'all_container_orientation_identity':all(r['container_orientation_xyzw']==[0.,0.,0.,1.] for r in rows),'limits':'One matched diagnostic per candidate. Selected particle history includes lowest and currently outside particles; absence before first recorded selection is not inferred. Velocity is expressed in body axes but retains container translation.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--trace',required=True);p.add_argument('--out',required=True);a=p.parse_args();path=Path(a.trace);raw=path.read_bytes();rows=[json.loads(x) for x in raw.decode().splitlines()];r=summarize(rows);r.update(trace=str(path.resolve()),trace_sha256=hashlib.sha256(raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());out=Path(a.out);assert not out.exists();out.write_text(json.dumps(r,indent=2)+'\n');print({k:r[k] for k in ['sample_count','outside_native_steps','max_outside_count','bad_particle_ids','outside_intervals']})
if __name__=='__main__':main()
