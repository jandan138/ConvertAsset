"""Bind reviewed original-only selections into matched final O/C capture lists."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_capture_logs import inspect_log
from check_view_selections import check


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--jobs', type=Path, required=True)
    p.add_argument('--capture-log', type=Path, required=True)
    p.add_argument('--up-axis', choices=['Y', 'Z'], required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    review = json.loads(a.review.read_text())
    geometry = check(review, a.up_axis)
    if not geometry['proposal_geometry_pass']:
        raise ValueError('Selected target/view geometry incomplete')
    audit = inspect_log(a.capture_log)
    if audit['material_error_count']:
        raise ValueError('Material errors invalidate original selection')
    marker = a.capture_log.with_suffix('.exit')
    if not marker.exists() or marker.read_text().strip() != '0':
        raise ValueError('Candidate capture not successfully terminated')
    capture_audits = {}
    for target in review['targets']:
        for frame in target['frames']:
            if not frame.get('proposed_selected'):
                continue
            log = Path(frame['output']).parent.with_suffix('.log')
            if str(log) in capture_audits:
                continue
            item = inspect_log(log)
            exit_file = log.with_suffix('.exit')
            if item['material_error_count'] or not exit_file.exists() or exit_file.read_text().strip() != '0':
                raise ValueError('Selected candidate source capture not qualified: ' + str(log))
            capture_audits[str(log)] = item
    jobs = json.loads(a.jobs.read_text())['jobs']
    index = {(r['pair_id'], r['condition']): r for r in jobs}
    if len(index) != len(jobs):
        raise ValueError('Duplicate candidate keys')
    selected = []
    for target in review['targets']:
        if target.get('review_status') != 'reviewed_original_candidates':
            raise ValueError('Unreviewed target')
        query = 'Point to the ' + target['query_object'] + ' in the image.'
        for frame in target['frames']:
            if not frame.get('proposed_selected'):
                continue
            if frame['visual_verdict'].startswith('FAIL'):
                raise ValueError('Failed visual candidate selected')
            pair = []
            for condition in ['original', 'converted']:
                row = dict(index[(frame['pair_id'], condition)])
                if row['target_prim'] != target['target_prim'] or row['scene_id'] != review['scene_id']:
                    raise ValueError('Candidate identity mismatch')
                row.update(query=query, status='selected_requires_final_capture',
                           stage_sha256=sha(Path(row['stage'])),
                           original_selection_image_sha256=frame['image_sha256'])
                pair.append(row)
            selected.append(pair)
    assert len(selected) == 16
    a.out.mkdir(parents=True, exist_ok=False)
    for condition in ['original', 'converted']:
        rows = [r for pair in selected for r in pair if r['condition'] == condition]
        (a.out / (condition + '.json')).write_text(json.dumps({'jobs': rows}, indent=2) + '\n')
    (a.out / 'selection_receipt.json').write_text(json.dumps({
        'scene_id': review['scene_id'], 'review': str(a.review), 'review_sha256': sha(a.review),
        'candidate_jobs_sha256': sha(a.jobs), 'candidate_log_audit': audit, 'all_selected_capture_log_audits': capture_audits,
        'geometry': geometry, 'pair_count': len(selected),
        'status': 'selected_not_final_image_qualified',
        'condition_job_hashes': {c: sha(a.out / (c + '.json')) for c in ['original', 'converted']}
    }, indent=2) + '\n')
    print('Prepared 16 paired final capture views:', review['scene_id'])


if __name__ == '__main__':
    main()
