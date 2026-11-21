#!/usr/bin/env python3
"""Package existing hero evidence; no simulation, inference or source mutation.

Run from any directory. Original sources are located relative to the nearest
ancestor containing CLAUDE.md. Image copies retain exact bytes. Navigation maps
are lossless right-half crops; prediction coordinates retain normalized-1000
and pixel representations. Generated material balls are conceptual illustrations.
"""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = next(p for p in OUT.parents if (p / 'CLAUDE.md').is_file())
RAW = ROOT / 'paper/shared/evidence/raw'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path):
    return str(path.relative_to(ROOT))

def source_path(record_path):
    text = str(record_path)
    if 'paper/' in text:
        text = 'paper/' + text.split('paper/', 1)[1]
    path = (ROOT / text).resolve()
    path.relative_to(ROOT)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path

def copy_image(src, dest, expected_sha=None, expected_size=None):
    digest = sha(src)
    if expected_sha is not None and digest != expected_sha:
        raise ValueError(f'Source digest mismatch: {src}')
    with Image.open(src) as im:
        size, mode = list(im.size), im.mode
    if expected_size is not None and size != list(expected_size):
        raise ValueError(f'Source dimensions mismatch: {src}: {size}')
    dst = OUT / dest
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    if sha(dst) != digest:
        raise ValueError(f'Copy mismatch: {dst}')
    return dict(source=rel(src), source_sha256=digest, file=dest,
                sha256=digest, size=size, mode=mode, extraction='byte-identical copy')

def unique(rows, sample_id):
    found = [r for r in rows if r['sample_id'] == sample_id]
    if len(found) != 1:
        raise ValueError(f'Expected exactly one record for {sample_id}: {len(found)}')
    return found[0]

def main():
    result = dict(schema_version=1, source_paths_relative_to='repository root',
                  output_paths_relative_to='this manifest directory', materials={}, grounding={}, navigation={})
    mats = ROOT / 'paper/shared/figures/generated_components/fig1_material_pairs_v1'
    for name in ('wood','stone','ceramic','metal'):
        for version in ('source','simplified'):
            key = f'{name}_{version}'
            item = copy_image(mats/f'{key}.png', f'data/materials/{key}.png')
            item.update(role='generated conceptual material illustration; not measured render evidence',
                        provenance_manifest=rel(mats/'manifest.yaml'), provenance_manifest_sha256=sha(mats/'manifest.yaml'))
            result['materials'][key] = item
    manifest_path = RAW/'iclr_model_behavior/interventions_clean_v2/manifest.json'
    original = json.loads(manifest_path.read_text())
    result['grounding_manifest'] = dict(source=rel(manifest_path), sha256=sha(manifest_path))
    for family, version in [('two_view_category','original'),('two_view_category','converted'),('target_window','converted'),('context_window','converted')]:
        sid = f'board02.q0.side0.{family}.{version}'
        row = unique(original['scoring_records'],sid)
        prediction_path = RAW/f'iclr_model_behavior/runs_clean_v2/qwen3vl2b/qwen3vl2b_{family}_predictions.jsonl'
        pred = unique([json.loads(line) for line in prediction_path.read_text().splitlines() if line.strip()],sid)
        if pred['image'] != row['image'] or pred['target'] != row['target']:
            raise ValueError(f'Prediction input identity mismatch: {sid}')
        if pred['prompt_contract']['coordinate_frame'] != 'normalized_1000' or pred['prediction']['parse_status'] != 'parsed':
            raise ValueError(f'Unexpected coordinate frame or unparsed point: {sid}')
        key = f'{family}_{version}'
        item = copy_image(source_path(row['image']['path']),f'data/grounding/{key}.png',row['image']['hash_sha256'],[1216,450])
        point = pred['prediction']['point_xy']
        width,height = item['size']
        pixels = [point[0]*width/1000,point[1]*height/1000]
        bbox = row['target']['bbox_xyxy']
        hit = bbox[0] <= pixels[0] <= bbox[2] and bbox[1] <= pixels[1] <= bbox[3]
        item.update(role='recorded model input and saved prediction evidence',sample_id=sid,
                    pair_id=row['pair_id'],family=family,condition=version,target_id=row['target_id'],
                    board_source_pairs=row['board_source_pairs'],target_side=row['target_side'],
                    bbox_xyxy_pixels=bbox,bbox_source=row['target']['bbox_source'],
                    point_normalized_1000=point,point_pixels=pixels,point_hits_bbox=hit,
                    model='Qwen3-VL-2B-Instruct',query='Locate the bottle.',prompt=pred['prompt']['text'],
                    prediction_source=rel(prediction_path),prediction_source_sha256=sha(prediction_path),
                    prediction_raw_text=pred['prediction']['raw_text'])
        item['input_semantics'] = {'two_view_category':'Full original or full converted paired indoor views.',
           'target_window':'Converted pixels inside target bbox; original pixels outside target bbox and entire original distractor view.',
           'context_window':'Original pixels inside target bbox; converted pixels outside target bbox and entire converted distractor view.'}[family]
        result['grounding'][key] = item
    navdir = RAW/'internnav_vln_downstream/official_selected_qualitative_videos/stills/kujiale0036_0066'
    for condition,frame in [('original','000106'),('nomdl','000382')]:
        src = navdir/f'kujiale0036_0066_898_898_{condition}_end_{frame}.png'
        item = copy_image(src,f'data/navigation/{condition}_end_composite.png',expected_size=[1024,512])
        crop = (512,0,1024,512)
        dst = OUT/f'data/navigation/{condition}_map.png'
        with Image.open(src) as im:
            piece = im.crop(crop)
            piece.save(dst)
            with Image.open(dst) as check:
                if check.size != (512,512) or check.tobytes() != piece.tobytes():
                    raise ValueError('Navigation crop pixel mismatch')
        item.update(composite_file=item.pop('file'),composite_sha256=item.pop('sha256'),
                    file=str(dst.relative_to(OUT)),sha256=sha(dst),size=[512,512],source_size=[1024,512],
                    extraction='lossless right-half map crop; no recoloring, resizing or redrawing',crop_xyxy=list(crop),
                    role='recorded navigation map excerpt',episode_id='898_898',scene='kujiale0036_0066',
                    condition=condition,frame_index=int(frame),legend={'red':'executed path','green':'reference path'},
                    framing_note='Recorded map excerpts; map framing may differ between recordings. Independent qualitative recording, not a main-run quantitative score.')
        result['navigation'][condition] = item
    result['preparation_notes'] = ['Sources are read-only; no experiments or inference performed.',
        'Grounding crossover images are full recorded two-view inputs, not display-time masks or crops.',
        'Prediction positions are scaled over the entire 1216 x 450 input; do not treat normalized coordinates as pixels.',
        'No material illustration is evidence of measured visual fidelity.']
    output = OUT/'evidence_manifest.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'Prepared {len(result["materials"])} material illustrations, {len(result["grounding"])} grounding inputs, {len(result["navigation"])} map excerpts.')
    for key,item in result['grounding'].items():
        print(key, item['point_pixels'], 'hit=',item['point_hits_bbox'])

if __name__ == '__main__':
    main()
