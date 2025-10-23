# Orbit Camera Headless Capture Notes

## Summary
- Authored fallback orbit heuristics in `convert_asset/camera/orbit.py` and exposed CLI switches in `convert_asset/cli.py` so we can synthesize an orbit when the stage has no authored cameras.
- Hardened `scripts/render_with_viewport_capture.py` for headless Kit by enabling the required viewport extension, waiting on stage loads, and handling SimulationApp timing quirks.
- Updated the render script to tolerate USD stage wrappers that omit `HasStartTimeCode` / `HasEndTimeCode`, fixing the crash observed when loading the exported orbit camera stage.
- Exported a new orbit camera animation via SimulationApp: `/opt/my_dev/ConvertAsset/asset/test_scene/orbit_cli_camera.usd`.
- Captured PNG frames headlessly to `/opt/my_dev/ConvertAsset/asset/test_scene/nomdl_images/orbit_cli` using the exported camera.

## Execution Details
```
/isaac-sim/python.sh -m convert_asset.cli camera-orbit \
  --usd /opt/my_dev/ConvertAsset/asset/test_scene/start_result_navigation_noMDL.usd \
  --output /opt/my_dev/ConvertAsset/asset/test_scene/orbit_cli_camera.usd \
  --camera-path /World/OrbitCam \
  --frames 10 \
  --fallback-horizontal-fov 68 \
  --fallback-aspect-ratio 1.7777778 \
  --fallback-distance-scale 1.2 \
  --fallback-min-distance 0.8

/isaac-sim/python.sh scripts/render_with_viewport_capture.py \
  --usd-path /opt/my_dev/ConvertAsset/asset/test_scene/orbit_cli_camera.usd \
  --camera /World/OrbitCam \
  --output-dir /opt/my_dev/ConvertAsset/asset/test_scene/nomdl_images/orbit_cli \
  --prefix orbit_cli \
  --ext png \
  --headless
```

## Observations
- Frame `orbit_cli_0001.png` matches the target interior framing; see `/opt/my_dev/ConvertAsset/asset/test_scene/nomdl_images/orbit_cli/orbit_cli_0001.png`.
- After wiring the capture loop to the timeline API (`set_current_time` + `time_code_to_time`), frames `orbit_cli_0000.png` through `orbit_cli_0009.png` now differ as expected (file sizes vary), confirming that the orbit transform samples are respected.
- Stage load continues to emit missing asset references and corrupted normal primvar warnings; these are pre-existing issues in the source USD.

## Next Steps
1. Review the new orbit image sequence for any exposure/noise artifacts and confirm it matches the legacy reference.
2. Package the working capture flow (CLI export + headless render command) into documentation or automation as needed.
3. Triage the persistent USD warnings separately if they impact downstream consumers.
