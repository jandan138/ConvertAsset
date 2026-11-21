# Task09 r4 near-full powder scene — persisted grain initial state

Date: 2026-09-11. The user approved r3 Git closeout first (ConvertAsset
`4090ec0`, Scenario Forge `bb36b24`), then a high thin tray supporting a real
particle bed, visually near-full with roughly 5 mm headspace. **The r4 candidate
passed static validation and three Isaac 4.5 fixture reports. Final video and
ZIP qualification are pending main's later closeout.**

## Architecture, completeness and risk review

- **Architecture:** ConvertAsset owns the fitted bottle model, collision/mass
  authoring and preparation/bake producer. SF owns runtime qualification,
  measurement, replay and delivery. Source review covered
  [`model_full_powder_bottle.py`](../../scripts/model_full_powder_bottle.py),
  [`build_full_powder_scene.py`](../../scripts/build_full_powder_scene.py),
  [`build_compact_powder_scene.py`](../../scripts/build_compact_powder_scene.py)
  and [`test_full_powder_scene.py`](../../tests/test_full_powder_scene.py).
- **Completeness:** distinguish manufacturing preparation from accepted initial
  state; preserve recorded grain positions **and orientations**, localize them
  against bottle drift, and cold-start the baked candidate. Check original
  object specs/dependencies, all grains, actual fill level and force calibration.
- **Risk:** the narrowing shoulder requires a shape-fitted tray; translating
  the old wide plate upward would be incorrect. An above-mouth seed column is
  manufacturing-only. New height/count require new runtime evidence; r3
  qualification cannot establish r4 containment or tool clearance.

## Producer changes and initial-state semantics

The [model record](2026-09-11-full-powder-bottle-model.md) retains the detailed
geometry, red-first tests and CPU Blender preview/reopen evidence. The unchanged
60 × 60 × 100 mm bottle shell now contains a **2 mm tray at z=82–84 mm**, clipped
to the actual triangulated interior with 0.15 mm visual wall overlap. Mass uses
the unchanged shell plus exact interior-only tray integration to floating-point
clipping tolerance; the overlapping seam is excluded from mass. This is exact
for the authored solid, not measured manufactured HDPE or a smooth ideal cavity.
Bottle/tray mass is **0.04680521063405403 kg**. The contact approximation has
**289 colliders: 256 walls + one base + 32 tray sectors**.

`build_compact_powder_scene.build(..., *, positions=None)` adds an optional
finite, count-matched positions input while retaining the existing default
fill path. The r4 producer reuses it to author **10,240 independent
`/World/obj_powder_grain_*` roots**, equal-volume diameter **1.4 mm**, total runtime
mass **22.0686 g**. Original **19 root-object specs and their dependencies are
identical** according to the static report; the bottle shell geometry is retained.

1. **Prepare:** seed a deterministic, throat-fitting, non-overlapping HCP gravity
   column (seed 42), allowing grains above the mouth exclusively for manufacturing.
   Config marks `initial_state=preparation_gravity_column`, `preparation_only=true`.
2. **Settle:** the recorded 8 s preparation passed with all 10,240 retained,
   no grains below the insert/table and no engine errors. Its median bed depth
   **10.60459 mm is preparation evidence, not the final cold-start result**.
3. **Bake:** require a healthy, retained, scene-hash-matched Isaac 4.5 settle
   report covering at least 8 s. Read actual recorded final poses, undo the
   recorded bottle translation/rotation, and reapply its canonical authored
   position. Validate ordered grain paths and finite poses; persist grain
   positions/orientations into a new USD, with zero initial velocities.
   The candidate records preparation scene/report/state hashes and sets
   `initial_state=presettled`, `preparation_only=false`, `status=candidate`.
   Other objects keep their authored initial states. **No warmed solver or
   contact cache is persisted**; the candidate must solve again from a cold start.

## Source-bound evidence

Paths are external generated artifacts, with these roots:

- **P:** `/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/task09_powder_bottle_r4_20260911/`
  — `model_r1/`, `preparation_r1/`, `candidate_r1/`.
- **E:** `/cpfs/user/zhuzihou/dev/scenario-forge/outputs/task09_powder_bottle_r4_20260911/`
  — preparation and three final runs, static/qualification summaries and logs.

| File | SHA-256 |
|---|---|
| `P/model_r1/geometry.json` | `121118a218ceb2581ad9584f0f5f756b1de4b062eec47d77f65b9cb7ca6ea09c` |
| `P/candidate_r1/scene.usda` | `50073c0b67f44992e5c55baebca4fe427f48de22599fdbe3feee4133c3807994` |
| `P/preparation_r1/scene.usda` | `253bcb566ff25b80271b1ac36378266016f8de7808143ede0aeeba1bc0890487` |
| `E/preparation_settle/report.json` | `540c5a06c55289bc66b981c6f7221c267c1cfd35826eb017aa20ca16f7f73ac9` |
| `E/preparation_settle/states.npz` | `2976d37bb124326f1d4c4fc96fe2000287b6545f4c11f88084df6a0a8cd13348` |

`E/qualification_summary.json` reports all three final runs **passed**, bound to
the candidate scene hash above. Conditions: **Isaac Sim 4.5.0, PGS, 240 Hz
(`dt=1/240 s`), 32 authored position iterations**, prescribed kinematic tool
fixture; no iteration or wake-all override. All three engine-error lists are empty.

| Evidence | Recorded result |
|---|---|
| `static_validation.json` | Passed; 10,240 root grains, 289 bottle colliders, 19 original objects preserved, 5 USD layers/19 assets, no unresolved dependencies. |
| `final_settle/report.json`, cold 8 s | All 10,240 retained; median bed depth **10.27848 mm** (p10/p90 **10.04846/10.72127 mm**); median headspace **5.72152 mm**, minimum **4.72370 mm**. Initial and settled near-full checks passed; no grains below insert/table. |
| `final_scoop/report.json`, 50 s | Tare, sustained carry, transfer and stable force checks passed. **253 grains** in boat; expected **0.5452486 g**, net measured **0.5452427 g**, LCD **0.55 g**. Thirty-sample crosscheck maximum error **0.0000158692 g**. |
| `final_calibration/report.json`, 43 s | Known loads **0 / 0.0991361 / 0.4008546 / 0.7995542 / 0 g** passed (0/46/186/371/0 grains). Maximum known-load error **0.0000805083 g**. Tared boat removal **−10 g** and instrument reset **0 g** passed; reset LCD **0.00 g**. Calibration uses teleport/CCD reset. |

Bed depth is the median of 4 mm XY column top surfaces in bottle coordinates;
minimum headspace checks the highest grain's bounding top. These are measured
particle surfaces above a thin support, not a false visual powder surface.

**Transfer is not lossless.** `E/transfer_inventory.json` accounts for **9,986
grains in the bottle, 253 in the boat and one on the table beside the bottle**:
`/World/obj_powder_grain_07556`, world XYZ
`[-0.0350851603, -0.0680815354, 0.7556576133] m`, about **0.658 mm** above the
table. No-below-table checks do not mean zero spill.

## Tests and check boundaries

Main's handoff records red-first preparation/localization tests failing for the
missing producer module, then passing. The separate model record documents its
17 new tests red → green. Main's targeted producer suite used
`OPENBLAS_NUM_THREADS=1`; `E/producer_tests.log` records **35 passed in 108.57 s**.
The initial 120 s tool timeout reported no assertion failure; a larger bounded
retry completed. Main also reports Ruff passed for the new files.

- **Task-only isolated SF `make check`: passed.** Actual `E/isolated_check.log`
  records **979 passed, 1 skipped in 277.72 s**, Ruff passed, scaffold/workflow/
  layout/task/scene/export/package smoke checks, suite quality and strict Phase
  10.x passed, ending with `git diff --check`.
- **Shared-workspace SF `make check`: failed at lint.** `E/make_check.log` records
  **994 passed, 1 skipped in 579.89 s**, then two unrelated F401 unused imports
  (`CONTACT_POLICY_VERSION`, `WATER`) in
  `scripts/generate_fehlings_water_bath_r4.py`. This is **not** a whole-workspace
  check pass.

This documentation pass reads existing evidence; it does not rerun the producer,
tests or Isaac. Documentation verification is local link/hash consistency and
whitespace, with the model record preserved byte-for-byte before its appended link.

## Reproduction sequence

The commands below describe the producer → SF → producer → SF sequence, using
an existing model and the r3 base. Select fresh output roots for replay; the
recorded `preparation_r1`, `candidate_r1` and run directories already exist.
`ISAAC45_PYTHON` must name an Isaac Sim 4.5 Python launcher.

```bash
CA=/cpfs/user/zhuzihou/dev/ConvertAsset
SF=/cpfs/user/zhuzihou/dev/scenario-forge
P="$CA/outputs/task09_powder_bottle_r4_20260911"
E="$SF/outputs/task09_powder_bottle_r4_20260911"
B="$CA/outputs/task09_powder_bottle_r3_20260910/candidate_r2"
"$ISAAC45_PYTHON" "$CA/scripts/build_full_powder_scene.py" prepare \
  --base "$B" --model "$P/model_r1/geometry.json" \
  --out "$P/preparation_r1" --count 10240 --radius .0007 --seed 42
"$ISAAC45_PYTHON" "$SF/scripts/validate_task09_powder.py" \
  --root "$P/preparation_r1" --out "$E/preparation_settle" --mode settle --seconds 8
"$ISAAC45_PYTHON" "$CA/scripts/build_full_powder_scene.py" bake \
  --source "$P/preparation_r1" --run "$E/preparation_settle" --out "$P/candidate_r1"
"$ISAAC45_PYTHON" "$SF/scripts/validate_task09_powder.py" \
  --root "$P/candidate_r1" --out "$E/final_settle" --mode settle --seconds 8
"$ISAAC45_PYTHON" "$SF/scripts/validate_task09_powder.py" \
  --root "$P/candidate_r1" --out "$E/final_scoop" --mode scoop --seconds 50
"$ISAAC45_PYTHON" "$SF/scripts/validate_task09_powder.py" \
  --root "$P/candidate_r1" --out "$E/final_calibration" --mode calibration --seconds 43
```

## Standards synchronization and remaining handoff

Apply existing [ASSET-001/002/003](../../../scenario-forge/docs/standards/asset-intake.md),
[STATE-001/002/003/007](../../../scenario-forge/docs/standards/task-state.md) and
[VAL-001/002/003/004/005/006](../../../scenario-forge/docs/standards/validation-and-delivery.md)
within this source/runtime scope. SF's task record identifies standards baseline
`2a61514` and source baseline `bb36b24`. **No general standards change is needed:**
tray height, HCP preparation, fill thresholds and run durations are task-specific
applications of existing ownership, measured-state and evidence-binding rules.
Follow the existing [maintenance workflow](../../../scenario-forge/docs/standards/maintenance.md).
Main owns SF design/operations/evidence synchronization; see the
[SF r4 record](../../../scenario-forge/docs/records/2026-09-11-task09-powder-bottle-r4.md)
and [r4 operations guide](../../../scenario-forge/docs/operations/task09-powder-bottle-r4-guide.md).

Qualification covers this prescribed kinematic fixture, not robot grasping, VR
interaction, repeated arbitrary scoops or real-time operation. Powder density
**1500 kg/m³** is an engineering assumption, with no calibrated true cohesion;
LCD resolution is not physical accuracy. Final video, independent visual review,
ZIP integrity/closure and delivery hashes await main's closeout. The candidate's
runtime pass does not qualify those artifacts.

## Final-delivery follow-up — 2026-09-11

The completed [SF canonical r4 record](../../../scenario-forge/docs/records/2026-09-11-task09-powder-bottle-r4.md)
now documents final delivery; the earlier sections above retain their stage-specific
claims and hashes. Qualified ZIP (relative to SF):
`outputs/task09_powder_bottle_r4_20260911/handoff/task09_powder_bottle_r4.zip`,
**480,811,518 bytes**, SHA-256
`cd30b2fc1e07da1ac13ec70ffaf7a3b860cc7eb0ded8add430fc2977c18fba89`.
Relocated static validation passed with **205 manifest file hashes, 5 USD layers
and 19 assets**, closed dependencies and ZIP CRC. A relocated package-local
**8 s cold settle with inherited PYTHONPATH removed** passed: all **10,240** grains
retained, median depth **10.27848 mm**, median headspace **5.72152 mm**.

Independent fresh reviewer `ses_f70f5580dffeJIkwxd8wlP8P2g` reviewed **22 images**
including a blind pair: **WARN, no blockers**; B (r4) looked fuller with comparable
camera framing. This was selected-image review, not frame-by-frame video review.
Both **1280×800, 30 fps, 50 s** videos passed full decode. The one grain on the
table remains documented; final delivery does **not** establish lossless transfer
or robot/VR qualification. Detailed evidence and remaining visual WARNs are in
the canonical record.
