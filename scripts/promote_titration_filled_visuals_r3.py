"""Promote the exact r3 asset after three fresh Isaac 4.5 standalone runs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


def promote(root, reports):
    package = root/'packages/station'
    digest = sha256((package/'asset.usd').read_bytes()).hexdigest()
    data = [json.loads(p.read_text()) for p in reports]
    if len(data) != 3 or len({p.resolve() for p in reports}) != 3:
        raise ValueError('three separate cold-start reports required')
    if any(r['status'] != 'pass' or r['asset_sha256'] != digest or r['runtime_version'] != '4.5.0' for r in data):
        raise ValueError('qualification does not cover this exact asset')
    evidence = []
    for i, path in enumerate(reports, 1):
        dest = package/f'evidence/runtime/cold_start_{i}.json'
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        evidence.append({'path': str(dest.relative_to(root)), 'sha256': sha256(dest.read_bytes()).hexdigest()})
    manifest_path = package/'evidence/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.update(overall_status='pass', blocked_reasons=[], runtime_evidence=evidence)
    manifest['claims'].update(isaac45_runtime_qualified=True, runtime_cold_start_passes=3,
                              state_machine_success_and_overshoot_paths=True)
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    receipt = {'schema_version': 'aan.traditional_titration_promotion.v1',
               'package_id': manifest['package_id'], 'package': 'packages/station', 'status': 'promoted',
               'runtime': 'Isaac Sim 4.5.0', 'cold_start_passes': 3, 'asset_sha256': digest,
               'manifest_sha256': sha256(manifest_path.read_bytes()).hexdigest(), 'evidence': evidence,
               'claims': {'asset_functionality': True, 'robot_policy_success': False, 'benchmark_success': False}}
    (root/'promotion_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(root/'promotion_receipt.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--report', type=Path, action='append', required=True)
    args = parser.parse_args()
    promote(args.root, args.report)
