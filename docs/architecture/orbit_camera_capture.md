# Orbit Camera Capture Architecture

## Overview
This document explains the headless orbit capture workflow that produces the interior reference renders. The implementation stitches together two utilities:

1. `convert_asset.cli camera-orbit` synthesizes an animated `UsdGeom.Camera` with time-sampled transforms when the source stage lacks an authored camera track.
2. `scripts/render_with_viewport_capture.py` opens the exported stage inside Isaac Sim, binds the requested camera to a viewport, advances the timeline, and saves each frame to disk.

The pipeline runs completely headless and is resilient to USD stages that only partially implement the standard time-code APIs.

## Major Components
- **Orbit authoring (`convert_asset/camera/orbit.py`):** Calculates fallback intrinsics and orbit positions, writing an animation clip with integer time codes. The CLI wrapper (`convert_asset/cli.py`) exposes parameters such as distance scale, minimum distance, FOV, and frame count.
- **Headless renderer (`scripts/render_with_viewport_capture.py`):** Boots `SimulationApp`, ensures the viewport extension is enabled, loads the stage via `omni.usd.get_context()`, and orchestrates capture.
- **Timeline bridge:** Uses `omni.timeline.get_timeline_interface()` to convert authored time codes into seconds so that the RTX renderer samples the correct transforms per frame.

## Execution Flow
1. **Orbit export:**
   ```bash
   /isaac-sim/python.sh -m convert_asset.cli camera-orbit \
     --usd /path/to/source.usd \
     --output /path/to/orbit_camera.usd \
     --camera-path /World/OrbitCam \
     --frames 10 \
     --fallback-horizontal-fov 68 \
     --fallback-aspect-ratio 1.7777778 \
     --fallback-distance-scale 1.2 \
     --fallback-min-distance 0.8
   ```
   - Loads the original stage, computes the bounding sphere of authored geometry, and produces `/World/OrbitCam` with `xformOp:transform` samples at frames `0..frames-1`.
   - Stores stage metadata such as `timeCodesPerSecond` so the renderer can honor authored pacing.

2. **Headless capture:**
   ```bash
   /isaac-sim/python.sh scripts/render_with_viewport_capture.py \
     --usd-path /path/to/orbit_camera.usd \
     --camera /World/OrbitCam \
     --output-dir /path/to/images \
     --prefix orbit_cli \
     --ext png \
     --headless
   ```
   - Creates `SimulationApp` with `headless=True` and `RayTracedLighting` preset.
   - Enables `omni.kit.viewport` extension if the environment started without UI extensions.
   - Opens the stage through the USD context, blocking on asynchronous loads while maintaining app updates.
   - Resolves start and end frame from the authored stage (falling back to `0` when optional USD APIs are missing).
   - Configures the viewport to render at the requested resolution and binds the camera prim provided via CLI.

3. **Frame stepping:**
   - Retrieves the global timeline interface and calls:
     - `timeline.set_time_codes_per_second(stage.GetTimeCodesPerSecond())` to match authored time units.
     - `timeline.time_code_to_time(code)` to map each integer frame to SimulationApp seconds.
     - `timeline.set_current_time(...)` for each frame in the loop.
   - Associates the USD context with the active timeline (`usd_context.set_timeline(...)`) when available so both subsystems stay in sync.
   - Waits a configurable number of simulation ticks (`--wait-frames`) before capturing to allow the renderer to converge.

4. **Image capture:**
   - Uses `omni.kit.viewport.utility.capture_viewport_to_file` to save PNGs with zero-padded indices.
   - Logs the absolute output path and the time code captured for traceability.

## Key Implementation Details
- **Time-code safety:** Many USD wrappers expose `GetStartTimeCode` / `HasStartTimeCode` conditionally. `_maybe_stage_timecode` guards each call and falls back to `0.0` to keep the capture loop robust.
- **Timeline synchronization:** Directly calling `usd_context.set_time_code` is unsupported in Isaac Sim 4.5. Converting time codes through the timeline API ensures transforms, materials, and other animated properties resolve correctly.
- **Viewport provisioning:** Headless sessions do not guarantee a viewport instance. `_get_viewport` first tries the modern viewport API, then falls back to the legacy interface to guarantee a render target.
- **Load waiting:** Stage loads and extension toggles are asynchronous. The script calls `_wait_frames` (which simply steps the app) while polling `ctx.is_stage_loading()` and `ctx.is_standby()` until the stage is ready.

## Failure Modes & Mitigations
- **Missing viewport extension:** Automatically enables `omni.kit.viewport`. If the extension registry is unreachable, the script emits the failure before rendering.
- **Static frames:** Previously caused by mismatched timeline units. The new timeline-driven stepping resolves this by honoring `timeCodesPerSecond`.
- **Corrupted primvars / missing assets:** These warnings originate from the authored USD stage and are surfaced during capture for separate investigation.

## Verification Checklist
- Visually inspect a subset of the output PNGs (e.g., frames 0000, 0003, 0006, 0009) to confirm the orbit path covers the expected arc.
- Validate file sizes differ across frames to ensure camera movement (a quick heuristic when running remotely).
- Keep a copy of the orbit export and capture command invocations in `docs/changes/orbit_camera_headless.md` for reproducibility.

## Future Enhancements
- Parameterize renderer quality presets or denoiser settings through CLI flags.
- Bundle the two commands into a single automation script or CI task.
- Incorporate regression tests that compare captured images against a golden set using structural similarity metrics.
