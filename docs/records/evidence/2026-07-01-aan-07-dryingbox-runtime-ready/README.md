# AAN-07 DryingBox Runtime-Ready Evidence

This directory retains the DryingBox runtime-ready refresh generated on 2026-07-01.

Artifacts:

- `dryingbox_runtime_ready_manifest.json`: AAN manifest with AAN-03/04/05/06/07 all
  passing.
- `runtime_report.json`: runtime smoke report copied from the package.
- `render.png`: representative render readback image.
- `package/`: retained package copy, including `asset.usd`, task files, dependency
  mirrors, and runtime smoke logs/artifacts.

Result summary:

- `overall_status`: `pass`
- `runtime_evidence.status`: `pass`
- `render_readback.status`: `pass`
- `benchmark_contract.status`: `pass`
- `render_readback.non_background_ratio`: `0.76343536`

This evidence lets the PM table classify `DryingBox_01_overlay` as `ready` instead of
`contract_ready_runtime_pending`.
