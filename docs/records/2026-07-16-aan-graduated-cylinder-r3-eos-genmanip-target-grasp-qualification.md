# 2026-07-16 AAN Graduated Cylinder r3 EOS/GenManip Target-Grasp Qualification

## Why this record exists

The 2026-07-15 r3 record established that the source-bound package has a
collision envelope compatible with the declared grasp section and retained only
a post-reset, pre-action consumer smoke result. This record adds a separate,
actual EOS/GenManip action qualification for that unchanged package. It does
not turn the package into a general task-ready vessel or revise the source USD.

The qualification deliberately stops after the right-arm target close, lift,
and hold protocol. Its narrow scope makes the result useful without treating a
single successful action trace as bimanual pouring or a benchmark result.

## Result at a glance

The fixed-candidate campaign passed. It ran all twelve declared candidates and
selected candidate index `0`, `positive_closing@0.135m`, as the only qualified
candidate. Its `target_grasp_hold` stage passed with direct bilateral target
contact, lift, hold, and target-scoped PhysX evidence.

| Field | Retained value |
|---|---|
| Source identity | LabUtopia 20260707 `lab_001.usd:/World/graduated_cylinder_03` |
| Source SHA-256 before / after | `b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2` / same |
| Package-tree digest before / after / current | `8a646296233e6dbbca42acf2549112d8d47ecd12c60a57fbf360b7a67d68a346` / same / same |
| Campaign status | `passed` |
| Candidate count | 12 fixed candidates, all terminal |
| Qualified candidate | index `0`: `positive_closing@0.135m` |
| Target-scoped PhysX warnings | 0 |
| Compact retained evidence | [`evidence_summary.json`](evidence/2026-07-16-aan-graduated-cylinder-r3-eos-genmanip-target-grasp/evidence_summary.json) |

The matching source hashes and package-tree digests are source and package
integrity locks. They show that the action run consumed the retained r3 package
without modifying raw LabUtopia USD or mutating the package during execution.

## Declared protocol and action evidence

The declared claim scope is
`source_bound_right_arm_target_grasp_hold_qualification`. The selected
candidate issued 165 command-and-acknowledgement pairs. Its approach phase
retained 504 target-pose samples, all stable under the pre-close policy:

| Observation | Result |
|---|---:|
| Maximum target translation delta during approach | `6.428258004821239e-07 m` |
| Maximum target rotation delta during approach | `0.00027441618481374925 deg` |
| Direct target contact at close | measured bilateral contact, one left and one right finger-side sample |
| Hold samples | 5 |
| Bilateral contact fraction during hold | `1.0` |
| Minimum lifted height | `0.034568727016448975 m` |
| Required minimum lift | `0.02 m` |
| First table-release observation | `lift_settle_step_1`, physical step 602 |

The campaign's target scope is the composed
`obj_obj_graduated_cylinder_03` runtime instance. No parsed `[omni.physx]`
warning was attributable to that scope. The capture also retained 36
out-of-scope warning lines: robot dummy-base negative-mass/inertia/small-sphere
messages and articulation duplicate-link messages. Those lines are not hidden
or waived, but they do not make this a globally warning-free run.

## Fixed-candidate campaign result

All candidates were executed under the same source/package locks. Candidate
local failures are retained as negative evidence; they are not suite-integrity
failures and do not invalidate the selected candidate's recorded result.

| Candidate indices | Candidate(s) | Result |
|---|---|---|
| 0 | `positive_closing@0.135m` | qualified; no blockers |
| 1 | `positive_closing@0.100m` | candidate-local failure: `target_contact_before_close` |
| 2 | `positive_closing@0.170m` | candidate-local failure: `bilateral_target_contact_not_measured` |
| 3--11 | negative-closing and transverse variants at 0.100 m, 0.135 m, or 0.170 m | candidate-local failure: `right_arm_motion_planning_failed` |

The campaign's selection rule was to execute all terminal records and select
the lowest-index qualified candidate. Therefore index 0 was not promoted by
skipping the other candidates. The selected raw worker reports
`task_status: blocked` only because it intentionally blocks the subsequent
`source_pick` stage with `scope_limited_to_target_grasp`; after the passed target
stage, that block preserves the protocol boundary rather than reporting a grasp
failure.

## Evidence canonicalization correction

An earlier trial was **inconclusive**, not a physics failure. Its live Oracle
evaluated an in-memory quaternion while the reducer replayed a normalized JSON
quaternion. The two otherwise identical calculations differed at floating-point
precision and triggered `approach_pose_trace_replay_mismatch`.

GenManip revision `014bf5435a373df9b3bcf5a69aa7fe22d17f613d` canonicalizes the
live pose at the same evidence boundary used by reducer replay. Strict equality
between live and replayed approach evidence remains required; no tolerance was
added to conceal a mismatch. The complete twelve-candidate campaign was then
rerun and passed.

## Provenance

| Component | Revision |
|---|---|
| Scenario Forge | `8e8973789b9aab3cccae6a43d299b3c33f3cc8c4` |
| ConvertAsset | `4bb541161a652cc4e5dd63253adffba018f17137` |
| EOS | `d6f1dfc891b4a2248c675c2253d6b7eaa57e703e` |
| GenManip runtime repository | `014bf5435a373df9b3bcf5a69aa7fe22d17f613d` |

The package remains the ConvertAsset-owned r3 delivery described in the
[grasp-section collision admission record](2026-07-15-aan-graduated-cylinder-r3-grasp-section-collision.md).
Scenario Forge and EOS/GenManip consume that package and its manifest; neither
owns a local collider, mass, inertia, or warning-suppression patch for this
asset.

## Claim boundary

The allowed claim is deliberately narrow:

> The recorded source-bound r3 package qualified under the declared fixed
> right-arm target close/lift/hold protocol, with the retained target-contact,
> pose, hold, source/package-integrity, and target-scoped PhysX evidence.

This record does **not** establish any of the following:

- bimanual pouring, source pick, mouth alignment, pour pose, or source return;
- policy success, an EBench score, or a benchmark result;
- qualification of a different candidate, task configuration, runtime, or
  sibling asset;
- global PhysX warning freedom; or
- calibrated real-world mass, inertia, friction, wall thickness, or other
  physical parameters.

The prior r3 collision admission stays relevant: it establishes source/package
visual-to-collision section agreement and is not by itself a robot action
claim. Conversely, this action trace does not expand the package's physical
parameter provenance beyond its declared provisional geometry profile.

## DryingBox claim correction remains unchanged

This cylinder qualification does not alter the separate DryingBox correction.
The authoritative wording remains:

> Retained readiness evidence applies only to the pre-repaired
> `DryingBox_01_overlay` source and its declared overlay prim scope. It does
> not establish normalization readiness for the raw LabUtopia `lab_001.usd`
> DryingBox family.

See the [2026-07-13 DryingBox family admission and claim correction](2026-07-13-aan-dryingbox-family-admission-and-claim-correction.md)
for the raw-family audit and the separately role-scoped DB03 `visual_static`
package. Neither a repaired overlay nor this graduated-cylinder action result
can be projected onto the raw DryingBox family.

## Evidence retention and follow-up

The repository retains a compact, path-safe summary rather than the large raw
action traces and runtime logs. The summary contains the source/package locks,
revisions, candidate outcomes, action measurements, warning boundary, and
forbidden claims needed to audit the conclusion.

A future claim for bimanual pouring or benchmark success requires a new,
separately bound action campaign with its own source/package locks, task
predicate, contact and state traces, and scoped warning evidence. It must not
reuse this target-grasp qualification as a substitute.
