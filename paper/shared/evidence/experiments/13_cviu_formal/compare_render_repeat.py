"""Compare independently captured identical batches without changing thresholds."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image


def compare(primary,repeat):
    if primary['errors'] or repeat['errors']:raise ValueError('Technical capture audit failed')
    if primary['scene_id']!=repeat['scene_id']:raise ValueError('Scene mismatch')
    left={p['pair_id']:p for p in primary['pairs']};right={p['pair_id']:p for p in repeat['pairs']}
    if len(left)!=16 or set(left)!=set(right):raise ValueError('Need identical 16-pair sets')
    for condition in ['original','converted']:
        for key in ['script_sha256','jobs_sha256']:
            if primary['capture_metadata'][condition][key]!=repeat['capture_metadata'][condition][key]:raise ValueError('Repeat recipe differs: '+key)
    rows=[]
    for pair in left:
        for condition in ['original','converted']:
            a=left[pair][condition];b=right[pair][condition]
            for key in ['camera_parameters','query','target_prim']:
                if a[key]!=b[key]:raise ValueError('Repeat identity mismatch: '+key)
            arrays=[];masks=[]
            for record in [a,b]:
                folder=Path(record['output'])
                for filename,key in [('rgb.png','image_sha256'),('target_mask.npy','mask_sha256')]:
                    if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=record[key]:raise ValueError('Capture changed')
                arrays.append(np.asarray(Image.open(folder/'rgb.png'),dtype=np.int16))
                masks.append(np.load(folder/'target_mask.npy',allow_pickle=False))
            if arrays[0].shape!=arrays[1].shape:raise ValueError('Image shape mismatch')
            delta=np.abs(arrays[0]-arrays[1]);mask_delta=masks[0]!=masks[1]
            rows.append({'pair_id':pair,'condition':condition,'primary_image':str(Path(a['output'])/'rgb.png'),
                         'repeat_image':str(Path(b['output'])/'rgb.png'),'primary_sha256':a['image_sha256'],
                         'repeat_sha256':b['image_sha256'],'mask_equal':not bool(mask_delta.any()),
                         'mask_changed_pixels':int(mask_delta.sum()),'mae':float(delta.mean()),'max_absolute_difference':int(delta.max())})
    passed=all(r['mask_equal'] and r['mae']<=1 for r in rows)
    return {'scene_id':primary['scene_id'],'status':'PASS_IMAGE_REPEATABILITY' if passed else 'REPEAT_DIFFERENCES_REQUIRE_ANALYSIS',
            'image_count':len(rows),'criteria':{'masks_identical':True,'rgb_mae_maximum':1},
            'max_mae':max(r['mae'] for r in rows),'mean_mae':float(np.mean([r['mae'] for r in rows])),
            'images_above_mae_threshold':sum(r['mae']>1 for r in rows),'images_with_mask_changes':sum(not r['mask_equal'] for r in rows),
            'rows':rows,'scope':'Image-level repeat control only. Model predictions on repeated images are still required.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--primary-audit',type=Path,required=True);p.add_argument('--repeat-audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=compare(json.loads(a.primary_audit.read_text()),json.loads(a.repeat_audit.read_text()))
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
