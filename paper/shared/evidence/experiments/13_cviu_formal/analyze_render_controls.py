"""Descriptive paired render-noise analysis on three preselected scenes only."""
import argparse
import json
from pathlib import Path
import numpy as np
from formal_inference import (sha, parse_point, validate_structure, validate_files,
                              validate_control_structure)
from analyze_formal import displacement


def load_verified_run(folder, manifest_path, refs, model, mode, protocol_hash, repeat=0):
    done = json.loads((folder/'completion.json').read_text())
    if done != {'mode': mode, 'records': len(refs), 'runtime_errors': 0, 'status': 'complete'}:
        raise ValueError('Run incomplete or has runtime errors')
    meta = json.loads((folder/'metadata.json').read_text())
    for key, value in {'model': model, 'mode': mode, 'repeat': repeat,
                       'manifest_sha256': sha(manifest_path),
                       'protocol_sha256': protocol_hash}.items():
        if meta.get(key) != value:
            raise ValueError('Run metadata mismatch: '+key)
    rows = [json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines() if x.strip()]
    expected = {(r['pair_id'], r['condition']): r for r in refs}
    index = {}
    for row in rows:
        key = (row['pair_id'], row['condition'])
        if key not in expected or key in index:
            raise ValueError('Unexpected or duplicate prediction')
        ref = expected[key]
        if row.get('mode') != mode or row.get('model') != model or row.get('repeat') != repeat or row.get('status') != 'ok':
            raise ValueError('Prediction identity/runtime mismatch')
        for field in ['scene_id', 'target_prim', 'view_id', 'query']:
            if row[field] != ref[field]:
                raise ValueError('Input identity mismatch')
        for field in ['image', 'mask']:
            if row[field]['sha256'] != ref[field]['sha256']:
                raise ValueError('Input hash mismatch')
        point = parse_point(row['raw_response'])
        valid = point is not None and all(0 <= v < 1000 for v in point)
        mask = np.load(ref['mask']['path'], allow_pickle=False)
        ys, xs = np.where(mask)
        hit = bool(mask[int(point[1]*768/1000), int(point[0]*1024/1000)]) if valid else False
        bbox = bool(xs.min() <= point[0]*1024/1000 < xs.max()+1 and ys.min() <= point[1]*768/1000 < ys.max()+1) if valid and len(xs) else False
        if any(row.get(k) != v for k, v in {'point_normalized': point, 'valid_point': valid,
                'hit': hit, 'visible_bbox_hit': bbox, 'target_visible': bool(mask.any())}.items()):
            raise ValueError('Stored score disagrees with raw response/mask')
        index[key] = row
    if set(index) != set(expected):
        raise ValueError('Missing predictions')
    return index, meta


def compare(a, b):
    return {'hit_flip': a['hit'] != b['hit'],
            'gain': not a['hit'] and b['hit'], 'loss': a['hit'] and not b['hit'],
            'validity_flip': a['valid_point'] != b['valid_point'],
            'raw_response_changed': a['raw_response'] != b['raw_response'],
            'point_displacement_px': displacement(a, b)}


def summarize(rows):
    shifts = [r['point_displacement_px'] for r in rows if r['point_displacement_px'] is not None]
    return {'n': len(rows), **{k: sum(r[k] for r in rows) for k in
            ['hit_flip', 'gain', 'loss', 'validity_flip', 'raw_response_changed']},
            'valid_pair_count_for_displacement': len(shifts),
            'mean_point_displacement_px': float(np.mean(shifts)) if shifts else None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--runs', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    primary_path = a.raw/'manifest.json'
    control_path = a.raw/'render_control_manifest.json'
    primary = json.loads(primary_path.read_text())
    control = json.loads(control_path.read_text())
    protocol = json.loads((a.raw/'protocol.json').read_text())
    expected = [r['scene_id'] for r in json.loads((a.raw/'scenes.json').read_text())['scenes']]
    refs = validate_structure(primary, expected)
    controls = validate_control_structure(control, refs, protocol['render_noise_control_scene_ids'])
    validate_files(refs)
    validate_files(controls)
    ph = sha(a.raw/'protocol.json')
    if primary['protocol_sha256'] != ph or control['protocol_sha256'] != ph or control['primary_manifest_sha256'] != sha(primary_path):
        raise ValueError('Frozen input/protocol binding mismatch')
    result = {'scope': 'Three preselected scenes only; descriptive controls, not a 30-scene causal estimate.',
              'primary_manifest_sha256': sha(primary_path), 'control_manifest_sha256': sha(control_path),
              'models': {}, 'input_hashes': {}}
    for model in ['8b', '32b']:
        original, pm = load_verified_run(a.runs/model/'formal_repeat0', primary_path, refs, model, 'formal', ph)
        repeated, cm = load_verified_run(a.runs/model/'render_control_repeat0', control_path, controls, model, 'render_control', ph)
        for field in ['seed', 'revision', 'runner_sha256', 'processor_image_config', 'do_sample', 'max_new_tokens', 'dtype']:
            if pm[field] != cm[field]:
                raise ValueError('Primary/control model configuration mismatch: '+field)
        if cm['primary_manifest_sha256'] != sha(primary_path):
            raise ValueError('Control run primary binding mismatch')
        rows = []
        for ref in controls:
            key = (ref['pair_id'], ref['condition'])
            if original[key]['image']['sha256'] != ref['render_repeat_of_image_sha256']:
                raise ValueError('Control reference image mismatch')
            if original[key]['image_grid_thw'] != repeated[key]['image_grid_thw']:
                raise ValueError('Primary/control preprocessing mismatch')
            rows.append({'pair_id': key[0], 'condition': key[1], 'scene_id': ref['scene_id'],
                         **compare(original[key], repeated[key])})
        scene_results = {}
        for scene in protocol['render_noise_control_scene_ids']:
            sr = [r for r in rows if r['scene_id'] == scene]
            pairs = sorted({r['pair_id'] for r in sr})
            scene_results[scene] = {
                'same_condition_render_repeat': {c: summarize([r for r in sr if r['condition'] == c]) for c in ['original', 'converted']},
                'material_change_primary_repeat0': summarize([compare(original[k, 'original'], original[k, 'converted']) for k in pairs]),
                'material_change_repeated_render': summarize([compare(repeated[k, 'original'], repeated[k, 'converted']) for k in pairs])}
        result['models'][model] = {'by_scene': scene_results, 'same_condition_render_repeat_all': summarize(rows), 'rows': rows}
        for run in ['formal_repeat0', 'render_control_repeat0']:
            path = a.runs/model/run/'predictions.jsonl'
            result['input_hashes'][str(path)] = sha(path)
    with a.out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')


if __name__ == '__main__':
    main()
