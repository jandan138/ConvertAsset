# 2026-07-13 AAN DryingBox Family Admission And Claim Correction

## Why this record exists

Scenario Forge integration exposed a scope error in the previous DryingBox
readiness wording. The retained AAN evidence for `DryingBox_01_overlay` was a
real, passing run, but its source was an already repaired EBench overlay. It did
not test the raw LabUtopia DryingBox family and therefore cannot establish a
`DryingBox normalization-ready` conclusion for that family.

This is a correction of claim scope, not a finding that the historical overlay
test was invalid. The problem was that product-facing wording used the family
label “DryingBox” without carrying the source identity, overlay status, and prim
scope into the claim.

## Reproduction identity

| Field | Value |
|---|---|
| Raw source | `/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd` |
| Raw source SHA-256 | `b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2` |
| Declared raw source scope | `/World/DryingBox_03` |
| Representative affected prims | `body/Group/door/mesh`, `handle/mesh` |
| Integration runtime evidence | `outputs/scientific_workbench_bimanual_pour/adapters/ebench/genmanip/evidence/initial_scene/runtime.log:351` |

The raw source has a metre-scale scene convention while the DryingBox family
contains source authoring whose density and local scale do not support PhysX
auto-mass calculation. The cited runtime evidence contains the relevant
negative-mass and small-sphere/inertia warnings for the composed DB03 path.

## Historical evidence and corrected interpretation

The historical AAN-07 refresh used the following different source and scope:

| Historical item | What it establishes | What it does not establish |
|---|---|---|
| `DryingBox_01_overlay` package and manifest | The pre-repaired overlay at its declared EBench prim scope passed the retained static, runtime, and benchmark checks. | The raw `lab_001.usd` DB01, DB02, DB03, or DB04 source prims are normalized or physics-ready. |
| AAN-09.5 PM table row named `DryingBox_01_overlay` | The table correctly reported that retained overlay manifest as ready. | A family-wide raw-LabUtopia readiness count, or a substitute for source-family admission. |

The earlier conclusion became too broad because it used “DryingBox” as the
acceptance-asset label and “first acceptance asset” as a summary, while omitting
the facts that the evidence source was a pre-repaired overlay and that its
declared required-prim scope was not the raw family. A passing overlay manifest
may be retained as evidence for that overlay; it must not be projected onto a
different source hash, prim scope, or asset family.

Safe historical wording is:

> Retained readiness evidence applies only to the pre-repaired
> `DryingBox_01_overlay` source and its declared overlay prim scope. It does
> not establish normalization readiness for the raw LabUtopia `lab_001.usd`
> DryingBox family.

## Raw-family source admission result

The AAN source audit was run against the actual 20260707 source family, not a
synthetic fixture. DB01 through DB04 each contain rigid-body semantics with
invalid or incomplete mass properties. In particular, DB03 has applied
RigidBody, Collision, and MassAPI semantics but includes zero/non-finite mass
property values and relies on invalid auto-compute behavior.

| Raw family member | Source-admission result | Claim consequence |
|---|---|---|
| DB01 | blocked; 4 of 4 rigid bodies invalid | Not dynamic-physics ready. |
| DB02 | blocked; 3 of 3 rigid bodies invalid | Not dynamic-physics ready; the common rule detects it without a DB02 special case. |
| DB03 | blocked as raw dynamic physics; 3 of 3 rigid bodies invalid | Eligible only for separately evidenced role-specific output admission. |
| DB04 | blocked; 4 of 4 rigid bodies invalid | Not dynamic-physics ready; the common rule detects it without a DB04 special case. |

“Blocked” in this source ledger is deliberate: it preserves the fact that the
source has a defect even when a later output has a valid non-dynamic role. It
must not be silently converted into a source-family pass by stripping physics in
an output overlay.

## AAN role-specific package admission

The 20260707 DB03 delivery is a ConvertAsset-owned package with:

| Field | Required boundary |
|---|---|
| Source | The immutable raw source above; its SHA-256 is captured before and after packaging. |
| Output role | `visual_static` only. |
| Output scope | The declared DB03 package prim scope, not a name-based DryingBox rule. |
| Preserved semantics | Visual geometry, material bindings, visibility, and transforms. |
| Disabled semantics | Articulation, joint, rigid-body, collision, and related Physics/Physx APIs in the declared output scope. |
| Consumer responsibility | Scenario Forge consumes the package and does not add local physics stripping or mass/inertia repairs. |
| Forbidden claims | Dynamic-physics-ready, articulated-ready, source-family-ready, or physical-parameter parity. |

The package root is an owned strong overlay over a package-local, scope-isolated
composed snapshot. AAN retains a package-local source-root mirror only as
closure input; the `visual_static` entrypoint sublayers
`deps/usd/scoped_source.usda`, not the full LabUtopia scene. AAN changes only
this output overlay; it never writes the LabUtopia source USD. The manifest
records source integrity as the before/after source SHA-256 and requires
equality.

The visual-static role has two independent checks:

1. A source audit records every raw scoped rigid body and its invalid
   mass/inertia provenance. This is an admission diagnostic, not an output pass.
2. An output-role audit requires zero active rigid-body, collision,
   articulation, or joint semantics in the declared output scope. A visual
   fingerprint compares raw source, package-before-role, and package-after-role
   transform/material/mesh state; a mismatch blocks the package.

This split prevents a role-specific visual-static output from laundering an
invalid raw dynamic asset into a family-wide readiness claim.

## Scope-isolated package closure

The `visual_static` AAN-03 rule is generic. It does not contain a DB03 path or
asset-name branch:

1. AAN composes the package-local immutable source root.
2. It identifies the declared scope subtrees and their effective bound material
   prims.
3. It opens a population-masked composed stage for exactly those roots, loads
   the composition, flattens it, and writes a package-local
   `deps/usd/scoped_source.usda` snapshot.
4. The owned `asset.usd` overlay sublayers that snapshot before role
   normalization removes physics semantics.

The manifest retains the strategy, scope paths, retained material paths, and
preserved stage metadata in
`dependency_closure.scope_extraction`. This prevents unrelated DryingBox
siblings or unrelated MDL graphs from entering the direct DB03 runtime candidate
while preserving the declared scope’s composed transform and material-binding
meaning.

The rule blocks rather than falls back to a full-scene package if the scope
cannot compose, the effective material roots disappear from the snapshot, the
snapshot cannot reopen, or the visual fingerprint differs. Collection binding,
external relationship targets, and instancing require explicit composed-snapshot
and visual-preservation evidence; they are not a reason to ship the entire
source scene.

## General physics rule

The rule is keyed by declared scope and USD semantics, never by DB03, DB02, or
any other asset name. For every scoped rigid body, the dynamic admission path
requires:

- explicit positive, finite mass;
- explicit positive, finite diagonal inertia;
- finite center of mass and a normalizable principal-axes quaternion;
- complete authored, derived, template, or manual-override provenance for every
  accepted value; and
- no remaining reliance on invalid PhysX auto-compute after MassAPI is applied.

An authored, valid mass remains the mass basis when inertia alone is missing or
invalid. AAN derives the inertia from that authored mass and records the basis in
persistent provenance; it must not replace that mass with a template mass merely
to produce inertia. When mass itself is invalid, a versioned density/template
derivation may be used only with complete provenance and target-runtime evidence.

## Runtime warning gate and diff semantics

The runtime gate parses the output package’s declared prim scope, not a global
warning count. It blocks readiness when a warning is attributable to that scope
and matches any of:

- negative mass;
- invalid inertia; or
- small-sphere approximated inertia.

Warnings with no extractable prim path are fail-closed rather than ignored. A
Scenario Forge baseline may use its composed DB03 scope while the candidate
package uses its package-local DB03 scope; the evidence records both scope maps,
the baseline log hash, candidate log hashes, categories, and per-scope counts.

The warning diff is explanatory evidence, not a waiver: candidate scoped counts
must be zero for a ready runtime result. The baseline records the known incoming
Scenario Forge defect and enables an auditable “before versus package” comparison;
it cannot make a candidate with a scoped warning pass.

## Consumer claim boundary

Scenario Forge must use the ConvertAsset package plus manifest as its input. It
must not contain a DB03-specific branch, physics API deletion, mass assignment,
inertia assignment, or warning suppression. If the output is used outside the
declared background role, it must be re-admitted under the appropriate role and
target contract.

The corrected DB03 wording is:

> The 20260707 `lab_001.usd:/World/DryingBox_03` package is admitted only as
> `visual_static` for the declared Scenario Forge background scope. It is not
> an articulated-physics-ready, dynamic-physics-ready, or family-wide readiness
> claim.

## Retained verification result

The final evidence is retained under
[`evidence/2026-07-13-aan-dryingbox-family-admission/`](evidence/2026-07-13-aan-dryingbox-family-admission/).
It contains the following independently consumable artifacts:

| Artifact | Purpose |
|---|---|
| [`package/`](evidence/2026-07-13-aan-dryingbox-family-admission/package/) | ConvertAsset-owned DB03 `visual_static` package, including `asset.usd`, the scope-isolated source snapshot, material closure, runtime log, render, and warning diff. |
| [`manifest.json`](evidence/2026-07-13-aan-dryingbox-family-admission/manifest.json) | Authoritative package manifest and gate/evidence index. |
| [`static_admission_report.json`](evidence/2026-07-13-aan-dryingbox-family-admission/static_admission_report.json) | DB03 raw-source audit and role-specific output admission. |
| [`dryingbox_01_04_raw_family_admission.json`](evidence/2026-07-13-aan-dryingbox-family-admission/dryingbox_01_04_raw_family_admission.json) | Real DB01--DB04 family audit, with no synthetic substitute. |
| [`runtime report`](evidence/2026-07-13-aan-dryingbox-family-admission/package/evidence/runtime_smoke/report.json) and [`warning diff`](evidence/2026-07-13-aan-dryingbox-family-admission/package/evidence/runtime_smoke/warning_diff.json) | Cold-load/render/step/reset and scoped PhysX comparison evidence. |

| Check | Retained result |
|---|---|
| Source integrity | pass; before/after SHA-256 are both `b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`. The original LabUtopia USD was not changed. |
| Raw-family admission | blocked; DB01/DB02/DB03/DB04 contain 4/3/3/4 invalid rigid bodies respectively (14 of 14 total). This is a source diagnostic, not a failure of the separately declared output role. |
| DB03 output-role admission | pass for `/World/DryingBox_03` as `visual_static`; the output scope has zero active rigid-body, collision, articulation, or joint residue while the visual-preservation fingerprint passes. |
| Isaac Sim 4.1 runtime gate | pass in Kit `4.1.0-rc.7+4.1.14801.71533b68.gl`: cold load, render readback, two-frame step, and reset all pass; the worker exit code is 0. |
| Scoped PhysX gate | pass; no negative-mass, invalid-inertia, or small-sphere-approximated-inertia event is attributable to the candidate output scope. |
| Warning diff | pass; the composed Scenario Forge DB03 baseline has 12 scoped events and the package candidate has 0 (`removed_count=12`, `introduced_count=0`). |

### Isolated runtime-worker exit policy

The retained runtime report deliberately records
`process_exit.policy = "os_exit_after_evidence"`. This is an isolated-worker
workaround for an Isaac Sim 4.1 native-plugin-unload crash that can occur after
the gates have finished and their report has been persisted. It is not a claim
that graceful `SimulationApp.close()` shutdown was exercised: the report records
`simulation_app_close = "not_called"`.

The policy is not a success override. A failed gate, a missing final report, or a
nonzero worker/protocol result remains fail-closed; this retained run records a
complete passing report and worker exit code 0. Consumers must use the manifest
result and declared scope, rather than treating the exit policy as a waiver.
