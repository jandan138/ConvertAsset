# 2026-08-25 Task11 r7 split-grasp tube

## Decision

The Task11 15 mL target tube now has separate producer-owned interaction roles:

- the lower insertion body keeps `0.05/0.05/min` friction and its existing
  liquid/SDF behavior;
- the red-cap grasp region uses `1.0/0.9/max` friction, a 1 mm contact offset,
  and a 19 x 19 x 18 mm inscribed flat grasp proxy;
- visual geometry, mass, liquid collision, and the original source package are
  unchanged.

The source cap cylinder collider is disabled in favor of the inscribed grasp
proxy because flat Lift2 fingers rolled and slipped on the circular proxy.

## Evidence

`outputs/task11_r7_target_tube_grasp_20260824/package` passed the Isaac Sim 4.1
parallel-jaw close/lift/hold fixture: approximately 0.10 m lift, negligible
vertical loss during the two-second hold, and zero direct tube pose writes.

## Claim boundary

This proves only the fixed producer grasp fixture and preserves the previous
target-slot insertion claim. It does not prove a Lift2 robot policy, the
canonical Task11 sequence, or benchmark success. Scenario Forge must consume
the package without tube-specific collider or material patches.
