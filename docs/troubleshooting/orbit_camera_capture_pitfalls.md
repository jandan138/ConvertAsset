# Orbit Camera Capture Pitfalls Log

This note captures every issue encountered while wiring up the headless orbit capture flow in October 2025. Use it as a checklist before attempting similar runs in new environments.

## Environment Snapshot
- Isaac Sim / Kit 4.5, headless (`SimulationApp(headless=True)`).
- Target stage: `/opt/my_dev/ConvertAsset/asset/test_scene/start_result_navigation_noMDL.usd`.
- Orbit export output: `/opt/my_dev/ConvertAsset/asset/test_scene/orbit_cli_camera.usd`.
- Capture script: `scripts/render_with_viewport_capture.py` (RayTracedLighting preset, 1920×1080).

## Pitfalls and Resolutions

### 1. CLI Orbit Export Fails Outside SimulationApp
- **Symptom:** Running `convert_asset.cli camera-orbit` in a bare Python interpreter hit `ImportError: No module named 'pxr'`.
- **Cause:** Isaac Sim bundles USD/PXR bindings inside the Kit environment.
- **Fix:** Always invoke the CLI through `/isaac-sim/python.sh -m convert_asset.cli ...` so the required extensions are preloaded.

### 2. Stage Lacked Authored Cameras
- **Symptom:** Original scene had no camera prims, making reference renders impossible.
- **Fix:** Implemented fallback orbit synthesis in `convert_asset/camera/orbit.py` with CLI switches for FOV, aspect ratio, distance scaling, and frame count.

### 3. Asynchronous Stage Load Race
- **Symptom:** First capture runs attempted to grab frames before USD finished loading, yielding empty or stale renders.
- **Fix:** Added `_wait_frames` loop while polling `ctx.is_stage_loading()` / `ctx.is_standby()` to guarantee the stage is ready before binding the viewport.

### 4. Viewport Extension Missing in Headless Sessions
- **Symptom:** `capture_viewport_to_file` raised errors because `omni.kit.viewport` was disabled in fast headless boots.
- **Fix:** `_enable_viewport_extension()` now toggles the extension on demand. When the local registry lacks cache entries, the script syncs from `kit/default`, `kit/sdk`, and `kit/community` before proceeding.

### 5. Static Frames Despite Animated Transform
- **Symptom:** Exported PNGs `orbit_cli_0001.png`–`orbit_cli_0009.png` were byte-identical even though the camera prim had time samples.
- **Root Cause:** Timeline advanced by integer seconds, ignoring the stage’s `timeCodesPerSecond` (24). RTX kept sampling the same transform at `t=0`.
- **Fix:** Converted time codes to seconds through `timeline.time_code_to_time(code)` and called `timeline.set_time_codes_per_second(tps)` each run. Frame stepping now matches authored samples.

### 6. Invalid `usd_context.set_time_code` Call
- **Symptom:** Crash with `AttributeError: 'omni.usd._usd.UsdContext' object has no attribute 'set_time_code'`.
- **Fix:** Removed the direct USD-context setter in favor of the timeline interface. Optionally associate the context with the live timeline via `usd_context.set_timeline(...)` when available.

### 7. Frames Captured Before Renderer Converged
- **Symptom:** Early frames appeared noisy when using path-traced presets.
- **Fix:** Added `--wait-frames` (default `2`) to spin the simulation loop before each capture so RTX can settle. Bump this value for heavier scenes.

### 8. Legacy Viewport Fallback Needed
- **Symptom:** In pure headless mode the modern viewport API occasionally fails to create a window, raising `RuntimeError: Failed to acquire viewport`.
- **Fix:** `_get_viewport()` falls back to `omni.kit.viewport_legacy` and constructs a `LegacyViewportWindow` when the new API is unavailable.

### 9. Asset and Primvar Warnings
- **Symptom:** Each capture prints messages such as `Mesh ... has corrupted data in primvar 'normal'` and unresolved material references.
- **Fix:** Warnings originate from the source USD and do not block rendering. Documented them in `docs/changes/orbit_camera_headless.md`; investigate separately if image artifacts become noticeable.

### 10. Extension Registry Reachability
- **Symptom:** Enabling `omni.kit.viewport` triggered `Failed to resolve extension dependencies` when the cache was empty.
- **Fix:** Allow the script to retry after the registry sync completes. When offline, pre-populate the extension cache or vendor a snapshot.

## Recommended Preflight Checklist
1. Launch `SimulationApp` headless once to warm up extension caches.
2. Confirm `timeCodesPerSecond` on the exported orbit stage (expect 24).
3. Validate filesystem permissions for the capture output directory.
4. Tail logs for primvar or material warnings—plan asset fixes if they affect quality.
5. Retain the command history in `docs/changes/orbit_camera_headless.md` for reproducibility.

Keeping this log up to date will minimize the time spent rediscovering environment quirks when the orbit capture pipeline moves to new scenes or machines.
