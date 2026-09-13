"""Promote only metadata after three exact Isaac 4.5 Fehling r7 fixture passes.

Never launches a simulator or modifies asset, Blender, geometry, MDL or scene
bytes. All preflight gates run before publication to either package. Identical
retries (including interrupted two-folder synchronization) are safe; conflicting
archived evidence or a different previous qualification is an explicit error.
"""
import argparse
import copy
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


PACKAGE_ID = 'chemistry_test_tube_18x150_r1'
SCOPE = 'Isaac Sim 4.5 Fehling r7 rack and bath prescribed fixtures'
REQUIRED_CHECKS = frozenset({
    'rack_stable', 'glass_body_mass', 'rack_extraction', 'rack_reinsertion',
    'rack_guided_path_clear', 'cup_bottom_blocks', 'cup_wall_blocks',
    'actual_materials', 'actual_geometry', 'sample_eight_ml', 'new_tube_dimensions',
    'finite_actual_poses', 'complete_at_30', 'observation_success', 'reset_complete',
})
_PROMOTION_KEYS = ('qualification_scope', 'runtime_version', 'runtime_qualification',
                   'runtime_evidence_sha256')


def _sha(path):
    return sha256(path.read_bytes()).hexdigest()


def _json(path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f'Expected JSON object: {path}')
    return value


def _encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _read_reports(paths, scene_sha, asset_sha):
    _require(len(paths) == 3 and len(set(paths)) == 3,
             'Exactly three nonduplicate report paths required')
    summaries, hashes, process_ids, identities = [], {}, set(), set()
    for path in paths:
        raw = path.read_bytes()
        report = json.loads(raw)
        _require(isinstance(report, dict), f'Report must be an object: {path}')
        _require(report.get('status') == 'pass', f'Report status must pass: {path}')
        _require(report.get('runtime_version') == '4.5.0', f'Expected runtime_version 4.5.0: {path}')
        _require(report.get('glass_tube_r7') is True, f'glass_tube_r7 must be true: {path}')
        identity = report.get('package_id')
        _require(isinstance(identity, str) and identity.endswith('_vr_r7'),
                 f'Expected scene package_id ending _vr_r7: {path}')
        identities.add(identity)
        _require(report.get('scene_sha256') == scene_sha, f'Stale scene_sha256: {path}')
        _require(report.get('tube_asset_sha256') == asset_sha, f'Stale tube_asset_sha256: {path}')
        process_id = report.get('process_id')
        _require(type(process_id) is int and process_id > 0 and process_id not in process_ids,
                 f'Three distinct nonmissing positive integer process IDs (process_id) required: {path}')
        process_ids.add(process_id)
        checks = report.get('checks')
        _require(isinstance(checks, dict), f'Missing checks object: {path}')
        missing = REQUIRED_CHECKS - checks.keys()
        _require(not missing, f'Missing required checks {sorted(missing)}: {path}')
        _require(all(value is True for value in checks.values()),
                 f'All checks, including additional checks, must be boolean true: {path}')
        digest = sha256(raw).hexdigest()
        hashes[path] = digest
        summaries.append(dict(
            schema='chemistry-test-tube-fehling-r7-runtime-summary-v1',
            original_report_path=str(path), original_report_sha256=digest,
            status='pass', runtime_version='4.5.0', glass_tube_r7=True,
            package_id=identity, scene_sha256=scene_sha, tube_asset_sha256=asset_sha,
            process_id=process_id, checks=checks, qualification_scope=SCOPE,
        ))
    _require(len(identities) == 1, 'Reports name different r7 scene packages')
    return sorted(summaries, key=lambda item: item['process_id']), hashes


def _immutable_files(package):
    """Protect all package files except the manifest and runtime evidence archive."""
    result = {}
    for path in package.rglob('*'):
        _require(not path.is_symlink(), f'Symlink within package is not supported: {path}')
        if path.is_file():
            relative = path.relative_to(package).as_posix()
            if relative != 'evidence/manifest.json' and not relative.startswith('evidence/runtime/'):
                result[relative] = _sha(path)
    return result


def _audit_bundle(package):
    # Local producer helper owns USD/MDL checks. No pxr import until it is called.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_chemistry_test_tube import audit_package

    manifest = _json(package/'evidence/manifest.json')
    _require(manifest.get('package_id') == PACKAGE_ID, 'Unexpected producer package_id')
    _require(manifest.get('parameter_status') == 'engineering_geometry', 'Engineering geometry status required')
    _require(manifest.get('source', {}).get('blend') == 'source/tube.blend'
             and manifest.get('source', {}).get('geometry') == 'source/geometry.json',
             'Unexpected Blender source entrypoints')
    _require(manifest.get('entrypoints') == dict(root_usd='asset.usd', default_prim='World',
                                               asset_entry_prim='/World/TestTube'),
             'Unexpected producer entrypoints')
    claims = manifest.get('claims', {})
    _require(claims.get('static_geometry') is True, 'Static geometry claim missing')
    for name in ('robot_qualified', 'heat_qualified', 'pbd_qualified', 'manufacturer_replica'):
        _require(claims.get(name) is False, f'Unsupported inherited claim: {name}')
    for name in ('blender_production.json', 'blender_reopen.json'):
        report = _json(package/'evidence'/name)
        _require(report.get('status') == 'pass' and report.get('blender_version') == '4.4.3',
                 f'Blender creation/reopen status/version invalid: {name}')
        for flag in ('closed_manifold', 'consistent_winding', 'outward_from_glass',
                     'nondegenerate', 'lumen_rays_pass'):
            _require(report.get(flag) is True, f'Blender {flag} missing/failed: {name}')
        if name == 'blender_reopen.json':
            _require(report.get('independent_process_reopen') is True, 'Independent Blender reopen missing')
        else:
            _require(report.get('device') == 'CPU' and report.get('engine') == 'CYCLES',
                     'Blender CPU Cycles production evidence required')
            _require(set(report.get('previews', {})) == {'preview_overview.png', 'preview_mouth.png'},
                     'Both Blender production previews required')
    result = audit_package(package)
    _require(result['status'] == 'pass', 'Producer package static audit did not pass')
    return manifest, result


def _base_manifest(manifest):
    status = manifest.get('overall_status')
    _require(status in ('runtime_pending', 'pass'), 'Unsupported existing promotion status')
    if status == 'runtime_pending':
        _require(manifest.get('runtime_evidence') == []
                 and manifest['claims'].get('runtime_qualified') is False
                 and not any(key in manifest for key in _PROMOTION_KEYS),
                 'Incomplete/conflicting pending promotion metadata')
    base = copy.deepcopy(manifest)
    for key in _PROMOTION_KEYS:
        base.pop(key, None)
    base.update(overall_status='runtime_pending', runtime_evidence=[])
    base['claims']['runtime_qualified'] = False
    return base


def _atomic_manifest(path, payload):
    """Publish a complete manifest, leaving its previous bytes on write failure."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.tube-promotion-', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), stat.S_IMODE(path.stat().st_mode))
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _archive(path, payload):
    # Exclusive creation: never overwrite another report, even on a retry.
    if path.exists():
        _require(path.read_bytes() == payload, f'Conflicting archived report: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def promote(package, scene, reports):
    """Validate all evidence, then synchronize narrowly scoped metadata only.

    The consumer materializes the mesh, so runtime reports bind the actual scene
    SHA and asset identity. This CLI does not infer runtime success from a USD
    reference or promote from diagnostics. No materialization/shadow edits occur.
    """
    package, scene = Path(package).resolve(), Path(scene).resolve()
    embedded = scene.parent/'deps'/PACKAGE_ID
    paths = [Path(path).resolve() for path in reports]
    _require(package != embedded.resolve(), 'Producer and consumer must be separate package copies')
    _require(package.is_dir() and embedded.is_dir(), 'Producer and embedded packages must exist')
    # Capture immutable bytes and inputs before any expensive USD inspection.
    scene_sha, asset_sha = _sha(scene), _sha(package/'asset.usd')
    _require(_sha(embedded/'asset.usd') == asset_sha, 'Producer and embedded asset SHA differ')
    summaries, report_hashes = _read_reports(paths, scene_sha, asset_sha)
    packages = (package, embedded)
    protected = {folder: _immutable_files(folder) for folder in packages}
    _require(protected[package] == protected[embedded],
             'Producer and embedded immutable asset/source/MDL/static/Blender evidence differ')
    manifests, old_hashes, audits = {}, {}, {}
    for folder in packages:
        old_hashes[folder] = _sha(folder/'evidence/manifest.json')
        manifests[folder], audits[folder] = _audit_bundle(folder)
    base = _base_manifest(manifests[package])
    _require(_base_manifest(manifests[embedded]) == base,
             'Producer and embedded base metadata differ')
    archives = {f'evidence/runtime/fehling_r7_cold_{i}.json': _encoded(report)
                for i, report in enumerate(summaries, 1)}
    promoted = copy.deepcopy(base)
    promoted.update(
        overall_status='pass', qualification_scope=SCOPE, runtime_version='4.5.0',
        runtime_evidence=list(archives),
        runtime_evidence_sha256={name: sha256(raw).hexdigest() for name, raw in archives.items()},
        runtime_qualification=dict(
            scene_sha256=scene_sha, scene_package_id=summaries[0]['package_id'],
            tube_asset_sha256=asset_sha, process_ids=[r['process_id'] for r in summaries],
            original_report_sha256=[r['original_report_sha256'] for r in summaries],
            embedded_package=f'deps/{PACKAGE_ID}',
            local_mdl_sha256=audits[package]['local_mdl_sha256'],
        ),
    )
    promoted['claims'].update(runtime_qualified=True, robot_qualified=False,
                              heat_qualified=False, pbd_qualified=False)
    for folder in packages:
        if manifests[folder]['overall_status'] == 'pass':
            _require(manifests[folder] == promoted, 'Different existing runtime qualification; refusing replacement')
        # Preflight EVERY destination before creating even the first archive.
        runtime = folder/'evidence/runtime'
        _require(not runtime.exists() or runtime.is_dir(), f'Runtime archive is not a directory: {runtime}')
        for name, raw in archives.items():
            target = folder/name
            _require(not target.exists() or (target.is_file() and target.read_bytes() == raw),
                     f'Conflicting archived report: {target}')

    def unchanged():
        _require(_sha(scene) == scene_sha, 'Scene changed during promotion')
        _require(all(_sha(path) == digest for path, digest in report_hashes.items()),
                 'Original runtime report changed during promotion')
        for folder in packages:
            _require(_immutable_files(folder) == protected[folder],
                     f'Asset/source/MDL/static evidence changed during promotion: {folder}')

    unchanged()
    _require(all(_sha(folder/'evidence/manifest.json') == old_hashes[folder] for folder in packages),
             'Manifest changed concurrently during preflight')
    # Archives first in BOTH copies. A manifest can never name missing summaries.
    for folder in packages:
        for name, raw in archives.items():
            _archive(folder/name, raw)
    unchanged()
    payload = _encoded(promoted)
    for folder in packages:
        target = folder/'evidence/manifest.json'
        _require(_sha(target) == old_hashes[folder], 'Manifest changed concurrently during publication')
        if target.read_bytes() != payload:
            _atomic_manifest(target, payload)
    unchanged()
    for folder in packages:
        _require((folder/'evidence/manifest.json').read_bytes() == payload, 'Manifest synchronization failed')
        for name, raw in archives.items():
            _require((folder/name).read_bytes() == raw, 'Runtime archive synchronization failed')
    return dict(status='pass', qualification_scope=SCOPE, asset_sha256=asset_sha,
                scene_sha256=scene_sha, process_ids=[r['process_id'] for r in summaries],
                manifests=[str(folder/'evidence/manifest.json') for folder in packages],
                runtime_evidence=list(archives))


def main(argv=None):
    """CLI for main to invoke only after all three completed cold-start passes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--scene', type=Path, required=True)
    parser.add_argument('--report', type=Path, action='append', required=True)
    args = parser.parse_args(argv)
    try:
        result = promote(args.package, args.scene, args.report)
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        parser.exit(1, f'Promotion failed: {exc}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
