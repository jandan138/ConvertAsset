# 2026-07-31 AAN Qualified Consumer Mounting Contract

## Problem

The centrifuge r9 package passed its existing articulated interaction gates, but
the consumer-facing contract did not state how to place the runtime
articulation root on a support plane. The authored entry prim is identity, while
Isaac reports the articulation root at a rotated runtime pose. Treating identity
as a ready-to-place pose therefore put the centrifuge on its side and displaced
it from the workbench.

The existing authoritative `named_frames.support` frame was not enough to solve
this. It is authored relative to `/World/Centrifuge`, whereas the runtime
articulation-root pose used for mounting has:

- position `[0, 0, 0.10363300144672394]` m;
- orientation `[0.5, 0.5, 0.5, 0.5]` in `wxyz` order;
- support offset `[0, -0.10363300144672394, 0]` m in that runtime-root-pose
  frame.

Conflating the two frames would leave the support plane approximately 10.36 cm
away from the intended base.

## Contract

`aan.articulated_mounting.v1` is now an optional section of an articulated
device profile. It is required exactly when the profile requires the
`benchtop_stability` runtime gate. The profile section is a qualification
candidate and deliberately has no `status`.

It records:

- fixed-base motion mode and the asset entry prim;
- explicit Z-up, metre, and `wxyz` coordinate semantics;
- the support frame relative to the runtime articulation-root pose;
- the support-plane-to-root mount pose at yaw zero;
- the complete initial DOF reset vector;
- warm-up and settled world-axis-aligned extents measured at that pose.

A consumer must not infer this information from the entry prim, an authored
support frame, or an asset bounding box. An application may add its chosen yaw
around the support-plane normal after applying the qualified yaw-zero mount
pose.

The contract is promoted only after independent runtime verification:

- the qualification report exposes the same mapping as
  `qualified_consumer_placement`, plus `status: pass`, the profile SHA-256, and
  the source SHA-256;
- the final manifest exposes it only at
  `articulation_contract.mounting`, plus `status: pass`, the profile SHA-256,
  runtime-report SHA-256, and source SHA-256.

The finalizer rejects a profile/report/manifest mismatch. Profiles that do not
require `benchtop_stability` continue to finalize without a mounting section,
which preserves the legacy articulated-package ABI.

## Evidence Lifecycle

The evidence was produced in an explicit bootstrap and requalification
sequence:

1. The prior source-bound profile was used only to run a candidate measurement
   worker. It was not relabelled as qualified mounting evidence.
2. Two local Isaac Sim 4.5 candidate observations were identified as the wrong
   runtime and retained only as rejected diagnostics.
3. The worker was changed to read the actual Kit version and block unless the
   observed fingerprint is `4.1.*`. Both the five-interaction-gate worker and
   the benchtop worker now retain that runtime gate in their reports.
   A post-fix negative run in local Isaac Sim 4.5 is retained at
   `outputs/centrifuge_identity_root_r9/evidence/mounting_candidate_rejected_isaac45_runtime_gate_v2.json`
   (SHA-256
   `29ba17199411d91b9df85283bc25644c7b61a6ea4ca4f48af69103f1d4dd1a2b`);
   it records `observed_kit_version: 4.5.0` and `status: blocked`.
4. A fresh candidate observation was captured in the EOS Isaac Sim 4.1
   environment and bound exactly to the old profile, package manifest, and
   unchanged source/asset hashes.
5. The r7 profile was built from that observation without a passing status.
6. A fresh normalized package was qualified through all five interaction gates
   and then through `benchtop_stability` in Isaac Sim 4.1.
7. Only that fresh passing report was accepted by the finalizer and copied into
   the promoted package.

No old report was rehashed or promoted as new evidence.
The earlier `a1308609...` manifest chain did not retain a measured qualifier
runtime fingerprint and is superseded. The two Isaac Sim 4.5 candidates and one
failed import candidate remain as rejected diagnostics rather than being
deleted or relabelled.

## Result

The promoted package is:

```text
outputs/centrifuge_identity_root_r9_mount_contract_v2/package
```

Its external final manifest is:

```text
outputs/centrifuge_identity_root_r9_mount_contract_v2/package.manifest.json
```

Important immutable hashes are:

- `asset.usd`:
  `3573bb0eb474b80f842ea4d70dd2be2c2b5019a181d604bc1e17d4c7b7754926`;
- source:
  `ed3c5e2c8d3cbb32fc1ee6438a5396cf71ff113b5b2ad1dcefa9f8b13f833b2e`;
- r7 device profile:
  `f081ccfb42b412945b475f171cdcefedcba783e62abdf4d2373879abcb313558`;
- runtime qualification report:
  `bdcca713b8539f270c50a8005cafa93ca3ec2de0babd06cca95c296c6156f0cd`;
- final manifest:
  `764321fbce11615713bb6af229ee2a6a56cd80d948446d0c2359b09733ef2807`.

All five prior articulated interaction gates and the new benchtop gate passed.
Both runtime gates observed
`4.1.0-rc.7+4.1.14801.71533b68.gl`.
The mounting-vector, root-pose, support-offset, and reset-extent comparisons had
zero error. The largest reset-state difference was the warm-up lid position at
`6.6267305764977635e-06` rad, below the declared `1e-3` rad tolerance. The
package `asset.usd` hash remained unchanged.

## Implementation And Validation

The r9 profile builder now consumes a hash-bound runtime candidate observation.
The benchtop worker records the actual runtime root pose, support offset, reset
positions, and extents; the evaluator compares those values to the profile and
emits qualified placement only on a passing result. The articulated finalizer
validates and binds the promoted mounting contract.

Candidate evidence must match the exact current manifest hash. A non-zero
worker exit blocks promotion even if a partial pass observation exists.
Qualifier and finalizer use one pure mounting validator, including one shared
unit-quaternion and reset-value rule; the builder canonicalizes accepted
floating-point reset measurements back to the profile's semantic reset values.

Focused validation covers candidate provenance, malformed and mismatched
mounting contracts, failed benchtop evidence, hash binding, final-manifest
promotion, and legacy packages without the benchtop requirement.

## Claim Boundary

This proves only the specified fixed-base mount and reset/settle protocol in the
recorded Isaac Sim 4.1 environment, in addition to the already declared
articulated interaction gates. It does not prove robot-policy success, task or
benchmark success, freely movable rigid-body behaviour, real-world physical
calibration, or arbitrary placement beyond the published coordinate semantics.
No USD, collider, mass/inertia, joint, drive, tube/rack scale, or GenManip code
was changed.
