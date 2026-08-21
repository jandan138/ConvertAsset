# 2026-08-21 conical flask 90/35 glass warp delivery

Date: 2026-08-21

## Outcome

ConvertAsset delivered the producer side of Scenario Forge request
`scientific_workbench_conical_flask_90x35_glass_warp_20260821`
(`scenario-forge/docs/operations/scientific-workbench-conical-flask-90x35-glass-warp-admission-request.yaml`).

This is a **new** asset. The identity package
`outputs/scientific_workbench_task_assets_20260731/conical_bottle_identity`
was hash-locked and not modified. Facade SHA-256 stayed
`82115bd942c40214fdb2bacc6f4327111b452e67280bb3405b2451ddee6a83b9`.

## Warp baked into mesh points

`scripts/build_conical_flask_90x35_glass_warp.py` loads composed visual points
from the identity facade (not raw LabUtopia), then applies:

```
k_h = 150 / 196.5674179
k_r(z) piecewise-linear:
  z_belly = 0.012295 m  ->  k = 90 / 113.3053223
  z_mouth = 0.195240 m  ->  k = 35 / 49.19089655
(x, y, z) -> (k_r(z)*x, k_r(z)*y, k_h*z)
```

Normals are re-normalized with the warp Jacobian. `k_r` is extrapolated below
the belly (sit-ring lands near 68 mm; 90 mm is belly OD). Root scale stays
identity. `OmniSurface_Glass` is copied from the identity `deps/mdl` tree.

Measured on the baked facade mesh:

| Quantity | Target | Measured |
|---|---|---|
| Belly OD | 90 mm | 90.000 mm |
| Inner mouth | 35 mm | 35.000 mm |
| Height / opening | 150 mm | 150.000 mm |

Provisional mass follows identity r2: scale mass by `mean(k_r)^2 * k_h`; COM z
and frames by `z * k_h`; inertia by the same axisymmetric affine map.

## Package and Isaac 4.1 gates

Output root:
`outputs/scientific_workbench_conical_flask_90x35_glass_warp_20260821/`

- Facade SHA-256: `e312d95bc9db389382125e3b4746e9bd88a0a69bcb00e8abb52567d4d4999ed3`
- Entry prim: `/World/ConicalFlask90x35Warp`
- Asset id: `scientific_workbench_conical_flask_90x35_glass_warp`
- AAN host used kit `pxr`; runtime worker was
  `/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python`
  (not `./scripts/isaac_python.sh`)
- `normalize-asset` overall_status: `pass` (static + Isaac 4.1 runtime smoke)
- Interaction runtime qualification report SHA-256
  `63e77548ff812f96c31dd05f3f866620679a3e918f849ad8f0c41b90b5d5bab5`,
  all four probes pass: `cooked_aperture`, `stable_support`,
  `root_motion_parity`, `bilateral_gripper_proxy_collision`

Four-view DomeLight proofs (HDRI photo-studio DomeLight; glass is invisible on
charcoal-only lighting) live next to the package:

```
four_view/asset/front.png
four_view/asset/left.png
four_view/asset/back.png
four_view/asset/right.png
```

## Claim boundary

Proportion fit toward 90/35/150 mm only. Not a 250 mL volume claim, not GPU-PBD
cavity qualification, not pour success, and not a replacement of
`scientific_workbench_conical_bottle03_dynamic`.
