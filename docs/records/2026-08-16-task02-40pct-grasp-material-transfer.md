# Task 02 40% fill and grasp-material transfer package

Date: 2026-08-16

## Outcome

ConvertAsset now publishes a source-bound graduated-cylinder package that keeps
the previously qualified 0812-style GPU-PBD collision topology and adds only a
package-owned grasp material. That container is composed with the qualified
325 ml beaker and a 580-particle initial state into the Task 02 transfer pair.

The promoted pair is:

```text
outputs/task02_cylinder_to_beaker_gpu_pbd_transfer_grasp_material_20260816_r58/
  final_package/task02_cylinder_to_beaker_gpu_pbd_transfer_pair_r4/
```

Package ID:
`scientific-workbench.task02-cylinder-to-beaker.gpu-pbd-transfer.r4`.

The promoted source container is:

```text
outputs/graduated_cylinder_250ml_gpu_pbd_dynamic_grasp_20260816_r57/
  final_package/graduated_cylinder_250ml_gpu_pbd_static_grasp_material_r6/
```

## Decisions

- Particle-system and particle-material parameters remain the LabUtopia
  `liquid_0812/test.usd` values. Visible volume is increased by particle count,
  not by radius, rest offset, cohesion, viscosity, surface tension, or renderer
  substitutions.
- The frozen state contains 580 particles and targets a settled source fill of
  `0.40 +/- 0.05` of effective cylinder height.
- Liquid rendering remains a single UsdPreviewSurface route. The only visual
  change is the agreed blue color, with opacity 0.34, IOR 1.333 and roughness
  0.02. No volume shader, duplicate particle spheres, or liquid-specific light
  was added.
- The cylinder collision mesh is unchanged from the accepted r8.4 topology: 50
  points and 96 faces. The package adds static friction 1.0, dynamic friction 0.9,
  max friction combine and zero restitution to make the existing surface
  graspable. Scenario Forge must not add a cylinder-specific physics patch.

## Runtime evidence

Three cold prescribed-transfer runs delivered 573, 574 and 573 of 580
particles to the target beaker. Settled fill ratios were 0.3895, 0.3891 and
0.38915. All runs recorded zero spill and zero below-support particles. Mean
rendered rates were 81.15, 83.74 and 70.90 FPS.

The static cylinder package also passed three cold starts before promotion.
The generator, qualifier, promotion and source-bound builder tests cover the
new count/fill contract and material propagation.

## Claim boundary

This package proves static containment and a prescribed kinematic
cylinder-to-beaker transfer. It does not by itself prove robot grasp, a
five-stage robot task, policy success, benchmark success, or a calibrated liquid
volume metric. Those claims belong to the downstream runtime evidence layer.
