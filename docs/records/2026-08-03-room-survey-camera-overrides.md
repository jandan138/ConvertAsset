# Room-survey camera overrides for workspace zones

Workspace-zone profiles may now carry an optional `room_survey` mapping. Each
reviewed view declares a source-composed camera position and target plus any
complete wall Xform roots that an evidence renderer may temporarily hide.

Accepted view names are `room_topdown`, `room_corner_a`, `room_corner_b`, and
`room_entrance_eye_level`. Only the two corner views may declare hidden roots.
Every hidden root must exist in the source stage as an authored `Wall_*` Xform;
anonymous mesh leaves are rejected.

This sidecar is source-bound evidence. It does not edit USD, MDL, meshes,
colliders, physics, or task state. Scenario Forge remains responsible for
mapping source-composed cameras through the final room instance transform and
for runtime framing gates. Automatic Scenario Forge camera placement remains
the default when no override is present.
