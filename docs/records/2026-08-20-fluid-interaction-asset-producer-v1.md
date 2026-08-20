# Fluid-interaction asset producer v1

ConvertAsset now owns source-bound proposal, collision authoring and Isaac Sim
4.1 qualification for three fluid behaviors: reservoir, conduit and external
surface guide. The CLI entrypoints are `fluid-interaction-propose`,
`fluid-interaction-derive-partitions`, and `fluid-interaction-qualify`.

The fast path uses reviewed source meshes and normalized SDF settings. The
fallback derives package-local axisymmetric convex wall pieces from measured
stations, preserves source visual geometry, and requires a second named review.
Qualification uses three fresh processes (six for a paired surface-guide test),
rejects non-4.1 runtime evidence, and emits no robot or benchmark claim.

Real evidence on 2026-08-20 qualified the open 50 mL centrifuge-tube body with
1.0 static and motion retention, zero structural leakage, and more than 0.88
pour outflow in all three runs. The tested funnel remained blocked because its
7.46 mm bore cannot pass the pinned Task02 recipe's 18 mm effective particle
diameter. The tested conical flask also remained blocked after its first
derived-profile attempt. These are intentional fail-closed outcomes.
The glass-rod paired fixture established no guide effect and therefore returned
`not_applicable` without a qualification claim.
