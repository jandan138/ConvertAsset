# HCI visual-cup physical insert-and-lid-close delivery (r2)

Date: 2026-08-19

## Outcome

The balanced-pair demo now shows two closed 15 mL tubes **physically dropped**
into the rotor's large visual arm-plate cups, then the lid closes over them.
This supersedes the kinematic-placement r1 cuts for acceptance review.

- Short tube package (consumer-authorized Z shrink):
  `outputs/hci_15ml_closed_insert_lid_r2_20260818/package`
  — k_d 0.53 (cap OD 11.045 mm, unchanged), k_h 0.21 (assembled height
  25.1 mm). AAN static + Isaac 4.1 runtime smoke pass.
- Device profile revision (final binding is on the r10 package; see below):
  `outputs/centrifuge_identity_root_r10_cup_colliders/articulation/device_profile_r11_visual_cup_sockets.json`
  — `tube_socket_1` (cup at world (+0.0208, +0.0142)) and `tube_socket_2`
  (its 180° balance partner at (-0.1016, -0.1107) about the measured spin
  center (-0.0404, -0.0482)); inserted targets sit on the measured cup floors
  (z = 0.1281 m). socket_0 frames are untouched; r9 package untouched.
- Qualification (kinematic sweeps, one per socket with the other tube parked;
  final runs against the r10 package):
  `outputs/centrifuge_identity_root_r10_cup_colliders/qualification/socket_{1,2}/report.json`
  — both `status: pass`; 0 rotor contacts on each sweep; `lid_contact_cycle`
  pass with **both** tubes parked at the cup seats (0 tube-lid contacts).
- Demos (Isaac 4.1, 290 frames @ 24 fps each, physical free drops onto
  package-true cup colliders):
  - `outputs/hci_15ml_closed_insert_lid_r2_20260818/demo/hci_15ml_closed_insert_lid_demo.mp4`
  - `outputs/hci_15ml_closed_insert_lid_r2_20260818/demo_topdown/hci_15ml_closed_insert_lid_demo_topdown.mp4`
  Evidence (`demo_evidence.json` in each dir) binds package/profile/report/mp4
  hashes and records the measured seated poses.

## Geometry findings that shaped this revision

- The visually obvious arm-plate holes are **17 mm deep blind cups** (rim
  z≈0.145, floor z≈0.1281). The long r1 tube (41.9 mm) could never seat in
  them lid-closed; the r1 "inserted" probe poses interpenetrated the cup
  floor (hidden below the rim) — caught by visual review, not by the gates.
- The hub-adjacent collar wells (socket_0's family) are ~42-47 mm deep and
  remain the only lid-closable homes for the long tube.
- The closed lid's inner surface above both cups measures z = 0.1569. With
  the cup floor at 0.1281, a 25.1 mm tube seats with cap top 0.1532 — a 3.7 mm
  lid margin, confirmed 0-contact by the lid gate.
- The r9 centrifuge package collides through **box proxies only** (hub + 4
  quad + 4 ring boxes); cup interiors have no colliders, so a free tube falls
  through the visual floors. The first r2 demo bridged this with session-only
  seat discs; the final r10 revision (below) authors the colliders in the
  package. PhysX empirically ignores static discs below ~15 mm radius on this
  host.
- Tubes are kinematic while positioned above the cups, then released
  (`physics:kinematicEnabled` toggled off) into a free 22 mm drop at 1/240 s.
  Both tubes settle upright (quaternion w = 1.0) exactly on the cup floors.

## Claim boundary

Scripted-positioning + physical-drop demonstration on the existing r9
centrifuge package with session-only seat colliders declared above. Not Feishu
Task 10/11, not a robot policy, not real 15 mL physical parity, not
cap-tightening reuse, no benchmark score. The r1 long-tube kinematic cuts and
the r10 profile (socket targets at z=0.105) are abandoned lineages retained
only for audit.

## r10 package revision: package-level cup colliders (final)

The session-seat-disc shim above was superseded the same day by the proper
producer fix: `outputs/centrifuge_identity_root_r10_cup_colliders/package`
(final manifest SHA-256 `59366d2a…78737`, bound to six-gate report
`993740c0…a5c2`). The r10 facade sublayers the r9 facade and adds, per
balanced cup, one 30 mm floor pad (top face on the measured visual cup floor
z=0.1281) and eight wall panels (inner face at the measured 8.5 mm cup wall),
authored in the group_6 local frame. PhysX ignores static discs below ~15 mm
radius on this host, so the pad is wider than the cup mouth and hides inside
the arm plate.

- Chain: `scripts/build_centrifuge_cup_collider_facade_r10.py` →
  normalize-asset (static+runtime gates pass) → five interaction gates →
  benchtop stability → `finalize_articulated_package` (status pass).
- Device profile r11 (`articulation/device_profile_r11_visual_cup_sockets.json`
  in the r10 output root) carries the socket_1/2 frames and is rebound to the
  r10 facade hash; socket_0 frames and the r9 package stay untouched.
- Gate-harness correction: the lid cycle's tube contact reading now uses the
  LID filter channel of the contact matrix; the rotor channel counts the
  expected seat contact once cup floors exist.
- Socket gates on r10 with the short tube: both sockets pass with 0 sweep
  contacts; lid cycle passes with both tubes seated (0 lid contacts).
- The demo recorder defaults to this r10 package and drops the session discs;
  both mp4 cuts were re-recorded against package-true colliders, and both
  tubes measured seated upright (w=1.0) at z=0.1281.

One authoring pitfall is pinned by tests: USDA `matrix4d` text is stored
transposed relative to the effective transform map (Gf prints transposed), so
collider prim matrices are written via a transpose helper, and a test
composes the stored text back to the intended world pose.

## r10v2 revision: legacy proxies hidden (display-only, final)

GUI review showed the r8-era housing/rotor/button/lid proxy cubes as stray
gray plates. `outputs/centrifuge_identity_root_r10v2_proxy_invisible/package`
(final manifest SHA-256 `33f851b1…f876a`, six-gate report `a9655048…d6af1`)
sublayers the r10 facade and marks all 15 legacy proxy prims
`visibility = "invisible"` (`scripts/build_centrifuge_proxy_visibility_facade.py`).
Collision content is unchanged (visibility is a display hint; invisible prims
still collide, as the benchtop pad and cup colliders already proved).

Caveat recorded: hiding proxies shrinks the package's measured visual AABB,
so the mounting contract's `qualified_reset_geometry` was re-measured on the
r10v2 benchtop observation (final extent [0.3727, 0.3500, 0.4449] m, was
[0.3894, 0.3500, 0.4449] with the proxies visible) and rebound in the r11
device profile before re-running the six-gate chain. Socket gates on r10v2
with the short tube: both pass; lid cycle passes with both tubes seated
(0 lid contacts).

## Testing and verification

- `python -m pytest tests/ -q`: 984 passed, 4 skipped.
- Ruff clean on all changed scripts/tests (repository-wide Ruff still reports
  ~75 legacy findings in unrelated historical scripts).
- Gate commands: `python -m scripts.qualify_hci_15ml_closed_insert_lid
  --short-cup-variant --centrifuge-package outputs/centrifuge_identity_root_r10_cup_colliders/package
  --device-profile .../device_profile_r11_visual_cup_sockets.json
  --socket-name tube_socket_N --additional-parked-socket tube_socket_M ...`
  (run under the Isaac 4.1 conda python from the repo root).
- Demo: `python -m scripts.record_hci_15ml_closed_insert_lid_demo [--top-down]`;
  the recorder fails loudly unless each released tube settles upright within
  5 mm of the measured cup floor.
