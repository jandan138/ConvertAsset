# Task 11 r5 static context tubes and rack support

## Investigation

Task 11 r4 composed each background tube from separate dynamic body and cap
packages. The 15 mL cap visual was at the tube mouth while its collider remained
near the tube bottom, so reset contact resolution separated the two bodies.
With caps disabled, all tube bodies still dropped about 17.8 mm because the
mixed rack had no socket-bottom support. The r4 rack manifest was still
`static_candidate_pending_isaac41`.

## Producer changes

`build_task11_r5_context_assets.py` produces two closed visual-static context
tubes, a mixed rack r2, and a promoted target-tube r2. Each context tube keeps
the complete source material namespace but has all Physics/PhysX API schemas
removed in the stronger package layer. The rack owns an invisible bottom
support at the authoritative `slot_15ml_r00_c02_inserted_bottom` frame.

## Qualification

Three isolated Isaac Sim 4.1 runs used the real target-tube collider and a
fixed-center prescribed insertion trajectory. Each run finished at about
`z=0.0210 m`, with radial offset about `0.026 mm` and upright error effectively
zero. Both context packages contained no enabled physics schemas. Promotion set
all four producer manifests to `pass` with empty blocked reasons.

The evidence is under
`outputs/task11_r5_context_assets_20260824/evidence/runtime_qualification/`.

## Claim boundary

The evidence covers visual-static background composition, target-slot support,
and prescribed non-robot insertion. It does not cover robot policy or complete
Task 11 success.
