# 2026-07-15 AAN Graduated Cylinder r3 Grasp-Section Collision Admission

## Why this record exists

`graduated_cylinder_03` failed the Lift2 grasp approach because its r2 collision
proxy was wider than the object at the intended grasp height. This was not a
source-model scale defect. It was a package-owned collision-shape regression
introduced while avoiding a different target-runtime problem: the source mesh's
SDF collision cooked a virtual top cap.

This record supersedes r2 as the current admission reference for this one
source-bound cylinder package. It documents the r3 geometry, the generic AAN
checks that detect the failure without an asset-name branch, and the exact limits
of the retained runtime evidence.

## Immutable source and scope

| Field | Value |
|---|---|
| Source USD | `/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd` |
| Source prim | `/World/graduated_cylinder_03` |
| Source SHA-256 before/after | `b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2` / same |
| Package role | `dynamic` |
| Interaction profile | `profiles/interaction/labutopia_lab001_graduated_cylinder_03_20260707.r3.interaction.json` |
| Retained delivery root | `docs/records/evidence/2026-07-15-aan-graduated-cylinder-r3-grasp-section/graduated_cylinder_03/` |

The source hash remained unchanged. The raw LabUtopia USD was not edited; r3
only authors ConvertAsset-owned package overlays and package-local dependencies.

## Root cause and r3 geometry

The source's wide base is about 117.16 mm, while the visual tube at the grasp
frame is about 47.01 mm. The historical r2 workaround disabled source mesh
collision and used a 55.5 mm-radius, 12-wall proxy through the full 272 mm
height. It avoided the SDF virtual cap, but it also exposed a roughly 115 mm
collider at the grasp height.

| Section at grasp frame | Source/package visual max width | Collision closing width | Collision max in-plane width | Result against 88 mm nominal opening |
|---|---:|---:|---:|---|
| r2 historical proxy | 47.0099 mm | 115.0000 mm | 118.8486 mm | blocked by the new preflight |
| r3 package proxy | 47.0099 mm | 47.0100 mm | 48.3258 mm | pass |

r2's retained, intentionally blocked comparison report is
[`r2_historical_rejected_grasp_cross_section.json`](evidence/2026-07-15-aan-graduated-cylinder-r3-grasp-section/graduated_cylinder_03/r2_historical_rejected_grasp_cross_section.json);
its central sample records the 115.0000 mm closing and 118.8486 mm max-in-plane
collision widths above. The r3 pass report remains
[`package/interaction/grasp_cross_section.json`](evidence/2026-07-15-aan-graduated-cylinder-r3-grasp-section/graduated_cylinder_03/package/interaction/grasp_cross_section.json).

r3 keeps the wide support only at the bottom: a 117.1587 mm-wide, 6 mm-high
bottom Cube. The source mesh remains visual-only for collision purposes. Twelve
narrow wall Cubes run from the top of the base to the 272.2942 mm opening and
remain open at the top; their radius and wall thickness were selected for the
47 mm tube, not for the wide base. The support collider is clear of all three
grasp samples (`-10`, `0`, and `+10` mm around the grasp frame).

This proves the package's declared geometry envelope. It does not prove that
the source's real material wall thickness, mass distribution, or all physical
parameters are measured accurately.

## Generic admission changes

### AAN-05G: source-bound grasp cross section

The new optional `grasp_cross_section` profile block measures the visual Meshes
and every active collision at declared body-local planes. It transforms both
source and package geometry into world-space metres, so root orientation and a
scaled child Mesh cannot turn a raw-coordinate comparison into a false pass.

The static gate fails closed when any of the following happens:

- visual section is absent, non-finite, or outside the source/profile tolerance;
- package visual no longer matches the source visual section;
- collision has no valid section, does not match visual width, or exceeds the
  declared nominal opening;
- an active collision is not an exactly supported Cube proxy; or
- a `support` collider intersects a grasp-band plane.

The retained report is
[`package/interaction/grasp_cross_section.json`](evidence/2026-07-15-aan-graduated-cylinder-r3-grasp-section/graduated_cylinder_03/package/interaction/grasp_cross_section.json).
It records source/package hashes, stage metrics, collision paths, per-sample
widths, and the support gap. It is included in the package runtime-tree artifact
list and is surfaced at `physics_closure.grasp_cross_section`; it intentionally
does **not** alter the strict `aan.interaction_contract.v1` payload that Scenario
Forge already validates.

The gate is an admission preflight, not a robot execution oracle. A pass means
the declared source-bound package envelope agrees with its visual section and
nominal opening contract. It does not establish a physical gripper aperture,
finger contact, force closure, close command, lift, retention, task success,
or pouring.

### AAN-06: all scoped PhysX warnings

The existing mass/inertia parser remains in place for `negative mass`, `invalid
inertia`, and `small sphere approximated inertia`. A second, broader gate now
parses every Warning that contains `[omni.physx]`, maps paths with a complete
one-to-one package/runtime scope binding, and blocks if any warning belongs to
the admitted output asset. It writes
`evidence/runtime_smoke/all_scoped_warning_diff.json` alongside the legacy
`warning_diff.json`.

For the Scenario Forge run, the package scope
`/World/graduated_cylinder_03` maps to
`/World/scientific_workbench_bimanual_pour/obj_obj_graduated_cylinder_03`.
The r3 scoped count is zero. Robot-only warnings remain recorded outside that
scope (and lines that cannot safely be assigned stay recorded as unattributed);
this evidence must never be described as a globally warning-free GenManip run.

## Retained verification evidence

The delivery sidecar `manifest.json` and
`package/evidence/manifest.json` are byte-identical and have final
`overall_status: pass`. They retain:

- AAN-05G pass for all three cross-section samples;
- direct isolated Isaac Sim 4.1 cold load, render readback, 120-frame step, and
  two-cycle reset pass;
- zero r3-scoped legacy mass/inertia warnings and zero r3-scoped broad PhysX
  warnings under the declared Scenario Forge mapping;
- direct Isaac interaction probes for cooked open-top aperture, stable support,
  root-motion parity, and bilateral **proxy** wall queries; and
- Scenario Forge/GenManip post-reset, pre-action `workspace_closeup` and
  `scene_overview` render pass under Isaac Sim 4.1.0.0.

The last item is a reset-and-render smoke only. The collected EOS/GenManip route
currently has no implemented genuine close/lift/hold executor for this package.
Consequently, neither this record nor the manifest claims a real gripper grasp,
lift, retention, dual-arm reachability, pouring, policy success, or benchmark
score.

Independent render QA returned overall `WARN`, not a render-gate failure. In the
consumer close-up, the cylinder is upright, fully visible, and plausibly scaled
beside the robot and flask; the broad scene also keeps it upright and visible,
but small. Direct material views retain the open rim and base, while the
transparent material has low contrast and the graduations are not legible. The
retained evidence therefore supports visual presence and placement only; it does
not support a material-parity, readable-graduation, product-display, or grasp
claim.

## Reproduction

The retained normalizer invocation used the source-bound r3 interaction profile,
the existing provisional physics profile, and an explicit Isaac 4.1 runner:

```bash
./scripts/isaac_python.sh ./main.py normalize-asset \
  /cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd \
  --out docs/records/evidence/2026-07-15-aan-graduated-cylinder-r3-grasp-section/graduated_cylinder_03/package \
  --asset-id LabUtopia_graduated_cylinder_03 \
  --asset-class rigid --asset-role dynamic \
  --source-runtime isaac51 --target-runtime isaac41 --target-benchmark scenario-forge \
  --task-id ScenarioForge.graduated_cylinder_03 \
  --required-prim /World/graduated_cylinder_03 \
  --asset-scope-prim /World/graduated_cylinder_03 \
  --physics-profile profiles/physics/labutopia_lab001_graduated_cylinder_03_20260707.provisional.json \
  --interaction-profile profiles/interaction/labutopia_lab001_graduated_cylinder_03_20260707.r3.interaction.json \
  --gates static,runtime \
  --runtime-python /cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/bin/python \
  --expected-runtime-version 4.1 --runtime-timeout-seconds 600 \
  --evidence-out docs/records/evidence/2026-07-15-aan-graduated-cylinder-r3-grasp-section/graduated_cylinder_03/manifest.json
```

After Scenario Forge generates the r3 consumer output, repeat the preceding
`normalize-asset` invocation as a **second ConvertAsset post-consumer
qualification pass**, adding the following arguments. This rereads the consumer
log and refreshes package/manifest evidence; it is not a Scenario Forge patch or
warning suppressor:

```bash
  --warning-baseline-log /cpfs/user/zhuzihou/dev/scenario-forge/outputs/scientific_workbench_bimanual_pour/adapters/ebench/genmanip/evidence/initial_scene/runtime.log \
  --warning-baseline-scope-prim /World/scientific_workbench_bimanual_pour/obj_obj_graduated_cylinder_03 \
  --runtime-physx-log /cpfs/user/zhuzihou/dev/scenario-forge/outputs/aan_graduated_cylinder_03_r3_consumer/adapters/ebench/genmanip/evidence/initial_scene/runtime.log \
  --runtime-scope-binding /World/graduated_cylinder_03=/World/scientific_workbench_bimanual_pour/obj_obj_graduated_cylinder_03
```

The compact Scenario Forge generator command is documented in the
[consumer handoff](../operations/asset-application-normalizer-consumer-handoff.md#graduated-cylinder-r3-reference-delivery).

## Required follow-up for an actual grasp claim

EOS/GenManip needs an action-level executor that uses the same package and
runtime-scope mapping, then writes an immutable report with at least:

1. robot/finger and object start poses plus the commanded aperture/close action;
2. contact or equivalent closure evidence at the intended grasp section;
3. lift displacement and hold duration with object pose and velocity traces;
4. a release/retention outcome and task-specific success predicate when relevant;
5. the scoped PhysX log from the action run; and
6. hashes binding the report to the r3 package, manifest, robot/task config, and
   runtime environment.

Only after that evidence passes may downstream documentation replace the current
geometry/pre-action boundary with a scoped grasp or lift claim.

## 2026-07-16 addendum: EOS/GenManip action qualification

The preceding description of the absent close/lift/hold executor was accurate
when this collision-admission record was written. It is now superseded only for
the declared target-grasp scope by the
[2026-07-16 EOS/GenManip target-grasp qualification](2026-07-16-aan-graduated-cylinder-r3-eos-genmanip-target-grasp-qualification.md).
That follow-up reran the unchanged source-bound r3 package through twelve fixed
candidates and qualified only `positive_closing@0.135m` for the recorded
right-arm target close/lift/hold protocol.

The new evidence includes direct bilateral target contact, 165 command and
acknowledgement pairs, 504 stable approach-pose samples, a five-sample hold, a
minimum `0.034568727016448975 m` lift, table release at physical step 602, and
zero target-scoped PhysX warnings. It does not revise this record's geometry
boundary into a general grasp, bimanual pouring, policy, benchmark, sibling, or
calibrated-physics claim. The action run also retained 36 out-of-scope robot and
articulation PhysX warning lines; it must not be described as globally
warning-free.
