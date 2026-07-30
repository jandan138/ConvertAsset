# Blender-generated environment admission

Date: 2026-07-30

## Scope

This change admits a Code-as-Room Blender 4.4 source only as
`visual_static_environment`. It does not broaden dynamic admission and does not
add simulator behavior to the source room.

## Reusable behavior

- `source_runtime=blender44` is accepted only for visual-static roles.
- A single source root such as `/Room` can be mounted directly at consumer
  `/World`; the builder does not create `/World/World`.
- The facade preserves source stage meters-per-unit and up-axis metadata.
- A legacy square DomeLight texture can receive a source-bound facade
  `latlong` override. The final Code-as-Room r2 source already authors the
  correct token, so its facade records zero overrides.
- Explicit `.usdc` dependencies remain binary after asset-path rewriting.
- `profile-room-zones` audits both open-floor and complete-assembly replacement
  workspaces. The request may pin the raw producer source hash separately from
  the facade geometry hash.

## Evidence

For `scientific_environment_code_room_example4_v1`:

- raw r2 source SHA-256:
  `b8dd5954a317ec0f7cacad608a0eb154ed6a67cd4c809433de49e4a6231243f3`;
- facade SHA-256:
  `b24683e2210ee8e2a8b29dfac20772ceddb30981a841fbb081ceedbf5a37e0a9`;
- package `asset.usd` SHA-256:
  `c36508887ad8859bde6eea14e957e21b761908ccef87187e40f3047f7f4f7160`;
- dependency closure: five declared local dependencies, zero missing, zero
  remote;
- Isaac 4.1 cold load, render readback, 120-frame step, and two reset cycles:
  pass;
- four requested workspace zones: four profiled, zero not applicable.

The producer USDC, textures, Blender file, and source evidence remain outside
ConvertAsset ownership. The admitted room is static visual context only.
