"""Extract a deterministic geometry-only target pool; selections are provisional until QA."""
import argparse,hashlib,json,math,re
from collections import Counter,defaultdict
from pathlib import Path

def choose_targets(candidates,n=8,seed=20261114):
 rank=lambda r:hashlib.sha256(f"{seed}:{r['scene_id']}:{r['prim']}".encode()).hexdigest()
 groups=defaultdict(list)
 for r in candidates:groups[r['category']].append(r)
 for group in groups.values():group.sort(key=rank)
 # Prefer category diversity and fewer same-category distractors, not model success.
 ordered=sorted(groups,key=lambda c:(len(groups[c]),hashlib.sha256(f'{seed}:{c}'.encode()).hexdigest()))
 selected=[groups[c][0] for c in ordered[:n]]
 selected_ids={r['prim'] for r in selected}
 reserve=sorted([r for r in candidates if r['prim'] not in selected_ids],key=rank)
 while len(selected)<n and reserve:selected.append(reserve.pop(0))
 return selected,reserve

def main():
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();record=json.loads(a.receipt.read_text())
 if record['status']!='ready_for_target_selection':raise ValueError('Scene not qualified')
 from pxr import Usd,UsdGeom
 stage=Usd.Stage.Open(record['restored']);bounds=UsdGeom.BBoxCache(0,[UsdGeom.Tokens.default_,UsdGeom.Tokens.render]);candidates=[];excluded=[]
 for prim in stage.Traverse():
  if not prim.HasAuthoredReferences():continue
  refs=str(prim.GetMetadata('references'))
  if not any(k in refs for k in ['models/object/','models/layout/articulated/']):continue
  category=prim.GetParent().GetName();item={'scene_id':record['scene_id'],'prim':str(prim.GetPath()),'category':category,'references':refs}
  if category in {'other','decoration','light','wall','ground','ceiling'}:excluded.append({**item,'reason':'ambiguous_or_structural_category'});continue
  box=bounds.ComputeWorldBound(prim).ComputeAlignedRange()
  if box.IsEmpty() or not all(math.isfinite(v) for v in [*box.GetMin(),*box.GetMax()]):excluded.append({**item,'reason':'invalid_bounds'});continue
  if UsdGeom.Imageable(prim).ComputeVisibility()==UsdGeom.Tokens.invisible:excluded.append({**item,'reason':'authored_invisible'});continue
  match=re.search(r'model_([0-9a-f]{32})',prim.GetName())
  item.update(bbox_min=list(box.GetMin()),bbox_max=list(box.GetMax()),template_hash=match[1] if match else None,requires_label_review=category in {'toy','microwave','backpack'},selection_status='candidate_not_visually_validated')
  candidates.append(item)
 selected,reserve=choose_targets(candidates)
 result={'scene_id':record['scene_id'],'split':record['split'],'original':record['restored'],'converted':record['converted'],'up_axis':str(UsdGeom.GetStageUpAxis(stage)),'meters_per_unit':UsdGeom.GetStageMetersPerUnit(stage),'selection_rule':'category diversity, rarity, then seeded hash; no model outputs','candidate_count':len(candidates),'selected':selected,'reserve':reserve,'excluded':excluded,'status':'provisional_8_targets' if len(selected)==8 else 'insufficient_candidates'}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.out.open('x') as f:json.dump(result,f,indent=2)
 print(record['scene_id'],len(candidates),len(selected),flush=True)
if __name__=='__main__':main()
