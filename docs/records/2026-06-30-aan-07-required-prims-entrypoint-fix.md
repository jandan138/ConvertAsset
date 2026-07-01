# 2026-06-30 AAN-07 Required Prims Entrypoint Fix

## Context

EBench-01 retained evidence over the real DryingBox AAN package initially
blocked with:

```text
blocked_manifest_entrypoint_mismatch
AAN manifest entrypoints.required_prims is missing
```

The package contained `task/required_prims.yaml`, but the AAN manifest did not
declare it under `entrypoints`. Downstream consumers should not infer or patch
this path.

## Decision / Change

`convert_asset/asset_application_normalizer/evidence_manifest.py` now writes:

```json
"required_prims": "task/required_prims.yaml"
```

inside manifest `entrypoints`.

The AAN-07 CLI test now asserts all three task handoff entrypoints:

```text
task/task_config.yaml
task/required_prims.yaml
task/evaluator.yaml
```

## Files Touched

```text
convert_asset/asset_application_normalizer/evidence_manifest.py
tests/test_asset_application_normalizer_cli.py
docs/design/asset-application-normalizer.md
docs/records/2026-06-30-aan-07-benchmark-contract.md
docs/records/evidence/2026-06-30-aan-07-dryingbox-benchmark-contract/overlay_level1_poc_dryingbox_01_benchmark.json
```

## Validation

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py::test_normalize_asset_benchmark_gate_writes_ebench_task_contract -q
```

Result:

```text
1 passed
```

Focused AAN CLI regression:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
```

Result:

```text
21 passed
```

The real DryingBox package was regenerated at:

```text
/tmp/aan07_real_packages/overlay_level1_poc_dryingbox_01_benchmark_ebench01_rerun
```

Its manifest entrypoints now include `required_prims`.

## Known Limitations

This fix only repairs the task handoff manifest declaration. It does not claim
real EBench runtime execution, score eligibility, official benchmark
reproduction, or full material/physics parity.

## Next Actions

Use the regenerated real package as the input for EOS EBench-01 retained
evidence.
