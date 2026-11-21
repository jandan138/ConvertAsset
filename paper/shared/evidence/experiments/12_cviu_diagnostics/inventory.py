"""Freeze outcome-independent scene ordering; never infer render readiness from existence."""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE = Path('/cpfs/user/zhuzihou/assets/zzh-grscenes')
CONVERTED = Path('/cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/nomdl_full/zzh-grscenes_nomdl_full_work_20260521')
COUNTS = {'home_scenes': [('pilot', 2), ('train', 10), ('validation', 3), ('test', 7)],
          'commercial_scenes': [('pilot', 1), ('train', 5), ('validation', 2), ('test', 3)]}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inventory(source, converted, seed=20261109):
    records = []
    for family, allocation in COUNTS.items():
        folder = source / 'scenes/GRScenes-100' / family / 'scenes'
        candidates = sorted(folder.glob('*/start_result_raw.usd'), key=lambda p: hashlib.sha256(f'{seed}:{family}:{p.parent.name}'.encode()).hexdigest())
        if len(candidates) < sum(n for _, n in allocation):
            raise ValueError(f'Insufficient {family} scenes: {len(candidates)}')
        assignments = [group for group, n in allocation for _ in range(n)]
        for i, original in enumerate(candidates):
            target = converted / original.relative_to(source).parent / 'start_result_raw_noMDL.usd'
            records.append({'scene_id': original.parent.name, 'family': family,
                'split': assignments[i] if i < len(assignments) else 'reserve',
                'order': i, 'original': str(original), 'converted': str(target),
                'original_sha256': digest(original),
                'converted_sha256': digest(target) if target.is_file() else None,
                'status': 'entries_present_dependencies_unverified' if target.is_file() else 'converted_entry_missing'})
    return {'schema_version': 1, 'seed': seed, 'selection': 'SHA256(seed:family:scene_id); independent of model outcomes; missing conversions do not silently change split', 'scenes': records}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=SOURCE)
    p.add_argument('--converted', type=Path, default=CONVERTED)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = inventory(a.source, a.converted)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({s: sum(r['split']==s for r in result['scenes']) for s in ['pilot','train','validation','test','reserve']}))

if __name__ == '__main__':
    main()
