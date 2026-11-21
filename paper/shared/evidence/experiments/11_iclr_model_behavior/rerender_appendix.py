#!/usr/bin/env python3
"""Rerender five historical appendix views without replacing inference inputs.

Run with ordinary Python; each capture uses the repository Isaac launcher.
Outputs are unapproved until a human-style visual review is recorded separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / 'paper/shared/evidence/raw'
DEFAULT_OUT = RAW / 'iclr_model_behavior/appendix_rerender_v1'
DEFAULT_WORK = Path('/cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/appendix_rerender_20260922')
CASES = (
    '47aa36277a54f6ca90cc.zoom_019', 'f35ef3d86c42446b7ddf.zoom_019',
    'bb985fd4504a1afe8516.zoom_017', 'c8ee4b66274b05d242c2.zoom_017',
    'ef6a4fe9448f672c2ecc.zoom_017',
)
ERROR_PATTERNS = {
    'mdl_compiler': r'\[MDLC:COMPILER\].*(?:comp error|error:)',
    'mdl_shader': r'Failed to create MDL(?: shade)? node',
    'missing_module': r'could not find module',
    'missing_texture': r'(?i)(?:failed|unable|could not|cannot).*(?:load|open|resolve).*texture|texture.*(?:not found|does not exist)',
    'unresolved_asset': r'(?i)(?:could not|failed to) (?:open|resolve) (?:asset|reference|sublayer)',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def preserve_inputs(out):
    """Freeze historical inputs and predictions before the first capture."""
    dest = out / 'preserved_inputs.json'
    if dest.exists():
        entries = json.loads(dest.read_text())
        changed = [p for p, digest in entries.items() if sha(ROOT / p) != digest]
        if changed:
            raise ValueError(f'Historical evidence changed: {changed}')
        return
    analysis = json.loads((RAW / 'iclr_model_behavior/analysis_v1/results.json').read_text())
    paths = {ROOT / r['source'] for r in analysis['runs']}
    for case in CASES:
        report = json.loads((RAW / f'grscene_vlm_grounding/retake_zoom_paired_render_reports/{case}.json').read_text())
        for record in report['records']:
            paths.add(Path(record['image']['path']))
    # Also protect all saved model inputs referenced by analyzed prediction files.
    for path in list(paths):
        if path.suffix == '.jsonl':
            for line in path.open():
                record = json.loads(line)
                image = record.get('image', {}).get('path')
                if image and Path(image).is_file():
                    paths.add(Path(image))
    dump(dest, {rel(p): sha(p) for p in sorted(paths)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--work', type=Path, default=DEFAULT_WORK)
    ap.add_argument('--pair-id', choices=CASES, action='append')
    ap.add_argument('--timeout', type=int, default=900)
    args = ap.parse_args()
    args.out = args.out.resolve(); args.work = args.work.resolve()
    args.out.mkdir(parents=True, exist_ok=True); args.work.mkdir(parents=True, exist_ok=True)
    preserve_inputs(args.out)
    manifest_path = args.out / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'schema_version': 1, 'purpose': 'qualitative_only_no_inference',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'generator': rel(__file__), 'generator_sha256': sha(__file__),
        'historical_inputs': rel(args.out / 'preserved_inputs.json'),
        'records': [], 'visual_review': {'verdict': 'PENDING'},
    }
    for case in args.pair_id or CASES:
        old_path = RAW / f'grscene_vlm_grounding/retake_zoom_paired_render_reports/{case}.json'
        old = json.loads(old_path.read_text())
        for r in old['records']:
            command = list(r['render_command'])
            condition = 'original' if '.original' in r['sample_id'] else 'converted'
            prior = next((x for x in manifest['records'] if x['pair_id'] == case and x['condition'] == condition), None)
            if prior:
                if not prior['capture_ready']:
                    raise ValueError(f'Previous capture failed; diagnose before retrying in a fresh work directory: {case}/{condition}')
                if sha(ROOT / prior['image']['path']) != prior['image']['sha256']:
                    raise ValueError('Completed image changed')
                continue
            folder = args.out / case / condition; folder.mkdir(parents=True, exist_ok=True)
            log_dir = args.work / case / condition; log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / 'render.log'
            command[command.index('--output-dir') + 1] = str(folder)
            command[command.index('--wait-frames') + 1] = '32'
            camera = Path(command[command.index('--usd-path') + 1])
            old_image = Path(r['image']['path'])
            image_path = folder / f'{condition}_0000.png'
            if image_path.exists() or log_path.exists():
                raise ValueError(f'Unregistered capture already exists: {folder} / {log_path}')
            before = time.monotonic()
            print(f'START {case}/{condition}', flush=True)
            with log_path.open('w') as log:
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True, env={**os.environ, 'PYTHONUNBUFFERED': '1'})
                try:
                    code = process.wait(timeout=args.timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait()
                    code = 'timeout'
            text = log_path.read_text(errors='replace')
            errors = {name: len(re.findall(pattern, text)) for name, pattern in ERROR_PATTERNS.items()}
            ready = code == 0 and image_path.exists() and 'Saved frame 0' in text and not any(errors.values())
            record = {
                'pair_id': case, 'condition': condition, 'command': command, 'return_code': code,
                'elapsed_seconds': round(time.monotonic() - before, 2),
                'camera_stage': {'path': rel(camera), 'sha256': sha(camera)},
                'old_report': {'path': rel(old_path), 'sha256': sha(old_path)},
                'old_image': {'path': rel(old_image), 'sha256': sha(old_image)},
                'image': {'path': rel(image_path), 'sha256': sha(image_path) if image_path.exists() else None},
                'log': {'path': str(log_path), 'sha256': sha(log_path)},
                'material_errors': errors, 'capture_ready': ready,
                'visual_review': {'verdict': 'PENDING'},
            }
            manifest['records'].append(record); dump(manifest_path, manifest)
            print(f'END {case}/{condition}: {code}, ready={ready}, errors={errors}', flush=True)
            if not ready:
                raise RuntimeError(f'Capture failed; see {log_path}')
    preserve_inputs(args.out)
    print(f'{len(manifest["records"])} captures recorded; visual review required', flush=True)


if __name__ == '__main__':
    main()
