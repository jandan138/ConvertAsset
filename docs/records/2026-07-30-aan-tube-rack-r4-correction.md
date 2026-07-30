# Tube-rack r4 collider correction and insertion qualification

Date: 2026-07-30

## Scope

This change corrects the source-bound tube-rack compound-collider facade and
adds a fail-closed, cross-package qualification for a real dynamic tube
entering one rack socket. It does not edit the original `asset.usd`, relax any
physics threshold, or claim robot-policy/benchmark success.

## Audit findings

The delivered r3 rack facade had three independent evidence problems:

1. It defined ten `UsdGeomCube` collision proxies, while its provenance claimed
   eleven.
2. Its `xformOp:scale` values represented the intended full proxy dimensions,
   but no `size` was authored. A USD Cube defaults to `size = 2`, so each
   composed collider was twice the intended size on every axis.
3. The collision proxies were render-visible.

The earlier tube-insertion evidence also did not prove a physical insertion. It
did not bind both package manifests and entry prims, did not require
pair-filtered bottom contact, and repeatedly authored the tube translation
during the rollout. That protocol could place a tube through geometry instead
of demonstrating a dynamic insertion.

The generic interaction runtime qualifier had separately regressed around
optional probes. A non-required `open_top` probe could still block the package.
The correction restores required-probe selection while retaining the original
10 mm stable-support tolerance:

```text
SUPPORT_HEIGHT_TOLERANCE_M = 0.01
```

No tolerance was widened.

## Implemented correction

### r4 facade and profile builder

`scripts/build_tube_rack_r4_facade.py` consumes the audited r3 facade and its
provenance plus the audited r3 interaction and physics JSON profiles. It
verifies the facade/provenance SHA-256 binding, exact ten-proxy ABI, the two
approved r3 schema/profile/revision identities, and that both profile
`source_binding.sha256` values equal the predecessor facade SHA-256. It then
creates a new stronger overlay. It:

- explicitly authors `double size = 1`;
- preserves the measured transform scale as the true full dimensions;
- authors `visibility = "invisible"` for every collision proxy;
- requires the corrected aggregate proxy minimum Z to be exactly the support
  plane, within `1e-9` m;
- records ten, and only ten, proxy names in the corrected provenance;
- records predecessor hashes and corrected aggregate bounds; and
- refuses to replace any existing facade, provenance, interaction, or physics
  output.

A local build against the delivered r3 inputs produced a ten-proxy overlay
whose composed aggregate bounds were:

```text
min = (-0.04015, -0.014024, 0.0) m
max = ( 0.04015,  0.013420, 0.0345) m
```

An independent `pxr` composition check confirmed `size = 1`, invisible
proxies, and the preserved full-dimension scales.

The same build deterministically emits strict JSON r4 profiles. The physics
profile changes only:

```text
profile_id
revision
source_binding.sha256
```

The interaction profile changes those three identity fields and one
authoritative frame:

```text
named_frames.socket_0_inserted_bottom.translation_body_local_usd
  r3: (-0.0100375, -0.0064240, 0.0098215) m
  r4: (-0.0100375, -0.0064240, 0.0035000) m
```

The r4 value is not a hand-tuned task pose. The builder derives it from the top
face of the corrected `socket_0_bottom` Cube: center Z `0.0025` m plus half of
its `0.002` m full height. An Isaac rollout with the r3 frame exposed that its
claimed inserted-bottom point was about `6.32` mm above the physical contact
plane. All stage metrics, raw-source binding, mass, inertia, center of mass,
other named frames, collider paths/purposes, runtime gates, and evidence claim
boundaries remain item-for-item equal.

The canonical r4 identities are:

```text
interaction profile_id  blenderkit.tube_rack.uniform_scale_k0365.interaction.r4
interaction revision    r4
physics profile_id      blenderkit.tube_rack.uniform_scale_k0365.provisional.r4-compound-proxy-cube-size-correction
physics revision        r4-compound-proxy-cube-size-correction
```

The final real-input build against the delivered r3 files produced:

```text
r4 facade SHA-256       f7672d7914164762ca788192680561a84e6062f9418eed711f72e889ad9d2cc9
r4 interaction SHA-256  365c33c0bfcf71355f50f440a587e4bd4a57d11ddd23b22a375f53b9ca2d069c
r4 physics SHA-256      f89bb8b87df5d78344bca8a75fef2141eb1c10478ada78c0b87be184b080d494
```

A recursive semantic diff of the physics profile reported exactly the three
identity paths above. The interaction profile reported those paths plus the
single measured inserted-bottom frame correction.

### Dynamic insertion qualifier

`scripts/qualify_tube_rack_insertion.py` implements report schema
`aan.tube_rack_insertion_qualification.v2`. Before starting Isaac Sim it
validates and hash-binds, for both rack and tube:

- the external and package-local manifests;
- package status and entry prim;
- the current `asset.usd` through the interaction closure;
- exactly one active rigid body at the declared entry prim; and
- authoritative named frames whose parent is the asset entry prim.

The rack contract must additionally bind one socket-bottom proxy and at least
one socket-side proxy.

The runtime composes the two exact entry prims into a fresh stage, uses the rack
as a session-only kinematic fixture, and keeps the tube dynamic. It authors one
initial tube pose and records zero per-frame translation updates. Gravity and
contact advance the tube after that point. The qualification protocol uses a
`0.001` second physics step because the bottom proxy is only `0.002` m high;
the earlier `0.01` second step allowed the dynamic tube to tunnel through that
thin collider. This is a producer qualification setting, not a downstream
benchmark-runtime override.

The report records dynamic travel, axis alignment, authoritative bottom-frame
axial error and lateral offset, pair-filtered bottom and side contacts, both
raw and force-bearing deepest contacts, runtime identity, and before/after
source hashes. A raw contact-buffer entry with zero normal force remains a
diagnostic and is not counted as an active physical contact. It fails closed
unless all of the following hold:

- observed insertion travel is at least 90% of expected travel;
- tube-axis error is at most 10 degrees;
- the final 12-sample stable bottom-contact window is observed;
- maximum side-proxy penetration in that settled window is at most 1 mm;
- at least one pair-filtered socket-bottom contact is observed;
- final support is within 2 mm axially of the authoritative bottom plane;
- no nested rigid body, kinematic tube, per-frame authored translation, missing
  observation, or source mutation is present.

The qualifier retains the deepest bottom-manifold separation and peak
free-fall impact penetration as diagnostics, but does not apply them to the
settled side-clearance gate. PhysX can report a large negative separation
against the square bottom block while a centered cylinder rests normally on
it, and the gravity-only qualification intentionally produces a harder bottom
impact than the guided robot task. Side clearance is therefore computed
exclusively from force-bearing contacts with the declared side proxies during
the final stable bottom-contact window. Lateral offset is recorded separately
because the tube may settle off the nominal socket center while remaining
inside the declared socket clearance. The 1 mm side threshold is unchanged.

### Task qualification finalizer

`scripts/finalize_interaction_task_qualification.py` accepts only a passing
runtime report whose exact rack/tube manifest hashes, `asset.usd` hashes, and
entry prims match the supplied packages. It also checks the dynamic protocol,
source integrity, all required gates, and authoritative support-frame
contracts.

It then copies the report without rewriting it to:

```text
evidence/task_qualifications/tube_insertion/report.json
```

and appends this consumer-facing top-level manifest binding:

```json
{
  "qualification_id": "tube_insertion",
  "status": "pass",
  "report_path": "evidence/task_qualifications/tube_insertion/report.json",
  "report_sha256": "<lowercase 64-hex SHA-256>"
}
```

The real binding also contains immutable input identities and a narrow claim
boundary. The finalizer writes the external and embedded manifests
byte-identically, emits a promotion receipt, and refuses to replace any prior
promotion or evidence file.

## Negative control on r3

The new qualifier was run against the old r3 rack and delivered test-tube
packages under Isaac Sim 4.5 as a negative control. Composition and source
integrity passed, but the rollout correctly returned `blocked`:

```text
observed travel             0.0030756 m
expected travel             0.0320000 m
axis error                 11.9769 degrees
bottom contact samples      0
side contact samples      240
final bottom-frame error    0.0289539 m
maximum penetration         0.0000058 m
```

This demonstrates that side contact or a visually nearby tube is no longer
misreported as a completed insertion. It is not evidence for r4 and is not an
Isaac Sim 4.1 qualification.

## Verification

The implementation was developed test-first. The focused suite covers facade
geometry/provenance, strict thresholds, package identity, dynamic-protocol
evaluation, immutable report binding, and refusal of mismatched or duplicate
promotion:

```bash
python3 -m pytest -q \
  tests/test_asset_application_normalizer_interaction_runtime_qualification.py \
  tests/test_tube_rack_r4.py \
  tests/test_finalize_interaction_task_qualification.py
```

Result:

```text
32 passed
```

Additional local checks:

```bash
git diff --check
python3 -m py_compile \
  convert_asset/asset_application_normalizer/interaction_runtime_qualification.py \
  scripts/build_tube_rack_r4_facade.py \
  scripts/qualify_tube_rack_insertion.py \
  scripts/finalize_interaction_task_qualification.py \
  tests/test_asset_application_normalizer_interaction_runtime_qualification.py \
  tests/test_tube_rack_r4.py \
  tests/test_finalize_interaction_task_qualification.py
```

Both completed successfully.

The repository-wide suite was also run:

```text
742 passed, 4 skipped, 2 failed
```

Both failures are pre-existing GLB hierarchy tests whose required fixture USDs
are absent from this worktree:

```text
assets/usd/chestofdrawers_nomdl/chestofdrawers_0004/instance_noMDL.usd
assets/usd/chestofdrawers_nomdl/chestofdrawers_0011/instance_noMDL.usd
```

They do not import or exercise the tube-rack correction.

## Completed producer run and handoff

The final source-bound r4 package was generated and qualified with the required
Isaac Sim 4.1 worker. The reproducible sequence was:

```bash
python3 scripts/build_tube_rack_r4_facade.py \
  --predecessor-facade <r3-facade.usda> \
  --predecessor-provenance <r3-facade-provenance.json> \
  --predecessor-interaction <r3-interaction.json> \
  --predecessor-physics <r3-physics.json> \
  --out-facade <new-r4-facade.usda> \
  --out-provenance <new-r4-facade-provenance.json> \
  --out-interaction <new-r4-interaction.json> \
  --out-physics <new-r4-physics.json>
```

After normalizing with those exact generated r4 profiles, run the actual
insertion protocol with the Isaac Sim 4.1 Python:

```bash
<isaac-4.1-python> scripts/qualify_tube_rack_insertion.py \
  --rack-package <r4-rack-package> \
  --rack-manifest <r4-rack-manifest> \
  --tube-package <qualified-tube-package> \
  --tube-manifest <qualified-tube-manifest> \
  --expected-runtime-version 4.1 \
  --out <runtime-report.json>
```

The report passed, so it was bound into the r4 rack package:

```bash
python3 scripts/finalize_interaction_task_qualification.py \
  --rack-package <r4-rack-package> \
  --rack-manifest <r4-rack-manifest> \
  --tube-package <qualified-tube-package> \
  --tube-manifest <qualified-tube-manifest> \
  --runtime-report <runtime-report.json>
```

The exact promoted outputs are:

```text
package
  outputs/tube_task_assets_20260730/uniform_scale_k0365/tube_rack_r4/package
runtime report SHA-256
  8e0d5473abd8ad01a88810f82188ab9dee690828a5a0a3420c8bb7a5ffa4b950
final manifest SHA-256
  cb3cff2b755221887d70af2165c518402e5e71635e9206645f4083a31e689550
```

The Isaac 4.1 qualification observed `38.254` mm of dynamic travel against
`38.322` mm expected, `0.067` mm final bottom-plane axial error, `1.160`
degrees axis error, 78 force-bearing bottom-contact samples, a final stable
12-sample bottom-contact window, and zero settled side penetration. All five
report gates passed. Peak free-fall side impact (`2.743` mm) and the bottom
manifold separation remain visible diagnostics and are not silently removed.

The promotion claim is intentionally narrow: the delivered rack/tube pair
supports the recorded fixed-rack gravity insertion protocol. It does not claim
robot insertion-policy or benchmark success.

The first production normalize attempt exposed one additional facade-authoring
regression before any runtime claim: an overlay that omitted the predecessor's
authored `framesPerSecond = 24` and `timeCodesPerSecond = 60` composed with the
USD defaults and no longer matched the source-bound profile. The builder now
copies both authored rates into the stronger r4 layer and blocks when either
rate is absent or invalid. A regression assertion covers the preserved values;
no profile stage metric was changed to accommodate the bad overlay.
