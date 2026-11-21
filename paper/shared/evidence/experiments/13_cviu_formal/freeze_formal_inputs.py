"""Freeze the complete cohort only after verifying each scene's evidence chain."""
import argparse,copy,datetime,json
from pathlib import Path
from formal_inference import sha,validate_structure,validate_files


def require_cohort(expected,documents):
    if len(expected)!=30 or len(set(expected))!=30:raise ValueError('Expected 30 unique frozen scene IDs')
    indexed={}
    for path,doc in documents:
        sid=doc['scene_id']
        if sid in indexed:raise ValueError('Duplicate qualified scene: '+sid)
        if doc.get('status')!='qualified_scene_inputs':raise ValueError('Unqualified scene document: '+sid)
        indexed[sid]=(path,doc)
    missing=set(expected)-set(indexed);extra=set(indexed)-set(expected)
    if missing or extra:raise ValueError(f'Incomplete frozen cohort: missing {len(missing)}, extra {len(extra)}; missing IDs={sorted(missing)}')
    return [indexed[sid] for sid in expected]


def freeze(raw):
    cohort_file=raw/'scenes.json';protocol_file=raw/'protocol.json';ready_file=raw/'ready_scenes.json';geometry_file=raw/'binary_geometry_audit/summary.json'
    cohort=json.loads(cohort_file.read_text())['scenes'];expected=[r['scene_id'] for r in cohort];metadata={r['scene_id']:r for r in cohort}
    documents=[(p,json.loads(p.read_text())) for p in sorted((raw/'qualified_scene_inputs').glob('*.json'))]
    ordered=require_cohort(expected,documents)
    ready={r['scene_id']:r for r in json.loads(ready_file.read_text())['scenes']};geometry={r['scene_id']:r for r in json.loads(geometry_file.read_text())['records']}
    if set(ready)!=set(expected) or set(geometry)!=set(expected):raise ValueError('Geometry/ready cohort mismatch')
    rows=[];provenance=[]
    for path,doc in ordered:
        sid=doc['scene_id'];review_file=Path(doc['review'])
        if sha(review_file)!=doc['review_sha256']:raise ValueError('Final review changed: '+sid)
        review=json.loads(review_file.read_text());audit_file=Path(review['audit'])
        if review['status']!='ACCEPTED_FINAL_PAIRS' or review['scene_id']!=sid:raise ValueError('Invalid final review')
        if sha(audit_file)!=review['audit_sha256'] or sha(audit_file)!=doc['audit_sha256']:raise ValueError('Technical audit changed')
        audit=json.loads(audit_file.read_text())
        if audit['errors'] or len(audit['pairs'])!=16:raise ValueError('Technical audit incomplete')
        audited={(p['pair_id'],c):p[c] for p in audit['pairs'] for c in ['original','converted']}
        assessed={p['pair_id']:p for p in review['pairs']}
        if len(assessed)!=16 or len(doc['records'])!=32:raise ValueError('Scene evidence count mismatch')
        if not geometry[sid]['equal']:raise ValueError('Geometry mismatch: '+sid)
        for condition in ['original','converted']:
            root_hash=sha(ready[sid][condition])
            if root_hash!=ready[sid][condition+'_sha256'] or root_hash!=geometry[sid]['root_hashes'][condition]:raise ValueError('Scene root changed since geometry audit')
        for record in doc['records']:
            row=copy.deepcopy(record);key=(row['pair_id'],row['condition']);capture=audited[key];verdict=assessed[row['pair_id']]
            if verdict['original_visual_qualification']!='PASS' or verdict['converted_technical_visual_qualification']!='PASS':raise ValueError('Pair not visually/technically qualified')
            for field in ['scene_id','target_prim','query']:
                if row[field]!=capture[field]:raise ValueError('Input/capture mismatch: '+field)
            if sha(row['capture_receipt'])!=row['capture_receipt_sha256']:raise ValueError('Capture receipt changed')
            receipt=json.loads(Path(row['capture_receipt']).read_text())
            if receipt['pair_id']!=row['pair_id'] or receipt['condition']!=row['condition']:raise ValueError('Wrong receipt identity')
            if sha(receipt['stage'])!=row['camera_stage_sha256']:raise ValueError('Camera layer changed')
            for kind in ['image','mask']:
                if row[kind]['sha256']!=capture[kind+'_sha256']:raise ValueError('Input/audit hash mismatch')
            if row['image']['sha256']!=verdict[row['condition']+'_image_sha256']:raise ValueError('Input/visual review mismatch')
            row['visual_target_assessment']='visible' if row['condition']=='original' else verdict['converted_visibility']
            row.update(family=metadata[sid]['family'],split=metadata[sid]['split'])
            rows.append(row)
        provenance.append({'scene_id':sid,'manifest':str(path),'manifest_sha256':sha(path),'review':str(review_file),'review_sha256':sha(review_file),'audit':str(audit_file),'audit_sha256':sha(audit_file)})
    result={'schema_version':1,'status':'frozen_formal_inputs','frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'cohort_sha256':sha(cohort_file),'protocol_sha256':sha(protocol_file),'ready_scenes_sha256':sha(ready_file),
            'geometry_summary_sha256':sha(geometry_file),'scene_provenance':provenance,
            'selection_corrections':{str(p):sha(p) for p in sorted(raw.glob('selection_rationale_correction*.json'))},'records':rows}
    validate_structure(result,expected);validate_files(rows)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=freeze(a.raw)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('Frozen 30 scenes, 480 pairs, 960 condition inputs:',a.out)
