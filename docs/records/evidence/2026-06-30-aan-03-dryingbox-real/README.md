# AAN-03 DryingBox Real Evidence

Date: 2026-06-30

This directory records the first real LabUtopia DryingBox AAN-03 runs.

The existing EBench overlay now produces `overall_status = pass` and a package-local USD tree.
The raw LabUtopia single-asset and full-lab inputs remain blocked with explicit reasons, which is
expected because AAN-03 does not invent missing source helper files and does not silently allow
remote URI dependencies.

| Manifest | Source | Required prim | Status | Main result |
|---|---|---|---|---|
| `single_dryingbox_01.json` | LabUtopia single `DryingBox_01.usd` | `/group_009` exists | blocked | missing `UnitsAdjust-*.metricsAssembler` helper sublayer |
| `labutopia_lab_001_dryingbox_01.json` | LabUtopia `lab_001.usd` | `/World/DryingBox_01` exists | blocked | unauthorized remote MDL/USD URI dependencies |
| `overlay_level1_poc_dryingbox_01.json` | existing EBench overlay `scene.usda` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` exists | pass | all USD/MDL/texture dependencies packaged locally |

The pass package for the overlay run was written to:

```text
/tmp/aan03_real_packages/overlay_level1_poc_dryingbox_01
```
