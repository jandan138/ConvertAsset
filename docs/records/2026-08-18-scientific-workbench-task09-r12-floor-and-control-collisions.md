# Scientific Workbench Task 09 r12 floor and oven collision admission

ConvertAsset produced two source-bound inputs for Scenario Forge Task 09 r12.
The original drying-box USD and Code-as-Room source USD were not modified.

The analytical-room floor support is a 6.5 by 5.5 by 0.02 metre static support
at top Z 0.  Its facade contains a visible source-bound Cube only so AAN can
perform render and physical-frame admission.  Scenario Forge hides that
presentation on the consumer wrapper; the Code-as-Room environment remains the
owner of visible floor rendering.  The package passed the six static-support
runtime probes in Isaac Sim 4.1.

An initial diagnostic facade set all twelve articulated oven link meshes to
`convexDecomposition`.  AAN static admission passed, but the Isaac Sim 4.1
cold-load physics cook exceeded the bounded 900-second runtime and was blocked.
That facade is retained as `facade_all_parts_experimental.usda` and is not the
consumer source.

The admitted r12 facade limits `convexDecomposition` to the main door, power
rocker, and upper temperature dial.  These are the three Task 09 controls;
fixed and non-task links preserve their source approximation.  There is no
fallback to `convexHull` on any of the three task controls.  The package passed
AAN load/render/step/reset, door/dial/rocker state cycles, locked-joint
stability, shelf support, and a zero-offset fixed-base floor stability gate,
then received articulated-package promotion.

These results do not prove robot contact, graspability of the 0.7-scale beaker,
complete Task 09 execution, benchmark success, thermal behavior, or calibrated
real-world physical parameters.
