"""Frozen-baseline preservation and actual-rate contract for Task10's 120 Hz lane."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('task10_120_producer', Path(__file__).parents[1] / 'scripts/task10_pbd_producer.py')
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


@pytest.fixture
def frozen_baseline(tmp_path):
    baseline = tmp_path / 'frozen'
    (baseline / 'package').mkdir(parents=True)
    # Byte preservation, including a collision marker and material dependency,
    # verifies that the derivation never regenerates the historical geometry.
    (baseline / 'package/pbd.usda').write_text('#usda 1.0\n# final convex OutletCollar plus analytic OutletFluxCap\n')
    (baseline / 'package/clear_water.mdl').write_bytes(b'original transparent water bytes')
    np.savez(baseline / 'initial_particles.npz', source=np.array([[1., 2., 3.]], dtype=np.float32),
             source_velocities=np.array([[.01, -.02, .03]], dtype=np.float32))
    manifest = {'source_sha256': 'source-hash', 'physics_configuration_sha256': 'collision-hash',
                'status': 'qualified', 'runtime_qualification': {'isaac41': 'pass', 'isaac45': 'pass'},
                'runtime_contract': {'physics_dt': 1/240, 'scene_min_position_iterations': 64,
                                     'scene_max_position_iterations': 64},
                'initial_state': {'kind': 'measured_physics_settled'},
                'producer_settling_observation': {'runtime': 'isaac45', 'all_passed': True}}
    (baseline / 'manifest.json').write_text(json.dumps(manifest))
    hashes = {str(p.relative_to(baseline)): producer.sha(p) for p in baseline.rglob('*') if p.is_file()}
    (baseline / 'snapshot_hashes.json').write_text(json.dumps(hashes))
    return baseline


def test_120_derivation_preserves_frozen_assets_and_measured_velocity(frozen_baseline, tmp_path):
    out = tmp_path / 'candidate'
    before = producer.sha(frozen_baseline / 'snapshot_hashes.json')
    manifest = producer.derive_runtime_candidate(frozen_baseline, out, physics_hz=120)
    for path in ['package/pbd.usda', 'package/clear_water.mdl', 'initial_particles.npz']:
        assert (out / path).read_bytes() == (frozen_baseline / path).read_bytes()
    assert producer.sha(frozen_baseline / 'snapshot_hashes.json') == before
    assert manifest['runtime_contract']['physics_dt'] == 1/120
    assert manifest['runtime_contract']['scene_time_steps_per_second'] == 120
    assert manifest['runtime_contract']['scene_min_position_iterations'] == 64
    assert manifest['runtime_contract']['scene_max_position_iterations'] == 64
    assert manifest['runtime_qualification'] == {'isaac41': 'not_run', 'isaac45': 'not_run'}
    assert 'producer_settling_observation' not in manifest
    assert manifest['initial_state']['kind'] == 'frozen_baseline_seed_re_equilibration_required'
    hashes = json.loads((out / 'snapshot_hashes.json').read_text())
    assert all(producer.sha(out / path) == digest for path, digest in hashes.items())


def test_changed_rate_cannot_reuse_runtime_signature(frozen_baseline, tmp_path):
    at120 = producer.derive_runtime_candidate(frozen_baseline, tmp_path / 'a', physics_hz=120)
    at240 = producer.derive_runtime_candidate(frozen_baseline, tmp_path / 'b', physics_hz=240)
    assert at120['runtime_configuration_sha256'] != at240['runtime_configuration_sha256']


def test_corrupt_frozen_collision_rejected_before_output(frozen_baseline, tmp_path):
    (frozen_baseline / 'package/pbd.usda').write_text('wrong old collider')
    with pytest.raises(ValueError, match='hash mismatch'):
        producer.derive_runtime_candidate(frozen_baseline, tmp_path / 'bad', physics_hz=120)
    assert not (tmp_path / 'bad').exists()


@pytest.mark.parametrize('rate', [0, -120, 120.5, float('nan'), True])
def test_invalid_rate_rejected_before_asset_writes(tmp_path, rate):
    with pytest.raises(ValueError, match='positive integer'):
        producer.build(tmp_path / 'missing.usd', tmp_path / 'bad', physics_hz=rate)
    assert not (tmp_path / 'bad').exists()


def actual_clock_report():
    return {'actual_step_dt_evidence': {'source': 'native_physics_step_callback',
             'count': 120, 'min_s': 1/120, 'max_s': 1/120, 'sum_s': 1.,
             'target_s': 1/120, 'world_physics_dt_s': 1/120,
             'scene_time_steps_per_second': 120}}


def test_120_settling_requires_observed_native_world_and_scene_agreement():
    producer.validate_actual_step_dt(actual_clock_report(), 1/120)
    with pytest.raises(ValueError, match='native'):
        producer.validate_actual_step_dt({'physics_dt': 1/120}, 1/120)


@pytest.mark.parametrize('field,value', [('min_s', 1/240), ('max_s', 1/60),
    ('sum_s', .5), ('count', 0), ('world_physics_dt_s', 1/240),
    ('scene_time_steps_per_second', 240), ('target_s', 1/240)])
def test_nominal_120_cannot_hide_mixed_or_inconsistent_native_clock(field, value):
    report = actual_clock_report()
    report['actual_step_dt_evidence'][field] = value
    with pytest.raises(ValueError, match='native'):
        producer.validate_actual_step_dt(report, 1/120)


def test_explicit_120_profile_changes_only_requested_system_scalars(frozen_baseline, tmp_path):
    from pxr import Usd, Sdf
    stage = Usd.Stage.CreateInMemory()
    path = '/World/Task10Fluid/SourceSystem'
    prim = stage.DefinePrim(path, 'PhysxParticleSystem')
    prim.CreateAttribute('fluidRestOffset', Sdf.ValueTypeNames.Float).Set(.000845)
    prim.CreateAttribute('maxVelocity', Sdf.ValueTypeNames.Float).Set(.2)
    stage.GetRootLayer().Export(str(frozen_baseline / 'package/pbd.usda'))
    manifest = json.loads((frozen_baseline / 'manifest.json').read_text())
    manifest['systems'] = {'Source': {'system_path': path}}
    manifest['particle_system_parameters'] = {'Source': {'fluidRestOffset': .000845, 'maxVelocity': .2}}
    (frozen_baseline / 'manifest.json').write_text(json.dumps(manifest))
    hashes = {str(p.relative_to(frozen_baseline)): producer.sha(p) for p in frozen_baseline.rglob('*')
              if p.is_file() and p.name != 'snapshot_hashes.json'}
    (frozen_baseline / 'snapshot_hashes.json').write_text(json.dumps(hashes))
    old_pbd = (frozen_baseline / 'package/pbd.usda').read_bytes()
    out = tmp_path / 'adjusted'
    result = producer.derive_runtime_candidate(frozen_baseline, out, physics_hz=120,
                                               system_overrides={'Source': {'fluidRestOffset': .00088}})
    # Keep the stage alive when obtaining its prim.
    changed_stage = Usd.Stage.Open(str(out / 'package/pbd.usda'))
    authored = changed_stage.GetPrimAtPath(path)
    assert authored.GetAttribute('fluidRestOffset').Get() == pytest.approx(.00088)
    assert authored.GetAttribute('maxVelocity').Get() == pytest.approx(.2)
    assert (out / 'initial_particles.npz').read_bytes() == (frozen_baseline / 'initial_particles.npz').read_bytes()
    assert (frozen_baseline / 'package/pbd.usda').read_bytes() == old_pbd
    assert result['physics_configuration_sha256'] != manifest['physics_configuration_sha256']


@pytest.mark.parametrize('overrides', [{'Source': {'maxVelocity': 0}},
    {'Falling': {'fluidRestOffset': -1}}, {'Source': {'physics:kinematicEnabled': True}}])
def test_profile_overrides_cannot_freeze_or_change_unrelated_properties(frozen_baseline, tmp_path, overrides):
    with pytest.raises(ValueError, match='override'):
        producer.derive_runtime_candidate(frozen_baseline, tmp_path / 'invalid', physics_hz=120,
                                           system_overrides=overrides)
    assert not (tmp_path / 'invalid').exists()


def test_native_120_certificate_rejects_transient_escape_even_when_tail_recovers():
    summary = {'max_outside_count': 1, 'tail_max_outside_count': 0,
               'tail_height_error_range_m': [-.0002, .0003]}
    with pytest.raises(ValueError, match='containment'):
        producer.validate_settled_summary(summary, .002, require_full_containment=True)
    # Existing 240 certificates retain their historical tail-only import scope.
    producer.validate_settled_summary(summary, .002, require_full_containment=False)
