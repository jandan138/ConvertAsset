# AAN-08 Replication Set Evidence

This directory retains the 2026-06-30 AAN-08 evidence for two non-DryingBox LabUtopia
assets:

- `MuffleFurnace`: articulated asset.
- `Beaker_01`: transparent rigid beaker prop.

Both were run through `static,runtime,benchmark` gates. The retained summary is
`replication_set_summary.json`; individual manifests are `muffle_furnace_manifest.json`
and `beaker_01_manifest.json`.

Package outputs from the run were written under `/tmp/aan08_real_packages/` and copied
into `packages/` here. The retained artifacts include full packages, contracts, runtime
reports, render PNGs, and task handoff YAML files needed for audit and weekly evidence.
