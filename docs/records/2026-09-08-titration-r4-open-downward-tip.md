# Titration station r4: open downward delivery tip

## Investigation and correction

The r3 delivery tip used a solid cone and its lower visual precharge did not
follow an open nozzle lumen. `scripts/build_titration_tip_r4.py` derives a new
package from r3, replacing the visual geometry at the existing
`/World/TitrationStation/Instance/Burette/body_link/Visual/delivery_tip` path.
The prim tree is preserved; the only prim type change is `delivery_tip` from
`Cone` to `Mesh`.

The hollow nozzle narrows downward over 50 mm, from body-local z=-0.23 m to
-0.28 m. Its existing local translation z=-0.25 m remains unchanged; mesh-local
endpoints are +0.02 m and -0.03 m. Top/bottom outer radii are 2.0/0.8 mm and
inner radii are 1.55/0.4 mm. Outer and inner walls connect through annular rims,
leaving both lumen openings clear. The 96-segment mesh has 384 vertices,
consistent face winding and explicit face-varying normals.

Only the affected lower portion of `liquid_precharge` is refitted. It follows
the lumen with 0.05 mm radial clearance and stops 0.2 mm above the outlet at
body-local z=-0.2798 m. The remaining precharge profile, metered column,
materials, controller, joints, colliders and mass are unchanged. This remains
visual precharge, not simulated fluid or additional metered volume.

## Validation and evidence

Package: `outputs/traditional_titration_assets_r4_open_tip_20260908/packages/station`.
The inspected `asset.usd` SHA-256 is
`6b9101c118c2ddbcc2d635c41d8fb1cbdd476e39f1cdc97fe3202dbb5b5502cb`.

- `packages/station/evidence/static_audit.json` reports pass on that SHA:
  downward taper, open lumen, zero precharge vertices outside the lumen,
  identical physical content, unchanged prim paths and local dependency closure.
- `tests/test_titration_tip_r4.py` covers manifold wall edges, outward face
  winding, nozzle endpoints, lumen radii and sampled precharge clearance.
  Implementer validation passed all four focused tests with
  `python -m pytest tests/test_titration_tip_r4.py tests/test_titration_filled_visuals_r3.py -q`.
  Ruff passed for `scripts/build_titration_tip_r4.py`,
  `scripts/finalize_titration_tip_r4.py` and `tests/test_titration_tip_r4.py`.
- At documentation inspection, all three reports already exist at
  `outputs/traditional_titration_assets_r4_open_tip_20260908/runtime/cold_{1,2,3}.json`.
  Each reports `status: pass`, all checks true and the exact SHA above, with
  distinct process IDs. These are Isaac Sim 4.5.0 standalone fixed-base tests
  using prescribed joint positions from
  `scripts/qualify_titration_filled_visuals_r3.py`.
- Runtime checks cover one DOF, endpoint success/window/hold, overshoot
  rejection, fixed-base stability, reset, volume-to-level agreement,
  initial visibility, hidden empty-scale column and persistent lower charge.
- `scripts/finalize_titration_tip_r4.py` promoted the exact asset after checking
  three distinct passing Isaac Sim 4.5.0 processes and rerunning its geometry
  audit. `outputs/traditional_titration_assets_r4_open_tip_20260908/promotion_receipt.json`
  reports `promoted`. Independent documentation verification matched its asset,
  static-audit and three packaged runtime-report hashes; the package manifest
  now reports `overall_status: pass` with no blocked reasons. Packaged reports
  reside at `packages/station/evidence/cold_start_{1,2,3}.json`.

## Delivery limits and follow-up

Runtime reports establish only their standalone prescribed-motion scope;
`robot_policy_success` is false. They do not establish robot manipulation,
fluid dynamics, other runtimes or composed-scene visual acceptance. The
separate downstream evidence is recorded below. The builder
initializes the manifest as `runtime_pending` and deliberately removes inherited
r3 runtime evidence; the separate finalizer binds the new passing reports to
the promoted package.

This is a producer geometry correction under existing asset boundaries, with
no new general package or physics rule. The historical r3 package and record
remain unchanged. This record was prepared by reading the producer, finalizer, focused tests,
prior r3 record and generated reports, independently verifying evidence hashes,
and incorporating the implementer's test/lint handoff. No runtime or test
execution was performed by the writer.


## Downstream Scenario Forge r1.7 evidence

Consumer integration is separate from the producer qualification above.
Scenario Forge reports three passing Isaac Sim 4.5 cold starts bound to scene
SHA-256 `d190860a6641629f4f61e661a8af93c79e6fb55b9e5f070e54a83738f302e132`.
Its physical revision audit retains all 2,579 prim paths, with only
`delivery_tip` changing type from `Cone` to `Mesh`; the five object poses match
the Xinyu ZIP reference. The audit permits those root-placement changes and
reports the remaining physics unchanged.

The consumer handoff reports local review of 21 static macro/full/mid/end
images. `evidence/initial_scene/visual_review.json` records `status: pass` with
`verdict: WARN`: retained room reflections reduce contrast at transparent
glass/clear-liquid boundaries. This was local assistant inspection, not an
independent review, and the images are static snapshots. Consumer
`evidence/repository_checks.json` records `make check` passing with 949 tests
passed and one skipped, plus 18 passing focused tests.

Delivered ZIP in Scenario Forge:
`outputs/scientific_workbench_traditional_acid_base_titration_vr_r1_7_20260908/handoff/scientific_workbench_traditional_acid_base_titration_vr_r1_7.zip`.
SHA-256: `cbaed136cb9bbb545fad35bba93674bf8bcedabc4d92493bd625d047309398ff`.
The writer independently verified that ZIP hash and read the packaged consumer
runtime, physical-revision, pose-reference, visual-review and repository-check
reports. These checks do not extend the evidence to robot-policy success or
other simulator versions.
