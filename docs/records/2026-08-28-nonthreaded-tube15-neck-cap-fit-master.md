# Non-threaded 15 mL neck/cap-fit geometry master

## Investigation

The reviewed legacy asset is
`outputs/task11_r5_context_assets_20260824/target_tube_r2/package/asset.usd`,
entry `/World/CentrifugeTube15mlClosed`. Its 6 mm upper neck and 17.24 mm cap
inner sleeve had only about 0.04 mm axial overlap. Radial fit was already
reasonable: tube outer radius 8.61 mm, cap inner radius 8.86 mm.

## Geometry correction

`scripts/build_nonthreaded_tube15_neck_cap_fit.py` creates a new immutable
master at
`outputs/centrifuge_tube_15ml_nonthreaded_neck_cap_fit_r1_20260828/`.
The tip/cone below 23.2 mm remains fixed. The middle straight band is compressed
and the neck is stretched to 17.24 mm while total body height remains 101 mm.
The cap is seated down so its inner sleeve covers z=83.76..101.00 mm and its
closed top lands near z=102.50 mm.

The transformation is baked into mesh points with normal correction; all
public entry roots remain identity. Body, cap and one-rigid closed assembly
packages are delivered separately with a machine-readable mating profile.
Old r7/r8/context packages are not replaced.

## Qualification and handoff

Three isolated Isaac Sim 4.1 runs pass gravity response, settling, cap-relative
pose invariance and 10 cm fixed-carrier transport. Matched local render review
shows the old perched cap and the corrected sleeve overlap. This was local
human-style QA, not an independent blind review.

The package is a non-threaded geometry master only. A downstream engineer may
add thread geometry only inside the registered neck/sleeve band and must return
the result for new collision and Isaac 4.1 admission. No liquid, robot, task or
benchmark claim is inherited.
