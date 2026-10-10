# Waterbath producer recovery: native Isaac Sim 4.1 diagnosis

## Scope and inherited evidence

This recovery continues the existing silver bad17/task12 producer work; no GenManip core, robot, action, task weight, runtime cap or B/D/main input is modified. Read `CLAUDE.md`, both full-tester role playbooks, role memory, ownership map, prior bad17 HANDOFF, probe and tests. Local GPU UUID is `GPU-6e398d5c-f441-2e34-490e-112e3e05a09c`, initially 0 MiB used. Only one local heavy Isaac process is allowed.

The inherited 264-cell tube proxy v2 passes bounded cold/lift/controlled-placement scopes, but D full silver mixed17 fails CUDA700 locally and in the root's original remote runtime. Those failures remain authoritative and preserved. A successful 700-prefix or CUDA blocking run cannot establish final engine health.

## Diagnostic and design

First diagnostic uses existing `--skip-contact-sampling`: only the graph's contact-data read/count is replaced by zero. View creation, graph, real PBD, SDK contact observer, 300 warmup and original actions remain enabled; ordinary asynchronous CUDA is used. This is explicitly nondeliverable because the wall guard is bypassed. Command, PID, environment and script hash are retained in `outputs/sciben_waterbath_120hz_20261010/silver_bad17_diagnostic/recovery_no_contact_sampling_700_launch.json` with separate log and output directory. No failure artifact is overwritten.

A subsequent asset candidate replaces the beaker's hollow-body and rolled-rim SDFs with 96 open convex cells: 32 wall sectors, 32 bottom sectors and 32 elliptical rim sectors. Source body measurements are z 0–113.49 mm, outer radius 37.27–38.69 mm, inner radius 35.27–36.69 mm; rim radius 36.69–41.245 mm and z 111.89–115.09 mm. The 32-sector inner chord bound is 0.177 mm. The original eight-vertex convex pouring spout remains enabled and unchanged. Fine PBD walls remain; particle systems explicitly filter only the new rigid proxy shapes, as separately demonstrated by the inherited shape-selective tests. No cavity cap or necessary rigid-contact filter is added.

This is a single collision-representation candidate, not a claim that SDF contacts cause CUDA700. Body mass, COM, inertia, visible meshes, fluid volume and particle attributes are unchanged. The structural build compares 133648 original attributes and validates source dimensions before authoring. Runtime behavior must still be tested.

## Changes and checks

- `scripts/sciben_waterbath_recovery_bath.py`: open beaker convex generation, source-dimension guard, invariant audit and portable delta export.
- `scripts/sciben_silver_bad09_probe.py`: opt-in `--bath-rigid-proxy` for independent producer diagnostics.
- `tests/test_sciben_waterbath_recovery_bath.py`: open-cavity/profile bounds, mass/source/spout preservation, shape-selective filtering assertions.

The two new tests first failed because the helper did not exist. `python -m pytest tests/test_sciben_waterbath_recovery_bath.py tests/test_sciben_silver_bad09_probe.py -q` subsequently passed all 10 tests. Static candidate is under `silver_bad17_diagnostic/recovery_bath_proxy_v1`; its composition audit is structural only.

## Open qualification

Native cold/lift/contact tests for each task, ordinary-CUDA full mixed17 replay, real finger geometry audit, original remote acceptance and all bad-case qualification remain required. Missing successful demonstrations can be marked for recollection but engine errors cannot be waived. No candidate is yet qualified for delivery. No general scene-authoring rule changes are justified by these diagnostic results; existing native clock, conservation, necessary-contact and independent task qualification requirements remain in force. Root should link this record from the relevant operations/record index when integrating; shared indices are outside this agent's write scope.

## Initial recovery result

The nondeliverable contact-sampling bypass completed all 700 requested original actions and 1002 native ticks at 1/120 s, with no reported engine error and unchanged input hashes. This neither proves a contact-read root cause nor qualifies the asset. The next normal-CUDA run restores full sampling and tests only the beaker proxy change with the same 700-action scope. Portable bath delta SHA256 is `c9bb470e5a3ae4f999480d3f0db6aa19127987037d0026be61ca252a72fb450f`; `recovery_bath_proxy_v1_composition_receipt.json` records two task compositions and verifies both particle systems retain all 264 tube plus 96 bath shape targets.
