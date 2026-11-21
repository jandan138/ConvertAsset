"""Descriptive paired/repeat analysis; never count runtime exceptions as task failures."""
import argparse,itertools,json
from pathlib import Path

def summarize(records):
 indexed={}
 for r in records:
  key=(r['pair_id'],r['condition'],r['repeat'])
  if key in indexed:raise ValueError('Duplicate prediction')
  if r['status']!='ok' or not isinstance(r['hit'],bool):raise ValueError('Unresolved runtime errors; no complete result')
  indexed[key]=r
 pairs=sorted({r['pair_id'] for r in records})
 if not pairs:raise ValueError('No predictions')
 if set(indexed)!={(p,c,i) for p in pairs for c in ['original','converted'] for i in range(3)}:raise ValueError('Incomplete repeat matrix')
 by_repeat=[];cases=[]
 for i in range(3):
  outcomes=[(indexed[p,'original',i]['hit'],indexed[p,'converted',i]['hit']) for p in pairs]
  losses=sum(a and not b for a,b in outcomes);gains=sum(not a and b for a,b in outcomes)
  summary={'repeat':i,'n_pairs':len(pairs),'original_hits':sum(a for a,b in outcomes),'converted_hits':sum(b for a,b in outcomes),'losses':losses,'gains':gains,'flips':losses+gains}
  for condition in ['original','converted']:
   summary[condition+'_hit_rate']=summary[condition+'_hits']/len(pairs)
   for field,label in [('valid_point','valid_point_rate'),('visible_bbox_hit','visible_bbox_hit_rate')]:
    values=[indexed[p,condition,i].get(field) for p in pairs]
    summary[condition+'_'+label]=sum(values)/len(values) if all(isinstance(v,bool) for v in values) else None
  summary['flip_rate']=(losses+gains)/len(pairs)
  summary['hit_rate_difference']=summary['converted_hit_rate']-summary['original_hit_rate']
  by_repeat.append(summary)
 within={}
 for c in ['original','converted']:
  different=sum(indexed[p,c,i]['hit']!=indexed[p,c,j]['hit'] for p in pairs for i,j in itertools.combinations(range(3),2))
  within[c]={'disagreements':different,'comparisons':len(pairs)*3,'rate':different/(len(pairs)*3)}
 for p in pairs:
  r=indexed[p,'original',0]
  cases.append({'pair_id':p,'scene_id':r['scene_id'],'query':r.get('query'),'original_hits':[indexed[p,'original',i]['hit'] for i in range(3)],'converted_hits':[indexed[p,'converted',i]['hit'] for i in range(3)],'images':{c:indexed[p,c,0]['image']['path'] for c in ['original','converted']},'points_normalized':{c:[indexed[p,c,i].get('point_normalized') for i in range(3)] for c in ['original','converted']},'raw_responses':{c:[indexed[p,c,i].get('raw_response') for i in range(3)] for c in ['original','converted']},'center_baseline':{c:indexed[p,c,0].get('center_baseline_hit') for c in ['original','converted']}})
 return {'n_pairs':len(pairs),'n_predictions':len(records),'by_repeat':by_repeat,'within_condition':within,'cases':cases,'interpretation':'Descriptive three-scene pilot. Repeats are not independent scenes; cross-condition flips are not automatically attributable to materials.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,nargs=3,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 rows=[json.loads(line) for f in a.inputs for line in f.read_text().splitlines() if line.strip()]
 result=summarize(rows)
 if result['n_pairs']<12 or len({r['scene_id'] for r in rows})!=3:raise ValueError('Pilot scope not met')
 result['by_scene']={s:summarize([r for r in rows if r['scene_id']==s]) for s in sorted({r['scene_id'] for r in rows})}
 a.out.mkdir(parents=True,exist_ok=False);(a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 lines=['# CVIU three-scene pilot','',result['interpretation'],'','| Repeat | Original hits | Converted hits | Losses | Gains | Flips |','|---|---|---|---|---|---|']
 for r in result['by_repeat']:lines.append('| '+' | '.join(str(r[k]) for k in ['repeat','original_hits','converted_hits','losses','gains','flips'])+' |')
 lines+=['','## Hit rates and output coverage','',json.dumps([{k:v for k,v in r.items() if 'rate' in k or k=='repeat'} for r in result['by_repeat']],indent=2),'','## Same-condition repeat disagreement','',json.dumps(result['within_condition'],indent=2),'','## Paired cases','']
 for case in result['cases']:lines += [f"### {case['pair_id']}",str(case['query']),f"Original: {case['original_hits']}; converted: {case['converted_hits']}",f"Points (0–1000): {case['points_normalized']}",f"Center baseline: {case['center_baseline']}",f"Images: {case['images']['original']} ; {case['images']['converted']}",'']
 (a.out/'report.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
