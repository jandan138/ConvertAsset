"""Run three independent primary processes and one auxiliary process per model."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--model', choices=['8b', '32b'], required=True)
    p.add_argument('--checkpoint', type=Path, required=True)
    a = p.parse_args()
    a.raw = a.raw.resolve()
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)
    runner = Path(__file__).with_name('formal_inference.py').resolve()
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    bound = {str(path): digest(path) for path in [runner, a.raw/'manifest.json',
             a.raw/'render_control_manifest.json', a.raw/'protocol.json', a.raw/'scenes.json']}
    receipt = {'model': a.model, 'pid': os.getpid(), 'status': 'running',
               'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
               'bound_files': bound, 'runs': []}
    def save():
        temp = a.out/'campaign.tmp'
        temp.write_text(json.dumps(receipt, indent=2)+'\n')
        temp.replace(a.out/'campaign.json')
    save()
    for mode, repeat in [('formal', i) for i in range(3)] + [('render_control', 0)]:
        if any(digest(Path(path)) != expected for path, expected in bound.items()):
            receipt['status'] = 'failed_input_mutation'
            save()
            raise RuntimeError('Bound campaign inputs or runner changed')
        name = f'{mode}_repeat{repeat}'
        output = a.out/name
        cmd = [sys.executable, str(runner), '--manifest', str(a.raw/(
            'manifest.json' if mode == 'formal' else 'render_control_manifest.json')),
            '--scenes', str(a.raw/'scenes.json'), '--protocol', str(a.raw/'protocol.json'),
            '--model', a.model, '--checkpoint', str(a.checkpoint), '--repeat', str(repeat),
            '--mode', mode, '--out', str(output)]
        if mode == 'render_control':
            cmd += ['--primary-manifest', str(a.raw/'manifest.json')]
        record = {'name': name, 'command': cmd, 'status': 'running'}
        receipt['runs'].append(record)
        save()
        with (a.out/(name+'.log')).open('x') as log:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
        record['exit_code'] = result.returncode
        completion = output/'completion.json'
        done = json.loads(completion.read_text()) if completion.exists() else {}
        record['completion'] = done
        expected = 960 if mode == 'formal' else 96
        if result.returncode or done.get('status') != 'complete' or done.get('records') != expected or done.get('runtime_errors') != 0:
            record['status'] = receipt['status'] = 'failed'
            save()
            raise RuntimeError('Run incomplete; preserve outputs for diagnosis: '+name)
        record['status'] = 'complete'
        save()
    receipt['status'] = 'complete'
    save()


if __name__ == '__main__':
    main()
