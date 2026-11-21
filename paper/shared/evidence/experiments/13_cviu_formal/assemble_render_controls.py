"""Bind 96 repeated-render inputs to a fully frozen 30-scene primary cohort."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from formal_inference import sha,validate_structure,validate_files,validate_control_structure


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--primary-manifest',type=Path,required=True);p.add_argument('--repeat-audits',type=Path,nargs=3,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    primary=json.loads(a.primary_manifest.read_text());protocol=json.loads((a.raw/'protocol.json').read_text());expected=[r['scene_id'] for r in json.loads((a.raw/'scenes.json').read_text())['scenes']]
    primary_rows=validate_structure(primary,expected);validate_files(primary_rows)
    if primary['protocol_sha256']!=sha(a.raw/'protocol.json'):raise ValueError('Primary protocol changed')
    reference={(r['pair_id'],r['condition']):r for r in primary_rows};provenance={r['scene_id']:r for r in primary['scene_provenance']};audits={}
    for path in a.repeat_audits:
        d=json.loads(path.read_text());sid=d['scene_id']
        if sid in audits or d['errors'] or len(d['pairs'])!=16:raise ValueError('Repeat audit incomplete or duplicated')
        audits[sid]=(path,d)
    if set(audits)!=set(protocol['render_noise_control_scene_ids']):raise ValueError('Wrong render-control cohort')
    rows=[];sources=[]
    for sid in protocol['render_noise_control_scene_ids']:
        path,audit=audits[sid];original_audit=Path(provenance[sid]['audit'])
        if sha(original_audit)!=provenance[sid]['audit_sha256']:raise ValueError('Primary audit changed')
        original=json.loads(original_audit.read_text());old={p['pair_id']:p for p in original['pairs']}
        for condition in ['original','converted']:
            for key in ['script_sha256','jobs_sha256']:
                if audit['capture_metadata'][condition][key]!=original['capture_metadata'][condition][key]:raise ValueError('Repeat recipe mismatch')
        for pair in audit['pairs']:
            for condition in ['original','converted']:
                capture=pair[condition];ref=reference[pair['pair_id'],condition];prior=old[pair['pair_id']][condition]
                for key in ['camera_parameters','query','target_prim']:
                    if capture[key]!=prior[key]:raise ValueError('Repeat identity mismatch')
                folder=Path(capture['output']);image=folder/'rgb.png';mask_file=folder/'target_mask.npy';receipt=folder/'receipt.json'
                if sha(image)!=capture['image_sha256'] or sha(mask_file)!=capture['mask_sha256']:raise ValueError('Repeat capture changed')
                mask=np.load(mask_file,allow_pickle=False);ys,xs=np.where(mask);row=copy.deepcopy(ref)
                row.update(image={'path':str(image),'sha256':capture['image_sha256'],'width':1024,'height':768},
                    mask={'path':str(mask_file),'sha256':capture['mask_sha256'],'pixels':int(mask.sum())},
                    capture_receipt=str(receipt),capture_receipt_sha256=sha(receipt),camera_stage_sha256=sha(capture['stage']),
                    center_baseline_hit=bool(mask[384,512]),uniform_pixel_baseline_probability=float(mask.mean()),
                    visible_bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None,
                    converted_visibility_loss=condition=='converted' and not bool(mask.any()),
                    visual_qa='PASS' if mask.any() else 'TARGET_NOT_VISIBLE',
                    render_repeat_of_image_sha256=ref['image']['sha256'],
                    visual_target_assessment='repeat_capture_bound_to_primary_review',
                    purpose='render_noise_control_not_primary_sample')
                rows.append(row)
        sources.append({'scene_id':sid,'audit':str(path),'audit_sha256':sha(path)})
    result={'schema_version':1,'status':'frozen_render_control_inputs','primary_manifest':str(a.primary_manifest),
            'primary_manifest_sha256':sha(a.primary_manifest),'protocol_sha256':sha(a.raw/'protocol.json'),
            'repeat_audits':sources,'scope':'96 auxiliary inputs; retain all repeated images, including image-level threshold exceedances. Never add them to 5760 primary predictions.', 'records':rows}
    validate_control_structure(result,primary_rows,protocol['render_noise_control_scene_ids']);validate_files(rows)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('Frozen 96 auxiliary repeated-render inputs')


if __name__=='__main__':main()
