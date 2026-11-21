"""Assemble one visually qualified final scene; never pretend it is the cohort."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();review=json.loads(a.review.read_text())
    if review['status']!='ACCEPTED_FINAL_PAIRS':raise ValueError('Final visual review not accepted')
    audit_path=Path(review['audit'])
    if sha(audit_path)!=review['audit_sha256']:raise ValueError('Audit changed after review')
    audit=json.loads(audit_path.read_text())
    if audit['errors'] or audit['status']!='TECHNICALLY_CHECKED_VISUAL_QA_PENDING':raise ValueError('Technical audit failed')
    reviews={r['pair_id']:r for r in review['pairs']}
    if len(reviews)!=16 or len(audit['pairs'])!=16:raise ValueError('Need sixteen final pairs')
    if set(reviews)!={r['pair_id'] for r in audit['pairs']}:raise ValueError('Review/audit pairs mismatch')
    rows=[]
    for pair in audit['pairs']:
        verdict=reviews[pair['pair_id']]
        if verdict['original_visual_qualification']!='PASS' or verdict['converted_technical_visual_qualification']!='PASS':
            raise ValueError('Unqualified final view')
        for condition in ['original','converted']:
            r=pair[condition];folder=Path(r['output']);image=folder/'rgb.png';mask_file=folder/'target_mask.npy'
            if sha(image)!=r['image_sha256'] or r['image_sha256']!=verdict[condition+'_image_sha256']:
                raise ValueError('Reviewed image changed')
            if sha(mask_file)!=r['mask_sha256']:raise ValueError('Mask changed')
            mask=np.load(mask_file,allow_pickle=False)
            if mask.shape!=(768,1024) or mask.dtype!=np.bool_:raise ValueError('Invalid mask')
            if condition=='original' and not mask.any():raise ValueError('Empty original mask')
            ys,xs=np.where(mask);pixels=int(mask.sum())
            rows.append({'pair_id':r['pair_id'],'condition':condition,'scene_id':r['scene_id'],
                         'target_prim':r['target_prim'],'view_id':r['pair_id'].rsplit(':',1)[1],
                         'query':r['query'],'source_category':r['category'],
                         'technical_qa':'PASS','original_qualification':'PASS',
                         'visual_qa':'PASS' if pixels else 'TARGET_NOT_VISIBLE',
                         'visual_target_assessment':'visible' if condition=='original' else verdict['converted_visibility'],
                         'converted_visibility_loss':condition=='converted' and not pixels,
                         'image':{'path':str(image),'sha256':r['image_sha256'],'width':1024,'height':768},
                         'mask':{'path':str(mask_file),'sha256':r['mask_sha256'],'pixels':pixels},
                         'center_baseline_hit':bool(mask[384,512]),
                         'uniform_pixel_baseline_probability':pixels/(768*1024),
                         'visible_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if pixels else None,
                         'capture_receipt':str(folder/'receipt.json'),'capture_receipt_sha256':sha(folder/'receipt.json'),
                         'camera_stage_sha256':sha(r['stage'])})
    if len({r['target_prim'] for r in rows})!=8:raise ValueError('Need eight distinct targets')
    out={'schema_version':1,'status':'qualified_scene_inputs','scene_id':review['scene_id'],
         'review':str(a.review),'review_sha256':sha(a.review),'audit_sha256':sha(audit_path),
         'scope':'One scene only; global 30-scene freeze required before formal inference.', 'records':rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print('Qualified scene inputs:',len(rows))


if __name__=='__main__':main()
