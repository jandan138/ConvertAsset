# Graduated cylinder round base connector glass v2

Date: 2026-08-19

## Outcome

`graduated_cylinder_250ml_glass_web_standard_v2` is admitted under
`outputs/scientific_workbench_glass_web_standard_20260819/packages/`.
The source USD and the v1 package remain unchanged.

The v1 visual profile omitted the independent round connector mesh between the
hollow body and the hexagonal outer base:

`/World/GraduatedCylinder250ml/Visual/Source/Base_Connector/Cylinder_005`

That mesh therefore retained the producer material
`USD_Translucent_PP_Base_002` and rendered as a cyan plastic ring. The v2
profile adds this exact mesh to the existing webpage-standard
`WebStandardClearBorosilicate` binding set. It now contains six binding targets:
body, closed inner bottom, spout, rim, hexagonal base, and round base connector.

## Admission evidence

- `overall_status: pass` and `blocked_reasons: []`;
- Isaac Sim 4.1 static and runtime gates pass;
- visual material profile and visual preservation fingerprint pass;
- `evidence/visual_material_only_audit.json` passes; and
- composed binding inspection resolves the connector, hexagonal base, and body
  to the same package-owned `WebStandardClearBorosilicate` material.

Only material authoring changed. Geometry, collision, interaction profile,
physics profile, mass, inertia, graduations, and labels are unchanged. This
admission does not claim robot-policy, liquid-transfer, or benchmark success.
