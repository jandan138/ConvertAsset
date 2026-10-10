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

## Beaker proxy result and immediate-report diagnostic

The normal-sampling beaker proxy run **FAILS** at action275 (275 actions completed; 578 native ticks; no dt error). Its first error remains `mArtiSolveBlockPartitionFunction`, followed by `artiPropagateImpulses2` CUDA700. Both tube and beaker have no enabled SDF in this candidate: 3745+264 tube convex shapes and 257+96+1 beaker convex shapes remain. Therefore replacing the remaining beaker SDFs is insufficient. This candidate is not promoted and its cold/lift probes are deferred while engine diagnosis takes priority.

`recovery_bath_proxy_v1_prefix700/contact_count_alignment.json` pairs all 575 successful warmup/action snapshots with the same run's event stream. Current-action event counts match graph tensor counts on every frame; offsets minus/plus one action mismatch on 8/9 frames. Positive contact actions267–274 count132,191,224,236,276,238,259,264. The observed maximum is276, below capacity8192;236 was only the coarser trace's final sampled count. Contact points are counted regardless of impulse magnitude.

The next explicitly diagnostic variant uses Isaac4.1's official `ContactReportImmediateAPIDemo.py` API, `get_physx_simulation_interface().get_contact_report()`, and sums exact tube–beaker header point counts at the original graph sampling location. It retains tensor-view creation to isolate the detailed tensor-data read. The heating gate, capacity/negative-count failure behavior and every physical collision remain active. The replacement is self-contained in the USD script and holds no subscription or persistent contact-count state, so no callback/reset/disposal state can leak between episodes. Runtime frame alignment and reset behavior still require validation; pure tests do not establish them. Three new tests passed (13 total), after initially failing for the missing helper. Initial runtime comparison retains the failed beaker-v1 combination to isolate the readout; a separate D tube-v2 plus readout run is needed for minimal-combination qualification.

## No-view readout and sleeping-contact correction

Keeping the tensor contact view while switching its read to immediate reports still failed with the beaker-v1 candidate at action271. Current-frame point counts nevertheless matched independent SDK headers on all571 successful frames. The next minimal combination restored the unchanged D tube-v2/old-beaker physical layers, removed the unused tensor contact-view creation, and used immediate reports. It passed700 actions/1002 native ticks. All1000 warmup/action snapshots matched current-frame SDK counts (187 positive frames, max139); ±1-frame offsets each mismatched160 times. Finger raw overlap was at most0.108/0.079 mm for this run only.

However, the isolated native GPU contact fixture demonstrated that sleeping bodies which remain physically touching produce empty immediate reports **and** zero tensor counts: all1366 sleeping-touch frames in the first1564-tick test were missed. This is a real gate limitation, not an excuse to qualify the stateless replacement. That failed fixture is preserved as `recovery_contact_sleep_reset41`.

The subsequent active-pair counter retains each collider pair's most recent FOUND/PERSIST point count until explicit LOST, and remains self-contained inside the USD script. The reported `wall_contact_count` now means the sum of recent point counts associated with **active contact records, including sleeping contacts**, not newly measured points on every frame. The existing gate only tests whether this value is positive. New state is keyed by stage ID, episode revision and actor paths; a backwards native-step index also resets it. Cleanup clears all added state. There are no new persistent SDK subscriptions. If first initialized after the tube is already asleep and no current matching report establishes contact state, it raises a clear exception into the existing fail-closed heating path. It does not invent a zero or a positive point count.

The pure counter test passed1564 native ticks with no missing sleeping-contact gate. More importantly, the actual embedded wrapper then passed2346 native ticks in three resets:2049 sleeping-touch frames retained positive records, release cleared them, late initialization blocked, episode revision reset, same-epoch native-index rollback and cleanup all passed. No engine errors occurred. This is an isolated box interface/lifecycle fixture, not whole-scene success qualification.

The active/no-view D-v2 candidate then passed700 original actions/1002 native ticks. All1000 frames agreed with the same-frame SDK contact **presence**. There was one point-count difference: action402 reported63 active points versus64 total transient event points because the same spout/Wall_03_04 pair generated FOUND1 followed by LOST0 in that frame. The active record correctly removed it. Maximum count was841. No reaction runtime error occurred, but later physical spilling made PBD invalid and heating stopped; no success claim is made.

This active run also had a real single-frame finger overlap at action146: link7 raw1.512 mm/SDK1.539 mm; link8 raw0.355 mm. This must not be replaced with the earlier run's better geometry result. Final grasp qualification remains open pending original-runtime evidence.

Portable active deltas are `recovery_active_no_view_silver/active_contact_delta.usda` (SHA256 `baeea3fe82c2ce78d11d252b9772bc506f3357d7795179318303f3e7a588d39e`) and `recovery_active_no_view_fehling/active_contact_delta.usda` (SHA256 `366a7c9e520065c302dc0aa2ef03bdd46570e177edb832e427b76959e9f4c372`). Each authors only its task's reaction `inputs:script`, stronger than tube-v2, fluid-only and the original task physical layer at `/World`, then mapped to `/World/_scene`. The rejected beaker-v1 delta is excluded. Root is testing these in a new isolated runtime, never frozen B/D/main.

Two actual-task reaction gate fixtures are in progress. The first silver attempt stopped immediately on a fixture setup error: inherited CCD was enabled on newly prescribed kinematic bodies, which PhysX does not support. The error was not ignored. Its log/report are retained; the corrected isolated fixture explicitly disables CCD only on its prescribed tube/heater bodies, with dynamic bath/liquid and all candidate delivery assets unchanged. Gate fixtures are separate from free-body/cold/lift or robot success qualification. Fourteen pure tests currently pass.
