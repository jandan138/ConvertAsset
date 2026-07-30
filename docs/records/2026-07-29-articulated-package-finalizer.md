# 2026-07-29 Articulated Package Finalizer

## Purpose

`scripts/finalize_articulated_package.py` promotes an already-normalized AAN
articulated package after the producer supplies two immutable artifacts:

- an `aan.articulated_device_profile.v1` JSON file;
- a passing `aan.articulation_runtime_qualification.v1` report.

It is intentionally a package finalizer rather than a replacement for AAN's
normalization pipeline. It does not modify `asset.usd`, USD overlays, colliders,
mass properties, joint drives, or reset-state opinions.

## Validation And Promotion

The finalizer checks that the input profile matches the package source hash,
articulation root, static contiguous DOF mapping, reset values, runtime units,
semantic states, and authoritative frames. It also checks that the report:

- is passing and has unchanged package-asset input hashes;
- is bound to the pre-promotion manifest SHA-256;
- records the same runtime DOF indices and joint prims as the static closure;
- accepts duplicate runtime DOF names when indices and joint prims remain unique;
- passes every profile-required task gate without changing drives.

On success it writes the profile and report at their package-relative contract
paths, emits a promotion receipt, and updates the external and embedded
manifests with a hash-bound `aan.articulation_contract.v1`. Every JSON input is
parsed strictly: `NaN`, `Infinity`, and `-Infinity` are rejected.

The finalizer also verifies the complete consumer-facing static closure: scope,
one articulation root, controllable joint records, limits, enablement, reset
values, DOF mapping, and summary counts. This prevents a promotion that later
fails Scenario Forge's handoff loader.

## Usage

```bash
python scripts/finalize_articulated_package.py \
  --package-root /path/to/package \
  --manifest /path/to/package.manifest.json \
  --profile /path/to/device_profile.json \
  --runtime-report /path/to/report.json
```

The command refuses to replace an existing articulation contract or promotion
artifact. Rebuild a fresh package for a changed profile or report.

## Validation

```bash
python -m pytest -q tests/test_finalize_articulated_package.py
python -m ruff check scripts/finalize_articulated_package.py \
  tests/test_finalize_articulated_package.py
python -m pytest -q
```

The focused finalizer suite passed 12 tests. The full ConvertAsset suite also
passed with `709 passed, 4 skipped`; Ruff and `compileall` passed.

Each file is written through atomic replacement. A process crash between file
replacements can still leave an incomplete local promotion, so rebuild a fresh
package rather than attempting to repair a partially promoted package by hand.

The repository-level tests use ABI-compatible synthetic fixtures. Before a real
producer profile is promoted, run the finalizer followed by Scenario Forge's
loader against that resulting package as an integration smoke test.

## Historical Limitation (Resolved 2026-07-30)

The HCI centrifuge contact report passes in Isaac Sim 4.1, but its producer
profile must still supply measured authoritative frame values before finalization.
The finalizer deliberately does not synthesize those values from Scenario Forge
task templates or consumer-side geometry guesses.

The strict, package-identity-bound candidate is stored at:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/tube_task_assets_20260729/
uniform_scale_k0365/centrifuge/package/evidence/
articulated_task_qualification_hybrid_arc_strict_identity_candidate/report.json
```

## Resolution (2026-07-30)

The required producer-owned r3 profile and passing runtime evidence now promote
the corrected package at:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/outputs/tube_task_assets_20260729/centrifuge_proxy_parent_local_r7/package
```

The immutable raw source is represented by an r7 facade that remaps collision
Cube centers into moving-parent local frames while preserving local scales; tube
and rack scale are unchanged. The r3 profile SHA-256 is
`8f53e05548b8681a8332d08c2442f7049d6c360c3e2352c342b4f4ca3961784d`; its lid
contact frame uses the actual Cube local +Z face (`translation + scale / 2`).
The source candidate report SHA-256 is
`10b5c31f856b9258e832487abdbf08f38801cea6fb28d6ab5d7e249bcb1c54bf`, now
packaged at `evidence/articulation_runtime_qualification/report.json`.

Isaac Sim 4.1 passed every profile-required gate. The lid reached
`-0.07981422543525696` rad in the closed band, remained within
`[-1.5556521049, 0.0]`, returned open at `-1.5554765462875366`, had no tube-lid
contact, and preserved drive integrity; `asset.usd` remained
`3573bb0eb474b80f842ea4d70dd2be2c2b5019a181d604bc1e17d4c7b7754926`.

Promotion produced final manifest SHA-256
`7948fff535514227b7e6cce636dc9be63145837bc783802b1f4ce63658233598` and
`evidence/articulation_runtime_qualification/promotion.json`. It does not alter
USD, physics, drives, or colliders. Scenario Forge accepted this final package
through `load_convert_asset_package_handoff(..., usage="articulated_object")`.

Focused finalizer tests passed 12 tests; the Scenario Forge proxy builder,
device-profile, and qualifier suite passed 14; Python `compileall` and
`python -m ruff` passed. These results cover only the stated
collider/contact and articulated-state gates, not robot-policy success,
benchmark performance, real-world parity, or a change to the `k=0.365`
tube/rack scale.
