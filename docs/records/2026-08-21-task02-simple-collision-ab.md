# 2026-08-21 Task 02 graduated-cylinder simple collision A/B

`scripts/compare_task02_graduated_cylinder_collision_routes.py` builds three
isolated variants from the formal r10.3 fill40 transfer fixture. It changes only
the source-vessel collision opinions; the 580-particle state, liquid parameters,
support, visuals, and target asset remain byte-identical.

The visual component SDF route and direct visual Hollow Body
`convexDecomposition` route both lost all 580 particles in their first eight
seconds. The SDF route placed all 580 below the declared floor; direct convex
placed 578 below it. Both were stopped before dynamic testing.

The formal unified control uses a 50-point, 96-triangle, watertight mesh with a
16.5 mm cavity radius. It passed three static runs with zero outside and zero
below-floor particles; settled fill ranged from 38.99% to 39.06%.

`scripts/qualify_task02_collision_vertical_lift.py` then ran the eligible control
through three independent 0.10 m lift/hold/return protocols. Every run retained
all particles, with zero below-floor particles and tracking error below
`1.2e-8 m`.

The result supports retaining the source-measured, 0812-topology-derived closed
proxy. It does not claim that every future remesher must fail, nor robot, pour,
metric, or benchmark success.
