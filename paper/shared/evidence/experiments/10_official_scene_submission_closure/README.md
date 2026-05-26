# Official-Scene Submission Closure Package

This package tracks the final submission-readiness goal over official
InternNav / InteriorAgent KuJiaLe scenes.

It has three gates:

1. multi-scene, multi-run scene-load/render-performance statistics;
2. selected qualitative video/still/contact-sheet evidence;
3. final claim-language and citation/provenance audit.

The current official scope is the local `val_unseen` trio already used by the
InternNav run:

```text
kujiale_0031
kujiale_0036
kujiale_0066
```

## Current Status

The current builder output records:

- official scene scope: ready;
- selected qualitative video package: ready;
- multi-run official-scene performance statistics: missing;
- final claim/citation audit: missing.

This means the package is started and auditable, but the overall submission
closure goal is not complete.

## Build The Status Package

Run:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

Outputs:

```text
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_submission_closure_summary.json
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_plan.json
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_video_evidence_summary.json
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_claim_audit_checklist.json
paper/shared/tables/official_scene_submission_closure_status.csv
paper/shared/tables/tab_official_scene_submission_closure_status.tex
```

## Run Official-Scene Performance

After building the plan, run the heavy benchmark with Isaac Sim available:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/run_official_scene_performance.py \
  --mode batch \
  --runs 3 \
  --warmup-updates 30
```

This writes:

```text
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_runs.csv
```

Then rebuild the package:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

The required performance gate is 3 successful fresh-process runs for each
official scene under both required conditions:

- `original_mdl`;
- `convertasset_nomdl`.

`nvidia_baseline` is optional and currently marked `not_available` because no
official-scene NVIDIA converted USDs have been generated and smoke-gated yet.
Only add it after official-scene NVIDIA conversions exist.

## Claim Boundary

Use this package to support an official KuJiaLe / InteriorAgent scoped
submission-readiness statement. Do not use it to claim broad GRScenes, R2R,
MP3D, or all-InteriorNav benchmark robustness.

Selected videos are qualitative evidence only. The full metric and performance
runs remain authoritative for quantitative claims.
