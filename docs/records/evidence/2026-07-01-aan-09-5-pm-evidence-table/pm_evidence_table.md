# AAN PM Evidence Table

| Asset | Status | Gates | Evidence | Failure / Waiver | Claims boundary |
|---|---|---|---|---|---|
| RemoteUriBlocked | blocked | usd_closure=blocked, material_closure=not_run, physics_static=not_run, runtime_smoke=not_run, benchmark_contract=not_run | manifest:present, runtime:not_run, benchmark_contract:not_run | aan03_block_remote_uri | Material closure is complete.; Physics or articulation closure is complete.; Isaac runtime smoke passed. |
| Beaker_01 | ready | usd_closure=pass, material_closure=pass, physics_static=pass, runtime_smoke=pass, benchmark_contract=pass | manifest:present, runtime:pass, render_readback:pass, render_non_background_ratio:0.30619049, benchmark_contract:pass | none | Exact Isaac Sim 4.1 binary conformance is verified without an explicit runtime environment fingerprint.; Binary USD layers with dependencies are fully supported by AAN-03 text rewriting.; Full visual material parity beyond recorded source-preservation evidence is achieved. |
| DryingBox_01_overlay | ready | usd_closure=pass, material_closure=pass, physics_static=pass, runtime_smoke=pass, benchmark_contract=pass | manifest:present, runtime:pass, render_readback:pass, render_non_background_ratio:0.76343536, benchmark_contract:pass | none | Exact Isaac Sim 4.1 binary conformance is verified without an explicit runtime environment fingerprint.; Binary USD layers with dependencies are fully supported by AAN-03 text rewriting.; Full visual material parity beyond recorded source-preservation evidence is achieved. |
| MuffleFurnace | ready | usd_closure=pass, material_closure=pass, physics_static=pass, runtime_smoke=pass, benchmark_contract=pass | manifest:present, runtime:pass, render_readback:pass, render_non_background_ratio:0.4051857, benchmark_contract:pass | none | Exact Isaac Sim 4.1 binary conformance is verified without an explicit runtime environment fingerprint.; Binary USD layers with dependencies are fully supported by AAN-03 text rewriting.; Full visual material parity beyond recorded source-preservation evidence is achieved. |

## Summary

- Asset count: 4
- Status counts: {"blocked": 1, "ready": 3}
- Waiver count: 0
- Failure modes: {"aan03_block_remote_uri": 1}
