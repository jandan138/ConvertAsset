"""Audit final paired captures before visual review and input freezing.

Empty converted masks are retained and flagged; they are not missing files or
runtime failures. Original masks must remain nonempty after final recapture.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from audit_capture_logs import inspect_log


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(selected, captures):
    selection = json.loads((selected/'selection_receipt.json').read_text())
    errors = []
    batches = {}
    audits = {}
    capture_metadata = {}
    if sha(selection['review']) != selection['review_sha256']:
        errors.append('selection_review_changed')
    for condition in ['original', 'converted']:
        spec = selected/(condition+'.json')
        if sha(spec) != selection['condition_job_hashes'][condition]:
            errors.append(condition+'_jobs_changed')
        planned = json.loads(spec.read_text())['jobs']
        marker = captures/(condition+'.exit')
        progress = captures/condition/'progress.json'
        log = captures/(condition+'.log')
        if not marker.exists() or not progress.exists() or not log.exists():
            errors.append(condition+'_capture_not_terminal')
            continue
        if marker.read_text().strip() != '0':
            errors.append(condition+'_capture_exit_nonzero')
        audits[condition] = inspect_log(log)
        if audits[condition]['material_error_count']:
            errors.append(condition+'_material_errors')
        data = json.loads(progress.read_text())
        capture_metadata[condition] = {k:data.get(k) for k in ['script_sha256','jobs_sha256','stage_open_count','process_start_count']}
        if data.get('jobs_sha256') != sha(spec) or data.get('script_sha256') != sha(captures/condition/'renderer_snapshot.py'):
            errors.append(condition+'_capture_recipe_hash_mismatch')
        if data.get('stage_open_count') != 1 or data.get('process_start_count') != 1:
            errors.append(condition+'_unexpected_capture_process_recipe')
        records = data['records']
        if data['completed'] != 16 or data['planned'] != 16 or len(records) != 16:
            errors.append(condition+'_wrong_capture_count')
            continue
        for record, job in zip(records, planned):
            for field in ['pair_id', 'scene_id', 'condition', 'target_prim', 'query', 'stage']:
                if record[field] != job[field]:
                    errors.append(condition+'_capture_job_mismatch_'+field)
            if sha(job['stage']) != job['stage_sha256']:
                errors.append(condition+'_camera_layer_changed')
            folder = Path(record['output'])
            for filename, field in [('rgb.png','image_sha256'), ('target_mask.npy','mask_sha256')]:
                if sha(folder/filename) != record[field]:
                    errors.append(condition+'_capture_hash_mismatch')
            mask = np.load(folder/'target_mask.npy', allow_pickle=False)
            with Image.open(folder/'rgb.png') as image:
                size = image.size
            if size != (1024,768) or mask.shape != (768,1024) or mask.dtype != np.bool_:
                errors.append(condition+'_image_mask_shape_or_type')
            if int(mask.sum()) != record['mask_pixels']:
                errors.append(condition+'_mask_pixel_count_mismatch')
            if condition == 'original' and (not mask.any() or record['rgb_blank']):
                errors.append('original_lost_qualification_after_recapture')
        batches[condition] = records
    pairs = []
    if len(batches) == 2:
        if capture_metadata['original']['script_sha256'] != capture_metadata['converted']['script_sha256']:
            errors.append('paired_renderer_script_mismatch')
        for original, converted in zip(batches['original'], batches['converted']):
            for field in ['pair_id','scene_id','target_prim','query','camera_parameters']:
                if original[field] != converted[field]:
                    errors.append('paired_'+field+'_mismatch')
            pairs.append({'pair_id':original['pair_id'],'target_prim':original['target_prim'],
                          'query':original['query'],'original':original,'converted':converted,
                          'converted_visibility_loss':converted['mask_pixels']==0,
                          'converted_blank_requires_review':converted['rgb_blank']})
    return {'scene_id':selection['scene_id'],'status':'FAIL_OR_INCOMPLETE' if errors else 'TECHNICALLY_CHECKED_VISUAL_QA_PENDING',
            'errors':sorted(set(errors)),'log_audits':audits,'capture_metadata':capture_metadata,'pairs':pairs,
            'scope':'Technical checks only; final RGB/mask visual qualification and global cohort freezing still required.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selected',type=Path,required=True)
    p.add_argument('--captures',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();result=audit(a.selected,a.captures)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'scene_id':result['scene_id'],'status':result['status'],'errors':result['errors'],'pairs':len(result['pairs'])}))
