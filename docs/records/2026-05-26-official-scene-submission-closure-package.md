# 2026-05-26 Official-Scene Submission Closure Package

## Scope

Started the official-scene submission-closure package for the next major paper
goal:

- use official InternNav / InteriorAgent KuJiaLe scenes;
- produce multi-scene, multi-run load/render performance statistics;
- keep selected qualitative videos/stills/contact sheets attached to the same
  evidence package;
- finish the final claim-language and citation/provenance audit.

This record does not mark the goal complete. It records the current package
scaffold and the remaining execution gates.

## Current Evidence

Official scene scope:

| Scene | Episode evidence | Required performance conditions |
| --- | ---: | --- |
| `kujiale_0031` | `33` paired episodes | `original_mdl`, `convertasset_nomdl` |
| `kujiale_0036` | `33` paired episodes | `original_mdl`, `convertasset_nomdl` |
| `kujiale_0066` | `33` paired episodes | `original_mdl`, `convertasset_nomdl` |

Existing selected qualitative video package:

| Item | Count |
| --- | ---: |
| mp4 rollout videos | `24` |
| png stills/contact sheets | `76` |
| manifest JSON files | `12` |
| QA-passing videos | `24/24` |

Current package gates:

| Gate | Status |
| --- | --- |
| official scene scope | `ready` |
| selected video package | `ready` |
| multi-run performance statistics | `missing` |
| final claim/citation audit | `missing` |

## Added Package Files

Experiment package:

```text
paper/shared/evidence/experiments/10_official_scene_submission_closure/
```

Generated status artifacts:

```text
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_submission_closure_summary.json
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_plan.json
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_video_evidence_summary.json
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_claim_audit_checklist.json
paper/shared/tables/official_scene_submission_closure_status.csv
paper/shared/tables/tab_official_scene_submission_closure_status.tex
```

## Next Execution Gate

Run the official-scene performance benchmark:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/run_official_scene_performance.py \
  --mode batch \
  --runs 3 \
  --warmup-updates 30
```

Then rebuild the package:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

The required successful run count is `3` fresh-process runs for each of:

- `kujiale_0031` original MDL;
- `kujiale_0031` ConvertAsset noMDL;
- `kujiale_0036` original MDL;
- `kujiale_0036` ConvertAsset noMDL;
- `kujiale_0066` original MDL;
- `kujiale_0066` ConvertAsset noMDL.

That is `18` required successful performance rows before the performance gate
can be marked ready.

The NVIDIA baseline is deliberately marked `not_available` for this official
scene performance package until official-scene NVIDIA converted USDs are
generated and smoke-gated. Do not imply an official-scene NVIDIA performance
comparison before that exists.

## Claim Boundary

Allowed after the package is complete:

```text
We add multi-scene, repeated official KuJiaLe / InteriorAgent load/render
performance statistics, with selected qualitative rollout videos attached for
paper and rebuttal inspection.
```

Not allowed:

```text
We complete a broad GRScenes embodied-navigation benchmark.
We prove all InteriorNav scenes are robust to no-MDL conversion.
The selected videos are quantitative evidence.
NVIDIA official-scene performance has been compared before official-scene
NVIDIA converted scenes exist.
```

## Verification

Executed:

```bash
python -m pytest -q tests/test_official_scene_submission_closure.py
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

Results:

- `6 passed`;
- package builder wrote the current status artifacts;
- `submission_closure_complete=false`, as expected before performance runs and
  final claim/citation audit.
