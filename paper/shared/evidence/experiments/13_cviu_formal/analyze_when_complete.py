"""Wait for both durable campaigns, then run full primary and control analyses."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--runs', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.raw, a.runs, a.out = (x.resolve() for x in [a.raw, a.runs, a.out])
    a.out.mkdir(parents=True, exist_ok=False)
    status_path = a.out/'status.json'
    def save(status, **fields):
        temp = a.out/'status.tmp'
        temp.write_text(json.dumps({'status': status, **fields}, indent=2)+'\n')
        temp.replace(status_path)
    while True:
        campaigns = {m: json.loads((a.runs/m/'campaign.json').read_text()) for m in ['8b', '32b']}
        states = {m: c['status'] for m, c in campaigns.items()}
        if any(s.startswith('failed') for s in states.values()):
            save('failed_upstream', campaigns=states)
            raise RuntimeError('Upstream failure; no partial analysis emitted')
        if all(s == 'complete' for s in states.values()):
            break
        save('waiting_for_complete_campaigns', campaigns=states)
        time.sleep(30)
    directory = Path(__file__).parent
    inputs = [a.runs/m/f'formal_repeat{r}'/'predictions.jsonl' for m in ['8b', '32b'] for r in range(3)]
    commands = [
        [sys.executable, str(directory/'analyze_formal.py'), '--manifest', str(a.raw/'manifest.json'),
         '--scenes', str(a.raw/'scenes.json'), '--inputs', *map(str, inputs), '--out', str(a.out/'primary')],
        [sys.executable, str(directory/'analyze_render_controls.py'), '--raw', str(a.raw),
         '--runs', str(a.runs), '--out', str(a.out/'render_controls.json')]]
    for name, command in zip(['primary', 'render_controls'], commands):
        save('analyzing', step=name)
        with (a.out/(name+'.log')).open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            save('failed_analysis', step=name, exit_code=result.returncode)
            raise RuntimeError('Analysis failed: '+name)
    save('analyses_complete_requires_interpretation',
         primary=str(a.out/'primary/results.json'), controls=str(a.out/'render_controls.json'),
         scope='Automated numeric outputs only; evidence interpretation and goal completion audit remain required.')


if __name__ == '__main__':
    main()
