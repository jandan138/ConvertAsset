# Centrifuge r9 benchtop stability repair

Date: 2026-07-30

## Context and investigation

The identity-root r8 package passed its five isolated articulation gates, but
the eBench/GenManip scene preview showed the centrifuge tipping onto its side
during a 50-frame zero-action warmup. The package root and all r7-to-r8 visual
world transforms were correct.

The composed r8 geometry identified the producer-side defect:

- the `group_0` parent carries approximately `0.175` world scale;
- the inherited `housing` Cube retained its parent-local scale instead of
  compensating for that parent scale;
- its composed support AABB was only about `0.04375 x 0.10192 m`;
- the explicit mass bundle places the combined COM projection at approximately
  `(0.011256, 0.0) m`, about `4.9 mm` outside the housing's positive-X edge.

The local USD scale is therefore not accepted as support evidence. The r9
builder measures composed world bounds. Six visual foot/contact meshes within
`2 mm` of the support plane span approximately `0.243731 x 0.327137 m`, which
is consistent with the visible base instead of the undersized inherited
collider.

## Design decisions

`scripts/build_centrifuge_identity_root_facade_r9.py` adds a stronger facade
overlay containing one `size=1`, render-invisible collision Cube on the
existing `group_0` rigid body. Its XY footprint is the composed-world convex
AABB of the six low visual contact meshes, extended only if needed to preserve
a `10 mm` target band around the mass-weighted COM projection. The hard
admission minimum is `5 mm`.

The overlay does not edit the raw source or lower-level `asset.usd`. It verifies
that:

- `/World/Centrifuge` remains identity;
- every pre-existing Xformable keeps the same composed world matrix;
- all authored `drive:*` values remain identical;
- the complete physics `scope_rules`, including mass, COM, inertia and
  principal axes, remain identical;
- the new collider's composed world AABB and COM margins match the generated
  measurement.

`scripts/build_centrifuge_device_profile_r9.py` carries forward the protected
r8 joint semantics and five interaction frames, binds them to the r9 source,
and adds an authoritative root-local `support` frame. It also adds
`benchtop_stability` to `required_runtime_task_gates`.

`scripts/qualify_articulated_benchtop_stability.py` runs the package's actual
fixed-base consumer protocol in a short-lived Isaac 4.1 worker:

1. verify the enabled fixed joint and articulation root without changing them;
2. author a session-only static table flush with the authoritative support
   frame;
3. reset every DOF to the profile value, including the open lid;
4. execute 50 zero-action warmup frames;
5. execute 240 settle frames;
6. reject root rotation above `1 degree`, root translation above `1 mm`,
   support gap or penetration above `1 mm`, extent drift above `5%`, source
   mutation, or an asset-scoped PhysX error.

The centrifuge is intentionally a fixed-base benchtop device. It is not
qualified as a freely movable rigid object. During review, a session-only
free-release experiment was attempted and rejected: removing the package fixed
joint changes the physics representation, while moving the articulation root
onto the source-scaled (`0.175`) base body is not transform-equivalent in Isaac
4.1. Those rejected observations remain diagnostic evidence and are not used
for admission. The accepted gate preserves the exact package semantics that
Scenario Forge consumes.

The public process captures worker stderr and merges the resulting
`benchtop_stability` gate into the existing
`aan.articulation_runtime_qualification.v1` report. The merged report is the
input to `finalize_articulated_package.py`; the stability result is not an
unbound sidecar.

The original five-gate physical-contact harness is now producer-owned at
`scripts/qualify_centrifuge_task_interactions.py`. Its tube sweep, pair-filtered
button contact, hinge-centered lid contact, reset-band, joint-travel,
drive-integrity and source-integrity semantics were migrated intact. The
migrated harness additionally requires all five gate names in the r9 profile
and binds its newly executed report to the exact r9 profile SHA, source SHA,
prequalification manifest SHA and before/after package USD SHA. It cannot turn
an old r8 report into r9 evidence by rewriting hashes. The r9 `support` frame
and sixth required gate are accepted but appended only by the subsequent
benchtop qualifier.

## Code and tests

New implementation:

- `scripts/build_centrifuge_identity_root_facade_r9.py`
- `scripts/build_centrifuge_device_profile_r9.py`
- `scripts/qualify_articulated_benchtop_stability.py`
- `scripts/qualify_centrifuge_task_interactions.py`

New tests:

- `tests/test_centrifuge_r9_facade.py`
- `tests/test_centrifuge_r9_device_profile.py`
- `tests/test_centrifuge_r9_benchtop_stability.py`
- `tests/test_qualify_centrifuge_task_interactions.py`

TDD red phase:

```text
./scripts/isaac_python.sh -m pytest -q \
  tests/test_centrifuge_r9_facade.py \
  tests/test_centrifuge_r9_device_profile.py \
  tests/test_centrifuge_r9_benchtop_stability.py

3 collection errors: the three producer scripts did not yet exist.
```

The five-gate migration was likewise test-first: its new test module initially
failed collection because the ConvertAsset-owned qualifier did not yet exist.

Green phase, including the existing articulated finalizer tests:

```text
39 passed in 0.46s
ruff: all checks passed
py_compile: pass
```

The facade builder was also run against the real r8 source-bound facade and
physics profile in a temporary output directory. It passed with:

- new support world AABB:
  `[-0.1473523, -0.1602253, 0.0] .. [0.0963790, 0.1669120, 0.008] m`;
- combined COM:
  `[0.0112560, 0.0, 0.103633] m`;
- minimum XY COM margin: `0.085123 m`;
- maximum existing world-transform error: `0.0`;
- entry identity, drive integrity and physics-scope integrity: pass.

## Producer handoff

Generate the facade:

```bash
./scripts/isaac_python.sh scripts/build_centrifuge_identity_root_facade_r9.py \
  --out-root outputs/centrifuge_identity_root_r9
```

Normalize the generated facade with its rebound physics profile using the same
articulated AAN route as r8. Then build the r9 device profile:

```bash
./scripts/isaac_python.sh scripts/build_centrifuge_device_profile_r9.py
```

Run a fresh five-gate centrifuge contact qualification with the r9 package and
r9 profile:

```bash
./scripts/isaac_python.sh scripts/qualify_centrifuge_task_interactions.py \
  --centrifuge-package outputs/centrifuge_identity_root_r9/package \
  --centrifuge-manifest \
    outputs/centrifuge_identity_root_r9/package.manifest.json \
  --tube-package \
    outputs/tube_task_assets_20260729/uniform_scale_k0365/test_tube/package \
  --tube-manifest \
    outputs/tube_task_assets_20260729/uniform_scale_k0365/test_tube/package.manifest.json \
  --device-profile \
    outputs/centrifuge_identity_root_r9/centrifuge.articulated_device_profile_r5_identity_root_benchtop.json \
  --out-dir /path/to/r9-five-gate-evidence
```

Feed that newly generated base report to the benchtop qualifier:

```bash
./scripts/isaac_python.sh scripts/qualify_articulated_benchtop_stability.py \
  --package outputs/centrifuge_identity_root_r9/package \
  --manifest outputs/centrifuge_identity_root_r9/package.manifest.json \
  --device-profile \
    outputs/centrifuge_identity_root_r9/centrifuge.articulated_device_profile_r5_identity_root_benchtop.json \
  --base-runtime-report /path/to/five-gate-report.json \
  --out-report /path/to/final-six-gate-report.json \
  --out-observation /path/to/benchtop-observation.json \
  --stderr-log /path/to/benchtop-stderr.log
```

Only the final six-gate report should be passed to
`finalize_articulated_package.py`.

## Final qualification

The exact r9 package was qualified in Isaac Sim 4.1 and promoted:

- facade/source SHA-256:
  `ed3c5e2c8d3cbb32fc1ee6438a5396cf71ff113b5b2ad1dcefa9f8b13f833b2e`;
- package USD SHA-256:
  `3573bb0eb474b80f842ea4d70dd2be2c2b5019a181d604bc1e17d4c7b7754926`;
- device profile SHA-256:
  `b55918913df6013e31fbc4b2534c5d0f7b1a804b7d7ee5d7a122c5e31b8238cb`;
- five-gate base report SHA-256:
  `f3261774f92af7e302d74d26380c6e8f05028c533e47af476b28bb76eff57020`;
- final six-gate report SHA-256:
  `919c47df33db1881d56a4087645c1dbb8e17949442144b38e77678c7288c038f`;
- final manifest SHA-256:
  `9cd6f2c0f84dc0fe952b96359aba86f5568a20b001fe8fd44ba9178f9ef14281`.

All six gates passed. The mounted observation recorded zero root translation,
zero root tilt, zero support gap, zero support drift, zero warmup-to-final
extent drift, and zero asset-scoped PhysX errors. Package `asset.usd`, joint
drives, colliders, mass/inertia values, and the fixed-base contract were not
changed by qualification or promotion.

The claim remains limited to the recorded fixed-base device and interaction
protocols. It does not claim robot policy success, benchmark success, freely
movable whole-device physics, or real-world physical calibration. No eBench
consumer collider, scale, mass/inertia, or warning-suppression patch is
permitted.
