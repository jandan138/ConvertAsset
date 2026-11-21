"""Validate the repaired qualitative appendix sources before composing figures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MANIFEST = ROOT / 'paper/shared/evidence/raw/iclr_model_behavior/appendix_rerender_v1/manifest.json'
CASES = (
    ('bb985fd4504a1afe8516.zoom_017', 'Cup\nview B'),
    ('c8ee4b66274b05d242c2.zoom_017', 'Faucet'),
    ('ef6a4fe9448f672c2ecc.zoom_017', 'Picture'),
    ('47aa36277a54f6ca90cc.zoom_019', 'Backpack\nview 019'),
    ('f35ef3d86c42446b7ddf.zoom_019', 'Clock\nview 019'),
)
REQUIRED_DIAGNOSTICS = {'mdl_compiler', 'mdl_shader', 'missing_module',
                        'missing_texture', 'unresolved_asset'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_repaired_pairs(manifest_path=MANIFEST):
    """Fail closed on missing, unreviewed, stale, or historical render inputs."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('purpose') != 'qualitative_only_no_inference':
        raise ValueError('Appendix renders must remain separate from historical inference')
    if manifest.get('visual_review', {}).get('verdict') != 'PASS':
        raise ValueError('Appendix renders require completed visual review')
    records = manifest['records']
    expected = {(case, version) for case, _ in CASES for version in ('original', 'converted')}
    indexed = {(r['pair_id'], r['condition']): r for r in records}
    if len(records) != len(expected) or set(indexed) != expected:
        raise ValueError('Expected exactly five complete repaired appendix pairs')
    old_hashes = {r['old_image']['sha256'] for r in records if r['condition'] == 'original'}
    rows = []
    for case, label in CASES:
        row = {'id': case, 'label': label}
        for condition in ('original', 'converted'):
            record = indexed[case, condition]
            path = (ROOT / record['image']['path']).resolve()
            if not path.is_relative_to(manifest_path.parent.resolve()):
                raise ValueError(f'Repaired image outside versioned output directory: {path}')
            digest = sha(path)
            if digest != record['image']['sha256'] or digest in old_hashes:
                raise ValueError(f'Stale or historical appendix image: {path}')
            if record.get('return_code') != 0 or not record.get('capture_ready'):
                raise ValueError(f'Incomplete render: {case}/{condition}')
            diagnostics = record.get('material_errors', {})
            if not REQUIRED_DIAGNOSTICS.issubset(diagnostics):
                raise ValueError(f'Missing material diagnostics: {case}/{condition}')
            if any(diagnostics.values()):
                raise ValueError(f'Material compilation/loading errors: {case}/{condition}')
            if record.get('visual_review', {}).get('verdict') != 'PASS':
                raise ValueError(f'Unreviewed image: {case}/{condition}')
            row[condition] = path
        rows.append(row)
    return rows
