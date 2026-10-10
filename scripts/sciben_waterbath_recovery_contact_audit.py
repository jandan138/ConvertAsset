"""Pair this run's exact post-step gate count with its own native SDK events."""
from pathlib import Path
import json,collections,argparse

def audit(run):
    run=Path(run);report=json.loads((run/'report.json').read_text());events=collections.defaultdict(lambda:{'count':0,'native_ticks':set(),'header_count':0})
    for line in (run/'contact_events_each_header.jsonl').open():
        row=json.loads(line)
        if not (any(p.endswith('/obj_sample_tube') for p in row['actors']) and any(p.endswith('/obj_beaker') for p in row['actors'])):continue
        e=events[row['action_step']];e['count']+=row['contact_points'];e['native_ticks'].add(row['native_tick_before_callback']);e['header_count']+=1
    matched=[]
    for line in (run/'poses_each_step.jsonl').open():
        row=json.loads(line);step=row['step']
        if step>=report['completed_actions']:continue
        e=events[step]
        matched.append({'action_step':step,'post_step_native_count':row['native_count'],'event_native_ticks_before_callback':sorted(e['native_ticks']),'sdk_event_count':e['count'],'graph_wall_contact_count':row['state']['wall_contact_count'],'heating_enabled':row['state']['heating_enabled'],'heating_block_reason':row['state']['heating_block_reason']})
    offsets={str(offset):sum(r['graph_wall_contact_count']!=events[r['action_step']+offset]['count'] for r in matched) for offset in [-1,0,1]}
    result={'run':str(run.resolve()),'requested_actions':report['requested_actions'],'completed_actions':report['completed_actions'],'comparison_scope':'Same run only. Successful post-step snapshots; failed engine step excluded. Warmup and zero-contact frames included.','mismatch_counts_by_event_action_offset':offsets,'paired_frame_count':len(matched),'max_sdk_count':max(r['sdk_event_count'] for r in matched),'max_graph_count':max(r['graph_wall_contact_count'] for r in matched),'positive_contact_frames':sum(r['sdk_event_count']>0 for r in matched),'rows':matched}
    (run/'contact_count_alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    return {k:v for k,v in result.items() if k!='rows'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(audit(a.run),indent=2))
