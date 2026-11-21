"""Verify reviewed original candidate identities and selected camera separation.

This validates proposals only. Final original/converted recapture and its own
technical/visual qualification are mandatory before model-input freezing.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path


def camera_azimuth(camera_parameters, up_axis):
    matrix = ast.literal_eval(camera_parameters['xformOp:transform'])
    back = matrix[2][:3]
    if up_axis == 'Z':
        x, y = back[0], back[1]
    elif up_axis == 'Y':
        x, y = back[0], back[2]
    else:
        raise ValueError('Unsupported up axis')
    if not all(math.isfinite(float(v)) for row in matrix for v in row):
        raise ValueError('Nonfinite camera')
    if math.hypot(x, y) < 1e-10:
        raise ValueError('Vertical camera has no azimuth')
    return math.degrees(math.atan2(y, x)) % 360


def separation(a, b):
    difference = abs(a - b) % 360
    return min(difference, 360 - difference)


def check(review, up_axis):
    records = []
    for target in review['targets']:
        selected = [r for r in target['frames'] if r.get('proposed_selected')]
        errors = []
        angles = []
        if len(selected) != 2:
            errors.append('requires_exactly_two_reviewed_views')
        for frame in selected:
            folder = Path(frame['output'])
            receipt = json.loads((folder / 'receipt.json').read_text())
            if receipt['pair_id'] != frame['pair_id'] or receipt['target_prim'] != target['target_prim']:
                errors.append('capture_identity_mismatch')
            if receipt['condition'] != 'original':
                errors.append('selection_must_use_original_only')
            for filename, key in [('rgb.png', 'image_sha256'), ('target_mask.npy', 'mask_sha256')]:
                actual = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
                if actual != frame[key] or actual != receipt[key]:
                    errors.append('changed_capture_' + key)
            if receipt['rgb_blank'] or receipt['mask_pixels'] <= 0:
                errors.append('unqualified_original_capture')
            angles.append(camera_azimuth(receipt['camera_parameters'], up_axis))
        delta = separation(*angles) if len(angles) == 2 else None
        if delta is not None and delta < 30 - 1e-6:
            errors.append('azimuth_separation_below_30_degrees')
        records.append({'target_prim': target['target_prim'], 'selected_pair_ids': [r['pair_id'] for r in selected],
                        'azimuth_degrees': angles, 'separation_degrees': delta, 'errors': errors})
    return {'scene_id': review['scene_id'], 'target_count': len(records), 'records': records,
            'proposal_geometry_pass': len(records) == 8 and all(not r['errors'] for r in records),
            'scope': 'Proposal identity/geometry only; runtime material log and final paired image QA remain separate.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--up-axis', choices=['Z', 'Y'], required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = check(json.loads(a.review.read_text()), a.up_axis)
    with a.out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({'scene_id': result['scene_id'], 'proposal_geometry_pass': result['proposal_geometry_pass'],
                      'separations': [r['separation_degrees'] for r in result['records']]}))
