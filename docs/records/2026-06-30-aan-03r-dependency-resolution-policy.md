# AAN-03R Dependency Resolution Policy

Date: 2026-06-30

## Context

AAN-03 proved the first real DryingBox overlay package path:

- input: existing EBench overlay `scene.usda`;
- output: package-local USD tree;
- status: `pass`;
- evidence: `docs/records/evidence/2026-06-30-aan-03-dryingbox-real/overlay_level1_poc_dryingbox_01.json`.

The same run also clarified two raw-source gaps:

- LabUtopia single `DryingBox_01.usd` is missing `UnitsAdjust-*.metricsAssembler`;
- raw LabUtopia `lab_001.usd` still contains unauthorized remote URI dependencies.

These do not mean AAN-03 is unfinished. They mean raw source inputs need a standard resolution
policy before they can be promoted from diagnostic evidence to accepted packages.

## Product Rule

AAN must not silently invent source files, ignore remote dependencies, or turn every missing file
into a waiver. Every missing or remote dependency must end in exactly one decision:

| Decision | Product meaning | Engineering requirement |
|---|---|---|
| `mirrored` | We found or legally synchronized the dependency and made the package self-contained | Record original source path/URI, local mirror path, package path, hash, owner layer, and command/provenance |
| `pruned` | The dependency is outside this target task and has been safely excluded | Prove required prims, runtime load, render, collision/articulation, and evaluator scope do not need it |
| `waived` | The risk is known and acceptable for a limited claim | Record waiver owner, reason, impact, review date, and forbidden claims; total status cannot be clean `ready` |
| `blocked` | The dependency is required and cannot be safely resolved | Keep CLI return code blocked and write required resolution into manifest/weekly evidence |

Discovery states such as `local_missing` or `remote_unresolved` are not final product outcomes.
They are intermediate diagnostics that must be resolved into the four decisions above.

## DryingBox Raw Single Asset

`DryingBox_01.usd` reports a missing helper sublayer:

```text
./SubUSDs/textures/UnitsAdjust-*.metricsAssembler
```

Resolution order:

1. Search LabUtopia original export, LabUtopia dataset mirrors, historical generated packages, and
   EBench overlay outputs for the exact file.
2. If found, mirror it into the AAN package and rewrite the sublayer reference.
3. If not found, inspect whether it is an exporter residue. It may be pruned or waived only if
   opening the package, required prim existence, scale/units, geometry, material, physics, and
   runtime smoke are unaffected.
4. If it affects units/scale or cannot be proven irrelevant, keep the raw single asset `blocked`.

Acceptance for a future raw-single pass:

- manifest has no `missing` dependency;
- required prim `/group_009` still exists;
- package contains no source-tree path escape;
- package opens from `asset.usd`;
- if pruned or waived, claims forbid full source-export closure.

## Raw Lab Scene Remote URI

`lab_001.usd` contains remote URI dependencies for MDL/USD assets. Raw remote URI is not allowed
in a target EBench package because runtime behavior would depend on network access, external
availability, and untracked content versions.

Resolution order:

1. Prefer local mirror: use existing Isaac/LabUtopia caches or legally synchronized remote content,
   then record original URI, hash, mirror source, and package path.
2. If the remote dependency is background scene content irrelevant to the DryingBox task, create a
   task-scope package that prunes it and forbids full-lab-scene closure claims.
3. Allow a resolver only when the target profile explicitly supports it and runtime evidence proves
   deterministic resolution. This is not the default for EBench Isaac 4.1 package handoff.
4. If the remote dependency is required and cannot be mirrored or explicitly allowed, keep the raw
   lab scene `blocked`.

Acceptance for a future raw-lab pass:

- manifest has no unauthorized remote URI;
- every formerly remote dependency is `mirrored`, `pruned`, or explicitly allowed with evidence;
- task-scope pruning does not remove DryingBox required prims or task semantics;
- package escape scan finds no `http://`, `https://`, `omniverse://`, `/cpfs/...`, or `/isaac-sim/...`
  path in package USD/MDL files.

## Next Work

`AAN-03R` should be scheduled before `AAN-04 Material Closure` if the team wants raw LabUtopia
sources, not only existing EBench overlay packages, to become first-class AAN inputs.

`AAN-04` should still own material semantics: source material preservation, channel provenance,
PreviewSurface fallback, transparent material policy, and material waivers. It should not absorb
raw-source missing/remote dependency triage.
