# Scientific Workbench r7 task assets

ConvertAsset admits the source-bound assets used by Scenario Forge r7 tasks 2,
7, and 8 from `实验室资产库.zip`. The admitted package root is
`outputs/scientific_workbench_r7_task_assets_20260813/packages/`.

The 250 mL graduated cylinder, 325 mL beaker, 300 mm glass stirring rod,
15 mL centrifuge-tube body and cap, 150 mm glass test tube, closed context tube,
and source-scale aluminum rack pass static and Isaac Sim 4.1 runtime admission.
Interaction packages also carry passing object-level runtime qualification.

The aluminum rack remains at source scale `k=1.0`. It exposes six authoritative
medium-socket aperture and inserted-bottom frames. Every medium socket has the
same compound support and side-wall proxy layout. The recorded gravity protocol
for medium socket 03 passes dynamic insertion, pair-filtered contact, bottom
arrival, side clearance, and source-integrity gates. This evidence is a fixed
rack/tube protocol, not a robot-policy result.

The 15 mL tube body is referenced from the non-animated body prim and receives
an intentional transparent polymer material binding. Its interaction contract
qualifies support, motion parity, and bilateral gripper collision. It does not
claim a contained-volume probe. The cap has an independent red-polymer material
binding. No threaded joint is present, so downstream task 8 must keep threaded
closure scoring inactive.

The 150 mm tubes used to dress task 7 are context objects in Scenario Forge.
Their qualification covers support, motion, gripper proxy, and the recorded
rack insertion; it does not claim liquid containment. Original source USD files
are unchanged. All collision, mass, material, and frame authoring remains in
source-bound ConvertAsset facades/profiles and packages.
