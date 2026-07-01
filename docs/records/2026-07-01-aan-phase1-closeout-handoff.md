# 2026-07-01 AAN Phase 1 Closeout And Handoff

## Summary

Asset Application Normalizer Phase 1 is closed as a bounded USD -> EBench Isaac 4.1
MVP. The completed scope is not "arbitrary USD conversion". The completed scope is:

- Isaac 5.1-oriented USD assets can be normalized into EBench / Isaac Sim 4.1 asset
  packages when dependencies, material closure, physics/articulation checks, runtime
  smoke, and benchmark task contract pass.
- Output packages carry machine-readable evidence, task handoff files, waiver/blocker
  state, and claim boundaries.
- Downstream projects should consume the package/manifest/task files, not reimplement
  USD, MDL, texture, physics, or articulation repair logic.

## Completed Milestones

| Milestone | Result | Retained evidence |
|---|---|---|
| `AAN-00` to `AAN-02` | Contract, schema, package layout, CLI skeleton | `docs/records/2026-06-30-aan-00-contract-freeze.md`, `docs/records/2026-06-30-aan-02-cli-skeleton.md` |
| `AAN-03` / `AAN-03R` | USD dependency closure and dependency resolution policy | `docs/records/2026-06-30-aan-03-usd-closure.md`, `docs/records/2026-06-30-aan-03r-resolution-records.md` |
| `AAN-04` | Source-first material closure with MDL/texture local mirror records | `docs/records/2026-06-30-aan-04-material-closure.md` |
| `AAN-05` / `AAN-06` | Physics/articulation static checks and Isaac runtime smoke | `docs/records/2026-06-30-aan-05-06-physics-runtime.md` |
| `AAN-07` | EBench task contract files and manifest entrypoints | `docs/records/2026-06-30-aan-07-benchmark-contract.md` |
| DryingBox runtime refresh | First acceptance asset has static/runtime/benchmark evidence | `docs/records/2026-07-01-aan-07-dryingbox-runtime-ready.md` |
| `AAN-08` | Replication set proves the path is not DryingBox-only | `docs/records/2026-06-30-aan-08-replication-set.md` |
| `AAN-09` | Negative gate proves blocked cases do not look ready | `docs/records/2026-07-01-aan-09-negative-gate.md` |
| `AAN-09.5` | PM evidence table for reports and acceptance review | `docs/records/2026-07-01-aan-09-5-pm-evidence-table.md` |
| `AAN-10` | MJCF scout records future semantic gaps without claiming conversion | `docs/records/2026-07-01-aan-10-mjcf-scout.md` |

## Final Evidence Snapshot

Current PM table:

`docs/records/evidence/2026-07-01-aan-09-5-pm-evidence-table/pm_evidence_table.md`

| Asset | Status | Notes |
|---|---|---|
| `DryingBox_01_overlay` | `ready` | First acceptance asset; USD/material/physics/runtime/benchmark gates pass |
| `MuffleFurnace` | `ready` | Non-DryingBox articulated asset; runtime and benchmark gates pass |
| `Beaker_01` | `ready` | Transparent rigid beaker; material mirror and render readback evidence pass |
| `RemoteUriBlocked` | `blocked` | Unauthorized remote URI negative case; failure mode `aan03_block_remote_uri` |

Summary:

- `ready`: 3 assets
- `blocked`: 1 asset
- `waiver_count`: 0
- failure modes: `aan03_block_remote_uri`

## Consumer Handoff

The stable downstream handoff is documented in:

`docs/operations/asset-application-normalizer-consumer-handoff.md`

Downstream projects should treat these as the public contract:

- `normalize-asset` CLI invocation
- target package layout: `asset.usd`, `task/`, `evidence/`
- AAN `manifest.json` / evidence manifest
- `task/task_config.yaml`
- `task/required_prims.yaml`
- `task/evaluator.yaml`
- PM evidence table JSON/Markdown
- explicit `claims_allowed` / `claims_forbidden`

Downstream projects should not depend on internal Python function names, intermediate
reports that are not listed in the handoff document, or `/tmp` run directories.

## Supported Claim

Safe product wording:

> AAN Phase 1 has completed a bounded USD -> EBench Isaac 4.1 normalization MVP. It
> has retained evidence for DryingBox, one additional articulated asset, one transparent
> rigid asset, and one blocked negative case. Downstream projects can consume the
> normalized package and evidence manifest without hand-maintaining USD/MDL/texture/
> physics/articulation repair logic.

Unsafe product wording:

> AAN can convert almost any USD asset to EBench.

## Still Out Of Scope

- Arbitrary USD coverage claims without a batch admission experiment.
- URDF / MJCF conversion to EBench packages.
- AutoBio official reproduction.
- Deformable, cloth, liquid, particle, or granular simulation closure.
- Full material parity, pixel-perfect render parity, physical-parameter parity, or
  official leaderboard comparability.
- Automatic task success predicate discovery.

## Recommended Next Work

1. `AAN-11 Batch Admission`: run 20-50 LabUtopia USD assets through the public CLI and
   report ready / blocked / waiver proportions.
2. `AAN-12 Consumer SDK`: add a thin manifest/task-file reader if downstream projects
   need a Python API instead of shelling out to CLI outputs.
3. `EBench-02 Runtime Episode`: let EBench consume the retained ready packages in its
   own runtime / EpisodeTrace path, still respecting AAN claim boundaries.
4. `AAN-13 Profile Split`: only after batch admission, split source adapters and target
   profiles if the flat MVP modules become a bottleneck.

## Verification

Commands run during closeout:

```bash
python -m pytest tests/test_asset_application_normalizer_cli.py tests/test_asset_application_normalizer_pm_and_mjcf.py -q
python -m compileall convert_asset/asset_application_normalizer
git diff --check
```

Evidence audit expectations:

```text
DryingBox runtime-ready manifest: all AAN-03/04/05/06/07 gates pass
PM evidence table status_counts: {"blocked": 1, "ready": 3}
MJCF scout manifest: overall_status=semantic_gap_report_only
```
