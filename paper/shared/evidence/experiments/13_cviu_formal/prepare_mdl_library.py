"""Copy MDL text into an isolated library and repair only broken local imports.

Texture resources remain read-only links. Never run the historical in-place
repair tool through a Materials symlink into the source dataset.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(source, output, repair_script):
    source = source.resolve()
    output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('mdl_import_repair', repair_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = []
    for item in sorted(source.iterdir()):
        target = output / item.name
        if item.is_file() and item.suffix == '.mdl':
            before = item.read_bytes()
            after, count = module.repair_text(before.decode('utf-8'))
            target.write_bytes(after.encode('utf-8'))
            assert item.read_bytes() == before, 'Source changed during copy'
            records.append({'source': str(item), 'output': str(target),
                            'source_sha256': hashlib.sha256(before).hexdigest(),
                            'output_sha256': sha(target), 'replacements': count})
        else:
            target.symlink_to(item, target_is_directory=item.is_dir())
    receipt = {'source': str(source), 'output': str(output.resolve()),
               'repair_script_sha256': sha(repair_script), 'files': records,
               'changed_files': sum(r['replacements'] > 0 for r in records),
               'status': 'prepared_requires_runtime_validation'}
    (output / 'repair_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repair-script', type=Path, default=Path('scripts/fix_mdl_absolute_imports.py'))
    args = parser.parse_args()
    result = prepare(args.source, args.out, args.repair_script)
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}))
