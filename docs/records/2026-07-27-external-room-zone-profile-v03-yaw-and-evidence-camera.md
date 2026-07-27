# 2026-07-27 External Room Zone Profile v0.3 (Yaw Convention + evidence_camera)

## Why this record exists

Scenario Forge consumed the 3FO4K5C9JD44 facade package successfully
(south_table_b passed eBench/GenManip initial scene + package check), then
requested a v0.3 follow-up: declare the yaw rotation convention, reverify
the sign, add validated evidence cameras, and supply Isaac 4.1 workcell
overlay renders. Their catch was real: the v0.2 `reviewed_yaw_deg: 90`
had no declared convention, and under `usd_z_up_right_handed_ccw` a +90
yaw maps the fixed -x robot offset to +y, landing the Lift2 robot beyond
the north bench row and the wall face.

## Corrections delivered

| Zone | v0.2 | v0.3 | Verification |
|---|---|---|---|
| north_bench_pair_east | yaw 90 (no convention) | **yaw -90**, `usd_z_up_right_handed_ccw` | robot lands (0.088, 1.371) free south-aisle floor; zero shell/furniture collisions at base radius 0.35 m |
| north_bench_pair_west | yaw 90 (no convention) | **yaw -90**, same convention | robot lands (-3.597, 1.371) free floor |
| south_table_b | yaw 0 | yaw 0 (SF-validated) | robot (-1.614, -4.275) free floor |

Each profiled zone gained `evidence_camera`: `position_xyz` /
`target_xyz` (source-composed, robot-equivalent viewpoint),
`frame_convention`, and a sight-line validation (camera and camera->target
segment intersect no room shell or actor geometry).

## Overlay renders (Isaac 4.1)

`zone_profiles/evidence/<zone>_evidence_camera.png` (robot view) and
`<zone>_overview.png` (wide 3/4 view) render the retained room with the
fixed eBench workcell as proxies (navy table at anchor, robot base+tower
at the audited spot, flask and graduated cylinder on the table), proving
room background, robot, table, and vessels compose in one frame. Camera
spots were chosen by free-space + sight-line search against composed
geometry (the central crane rail z>2.22 and the central rack z<1.77 bound
the only valid sight corridor for the east zone).

Render-engineering notes for future agents: omni `set_focal_length`
returned a 10x value in this build (18.0 -> 180 mm telephoto; 1.8 gives a
sane 18 mm FOV), `Xformable.ClearXformOpOrder` can kill the process
silently, and camera objects should be created fresh per shot.

## Claim boundary

Sidecar-only delivery: no raw USD/MDL/mesh/physics/robot/table/vessel/task
pose changes; facade package and visual_static_environment semantics
unchanged; east_bench stays not_applicable.

## Verification

- Yaw sign recomputed from the composer mapping
  `robot = anchor + R(yaw)^-1 * (robot_task - table_task)/scale` and
  audited on composed geometry.
- `python -m pytest tests/ -q` -> `687 passed, 4 skipped`.
