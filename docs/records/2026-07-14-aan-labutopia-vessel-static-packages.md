# 2026-07-14 AAN LabUtopia Vessel Static Packages

> Historical stage record. Its earlier statement that interaction runtime
> qualification was not implemented has been superseded by
> [2026-07-14 AAN LabUtopia Vessel Runtime Qualification](2026-07-14-aan-labutopia-vessel-runtime-qualification.md).
> Use that record and the current manifests for runtime status and final hashes.

## Scope

This record applies to exactly two object scopes from the immutable LabUtopia
source:

| Asset | Source prim |
|---|---|
| Conical bottle | `/World/conical_bottle03` |
| Graduated cylinder | `/World/graduated_cylinder_03` |

The source is
`/cpfs/shared/simulation/zhuzihou/dev/LabUtopia/outputs/usd_asset_packages/lab_001_localized_20260707/lab_001.usd`
with SHA-256
`b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`.
The hash was checked before profile admission and remained unchanged.

## TDD sequence

`tests/test_asset_application_normalizer_labutopia_vessel_profiles.py` was
written before the real profiles. With
`AAN_RUN_REAL_LABUTOPIA_VESSELS=1`, both parameterized cases initially failed
because their interaction profile paths did not exist. After adding the four
source-bound profiles, both tests generated static packages and passed. Later
runtime tests exposed two behaviors that static readback could not detect: an
SDF scene needed GPU physics, and the cylinder SDF cooked a virtual top cap.
Those findings and the final runtime results are recorded in the superseding
runtime-qualification record.

## Profiles

### Interaction

Both current profiles:

- move runtime identity from child `mesh` to the object Xform root;
- use body-local `+Y` as the opening axis;
- use quaternion `[0.7071067811865476, -0.7071067811865475, 0, 0]`
  for opening, grasp, and support frames;
- require root motion of at least 0.05 m plus open-top, stable-support, and
  bilateral gripper-collision runtime gates.

| Asset | Revision | Collider strategy | Opening Y | Grasp Y | Support Y | Profile SHA-256 |
|---|---|---|---:|---:|---:|---|
| Conical bottle | `r1` | Preserve `mesh`; request SDF for gripper, support, and containment | 0.1965674179 | 0.16 | 0.0 | `c700b887cea7c7f0bad34ded178df3e725cc93ef5f30b5af837cf74da81b87c6` |
| Graduated cylinder | `r2` | Disable source-mesh collision; author one bottom plus twelve wall Cubes | 0.2722941904 | 0.14 | 0.0 | `136b2a12db88882f00d5e0e016e5f4661074e02d653a0337b890b10df400725a` |

The cylinder's initial `r1` SDF profile SHA-256 was
`2161e1393a8aeb63e5d58902a23ee5b570854e21c83bc6372e87c16739544fe1`.
It remains represented by the retained `sdf_virtual_cap` iteration evidence;
it is not the final admitted profile.

### Provisional physics

These values are complete simulation candidates, not measured real-world
parameters.

| Asset | Mass kg | COM body-local | Diagonal inertia kg m2 | Profile SHA-256 |
|---|---:|---|---|---|
| Conical bottle | 0.25 | `[0, 0.075, 0]` | `[0.001874, 0.00214, 0.001874]` | `1042b748ec6e3e4a1e19dec5384637d07912a8219aa107fb0ccb46e585b178c3` |
| Graduated cylinder | 0.15 | `[0, 0.136, 0]` | `[0.001097, 0.000343, 0.001097]` | `7bf298de5e8ed014d0f37717539dd4b0aa471a29eee2e2bcd1deb9efd62ce67e` |

Both use identity principal axes and target the interaction-normalized root with
physics-profile relative path `.`.

## Static package evidence

Evidence is under
`docs/records/evidence/2026-07-14-aan-labutopia-vessel-interaction-profile/`.
Each asset has an independent `manifest.json` and self-contained `package/`.

| Asset | Static status | Active rigid body | Collider readback | Prequalification payload SHA-256 | Runtime-tree SHA-256 |
|---|---|---|---|---|---|
| Conical bottle | pass | `/World/conical_bottle03` only | source `mesh` SDF | `277cde9796ae85979ca4cd84b00ca92ed17c25887dd39e95a4e7231e33c167ac` | `c9af6eb83aa2ec685bc987bf14d0ba0fb009988e775644d0c838fb992a6e7f9c` |
| Graduated cylinder | pass | `/World/graduated_cylinder_03` only | source `mesh` disabled; 13 package proxy colliders enabled | `6f8564d9ca073b171f2962cbc386b4c83c549c34818a6a68470401376d607d7c` | `7392a8f21269820fc0adc4dab60489b8004bbab49e39046cf9433304367ba992` |

The current conical package closure contains 41 runtime artifacts; the cylinder closure
contains 34. The package manifest under `evidence/` is excluded from the tree
hash by contract.

## Commands and verification

The initial milestone used `normalize-asset`, target `scenario-forge`, asset
role `dynamic`, both source-bound profiles, and `--gates static`. The current
retained manifests were rebuilt with `--gates static,runtime`; their exact
normalization and conventional-runtime commands are retained in each manifest.

```text
AAN_RUN_REAL_LABUTOPIA_VESSELS=1 ./scripts/isaac_python.sh -m pytest -q \
  tests/test_asset_application_normalizer_labutopia_vessel_profiles.py
# 2 passed
```

The broader AAN regression and changed-file Ruff checks remain part of the
handoff verification.

## Runtime probe boundary: superseded

At the time of this static milestone, `open_top.status` was `declared` and the
root-motion, stable-support, and gripper-collision gates were `not_run`. That
historical limitation is no longer the current package state.

The TDD-backed qualifier now performs cooked aperture, stable support,
root-motion parity, and bilateral gripper-proxy collision probes in Isaac Sim
4.1. Both current packages pass all four probes. Evidence remains under
`package/evidence/`, outside the runtime-tree digest, and failed probes remain
fail-closed. See the
[runtime qualification record](2026-07-14-aan-labutopia-vessel-runtime-qualification.md)
for the report hashes, prequalification/final payload digests, cylinder SDF
failure, compound-proxy revision, and claim boundary.
