# Funnel-to-tube live Isaac video evidence

## Goal

Record human-readable evidence that the admitted small-v2 GPU-PBD liquid
passes through the 7 mm funnel throat and is retained by the 15 mL receiver.
The recording must be a live Isaac Sim session rather than an animation made
from previously exported particle positions.

## Implementation

`scripts/record_funnel_tube15_gravity.py` opens the promoted integration
fixture in the pinned EOS-managed Isaac Sim 4.1 runtime. It advances physics at
120 Hz and captures one Isaac sensor-camera RGB frame after every physics step.
Three simulated seconds therefore produce 360 frames, encoded at 30 FPS as a
12-second 4x slow-motion video at 1920 x 1080. Lighting and the neutral backdrop
are authored only in the session layer and have no physics APIs. The package
liquid recipe, collision geometry, particle count, and physics scene remain
unchanged. Intermediate PNG frames are removed after successful MP4 encoding
unless the diagnostic `--keep-frames` flag is used.

Isaac 4.1 generates the isosurface from the `ParticleSystem` and reads its
render material from that prim. The fixture originally bound the liquid
material only to the `ParticleSet`, which left the generated isosurface using a
white fallback. Both video modes therefore repeat the existing material
binding on the `ParticleSystem` in the anonymous recording session. The exact
mode changes no shader parameter. The evidence-blue mode additionally authors
a high-contrast blue shader override in that same anonymous session; neither
mode persists these opinions into the source USD.

The recorder calculates funnel outlet crossings, structural leaks, and final
tube capture from the same live particle positions used during recording. It
also rejects flat gray/black checkpoint frames and records frame-to-frame RGB
change. Isaac 4.1 can terminate the interpreter from `SimulationApp.close()`
before ffmpeg and JSON persistence complete, so the recorder follows the
existing repository video tools: it persists the MP4 and evidence first and
then performs a controlled process exit.

## Results

Both recorded runs used Isaac Sim
`4.1.0-rc.7+4.1.14801.71533b68.gl` and 4,095 particles. Each measured:

- legal funnel outlet ratio: `1.0`;
- tube capture ratio: `0.9921855921855922`;
- structural leak count: `0`;
- hard PhysX/CUDA errors: `0`;
- visual checkpoint QA: `pass`.

The primary high-contrast video and machine-readable evidence are
`evidence/funnel_to_tube_isaac41.mp4` and
`evidence/funnel_to_tube_isaac41.json`. The exact package-material comparison is
`evidence/funnel_to_tube_isaac41_exact_material.mp4` with its adjacent JSON.
The earlier gray-screen and low-contrast attempts are retained only under
`evidence/withdrawn/` and are not deliverables.

## Verification

- `python3 -m pytest -q tests/test_record_funnel_tube15_gravity.py` — 6 passed.
- `scripts/isaac41_python.sh scripts/record_funnel_tube15_gravity.py ...` — pass.
- `ffprobe` confirmed H.264/yuv420p, BT.709, 1920 x 1080, 30 FPS, 360 frames,
  and 12 seconds for both deliverables.
- The recorder decoded frames 0, 15, 30, 60, 120, and 359 from each final MP4;
  both passed flat-frame and motion checks, and the blue version passed its
  explicit blue-pixel gate.
- Local human visual review of decoded MP4 frames confirmed the initial liquid,
  funnel throat flow, receiver entry, and final settling are visible. The blue
  version passed; the exact version passed with lower contrast. This was not an
  independent blind review.

## Claim boundary

This evidence covers live Isaac Sim 4.1 GPU-PBD funnel transport and receiver
capture only. It does not claim robot-policy success, benchmark success, or
generalization to other funnel, receiver, or liquid recipes.
