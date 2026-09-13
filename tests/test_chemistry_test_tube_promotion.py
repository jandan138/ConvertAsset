"""Promotion evidence gates; every write is to disposable copied packages."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/promote_chemistry_test_tube.py'
PACKAGE_ID = 'chemistry_test_tube_18x150_r1'
REQUIRED = {
    'rack_stable', 'glass_body_mass', 'rack_extraction', 'rack_reinsertion',
    'rack_guided_path_clear', 'cup_bottom_blocks', 'cup_wall_blocks',
    'actual_materials', 'actual_geometry', 'sample_eight_ml', 'new_tube_dimensions',
    'finite_actual_poses', 'complete_at_30', 'observation_success', 'reset_complete',
}
SCOPE = 'Isaac Sim 4.5 Fehling r7 rack and bath prescribed fixtures'


@pytest.fixture(scope='module')
def promoter():
    spec = importlib.util.spec_from_file_location('promote_chemistry_test_tube', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def snapshot(root):
    return {str(p.relative_to(root)): digest(p) for p in root.rglob('*') if p.is_file()}


@pytest.fixture(scope='module')
def pending_package(tmp_path_factory):
    """Exercise promotion from a new static build, never from the live qualification."""
    script = ROOT/'scripts/build_chemistry_test_tube.py'
    spec = importlib.util.spec_from_file_location('promotion_fixture_builder', script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    package = tmp_path_factory.mktemp('pending-tube')/'package'
    builder.build(ROOT/f'outputs/{PACKAGE_ID}_20260912/model', package)
    assert json.loads((package/'evidence/manifest.json').read_text())['overall_status'] == 'runtime_pending'
    return package


@pytest.fixture
def fixture(tmp_path, pending_package):
    source = pending_package
    producer = tmp_path/'producer'
    embedded = tmp_path/'handoff/deps'/PACKAGE_ID
    shutil.copytree(source, producer)
    shutil.copytree(source, embedded)
    # These are simulated test evidence, never the live SF delivery/reports.
    scene = tmp_path/'handoff/scene.usd'
    scene.write_text('#usda 1.0\ndef Xform "World" {}\n')
    reports = []
    for i in range(3):
        path = tmp_path/f'cold_start_{i+1}.json'
        write_json(path, dict(status='pass', runtime_version='4.5.0', glass_tube_r7=True,
                              package_id='synthetic_test_fixture_vr_r7',
                              scene_sha256=digest(scene),
                              tube_asset_sha256=digest(producer/'asset.usd'), process_id=100+i,
                              checks=dict.fromkeys(REQUIRED | {'extra_check'}, True),
                              snapshots=['large diagnostic data'], trajectories=[[0]*100]))
        reports.append(path)
    return dict(root=tmp_path, package=producer, embedded=embedded, scene=scene, reports=reports)


def invoke(promoter, fixture):
    return promoter.promote(fixture['package'], fixture['scene'], fixture['reports'])


def test_report_validation_uses_process_id_without_pid(promoter, fixture):
    for path in fixture['reports']:
        report = json.loads(path.read_text())
        assert 'process_id' in report and 'pid' not in report
    summaries, _ = promoter._read_reports(
        fixture['reports'], digest(fixture['scene']), digest(fixture['package']/'asset.usd'))
    assert [summary['process_id'] for summary in summaries] == [100, 101, 102]
    assert all('pid' not in summary for summary in summaries)


def test_completed_sf_reports_read_only(promoter):
    directory = os.environ.get('CHEMISTRY_TUBE_R7_REPORT_DIR')
    if not directory:
        pytest.skip('Set CHEMISTRY_TUBE_R7_REPORT_DIR for read-only actual-report validation')
    directory = Path(directory)
    paths = [directory/f'cold_start_{i}.json' for i in (1, 2, 3)]
    records = [json.loads(path.read_text()) for path in paths]
    scene = directory/'handoff'/records[0]['package_id']/'scene.usd'
    asset = ROOT/f'outputs/{PACKAGE_ID}_20260912/package/asset.usd'
    before = {path: digest(path) for path in [*paths, scene, asset]}
    summaries, hashes = promoter._read_reports(paths, before[scene], before[asset])
    assert [summary['process_id'] for summary in summaries] == sorted(r['process_id'] for r in records)
    assert all('pid' not in record for record in records + summaries)
    assert hashes == {path: before[path] for path in paths}
    assert {path: digest(path) for path in before} == before


def test_promotion_preserves_bytes_scopes_claims_and_is_idempotent(promoter, fixture):
    before = snapshot(fixture['root'])
    result = invoke(promoter, fixture)
    assert result['status'] == 'pass'
    producer_manifest = fixture['package']/'evidence/manifest.json'
    manifest = json.loads(producer_manifest.read_text())
    assert manifest['overall_status'] == 'pass'
    assert manifest['qualification_scope'] == SCOPE
    assert manifest['parameter_status'] == 'engineering_geometry'
    assert manifest['claims']['runtime_qualified'] is True
    for name in ('robot_qualified', 'heat_qualified', 'pbd_qualified', 'manufacturer_replica'):
        assert manifest['claims'][name] is False
    assert producer_manifest.read_bytes() == (fixture['embedded']/'evidence/manifest.json').read_bytes()
    assert len(manifest['runtime_evidence']) == 3
    for relative in manifest['runtime_evidence']:
        path = fixture['package']/relative
        summary = json.loads(path.read_text())
        assert summary['original_report_sha256'] in [digest(p) for p in fixture['reports']]
        assert summary['process_id'] in (100, 101, 102)
        assert REQUIRED <= summary['checks'].keys()
        assert all(value is True for value in summary['checks'].values())
        assert summary['scene_sha256'] == digest(fixture['scene'])
        assert summary['tube_asset_sha256'] == digest(fixture['package']/'asset.usd')
        assert 'snapshots' not in summary and 'trajectories' not in summary
        assert path.read_bytes() == (fixture['embedded']/relative).read_bytes()
    after = snapshot(fixture['root'])
    mutable = {'producer/evidence/manifest.json', f'handoff/deps/{PACKAGE_ID}/evidence/manifest.json'}
    assert all(after[path] == value for path, value in before.items() if path not in mutable)
    fixture['reports'].reverse()
    assert invoke(promoter, fixture)['status'] == 'pass'
    assert snapshot(fixture['root']) == after


@pytest.mark.parametrize('change', [
    'stale_scene', 'stale_asset', 'failed_status', 'old_runtime', 'not_r7', 'wrong_package',
    'duplicate_process_id', 'missing_process_id', 'bool_process_id', 'legacy_pid_only',
    'string_process_id', 'float_process_id', 'zero_process_id', 'negative_process_id', 'null_process_id',
    'duplicate_path', 'missing_report',
    'missing_check', 'failed_check', 'truthy_check', 'failed_extra_check',
])
def test_report_gates_do_not_write_any_metadata(promoter, fixture, change):
    paths = fixture['reports']
    report = json.loads(paths[1].read_text())
    updates = {
        'stale_scene': {'scene_sha256': '0'*64},
        'stale_asset': {'tube_asset_sha256': '0'*64},
        'failed_status': {'status': 'fail'}, 'old_runtime': {'runtime_version': '4.1.0'},
        'not_r7': {'glass_tube_r7': False}, 'wrong_package': {'package_id': 'synthetic_vr_r6'},
        'duplicate_process_id': {'process_id': 100}, 'bool_process_id': {'process_id': True},
        'string_process_id': {'process_id': '101'}, 'float_process_id': {'process_id': 101.0},
        'zero_process_id': {'process_id': 0}, 'negative_process_id': {'process_id': -101},
        'null_process_id': {'process_id': None},
    }
    report.update(updates.get(change, {}))
    if change in ('missing_process_id', 'legacy_pid_only'):
        process_id = report.pop('process_id')
        if change == 'legacy_pid_only':
            report['pid'] = process_id
    elif change == 'duplicate_path':
        paths[1] = paths[0]
    elif change == 'missing_report':
        paths.pop()
    elif change == 'missing_check':
        report['checks'].pop('rack_extraction')
    elif change in ('failed_check', 'truthy_check', 'failed_extra_check'):
        key = 'extra_check' if change == 'failed_extra_check' else 'rack_reinsertion'
        report['checks'][key] = 1 if change == 'truthy_check' else False
    if change not in ('duplicate_path', 'missing_report'):
        write_json(paths[1], report)
    before = snapshot(fixture['root'])
    with pytest.raises(ValueError):
        invoke(promoter, fixture)
    assert snapshot(fixture['root']) == before


@pytest.mark.parametrize('relative', [
    'asset.usd', 'deps/mdl/OmniGlass_Opacity.mdl', 'source/tube.blend',
    'source/geometry.json', 'evidence/static_validation.json',
    'evidence/blender_reopen.json',
])
def test_changed_embedded_evidence_or_artifacts_fail_closed(promoter, fixture, relative):
    path = fixture['embedded']/relative
    if relative == 'evidence/blender_reopen.json':
        data = json.loads(path.read_text())
        data['independent_process_reopen'] = False
        write_json(path, data)
    else:
        path.write_bytes(path.read_bytes()+b'\ncorrupted\n')
    before = snapshot(fixture['root'])
    with pytest.raises((ValueError, RuntimeError)):
        invoke(promoter, fixture)
    assert snapshot(fixture['root']) == before


def test_producer_stale_hash_is_rejected(promoter, fixture):
    path = fixture['package']/'evidence/manifest.json'
    data = json.loads(path.read_text())
    data['asset_sha256'] = '0'*64
    write_json(path, data)
    before = snapshot(fixture['root'])
    with pytest.raises(ValueError):
        invoke(promoter, fixture)
    assert snapshot(fixture['root']) == before


def test_different_archive_is_never_overwritten(promoter, fixture):
    invoke(promoter, fixture)
    manifest_path = fixture['package']/'evidence/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    archive = fixture['embedded']/manifest['runtime_evidence'][0]
    archive.write_text('{"different": "archived evidence"}\n')
    before = snapshot(fixture['root'])
    with pytest.raises(ValueError, match='archiv'):
        invoke(promoter, fixture)
    assert snapshot(fixture['root']) == before


def test_changed_reports_after_promotion_rejected(promoter, fixture):
    invoke(promoter, fixture)
    report = fixture['reports'][0]
    report.write_bytes(report.read_bytes()+b'\n')
    before = snapshot(fixture['root'])
    with pytest.raises(ValueError):
        invoke(promoter, fixture)
    assert snapshot(fixture['root']) == before


def test_interrupted_manifest_sync_can_retry_same_evidence(promoter, fixture, monkeypatch):
    original = promoter._atomic_manifest
    calls = []

    def fail_second(path, payload):
        calls.append(path)
        if len(calls) == 2:
            raise OSError('simulated manifest publication failure')
        original(path, payload)

    monkeypatch.setattr(promoter, '_atomic_manifest', fail_second)
    with pytest.raises(OSError, match='simulated'):
        invoke(promoter, fixture)
    monkeypatch.setattr(promoter, '_atomic_manifest', original)
    assert invoke(promoter, fixture)['status'] == 'pass'
    assert (fixture['package']/'evidence/manifest.json').read_bytes() == (
        fixture['embedded']/'evidence/manifest.json').read_bytes()


def test_cli_help_has_no_sdk_dependency(promoter):
    result = subprocess.run([sys.executable, '-I', '-S', '-B', str(SCRIPT), '--help'],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for option in ('--package', '--scene', '--report'):
        assert option in result.stdout


def test_matching_but_invalid_blender_reopen_proof_rejected(promoter, fixture):
    for folder in (fixture['package'], fixture['embedded']):
        path = folder/'evidence/blender_reopen.json'
        report = json.loads(path.read_text())
        report['independent_process_reopen'] = False
        write_json(path, report)
    before = snapshot(fixture['root'])
    with pytest.raises(ValueError, match='Independent Blender reopen'):
        invoke(promoter, fixture)
    assert snapshot(fixture['root']) == before


def test_archive_io_failure_cannot_publish_success(promoter, fixture, monkeypatch):
    original = promoter._archive
    calls = []

    def fail_second(path, payload):
        calls.append(path)
        if len(calls) == 2:
            raise OSError('simulated archive write failure')
        original(path, payload)

    monkeypatch.setattr(promoter, '_archive', fail_second)
    with pytest.raises(OSError, match='simulated archive'):
        invoke(promoter, fixture)
    for folder in (fixture['package'], fixture['embedded']):
        manifest = json.loads((folder/'evidence/manifest.json').read_text())
        assert manifest['overall_status'] == 'runtime_pending'
        assert manifest['claims']['runtime_qualified'] is False


def test_cli_promotes_only_disposable_copy_with_three_report_flags(promoter, fixture):
    command = [sys.executable, '-B', str(SCRIPT), '--package', str(fixture['package']),
               '--scene', str(fixture['scene'])]
    for report in fixture['reports']:
        command.extend(['--report', str(report)])
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary['status'] == 'pass'
    assert summary['process_ids'] == [100, 101, 102]
    assert summary['qualification_scope'] == SCOPE


def test_atomic_manifest_preserves_existing_access_mode(promoter, tmp_path):
    path = tmp_path/'manifest.json'
    path.write_text('{}\n')
    path.chmod(0o644)
    promoter._atomic_manifest(path, b'{"status": "test-only"}\n')
    assert path.stat().st_mode & 0o777 == 0o644
