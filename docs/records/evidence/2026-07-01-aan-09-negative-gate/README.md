# AAN-09 Negative Gate Evidence

This directory retains the 2026-07-01 AAN-09 blocked negative-gate evidence.

The source fixture `sources/remote_uri_block.usda` contains an unauthorized remote URI
reference. AAN must keep it blocked instead of mirroring, downloading, or pretending the
asset is ready.

Key retained artifacts:

- `remote_uri_block_manifest.json`: blocked AAN manifest.
- `negative_gate_summary.json`: weekly-friendly failure-mode summary.
- `return_code_probe.json`: ConvertAsset CLI return-code evidence.
- `contracts/remote_uri_block_contract.json`: valid task contract supplied to prove the
  block happens before benchmark handoff.
