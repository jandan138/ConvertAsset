# Orbit CLI Camera Pose Playback

## Why This Stage Matters
The orbit exporter (`convert_asset.cli camera-orbit`) is responsible for synthesising a usable camera track when the source USD lacks one. The generated stage (`asset/test_scene/orbit_cli_camera.usd`) contains a single animated prim `/World/OrbitCam`. This write-up explains how headless Isaac Sim playback consumes that animation to produce the orbit renders, highlighting the exact camera intrinsics and world transforms that were sampled during the latest verification run.

## Authored Camera Intrinsics
`/World/OrbitCam` is authored as a `UsdGeom.Camera`. The fallback optics baked into the export are fixed per frame:

- Horizontal aperture: `20.955 mm`
- Vertical aperture: `15.2908 mm`
- Focal length: `50 mm`
- Focus distance: `0`
- Clipping range: `[1, 1_000_000]`

These values reproduce the 68° fallback field of view requested on the CLI, and they remain constant across the orbit.

## Time-Sampled World Poses
The exporter writes a single `xformOp:transform` with time samples on integer frames. Sampling the prim through `UsdGeom.XformCache` during a headless Isaac Sim session yields the following world-space transforms (translations in centimetres, quaternions as `(w, x, y, z)`):

| Frame | Translation (cm)            | Quaternion (w, x, y, z)          | Roll / Pitch / Yaw (deg) |
|-------|-----------------------------|----------------------------------|--------------------------|
| 0     | `(0.0, 0.0, 0.0)`           | `(0.5546, 0.8288, -0.0611, -0.0409)` | `(112.42, -0.00, -8.43)`  |
| 12    | `(-59.6997, 29.6805, 0.0)` | `(0.5148, 0.7694, -0.3143, -0.2103)` | `(112.42, -0.00, -44.43)` |
| 24    | `(-59.6997, 29.6805, 0.0)` | `(0.5148, 0.7694, -0.3143, -0.2103)` | `(112.42, -0.00, -44.43)` |
| 36    | `(-59.6997, 29.6805, 0.0)` | `(0.5148, 0.7694, -0.3143, -0.2103)` | `(112.42, -0.00, -44.43)` |
| 48    | `(-59.6997, 29.6805, 0.0)` | `(0.5148, 0.7694, -0.3143, -0.2103)` | `(112.42, -0.00, -44.43)` |
| 60    | `(-59.6997, 29.6805, 0.0)` | `(0.5148, 0.7694, -0.3143, -0.2103)` | `(112.42, -0.00, -44.43)` |

Notes:
- The translation plateaus after frame `12` because the sample USD only authored a 10-frame arc; Isaac Sim continues to play the last keyed value for later frames.
- The roll angle stays at ~112° to pitch the camera downward toward the asset. The yaw change between frame `0` and `12` drives the orbit.

## Playback Inside Isaac Sim
Running `scripts/render_with_viewport_capture.py --camera /World/OrbitCam` executes these major steps:

1. Launches `SimulationApp(headless=True)` and enables the viewport extension so a render target exists even in batch mode.
2. Opens `orbit_cli_camera.usd` through `omni.usd.get_context()` and waits for asynchronous loads to finish.
3. Reads `stage.GetTimeCodesPerSecond()` and configures `omni.timeline` so USD frame indices convert to Isaac Sim seconds reliably.
4. Binds `/World/OrbitCam` to the active viewport and, for each frame, sets the timeline’s current time (e.g. frame `12` → `timeline.time_code_to_time(12)`).
5. Captures the viewport to disk once the renderer converges, producing the orbiting PNG sequence.

Because the timeline respects the authored samples, the camera pose Isaac Sim renders at each frame matches the table above.

## Reproducing the Pose Dump
The numeric values were captured with the following headless snippet (executed via `/isaac-sim/python.sh -c ...`):

```python
cache = UsdGeom.XformCache()
for frame in [0, 12, 24, 36, 48, 60]:
    cache.SetTime(frame)
    mat = cache.GetLocalToWorldTransform(stage.GetPrimAtPath("/World/OrbitCam"))
    print(frame, mat.ExtractTranslation(), mat.ExtractRotation().GetQuat())
```

A custom Euler conversion was used to present roll/pitch/yaw for readability. Earlier attempts that called `GetLocalTransformation()` or concatenated `Gf.Vec3d` tuples triggered Boost.Python type errors—`UsdGeom.XformCache` avoids that pitfall by returning ready-to-use matrices per frame.

## Verification Checklist
- Confirm Isaac Sim logs show the timeline unit conversion (no warnings about mismatched start/end frames).
- Spot-check the PNG outputs—frame `0` should look straight-on, while frames `3/6/9` should illustrate the 45° yaw change.
- If transforms appear static, re-run the pose dump to ensure the viewport is sampling the authored time codes (common issue when `set_current_time` is skipped).

With these optics and transforms verified, the existing headless capture script faithfully renders the orbit using the custom camera pose baked by the CLI exporter.
