# 2026-07-14 AAN LabUtopia Vessel Runtime Qualification

## Why this record exists

The earlier [static package record](2026-07-14-aan-labutopia-vessel-static-packages.md)
proved that two LabUtopia vessels could be compiled into package-owned dynamic
objects with one rigid root, explicit mass properties, collision intent, and
authoritative interaction frames. It deliberately stopped before claiming that
the cooked Isaac Sim collider was open at the mouth, stable on a support, moved
with the declared rigid root, or could be contacted from both sides.

This record closes that runtime-only gap for exactly these two source scopes:

| Asset | Source prim | Final interaction profile |
|---|---|---|
| Conical bottle | `/World/conical_bottle03` | `r1`, preserved mesh with SDF collision |
| Graduated cylinder | `/World/graduated_cylinder_03` | `r2`, source mesh collision disabled plus package-owned open-top compound proxy |

The immutable source is
`/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd`.
Its SHA-256 remained
`b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`
before and after both package builds. The runtime work did not modify the
LabUtopia USD.

## Qualification contract

`convert_asset/asset_application_normalizer/interaction_runtime_qualification.py`
runs one isolated Isaac Sim 4.1 worker against an immutable package closure. It
collects four independent measurements and promotes each measurement only to
its corresponding `aan.interaction_contract.v1` field:

| Probe | What is measured | Promoted field | What a pass does not prove |
|---|---|---|---|
| `cooked_aperture` | A cooked PhysX sphere probe enters below the opening without overlap, reaches a sufficiently deep bottom hit, and sees both sidewalls | `open_top.status` and `open_top.evidence` | Liquid simulation, pouring success, or arbitrary object insertion |
| `stable_support` | The object settles on a support aligned to the authoritative support frame; height error, tail speeds, tilt, lateral drift, and scene/rigid pose parity stay within fixed limits | `stable_support_gate` | Long-horizon stability, impact robustness, or calibrated friction |
| `root_motion_parity` | A controlled root pose delta exceeds the declared minimum translation while USD-stage and rigid-view position/orientation agree | `root_motion_gate` | Robot planning, collision-free transport, or policy success |
| `bilateral_gripper_proxy_collision` | Cooked sphere sweeps from both sides of the grasp frame hit the vessel wall without starting inside it | `gripper_collision_gate` | A real robot-finger grasp, contact force, closure, holding, or retention |

The fourth probe is intentionally named a proxy-collision probe. Its pass is not
a robot grasp experiment and must not be reported as one.

The evaluator is fail-closed. Missing, non-finite, shallow, overlapping,
one-sided, unstable, or scene/rigid-divergent observations produce `blocked`.
A failed probe cannot inherit a stale pass from a previous report.

## Evidence binding and digest transition

Interaction evidence is written below the package at
`evidence/interaction_runtime_qualification/report.json`. This directory is
outside the runtime-tree digest, so adding a report cannot change the USD/MDL/
overlay/profile closure that the report qualifies.

The host binds each worker invocation to all of the following before any gate
is promoted:

- a unique `run_id`;
- the exact `asset.usd` SHA-256;
- `closure.runtime_tree_sha256` recomputed from `asset.usd`, `deps/**`,
  `overlays/**`, `interaction/**`, and `physics/**`;
- `binding.prequalification_contract_payload_sha256` from the input
  interaction contract.

The report path stored in every promoted gate is package-relative. Consumers
must reject an absolute path, `..` escape, missing/non-regular file, report hash
mismatch, unsupported report schema, or binding mismatch. The report SHA-256
is repeated in all four promoted evidence records.

`open_top` is part of the canonical interaction payload. Promoting its status
and evidence therefore changes the payload by design. The worker report remains
bound to the prequalification payload digest, while promotion recomputes
`closure.contract_payload_sha256` for the final contract. Each promoted gate
retains the prequalification digest so the transition is auditable.

The external sidecar manifest and
`package/evidence/manifest.json` are written from the same serialized bytes.
They are byte-identical in both retained packages.

Promotion also removes only the static-era forbidden claim whose corresponding
measurement has passed: aperture, root motion, or the joint support-plus-proxy
collision statement. All unrelated restrictions, including provisional
physical parameters and robot/task claims, remain in force.

## Runtime implementation findings

### Conical bottle: SDF requires GPU physics

The first conventional runtime attempt created a CPU physics scene. PhysX
reported that a dynamic rigid actor with an SDF collider is supported only by a
GPU-accelerated scene. Treating the static `physics:approximation = "sdf"`
readback as runtime success would therefore have been incorrect.

The conventional runtime worker now scans the active package scope before its
first reset. If an enabled mesh collider requests SDF, it selects GPU
broadphase and enables GPU dynamics. The interaction-qualification worker also
uses GPU physics for its cooked scene queries. The final conical runtime and
interaction reports both record GPU broadphase/dynamics and pass without a
scoped PhysX mass/inertia warning.

### Graduated cylinder: retained SDF virtual-cap failure

The first cylinder profile (`r1`) preserved the source mesh and requested SDF.
The cooked result behaved like a closed volume rather than an open vessel:

- the entry-center probe overlapped the collider;
- the first axial hit was only about `0.000708 m` below the opening for a
  `0.272294 m` vessel;
- both grasp sweeps started at zero reported distance;
- `cooked_aperture` and `bilateral_gripper_proxy_collision` were blocked, while
  stable support and root-motion parity passed.

That failed attempt is retained, not overwritten, under
`graduated_cylinder_03/runtime_attempts/sdf_virtual_cap/`. Its report SHA-256 is
`af8636a32ec219be967dca0f3a75e7dd664ec5f8c9747e41a1e499c66e865e52`.

The final `r2` profile disables collision on the source mesh and authors a
package-owned open-top compound collider: one bottom Cube and twelve rotated
wall Cubes under `__aan_collision_proxy/`. The proxy is data in the source-bound
profile, not an asset-name branch in the normalizer. The final cooked aperture
probe enters through the center, reaches the bottom at about `0.266294 m`, and
hits the opposite wall proxies from both grasp directions.

### Conventional support fixture and reset

The conventional AAN runtime smoke previously reset a freestanding dynamic
object without first adding a support. Its initial state could already include
gravity-induced motion, making reset drift a fixture artifact rather than an
asset defect.

The worker now authors a session-layer-only ground plane before the first
reset. It uses `__aan_frame_support` when present and falls back to the scoped
world-bounds minimum otherwise. The support plane is runtime evidence, not a
new runtime-tree artifact or a change to the source USD. Both final packages
pass cold load, functional non-empty render readback, 120 physics steps, two
reset cycles, root-hash binding, and the scoped PhysX warning gate. Functional
readback pass is not a human visual-quality pass.

### Isaac 4.1 OmniGlass root substitution

The cylinder source carried a newer `OmniGlass.mdl` root whose helper API did
not compile against the selected Isaac Sim 4.1 helper set. AAN-11 now permits an
explicit-target runtime root substitution when the caller provides that target
MDL root:

- the source `OmniGlass.mdl` bytes are preserved at
  `deps/mdl_source/OmniGlass.mdl`, SHA-256
  `cd7c97781dc95f1694f9acc70c0b9ae327361a3b1c84abf917e55a9d672e627a`;
- the package-visible `deps/mdl/OmniGlass.mdl` uses the selected Isaac 4.1 root,
  SHA-256
  `d71555550deb30af245c0ec939c8647442df5709a2977549cad7f6ddcc8c1182`;
- `material_closure` and `material_runtime_closure.rewrite_actions` record both
  paths, both hashes, the explicit runtime root, and
  `target_runtime_mdl_substitution_not_visual_parity`.

The final cylinder material runtime compiler gate has zero MDLC, USD_MDL,
failed-shader-node, and missing-texture errors. This is a target-runtime
compatibility result, not a source/target visual-equivalence claim.

## Final retained evidence

The target runtime for both runs is Isaac Sim Kit
`4.1.0-rc.7+4.1.14801.71533b68.gl` from the existing EOS-managed environment.
No environment installation or update was required.

An independent blind visual review of the final eight asset images returned
overall `WARN`, not `PASS`. Both objects are complete and recognizable, with no
white/black fallback blocks or severe visible geometry defect. The warnings are
low-contrast/soft glass appearance, grid interference, and the lack of clearly
readable graduation marks on the cylinder. The available source reference also
does not show clear graduations, so that observation is not classified as a
conversion blocker; it still prevents a stronger visual-fidelity claim.

| Asset | Conventional runtime | Four interaction probes | Blind asset-render QA | Interaction report SHA-256 | Prequalification payload SHA-256 | Final payload SHA-256 | Runtime-tree SHA-256 |
|---|---|---|---|---|---|---|---|
| Conical bottle | pass | all pass | warn | `807b89aa1374a4d8cbd211601a69f85a36c81e1554b2c57f81a3eada19ef59aa` | `277cde9796ae85979ca4cd84b00ca92ed17c25887dd39e95a4e7231e33c167ac` | `5327f93240e3221d7e5b67b78e892cc4bfe665aeb4df64328a93a7eb7dea8b42` | `c9af6eb83aa2ec685bc987bf14d0ba0fb009988e775644d0c838fb992a6e7f9c` |
| Graduated cylinder | pass | all pass | warn | `56e71ac7e871b47bf6f9b0250da6046e457e024212ce74f3f83272d0a48726b1` | `6f8564d9ca073b171f2962cbc386b4c83c549c34818a6a68470401376d607d7c` | `f143fe894f3f668453bd7afd5d592a0dcb41811b7f18d33bf5a8691dad345bbb` | `7392a8f21269820fc0adc4dab60489b8004bbab49e39046cf9433304367ba992` |

The visual-review input hashes are retained separately from the functional
interaction reports:

| Asset | Runtime render | Front | Orbit 3/4 | Side |
|---|---|---|---|---|
| Conical bottle | `cdfbfd5bc5320f6c639771a52f2f5929929128e23e309ba47b89f34a2e62860f` | `cd3ecc4fd1a41b1c324a1a0c82fdb8b736872a7d9265af79482711bd8ebab45a` | `d255d58b4406b79ec83581d1636887f709fc65d3a5ed2b30364bc9b3ff748dbd` | `22c9853e8fd99fa82d7a201ea83221a8a0d9a65a74333ba3ba94d9db67954a06` |
| Graduated cylinder | `a182c0560f735baff6cfce5b490df509c02fc09b4f139d514aececae28437fcc` | `ef0f237e2cff240dde12b70d7b290c974a6e18ee2802b6d53c202b96a2e4c58c` | `42af4b1615aa584402bbb1ca87e273e7b1b113fc312284e18110027cc0a07c96` | `554a8aba7b4c8ceb0712d4166b4d82130a916fb4315f6b0705ee66aa8b7bcde8` |

Retained entrypoints:

- [conical manifest](evidence/2026-07-14-aan-labutopia-vessel-interaction-profile/conical_bottle03/manifest.json)
- [conical interaction report](evidence/2026-07-14-aan-labutopia-vessel-interaction-profile/conical_bottle03/package/evidence/interaction_runtime_qualification/report.json)
- [cylinder manifest](evidence/2026-07-14-aan-labutopia-vessel-interaction-profile/graduated_cylinder_03/manifest.json)
- [cylinder interaction report](evidence/2026-07-14-aan-labutopia-vessel-interaction-profile/graduated_cylinder_03/package/evidence/interaction_runtime_qualification/report.json)
- [retained cylinder SDF failure](evidence/2026-07-14-aan-labutopia-vessel-interaction-profile/graduated_cylinder_03/runtime_attempts/sdf_virtual_cap/report.json)

## TDD and verification

The implementation was developed test-first across four boundaries:

- `tests/test_asset_application_normalizer_interaction_runtime_qualification.py`
  covers closure immutability, fail-closed probe evaluation, one-probe/one-gate
  promotion, report-binding rejection, and byte-identical manifest updates;
- `tests/test_asset_application_normalizer_object_interaction_profile.py`
  covers source-mesh disable, package-owned compound proxy authoring, exact
  collider coverage, and idempotent package rebuilds;
- `tests/test_asset_application_normalizer_physics_admission.py` covers
  support-before-reset and SDF-triggered GPU physics;
- `tests/test_asset_application_normalizer_mdl_runtime_closure.py` covers
  explicit target-root MDL substitution, source-byte preservation, updated
  material closure, and non-parity provenance.

The real LabUtopia profile test and both retained Isaac workers then exercised
the exact source USD and final package closures. The manifests retain the
normalization and conventional runtime commands; the interaction reports retain
their exact invocation bindings.

## Claim boundary and follow-up

These packages establish target-runtime collision/support/root-readback
qualification for two source-bound, provisional-geometry object profiles. They
do not establish measured mass/inertia, real density, friction calibration,
liquid behavior, pouring success, force closure, grasp retention, robot
reachability, collision-free dual-arm execution, policy success, or EBench
score. The render review's `WARN` also forbids a visual-fidelity, readable-scale,
or product-display-quality claim. Replacing provisional values or improving
appearance still requires a new ConvertAsset profile/package revision and the
same static, conventional-runtime, interaction-runtime, and visual review
boundaries.
