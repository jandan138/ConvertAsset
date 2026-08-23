# 2026-08-24 LABSPIN X8 r3 embedded lid behavior

The r3 package adds `/World/Centrifuge/__device_behavior` without changing the
raw source or r1/r2 packages. An initial standard-node graph was rejected after
Isaac 4.1 `IsaacArticulationState` returned unresolved empty arrays when the
graph lived inside and moved with the articulation subtree. The accepted
fallback is an OmniGraph ScriptNode whose source is stored inside the USD; it
derives the articulation path from its own prim path and requires no external
Python file.

Isaac 4.1 button-drive qualification reached 2.49997 mm and opened the lid to
-1.35987 rad, retaining that angle after button release. Contact press, manual
close/latch and rotor interlock remain explicitly unqualified. Generated output:
`outputs/labspin_x8_task11_r3_20260824/package/`.
