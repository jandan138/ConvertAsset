# AAN-03 DryingBox Real Evidence

Date: 2026-06-30

This directory records the first real LabUtopia DryingBox AAN-03 / AAN-03R runs.

The existing EBench overlay now produces `overall_status = pass` and a package-local USD tree.
The raw LabUtopia single-asset and full-lab inputs remain blocked with explicit reasons, which is
expected because AAN-03 does not invent missing source helper files and does not silently allow
remote URI dependencies.

AAN-03R adds `dependency_closure.resolution_records` and
`dependency_closure.resolution_summary` so each missing or unauthorized remote gap has a final
decision.

| Manifest | Source | Required prim | Status | Resolution summary | Main result |
|---|---|---|---|---|---|
| `single_dryingbox_01.json` | LabUtopia single `DryingBox_01.usd` | `/group_009` exists | blocked | `mirrored=0, pruned=0, waived=0, blocked=1` | missing `UnitsAdjust-*.metricsAssembler` helper sublayer remains blocked |
| `labutopia_lab_001_dryingbox_01.json` | LabUtopia `lab_001.usd` | `/World/DryingBox_01` exists | blocked | `mirrored=0, pruned=0, waived=0, blocked=4` | unauthorized remote MDL/USD URI dependencies remain blocked |
| `overlay_level1_poc_dryingbox_01.json` | existing EBench overlay `scene.usda` | `/World/labutopia_level1_poc/obj_obj_DryingBox_01` exists | pass | `mirrored=6, pruned=0, waived=0, blocked=0` | local mirror MDL dependencies were written into the package |

The pass package for the overlay run was written to:

```text
/tmp/aan03r_real_packages/overlay_level1_poc_dryingbox_01
```
