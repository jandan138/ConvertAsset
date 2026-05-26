# 2026-05-26 Official-Scene Submission Closure Package

## Scope

Started the official-scene submission-closure package for the next major paper
goal:

- use official InternNav / InteriorAgent KuJiaLe scenes;
- produce multi-scene, multi-run load/render performance statistics;
- keep selected qualitative videos/stills/contact sheets attached to the same
  evidence package;
- finish the final claim-language and citation/provenance audit.

This record now covers the completed original/noMDL official-scene closure pass.
It does not add an NVIDIA official-scene baseline; that remains out of scope
until matching official-scene NVIDIA converted USDs exist and pass smoke gates.

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
| multi-run performance statistics | `ready` |
| final claim/citation audit | `ready` |

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
paper/shared/evidence/raw/official_scene_submission_closure/official_scene_claim_audit_decision.json
paper/shared/tables/official_scene_submission_closure_status.csv
paper/shared/tables/tab_official_scene_submission_closure_status.tex
paper/shared/tables/official_scene_performance_summary.csv
paper/shared/tables/tab_official_scene_performance_summary.tex
```

## Performance Result

Executed the official-scene performance benchmark:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/run_official_scene_performance.py \
  --mode batch \
  --runs 3 \
  --warmup-updates 30
```

Result:

| Condition | Scenes | Successful runs | Failed runs | Aggregate ready time |
| --- | ---: | ---: | ---: | --- |
| original MDL | `3` | `9` | `0` | `13.95` s, 95% CI `[11.64, 16.28]` |
| ConvertAsset noMDL | `3` | `9` | `0` | `14.12` s, 95% CI `[12.31, 16.24]` |

This supports official-scene loadability/stability evidence with repeated runs
and failure counts. It does **not** support an official-scene noMDL speedup
claim because the ready-time intervals overlap.

Rebuilt the package:

```bash
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

The NVIDIA baseline is deliberately marked `not_available` for this official
scene performance package until official-scene NVIDIA converted USDs are
generated and smoke-gated. Do not imply an official-scene NVIDIA performance
comparison before that exists.

## Claim Boundary

Allowed after the package is complete:

```text
We add multi-scene, repeated official KuJiaLe / InteriorAgent load/render
performance statistics for original MDL and ConvertAsset noMDL scenes, with
failure counts, bootstrap confidence intervals, and selected qualitative
rollout videos attached for paper and rebuttal inspection. On these scenes,
ready-time intervals overlap, so the claim is stability/loadability rather than
speedup.
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
python -m pytest -q tests/test_official_scene_submission_closure.py tests/test_paper_layout.py
python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py
```

Results:

- official benchmark wrote `18` rows with `18` success and `0` failures;
- package builder wrote the updated status and performance tables;
- `submission_closure_complete=true` after loading
  `official_scene_claim_audit_decision.json`.
