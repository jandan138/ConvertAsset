# Capless 15 mL tube for the Fehling VR water-bath fixture

## Source and derivation

Source is the existing `centrifuge_tube_15ml_closed` r7 package used by the old
water-bath task. Its hollow tube body and cap are separate meshes. The derived
package disables the complete Cap_Controller subtree and both legacy closed
collision/support proxy groups; it does not merely hide the red cap.

The unchanged hollow body mesh receives an SDF collision (resolution 256,
contact offset 1 mm, rest offset 0). Geometry remains watertight, with no
consumer-side cube plug or scaling. The old entry prim name
`/World/CentrifugeTube15mlClosed` is retained for path compatibility; the new
manifest identity is `fehlings_open_tube15_r1` and the physical vessel is open.

Trimesh volume/mass properties exclude the cap's volume contribution. Nominal
mass becomes about 13.776 g, with body-derived COM/inertia/principal axes.
These are provisional geometry estimates, not measured material parameters or
a calibration of reagent mass. The producer also measures a conservative
axial cavity profile for Scenario Forge's 3 mL visual sample.

## Qualification and scope

`build_fehlings_open_tube.py` builds a source-bound candidate. The separate
promotion command requires three exact-asset/exact-scene water-bath fixtures.
It confirms that only the hollow body mesh remains an active collider, records
the authoritative open-body mass profile, and retains scoped runtime reports.

Qualification covers the published original rack and PBD bath integration in
Isaac 4.5: static rack stability, controlled insertion, 120 s heating fixture,
withdrawal and reset with particle retention. This is not arbitrary robot
grasp qualification, resistance to aggressive rim impacts, internal small-PBD
containment, calibrated chemistry, or a cross-Isaac-version claim.

Output: `outputs/fehlings_open_tube15_r1_20260907/package/`.
Source asset and unrelated worktree changes are preserved. Focused tests and
Ruff cover the added producer commands. Integration scripts and task rendering
remain in Scenario Forge, outside simulator-neutral package layers.

The three published fixture runs passed in Isaac 4.5, with approximately
1.364 mm tube settling in the rack and 969/969 bath particles retained.
Promotion records the exact scene/asset hashes and authoritative open-body
profile; the inherited closed-body profile remains source history, not the
active authority for this derivative. The body mesh is the sole active collider.
