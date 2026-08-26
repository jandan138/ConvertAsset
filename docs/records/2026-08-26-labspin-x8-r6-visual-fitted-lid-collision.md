# LABSPIN X8 r6 visual-fitted lid collision

## Investigation

The Task 11 r5 package retained the two coarse lid boxes declared by the intake
URDF.  At the closed rest pose, `main_shell` occupied world Y `0.034 .. 0.284 m`
while the complete visible lid ended near `0.216 m`.  It therefore created an
approximately `68 mm` invisible rear wall and covered too little of the front
lid.  The handle-post proxies were `75 mm` deep while their named visual parts
were approximately `22 mm` deep.

The apparent base asymmetry is not the same defect.  The left and right upper
visual shoulders are respectively `38 mm` and `101 mm` thick, and the existing
base proxies match those bounds.  Rebuilding the whole device collision would
discard correct source geometry and add unnecessary regression risk.

## Design and implementation

`scripts/build_labspin_x8_r6_visual_fitted_lid_collision.py` derives a new
package from r5 without changing the raw archive, facade, base/rotor/control
colliders, joints, drives, behavior graph, mass, or inertia.  It replaces only
the lid compound with nine boxes derived from named visual prim bounds in the
`lid_link` frame: top panel, four perimeter groups, handle grip, two handle
posts, and latch tongue.  Every derived bound receives a documented `1 mm`
outward contact allowance.

The package is built candidate-first.  Promotion requires hash-bound collision
audit, rest-pose qualification, contact-driven behavior qualification, and
closed/open overlay review.  `scripts/promote_labspin_x8_r6_visual_fitted_lid_collision.py`
rejects stale evidence and keeps robot/Task 11 claims false.

Output:

`outputs/labspin_x8_task11_r6_visual_fitted_lid_collision_20260826/package/`

## Validation

Isaac Sim 4.1 results:

- closed rest constraint residual: `0 m`;
- reset and ten-step maximum jump: `0 m`;
- OPEN contact travel: `2.50 mm`;
- lid open and held position: `-1.3610 rad`, state `open_hold`;
- spinning-rotor OPEN interlock: pass at approximately `8.0 rad/s`;
- STOP contact and power-off transition: pass;
- closed/open collision overlays: local visual QA pass;
- robot policy and canonical Task 11: not run and false.

Evidence is under `evidence/collision_fit/`, `evidence/rest_pose/`,
`evidence/lid_behavior/`, and `evidence/promotion.json` in the package.  The
overlay review is local rather than an independent blind review.

Code validation:

```text
python -m pytest -q tests/test_labspin_x8_r5_rest_pose.py \
  tests/test_labspin_x8_r6_visual_fitted_lid_collision.py
# 7 passed

python -m ruff check <changed r6 scripts and tests>
# pass
```

## Claim boundary and follow-up

The promoted r6 package proves visual-fitted lid collision and robot-free device
mechanics.  It does not prove Lift2 reachability, tube extraction, canonical
episode completion, robot-policy success, or benchmark success.  Scenario
Forge must consume the package directly and must not add a local centrifuge
physics patch.
