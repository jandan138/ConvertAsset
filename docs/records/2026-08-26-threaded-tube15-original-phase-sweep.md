# Threaded 15 mL colleague USD: original-scale gravity phase sweep

## Question

Determine whether the delivered `shiguan.usd` thread geometry can engage in
Isaac Sim 4.1 under the producer-described protocol: rotate the cap to a
suitable initial phase, then apply no motion control and let gravity seat it.

The source SHA-256 is
`a2bc4b55af223f55c43b8001038990ec30ad08c10ebd632b2859a0ac3d9d4af5`.
This record covers the delivered oversized source only. Its composed tube body
is approximately 1.01 m high, ten times the intended 15 mL dimensions.

## Protocol

- Runtime: pinned EOS-managed Isaac Sim 4.1.
- Source USD, source SDF colliders, four source kinematic clamp cubes and
  source physics scene remain unchanged.
- Cap root starts at `z = 1.104 m` above the thread entrance.
- Initial yaw is authored only in an anonymous session layer.
- After timeline Play, no cap rotation, torque, force, joint, guide or Z
  trajectory is applied; motion is gravity-only.
- Twenty-four independent cold starts cover 0 through 345 degrees in 15-degree
  increments. A 245/250/255/260/265-degree refinement follows.

The original static closed root height (`~1.080 m`) is not the physical stop.
Successful contact settles near `1.074 m`; the measured acceptance band is
therefore `1.075 +/- 0.0051 m`.

## Result

The coarse sweep showed strong phase dependence. Most phases missed the thread
and the cap fell sideways to the ground. Several phases caught temporarily;
only 255 degrees satisfied the final closed band, body stability, radial
alignment and settled-tail gates after the refined classification.

The selected 255-degree phase was repeated in three independent cold starts.
All three produced the same rounded measurements:

- final cap-to-body relative Z: `1.074 m`;
- descent from the entrance: `0.030 m`;
- maximum radial offset: `0.00371 m`;
- tail relative-Z span: `0.0 m`;
- no continuous rotation or Z control after Play;
- no hard PhysX/CUDA errors.

Adjacent 250- and 260-degree controls both missed and fell sideways. This
supports the producer statement that the cap must first be turned to a valid
thread phase; the successful motion is not generic free fall.

## Evidence

- Aggregate: `outputs/threaded_tube15_original_phase_sweep_20260826/phase_sweep_report.json`
- Per-phase observations: adjacent `phases/yaw_*.json`
- Three selected-phase repetitions: adjacent `repeats/yaw255_run_*.json`
- Video: `video/original_thread_yaw255_gravity_only_isaac41.mp4`
- Video SHA-256:
  `f4714b9887f95a4927f2b776a921455991c4b474131985628833514d0f20a013`

Local visual review of decoded frames confirms the cap shell and tube are
visible and the cap moves downward into the threaded region. The white source
material makes the small axial displacement subtle, so the visual verdict is
WARN rather than standalone proof; the numeric phase sweep is the primary
evidence. The visual review was local, not an independent blind review.

## GUI-like slow-rotation follow-up

A second protocol reproduces what an operator sees after opening the source
USD and pressing Play.  The default phase only slides a few millimetres.  From
the thread-entrance start, a GUI-like controller keeps the cap coaxial and
changes yaw at `-15 deg/s`; it never authors a Z trajectory.  In the pinned
Isaac Sim 4.1 run, approximately `5 deg` of commanded yaw unlocks the
phase-sensitive contact and gravity lowers the cap by `30.49 mm` into the
measured closed band.  The final 60-frame tail spans `1.09 mm`.

The supplied cap mesh is an open sleeve: its visual mesh has no centre face at
the top.  For legibility, the follow-up video binds the verified red 15 mL PP
appearance and adds a session-only, visual-only `1.5 mm` closed top.  Neither
override participates in the measured source contact.  The real-scale
candidate builder authors the same closed top under the cap rigid root with a
collider, but that candidate still requires separate interaction
qualification.

Camera readback changes the timing of this unusually phase-sensitive source.
The recorder therefore first measures the uninterrupted PhysX trajectory, then
stops physics and uses the same Isaac renderer to replay those measured poses
at 4x visual slow motion.  This is not a synthetic screw-pitch animation: every
displayed Z position comes from the same-run PhysX trace, while replay prevents
render updates from changing the measurement.

- Evidence JSON:
  `outputs/threaded_tube15_original_slow_manipulator_20260826/video/slow_rotate_video_evidence.json`
- Video:
  `outputs/threaded_tube15_original_slow_manipulator_20260826/video/original_thread_slow_rotate_red_cap_stop_isaac41.mp4`
- Video SHA-256:
  `4facdc5d1e8178909a7a419e930b827caf33b6b4359337da4d28034716f7e7ee`
- Encoded stream: H.264, 1280x720, 30 fps, 200 frames, 6.667 seconds.

Local decoded-frame review passes: the red cap, newly visible closed top,
external tube thread and axial before/after change are identifiable.  This was
a local review rather than an independent blind review.

## Real-scale closed-cap candidate

The corrected-size candidate was rebuilt without overwriting earlier evidence:

`outputs/threaded_tube15_pbd_glass_closed_cap_r2_20260826/`

It retains the source-derived internal/external thread meshes, uses identity
entry transforms, and adds the red PP closed top as a `1.5 mm` thick collider
under `/World/Cap`.  Its measured body height is `101.0 mm`; cap height and
diameter are `18.74 mm` and `20.84 mm`.

This candidate is **blocked**, not promoted.  The first Isaac Sim 4.1 contact
observation remains coaxial and upright with no hard errors, but preload alone
descends `1.19 mm`, driven rotation descends only `1.22 mm`, and reverse
rotation rises only `0.056 mm`.  It therefore does not prove a reversible
pitch-coupled screw at real scale.  Evidence is stored at
`evidence/thread_contact/run_00.json` inside the candidate directory.

## Claim boundary

This result confirms phase-dependent gravity seating for the original
oversized colleague USD in Isaac Sim 4.1. It does not yet qualify the corrected
real-scale package, native pitch-coupled continuous screwing, reverse
unscrewing, passive self-locking, transparent material, PBD containment, robot
policy or benchmark success. The successful original-scale protocols must be
requalified after the body/cap packages are normalized to real 15 mL
dimensions.
