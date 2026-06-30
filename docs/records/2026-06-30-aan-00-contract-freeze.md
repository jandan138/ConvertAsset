# AAN-00 Contract Freeze

Date: 2026-06-30

## Status

`AAN-00 Contract Freeze` is complete for the Phase 1 Asset Application Normalizer MVP.

Authoritative contract:

- `docs/design/asset-application-normalizer.md`

This record freezes the implementation boundary for `AAN-01` through `AAN-09`. Later
changes to supported source formats, target profiles, manifest schema, gate semantics,
waiver/blocker policy, or product claims must be captured in a new dated record.

## Frozen Scope

1. Phase 1 only supports Isaac 5.1-oriented USD rigid/articulated assets entering the
   EBench Isaac Sim 4.1 target package contract.
2. ConvertAsset owns the normalizer implementation. LabUtopia, EBench, GenManip, and EOS
   consume the package, task contract, evidence manifest, and claim boundary.
3. The first acceptance asset is DryingBox.
4. AAN-08 replication candidates are Cabinet Drawer and Transparent Beaker / `Beaker_01`.
5. The CLI contract is the flat `normalize-asset` subcommand.
6. The target package layout is `asset.usd`, `assets/`, `task/`, `evidence/`, and
   `waivers/`.
7. The manifest is the handoff interface for source/target lineage, required prims,
   dependency/material/physics/articulation closure, gates, runtime evidence, environment,
   waivers, blockers, claims, and commands.
8. Gate statuses are `pass`, `fail`, `blocked`, `waived`, `not_applicable`, and `not_run`.
9. Total statuses are `ready`, `ready_with_waivers`, `failed`, `blocked`, and
   `dry_run_incomplete`.
10. Material handling is source-first: preserve original MDL / texture / material binding,
    then add compatibility fallback when Isaac 4.1 needs it.
11. Physics handling is authored-first: preserve source-authored values; generated values
    must be marked as `derived`, `template`, or `manual_override` with provenance.
12. Waiver is not pass. It changes total status and forbids over-claims such as full
    material parity, physical parameter parity, or official comparability.

## Acceptance Audit

| AAN-00 requirement | Evidence | Result |
|---|---|---|
| Document explicitly limits MVP to USD rigid/articulated -> EBench Isaac 4.1 | `asset-application-normalizer.md` introduction, long-term architecture, numbered acceptance plan, MVP check matrix | Pass |
| Document defines lineage without hard-coding LabUtopia / AutoBio as core abstraction names | `名字和谱系要分清`, `AAN-00 Contract Freeze` | Pass |
| Document defines repo boundary | `仓库边界` and this record's frozen scope | Pass |
| Document defines CLI contract | `CLI contract` section | Pass |
| Document defines package layout | `Target package layout` section | Pass |
| Document defines manifest schema | `Evidence manifest schema` section | Pass |
| Document defines gate semantics and machine-readable statuses | `Stage gate semantics` section | Pass |
| Document defines waiver impact on total status and forbidden claims | `Stage gate semantics`, `Temporary waiver and blocked policy`, `Product claim boundary` | Pass |
| Document defines material policy | `Preservation-first normalization policy`, `Material closure policy` | Pass |
| Document defines physics policy | `Preservation-first normalization policy`, `Physics and articulation checks` | Pass |
| Document excludes MJCF / URDF / deformable / leaderboard claims from Phase 1 support | introduction, `Future adapter families`, `暂不承诺的范围`, `Product claim boundary` | Pass |

## Next Milestone

Start `AAN-01 Manifest Seed` for DryingBox. The manifest seed must use this frozen contract
as the field checklist and must record required prims, source USD path, MDL/texture closure,
physics/articulation facts, known waivers, known blockers, and EBench task entrypoints.
