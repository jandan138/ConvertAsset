# 2026-08-20 GPU-PBD liquid autofill producer

Implemented the source-bound producer used by Scenario Forge's `liquid inspect/add` workflow.
The effective Task 02 r10.3 recipe is hash-pinned, source USD remains unchanged, and all formal
promotion requires three live-`points` Isaac Sim 4.1 cold runs.

During the real Task 02 regression, the first generic detector rejected the production two-ring
`Hollow_Body`. The detector was corrected without relaxing to bbox inference: it now recognizes
two-ring inner/outer wall samples and uniquely selected semantic hollow walls. The same regression
also removed graduation/label meshes from collider generation.

A runtime-version gate correctly blocked three otherwise healthy 4.5 observations. Cross-runtime
environment cleanup was then added so the EOS-managed 4.1 interpreter cannot inherit 4.5 wrapper
paths. This record does not turn the 4.5 observations into 4.1 evidence.

The EOS-managed worker now performs a controlled process exit after durable evidence write.
This avoids an intermittent Isaac Sim 4.1 `unload_all_plugins` teardown segfault without
weakening the version, live-points, retention, fill, drift, or runtime-error gates.
