"""The appendix must never silently reuse broken or unreviewed render evidence."""
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'appendix_render_sources', ROOT / 'paper/venues/iclr27/scripts/appendix_render_sources.py')
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)


@pytest.fixture
def approved(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, 'ROOT', tmp_path)
    out = tmp_path / 'rerender'; out.mkdir()
    records = []
    for pair, _ in sources.CASES:
        for condition in ('original', 'converted'):
            image = out / f'{pair}.{condition}.png'
            image.write_bytes(f'new-render-{pair}-{condition}'.encode())
            records.append({
                'pair_id': pair, 'condition': condition,
                'image': {'path': str(image.relative_to(tmp_path)), 'sha256': sources.sha(image)},
                'old_image': {'sha256': f'old-{pair}-{condition}'},
                'return_code': 0, 'capture_ready': True,
                'material_errors': {k: 0 for k in sources.REQUIRED_DIAGNOSTICS},
                'visual_review': {'verdict': 'PASS'},
            })
    path = out / 'manifest.json'
    data = {'purpose': 'qualitative_only_no_inference', 'visual_review': {'verdict': 'PASS'},
            'records': records}
    path.write_text(json.dumps(data))
    return path, data


def test_complete_approved_pairs_load_in_figure_order(approved):
    path, _ = approved
    rows = sources.load_repaired_pairs(path)
    assert [r['id'] for r in rows] == [c for c, _ in sources.CASES]
    assert all(r[v].is_file() for r in rows for v in ('original', 'converted'))


@pytest.mark.parametrize('failure', ['missing_pair', 'duplicate', 'compiler_error', 'unreviewed',
                                     'global_unreviewed', 'timeout', 'no_capture', 'old_pixels',
                                     'wrong_hash', 'outside_output', 'missing_diagnostics'])
def test_rejects_invalid_render_evidence(approved, failure):
    path, data = approved
    r = data['records'][0]
    if failure == 'missing_pair':
        data['records'].pop()
    elif failure == 'duplicate':
        data['records'][-1] = r
    elif failure == 'compiler_error':
        r['material_errors']['mdl_compiler'] = 1
    elif failure == 'unreviewed':
        r['visual_review']['verdict'] = 'PENDING'
    elif failure == 'global_unreviewed':
        data['visual_review']['verdict'] = 'PENDING'
    elif failure == 'timeout':
        r['return_code'] = 'timeout'
    elif failure == 'no_capture':
        r['capture_ready'] = False
    elif failure == 'old_pixels':
        r['old_image']['sha256'] = r['image']['sha256']
    elif failure == 'wrong_hash':
        r['image']['sha256'] = 'stale'
    elif failure == 'outside_output':
        r['image']['path'] = 'historical.png'
    elif failure == 'missing_diagnostics':
        r['material_errors'] = {}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        sources.load_repaired_pairs(path)


def test_missing_file_is_not_replaced_with_historical_input(approved):
    path, data = approved
    (sources.ROOT / data['records'][0]['image']['path']).unlink()
    with pytest.raises(FileNotFoundError):
        sources.load_repaired_pairs(path)
