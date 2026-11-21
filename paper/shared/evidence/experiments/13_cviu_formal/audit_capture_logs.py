"""Reject material compilation failures before visual qualification or freezing."""
import argparse
import hashlib
import json
import re
from pathlib import Path

MATERIAL_ERRORS = re.compile(
    r"MDLC\s+comp error|could not find module|Failed to create MDL shade node|"
    r"Loading MdlModule to DB.*failed|Unable to resolve.*(?:texture|\.mdl)|"
    r"Failed to load.*(?:texture|\.mdl)", re.IGNORECASE)


def inspect_log(log):
    data = log.read_bytes()
    lines = data.decode('utf-8', errors='replace').splitlines()
    errors = [{'line': i, 'text': line} for i, line in enumerate(lines, 1)
              if MATERIAL_ERRORS.search(line)]
    return {'log': str(log), 'log_sha256': hashlib.sha256(data).hexdigest(),
            'material_error_count': len(errors), 'material_errors': errors,
            'status': 'FAIL' if errors else 'NO_MATCHED_MATERIAL_ERRORS'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--captures', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    records = []
    for log in sorted(a.captures.glob('*.log')):
        row = inspect_log(log)
        row['scene_id'] = log.stem
        marker = log.with_suffix('.exit')
        row['exit_code'] = int(marker.read_text().strip()) if marker.exists() else None
        progress = a.captures / log.stem / 'progress.json'
        if progress.exists():
            data = json.loads(progress.read_text())
            row['completed'] = data['completed']
            row['planned'] = data['planned']
        row['capture_complete'] = (row['exit_code'] == 0 and
            row.get('completed', -1) == row.get('planned', -2))
        records.append(row)
    result = {'scope': 'Runtime log screening only; clean logs do not replace visual QA.',
              'records': records, 'failed_material_scenes': sum(r['status'] == 'FAIL' for r in records)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({'scanned_logs': len(records), 'failed_material_scenes': result['failed_material_scenes']}))


if __name__ == '__main__':
    main()
