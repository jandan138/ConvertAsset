# 2026-06-30 AAN-05/06 Physics and Runtime Gates

## Summary

Implemented the next two Asset Application Normalizer gates:

- `AAN-05-physics-static`: static rigid-body, collision, mass/inertia, articulation, joint axis/limit, DOF mapping, and reset-pose evidence.
- `AAN-06-runtime-smoke`: optional Isaac headless subprocess smoke for cold load, render readback, short physics step, and reset.

Static normalization now ends at AAN-05 by default. AAN-06 only runs when the caller requests `--gates static,runtime`.

## Code changes

- Added `convert_asset/asset_application_normalizer/physics_checks.py`.
  - Scopes checks to `required_prim_paths`.
  - Records authored rigid body, collision, mass, inertia, articulation root, and joint values with provenance.
  - Blocks articulated assets when articulation root or joint semantics are missing.
- Added `convert_asset/asset_application_normalizer/runtime_smoke.py`.
  - Runs a new `scripts/isaac_python.sh -m convert_asset.asset_application_normalizer.runtime_smoke --worker ...` process.
  - Captures command contract, stdout/stderr, worker report, and render PNG paths.
  - Writes the worker report before `SimulationApp.close()` so Isaac shutdown cannot drop the report.
  - Waits for non-empty camera RGBA readback instead of sampling only once.
- Extended `evidence_manifest.py` with physics/articulation/static runtime fields and extra command records.
- Updated `pipeline.py` to chain AAN-03 -> AAN-04 -> AAN-05 -> optional AAN-06.
- Updated tests in `tests/test_asset_application_normalizer_cli.py`.

## DryingBox evidence

Evidence directory:

`docs/records/evidence/2026-06-30-aan-05-06-dryingbox-physics-runtime/`

Static DryingBox manifest:

`overlay_level1_poc_dryingbox_01_static.json`

Runtime DryingBox manifest:

`overlay_level1_poc_dryingbox_01_runtime.json`

Runtime artifacts copied for review:

- `runtime_smoke/report.json`
- `runtime_smoke/render.png`
- `runtime_smoke/stdout.log`
- `runtime_smoke/stderr.log`

Observed DryingBox results:

- AAN-03: pass
- AAN-04: pass
- AAN-05: pass
- AAN-06: pass
- Rigid bodies: 4
- Collision prims: 8
- Authored mass records: 4
- Authored inertia records: 4
- Articulation roots: 1
- Physics joints: 4
- Controllable DOFs: 2
- Runtime render: 512 x 512 RGB, `non_background_ratio=0.76338577`, `bbox_ratio=0.84765625`
- Runtime step/reset: finite, `max_abs_delta=0.0`

## Claim boundary

AAN-06 proves this normalized DryingBox package can cold-load, render non-empty pixels, step, and reset in the available Isaac runtime. It does not prove full visual material parity or EBench task readiness. The manifest therefore still forbids:

- EBench task readiness
- exact Isaac Sim 4.1 binary conformance without an explicit runtime environment fingerprint
- binary USD dependency rewrite completeness beyond AAN-03 scope
- full visual material parity beyond recorded source-preservation evidence

Runtime logs still contain MDL compiler warnings for package-local MDL dependencies. The target object is visible in `runtime_smoke/render.png`, but material parity remains a later material/render parity claim, not part of this AAN-06 pass.

## Verification

Commands run:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py -q
python -m pytest tests/test_render_single.py::test_cli_import_does_not_load_runtime_modules tests/test_render_single.py::test_thumbnails_missing_input_returns_before_runtime_imports tests/test_asset_application_normalizer_cli.py::test_asset_application_normalizer_imports_do_not_load_runtime_modules -q
python -m py_compile convert_asset/asset_application_normalizer/*.py
./scripts/isaac_python.sh ./main.py normalize-asset ... --gates static
./scripts/isaac_python.sh ./main.py normalize-asset ... --gates static,runtime
```
