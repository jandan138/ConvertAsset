"""Paired scene-cluster analysis of the complete 5,760-prediction cohort.

Recalculate scores from masks, reject runtime failures/missing predictions,
and resample scenes while retaining all targets, views and repeats together.
"""
import argparse,itertools,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
from formal_inference import parse_point,validate_structure,validate_files,sha


def ratio_draws(numerator, denominator, indices):
    num=np.asarray(numerator,dtype=float);den=np.asarray(denominator,dtype=float)
    totals=den[indices].sum(axis=1)
    return np.divide(num[indices].sum(axis=1),totals,out=np.full(len(indices),np.nan),where=totals>0)


def summarize_ratio(numerator,denominator,indices):
    num=np.asarray(numerator,dtype=float);den=np.asarray(denominator,dtype=float)
    values=ratio_draws(num,den,indices);finite=values[np.isfinite(values)]
    return {'estimate':float(num.sum()/den.sum()) if den.sum()>0 else None,
            'numerator':float(num.sum()),'denominator':float(den.sum()),
            'scene_bootstrap_ci95':np.quantile(finite,[.025,.975]).tolist() if len(finite) else None,
            'finite_bootstrap_draws':len(finite),
            'degenerate_bootstrap':bool(len(finite) and np.ptp(finite)<1e-12)}


def index_predictions(rows,manifest):
    expected={(r['pair_id'],r['condition']):r for r in manifest};index={}
    for r in rows:
        key=(r['model'],r['repeat'],r['pair_id'],r['condition'])
        if key in index:raise ValueError('Duplicate prediction')
        if r.get('mode')!='formal' or r['status']!='ok':raise ValueError('Nonformal or unresolved runtime error')
        ref=expected.get((r['pair_id'],r['condition']))
        if ref is None:raise ValueError('Unexpected input')
        for field in ['scene_id','target_prim','view_id','query']:
            if r[field]!=ref[field]:raise ValueError('Prediction/input identity mismatch')
        if any(r[k]['sha256']!=ref[k]['sha256'] for k in ['image','mask']):raise ValueError('Prediction input hash mismatch')
        index[key]=r
    full={(model,repeat,pair,condition) for model in ['8b','32b'] for repeat in range(3) for pair,condition in expected}
    if set(index)!=full or len(index)!=5760:raise ValueError('Incomplete 5760-prediction matrix')
    return index


def verify_scores(index,manifest):
    for ref in manifest:
        mask=np.load(ref['mask']['path'],allow_pickle=False);ys,xs=np.where(mask)
        if ref['mask']['pixels']!=int(mask.sum()) or ref['center_baseline_hit']!=bool(mask[384,512]) or abs(ref['uniform_pixel_baseline_probability']-float(mask.mean()))>1e-12:
            raise ValueError('Manifest baseline or mask count mismatch')
        for model in ['8b','32b']:
            for repeat in range(3):
                r=index[model,repeat,ref['pair_id'],ref['condition']]
                point=parse_point(r['raw_response']);valid=point is not None and all(0<=v<1000 for v in point)
                hit=bool(mask[int(point[1]*768/1000),int(point[0]*1024/1000)]) if valid else False
                bbox=bool(xs.min()<=point[0]*1024/1000<xs.max()+1 and ys.min()<=point[1]*768/1000<ys.max()+1) if valid and len(xs) else False
                if r['point_normalized']!=point or r['valid_point']!=valid or r['hit']!=hit or r['visible_bbox_hit']!=bbox:
                    raise ValueError('Stored score disagrees with raw response and mask')
                if r['target_visible']!=bool(mask.any()):raise ValueError('Visibility score mismatch')


def scoring_components(original, converted):
    oo=int(original['hit_on_original_mask']);oc=int(original['hit_on_converted_mask'])
    co=int(converted['hit_on_original_mask']);cc=int(converted['hit_on_converted_mask'])
    return {'fixed_original_mask_flip_rate':oo!=co,
            'fixed_converted_mask_flip_rate':oc!=cc,
            'converted_prediction_on_original_mask_hit_rate':co,
            'original_prediction_on_converted_mask_hit_rate':oc,
            'prediction_score_component':.5*((co-oo)+(cc-oc)),
            'mask_score_component':.5*((oc-oo)+(cc-co))}


def add_cross_mask_scores(index, manifest):
    refs={(r['pair_id'],r['condition']):r for r in manifest};reports=[]
    for original in [r for r in manifest if r['condition']=='original']:
        pair=original['pair_id'];converted=refs[pair,'converted']
        masks={c:np.load(refs[pair,c]['mask']['path'],allow_pickle=False) for c in ['original','converted']}
        intersection=int((masks['original']&masks['converted']).sum());union=int((masks['original']|masks['converted']).sum())
        reports.append({'pair_id':pair,'scene_id':original['scene_id'],'original_pixels':int(masks['original'].sum()),
                        'converted_pixels':int(masks['converted'].sum()),'intersection_pixels':intersection,'union_pixels':union,
                        'iou':intersection/union,'pixel_disagreement_rate':float((masks['original']!=masks['converted']).mean())})
        for model in ['8b','32b']:
            for repeat in range(3):
                for condition in ['original','converted']:
                    r=index[model,repeat,pair,condition];point=r['point_normalized']
                    for mask_condition,mask in masks.items():
                        r['hit_on_'+mask_condition+'_mask']=bool(mask[int(point[1]*768/1000),int(point[0]*1024/1000)]) if r['valid_point'] else False
    return reports


def displacement(a,b):
    if not a['valid_point'] or not b['valid_point']:return None
    return float(np.linalg.norm((np.array(a['point_normalized'])-b['point_normalized'])*np.array([1.024,.768])))


def components(index,manifest,model):
    scenes=sorted({r['scene_id'] for r in manifest});positions={s:i for i,s in enumerate(scenes)}
    values=defaultdict(lambda:np.zeros((len(scenes),2),dtype=float));repeat_counts=[]
    for name in ['cross_condition_point_displacement_px','cross_condition_point_displacement_image_diagonal'] + [c+suffix for c in ['original','converted'] for suffix in ['_repeat_point_displacement_px','_both_mask_supported_hit_rate']]:
        values[name] # Preserve undefined/zero-support metrics explicitly.
    original=[r for r in manifest if r['condition']=='original'];refs={(r['pair_id'],r['condition']):r for r in manifest}
    def add(metric,scene,num,den=1):values[metric][positions[scene]] += [num,den]
    for ref in original:
        pair=ref['pair_id'];scene=ref['scene_id'];visible=refs[pair,'converted']['mask']['pixels']>0
        add('converted_mask_visibility_loss_rate',scene,not visible)
        for condition in ['original','converted']:
            source=refs[pair,condition]
            add(condition+'_center_baseline_hit_rate',scene,source['center_baseline_hit'])
            add(condition+'_uniform_pixel_baseline_rate',scene,source['uniform_pixel_baseline_probability'])
            for i,j in itertools.combinations(range(3),2):
                a=index[model,i,pair,condition];b=index[model,j,pair,condition]
                add(condition+'_repeat_hit_disagreement_rate',scene,a['hit']!=b['hit'])
                shift=displacement(a,b)
                if shift is not None:add(condition+'_repeat_point_displacement_px',scene,shift)
        for repeat in range(3):
            a=index[model,repeat,pair,'original'];b=index[model,repeat,pair,'converted'];loss=a['hit'] and not b['hit'];gain=not a['hit'] and b['hit']
            for condition,r in [('original',a),('converted',b)]:
                for name,field in [('hit_rate','hit'),('valid_point_rate','valid_point'),('bbox_hit_rate','visible_bbox_hit')]:add(condition+'_'+name,scene,r[field])
                if visible:add(condition+'_both_mask_supported_hit_rate',scene,r['hit'])
            for metric,value in [('loss_rate',loss),('gain_rate',gain),('flip_rate',loss or gain),('hit_rate_difference',int(b['hit'])-int(a['hit']))]:add(metric,scene,value)
            for metric,value in scoring_components(a,b).items():add(metric,scene,value)
            add('loss_given_original_success',scene,loss,int(a['hit']))
            add('gain_given_original_failure',scene,gain,int(not a['hit']))
            shift=displacement(a,b)
            if shift is not None:
                add('cross_condition_point_displacement_px',scene,shift)
                add('cross_condition_point_displacement_image_diagonal',scene,shift/1280)
    for repeat in range(3):
        pairs=[(index[model,repeat,r['pair_id'],'original']['hit'],index[model,repeat,r['pair_id'],'converted']['hit']) for r in original]
        repeat_counts.append({'repeat':repeat,'pairs':len(pairs),'original_hits':sum(a for a,b in pairs),'converted_hits':sum(b for a,b in pairs),'gains':sum(not a and b for a,b in pairs),'losses':sum(a and not b for a,b in pairs)})
    return scenes,dict(values),repeat_counts


def verify_run_metadata(inputs, manifest_path, protocol_path):
    protocol=json.loads(protocol_path.read_text());seen=set();reports=[];common=None
    for path in inputs:
        folder=path.parent;meta=json.loads((folder/'metadata.json').read_text())
        done=json.loads((folder/'completion.json').read_text())
        if done!={'mode':'formal','records':960,'runtime_errors':0,'status':'complete'}:
            raise ValueError('Incomplete formal run receipt')
        key=(meta['model'],meta['repeat'])
        if key in seen or key[0] not in ['8b','32b'] or key[1] not in range(3):
            raise ValueError('Duplicate or unexpected model/repeat receipt')
        seen.add(key)
        required={'mode':'formal','manifest_sha256':sha(manifest_path),'protocol_sha256':sha(protocol_path),
                  'revision':protocol['models'][key[0]]['revision'],'seed':20261114+key[1],
                  'dtype':'bfloat16','do_sample':False,'max_new_tokens':128}
        if any(meta.get(k)!=v for k,v in required.items()):raise ValueError('Formal run configuration mismatch')
        if sha(folder/'runner_snapshot.py')!=meta['runner_sha256']:raise ValueError('Runner snapshot changed')
        for name,digest in meta['checkpoint_config_hashes'].items():
            if sha(folder/name)!=digest:raise ValueError('Checkpoint config snapshot changed')
        placement=meta['placement'];devices=placement['parameter_devices']
        expected_devices=['cuda:0'] if key[0]=='8b' else ['cuda:0','cuda:1']
        if devices!=expected_devices or placement['parameter_dtypes']!=['torch.bfloat16']:
            raise ValueError('Unexpected precision or GPU placement')
        signature={k:meta[k] for k in ['runner_sha256','processor_image_config','torch','transformers']}
        if common is not None and signature!=common:raise ValueError('Cross-run implementation/preprocessing mismatch')
        common=signature
        rows=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if len(rows)!=960 or any((r['model'],r['repeat'])!=key for r in rows):
            raise ValueError('Prediction file disagrees with run receipt')
        reports.append({'model':key[0],'repeat':key[1],'metadata_sha256':sha(folder/'metadata.json'),
                        'completion_sha256':sha(folder/'completion.json'),'runner_sha256':meta['runner_sha256']})
    if seen!={(m,r) for m in ['8b','32b'] for r in range(3)}:raise ValueError('Missing model/repeat receipts')
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--scenes',type=Path,required=True);p.add_argument('--inputs',type=Path,nargs=6,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    manifest=json.loads(a.manifest.read_text());expected=[r['scene_id'] for r in json.loads(a.scenes.read_text())['scenes']];refs=validate_structure(manifest,expected);validate_files(refs)
    run_reports=verify_run_metadata(a.inputs,a.manifest,a.manifest.parent/'protocol.json')
    rows=[json.loads(line) for f in a.inputs for line in f.read_text().splitlines() if line.strip()];index=index_predictions(rows,refs);verify_scores(index,refs);mask_reports=add_cross_mask_scores(index,refs)
    draws=np.random.default_rng(20261114).integers(0,30,size=(10000,30));models={};raw={}
    for model in ['8b','32b']:
        scenes,metrics,repeats=components(index,refs,model);raw[model]=metrics
        models[model]={'metrics':{k:summarize_ratio(v[:,0],v[:,1],draws) for k,v in metrics.items()},'by_repeat':repeats,'scene_components':{k:v.tolist() for k,v in metrics.items()}}
    comparison={}
    for metric in sorted(set(raw['8b'])&set(raw['32b'])):
        x=raw['8b'][metric];y=raw['32b'][metric];delta=ratio_draws(y[:,0],y[:,1],draws)-ratio_draws(x[:,0],x[:,1],draws);finite=delta[np.isfinite(delta)]
        estimates=[models[m]['metrics'][metric]['estimate'] for m in ['8b','32b']]
        comparison[metric]={'difference_32b_minus_8b':estimates[1]-estimates[0] if None not in estimates else None,'paired_scene_bootstrap_ci95':np.quantile(finite,[.025,.975]).tolist() if len(finite) else None}
    result={'predictions':5760,'pairs':480,'scenes':scenes,'bootstrap':{'unit':'scene','draws':10000,'seed':20261114},'models':models,'model_comparison':comparison,
            'mask_support_by_pair':mask_reports,'mask_support_changed_pairs':sum(r['intersection_pixels']!=r['union_pixels'] for r in mask_reports),
            'manifest_sha256':sha(a.manifest),'input_hashes':{str(f):sha(f) for f in a.inputs},'verified_run_receipts':run_reports,
            'interpretation_constraints':['Repeats are not independent scenes.','Fixed-mask scores are diagnostic, not the primary condition-specific visible-mask task.','Prediction and mask score components are a symmetric arithmetic decomposition, not causal mechanism attribution.','Both-mask-supported is an operational visibility subset, not a guarantee of visual identifiability.','Point displacement is conditional on valid outputs; consult format coverage.','Degenerate zero-effect bootstrap intervals do not establish universal absence.','Model-size comparison does not isolate parameter count causally.','Compare render-repeat controls before material attribution; these are analyzed separately.']}
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('Verified and analyzed 5760 formal predictions')


if __name__=='__main__':main()
