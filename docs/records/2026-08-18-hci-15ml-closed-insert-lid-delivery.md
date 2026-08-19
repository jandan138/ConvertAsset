# HCI-fit closed 15 mL tube: package, qualification, and Isaac demo delivery

Date: 2026-08-18

> **Superseded by [the r2 physical-cup revision](2026-08-19-hci-15ml-physical-cup-insert-lid.md).**
> The arm-plate holes used here for the demo turned out to be 17 mm shallow
> cups: the long tube could only be "inserted" by interpenetrating the cup
> floor. The r2 revision ships the consumer-authorized short tube and physical
> free drops into the cups. This r1 record stays for audit only.

## Outcome

ConvertAsset delivered the producer side of the Scenario Forge admission
request `scientific_workbench_hci_15ml_closed_insert_lid_20260818`
(`scenario-forge/docs/operations/scientific-workbench-hci-15ml-closed-insert-lid-admission-request.yaml`):

- Package:
  `outputs/hci_15ml_closed_insert_lid_20260818/package`
  (`asset.usd` SHA-256 `cd837ffe5c1a40102fb461b58831c4c0a0c018bff529887907469e95c312cc65`),
  overall AAN status `pass` (static + Isaac 4.1 runtime smoke).
- Qualification report:
  `outputs/hci_15ml_closed_insert_lid_20260818/qualification/report.json`
  (SHA-256 `39b2a3ac1ddfeb6e23103e2336289bd62af457b3dcc71abc51bdda140a57e396`),
  overall `status: pass`; both contract gates pass:
  - `socket_insertion_clearance`: pass, 0 rotor pair-contact samples, bound to
    the new tube asset hash and entry prim `/World/CentrifugeTube15mlClosed`;
  - `lid_contact_cycle`: pass with the closed tube parked at the inserted
    target.
- Scripted-kinematic Isaac 4.1 demo:
  `outputs/hci_15ml_closed_insert_lid_20260818/demo/hci_15ml_closed_insert_lid_demo.mp4`
  (SHA-256 recorded in `demo/demo_evidence.json`), 270 frames at 24 fps,
  sequence `lid_open → tube_insert → lid_close`, RTX sensor-camera readback.
  The admission's `git_commit_forbidden` rule is honoured: the mp4 lives only
  under `outputs/`.
- A `socket_reveal`/`reveal_hold` camera beat between insertion and lid close
  pushes the camera to a steep close-up of socket_0 so the viewer can see the
  tube seated in the rotor hole; socket_0 is the arm-root hole next to the hub
  whose mouth is a raised collar, so it reads poorly from the main oblique
  view. Mesh measurement confirmed the socket is a real vertical channel:
  rim radius ≈7.2 mm at the upper plate, axis within ≈1.2 mm of the profile
  frame, worst-case radial clearance ≈1.6 mm against the baked tube body.
- A second fixed-camera cut keeps the whole sequence in one overhead view:
  `outputs/hci_15ml_closed_insert_lid_20260818/demo_topdown/hci_15ml_closed_insert_lid_demo_topdown.mp4`
  (`--top-down`, `CAMERA_TOPDOWN`; evidence in `demo_topdown/demo_evidence.json`
  with `camera_mode: top_down`). Physics keyframes are identical; only the
  camera is pinned.

## Build: baked non-uniform scale, closed rigid assembly

`scripts/build_hci_15ml_closed_insert_lid_assets.py` bakes the lab-library
`centrifuge_tube_15ml_red_cap.usda` (red cap, closed pose at source frame 1)
into an HCI-fit closed assembly:

- `k_d = 0.53` radial, `k_h = 0.35` height (admission bands 0.50–0.55 /
  0.33–0.37), giving cap OD 11.045 mm (band 10.4–11.5) and assembled height
  41.895 mm (band 39.5–44.3), i.e. 0.7–1.4 mm radial clearance in the r9
  rotor holes (ID 12.5–13.3 mm).
- Scale is baked into mesh `points`/`extent` and child `xformOp:translate`;
  normals are re-normalized under the non-uniform map. The entry prim and all
  `xformOp:scale` ops stay identity.
- The cap `Cap_Controller` timeSamples are stripped and the controller is
  frozen at frame 1: the assembly is one closed rigid body. It is not a
  cap-tightening asset (the source has no helical thread anyway).
- Interaction profile v2 authors body+cap cylinder colliders, bottom-center
  `support` frame and `grasp` frame; physics profile v1 carries
  provisional-geometry mass/inertia scaled by `k_d²·k_h`.
- The raw source USDA is hash-checked before and after the bake; the k=0.365
  glass test-tube hash (`7877f65a…e794`) is explicitly rejected, and the
  provenance manifest records the `forbidden_reuse` list.

Package build (facade in, source-bound package out):

```bash
python scripts/build_hci_15ml_closed_insert_lid_assets.py \
  --out outputs/hci_15ml_closed_insert_lid_20260818

./scripts/isaac_python.sh ./main.py normalize-asset \
  outputs/hci_15ml_closed_insert_lid_20260818/input/facades/centrifuge_tube_15ml_closed_hci_fit/facade.usda \
  --out outputs/hci_15ml_closed_insert_lid_20260818/package \
  --asset-id scientific_workbench_centrifuge_tube_15ml_red_cap_closed_hci_fit \
  --asset-class rigid --asset-role dynamic \
  --source-runtime generic_usd --target-runtime isaac41 \
  --target-benchmark scenario-forge \
  --task-id scientific_workbench.hci_15ml_closed_insert_lid \
  --interaction-profile outputs/hci_15ml_closed_insert_lid_20260818/input/profiles/centrifuge_tube_15ml_closed_hci_fit.interaction.json \
  --physics-profile outputs/hci_15ml_closed_insert_lid_20260818/input/profiles/centrifuge_tube_15ml_closed_hci_fit.physics.json \
  --asset-scope-prim /World/CentrifugeTube15mlClosed \
  --required-prim /World/CentrifugeTube15mlClosed \
  --gates static,runtime \
  --runtime-python /cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python \
  --evidence-out outputs/hci_15ml_closed_insert_lid_20260818/package.manifest.json
```

## Qualification against the r9 HCI centrifuge

`scripts/qualify_hci_15ml_closed_insert_lid.py` binds the new tube package to
`scripts/qualify_centrifuge_task_interactions.py`, which now accepts
`--tube-entry-prim`, `--tube-radius-m`, and `--tube-height-m` so the sweep
report names the delivered collider instead of the legacy k=0.365 test tube.
Runtimes on this host: `/isaac-sim` is 4.5rc, so qualification runs under the
Isaac 4.1 conda env, as a module from the repo root:

```bash
/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python \
  -m scripts.qualify_hci_15ml_closed_insert_lid \
  --device-profile outputs/centrifuge_identity_root_r9_mount_contract_v2/package/articulation/device_profile.json \
  --centrifuge-manifest outputs/centrifuge_identity_root_r9_mount_contract_v2/package.manifest.json \
  --tube-manifest outputs/hci_15ml_closed_insert_lid_20260818/package.manifest.json \
  --out-dir outputs/hci_15ml_closed_insert_lid_20260818/qualification
```

Result: `status: pass` (all five interaction gates, runtime profile isaac41).
The old k=0.365 report was not reused; the new report binds the closed-tube
asset hash.

## Isaac 4.1 demo mp4

`scripts/record_hci_15ml_closed_insert_lid_demo.py` records the contract
sequence in one live headless Isaac 4.1 session (RayTracedLighting):

- Lid is keyframed through the package's own joint (DOF 2) between the
  qualified closed/open bands; the tube is the session-only kinematic probe
  following the device-profile socket frames (`tube_socket_0_aperture` →
  `tube_socket_0_inserted_bottom_parked_root`). No robot policy.
- Phases: closed hold → lid open → open hold → tube slide-in → tube insert →
  inserted hold → socket reveal (camera move) → reveal hold → reveal return →
  lid close → final hold (270 frames, 24 fps, 5 physics substeps of 1/120 s
  per frame).
- Capture uses the `omni.isaac.sensor.Camera` RGBA readback path from
  `convert_asset.render.single` (the same mechanism as the AAN runtime-smoke
  render gate). Frames are encoded with system `ffmpeg` (libx264, yuv420p).

```bash
/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python \
  -m scripts.record_hci_15ml_closed_insert_lid_demo
```

`demo/demo_evidence.json` binds centrifuge/tube package hashes, the device
profile hash, the qualification report hash, and the mp4 hash.

### Recording pitfalls encoded in the script

- Headless viewport capture (`capture_viewport_to_file`) is not viable on
  this host: GLFW never initialises, the first frame shows an empty grid, and
  later frames are stale/black. The sensor-camera readback is the proven
  path.
- The sensor render product lags one render, so each frame applies poses,
  steps physics, then renders twice before the RGBA read.
- Isaac 4.1's single-`Articulation` wrapper has no
  `set_joint_position_targets`; the underlying `ArticulationView` API is used.
- `app.close()` can kill the interpreter before evidence persists, and Kit
  teardown can segfault at process exit; the CLI never calls `close()` and
  ends with `os._exit` after flushing, matching `runtime_smoke.py`.

## Bugs fixed during this delivery

- `build_hci_15ml_closed_insert_lid_assets.py`: the vec3-array rewriter
  searched for `[` from the prefix start, matching the `[]` inside
  `point3f[]`/`float3[]` type names and never touching the payload arrays;
  the search now starts after the prefix. Frozen-cap injection also dropped a
  duplicate `xformOpOrder` line.
- `tests/test_record_hci_15ml_closed_insert_lid_demo.py`: the inserted-target
  hold assertion now starts from the last insert keyframe, not the first.

## Testing

- `python -m pytest tests/ -q`: 954 passed, 4 skipped.
- Focused suites: `test_hci_15ml_closed_insert_lid_assets.py` (6),
  `test_record_hci_15ml_closed_insert_lid_demo.py` (8).
- `python -m ruff check` on all changed scripts/tests: clean.
- `record_hci_15ml_closed_insert_lid_demo --skip-record` re-encodes and
  re-binds evidence with exit code 0.

## Claim boundary

This delivery proves kinematic insert-and-lid-close geometry on the existing
r9 HCI centrifuge package. It does not claim Feishu Task 10/11, robot-policy
success, real 15 mL physical parity, cap-tightening reuse of the scaled tube,
or any benchmark score. The Scenario Forge desktop prototype task package is
explicitly out of scope until this evidence is accepted.
