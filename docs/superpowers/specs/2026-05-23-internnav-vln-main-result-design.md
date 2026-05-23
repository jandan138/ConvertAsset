# InternNav VLN Main-Result Design

## Goal

Upgrade the current one-episode InternNav/DualVLN smoke run into an ACL
main-result-ready paired downstream benchmark over GRScenes original and
ConvertAsset modified scenes.

## Current Baseline

The repository currently has a real one-episode smoke result under
`paper/shared/evidence/raw/internnav_vln_downstream/`. That result proves the
runtime bridge works, but it is not broad benchmark evidence because it covers
one scene, one episode, and aggregate metrics only.

The main-result benchmark must keep that smoke evidence as provenance and add a
larger paired protocol around it.

## Recommended Approach

Use a three-layer design:

1. **Input and run manifest layer**
   - Select many GRScenes SN episodes from the clean source tree.
   - Pair each episode with the same scene in the ConvertAsset modified tree.
   - Generate InternNav configs with task names derived from the split/profile,
     not hard-coded `mini` names.
   - Keep metric runs video-free by default to save space.

2. **Result and statistics layer**
   - Preserve InternNav aggregate `result.json` files.
   - Extract per-episode metrics from InternNav LMDB outputs for paired
     statistics and failure-case classification.
   - Compute original-vs-modified deltas, paired win/loss counts, paired effect
     sizes, and confidence intervals where applicable.

3. **Video and trajectory layer**
   - Select only a small representative subset for video reruns.
   - Enable InternNav `vis_output` or equivalent trace capture only for those
     selected cases.
   - Produce side-by-side original/modified clips and top-down trajectory plots
     as paper or supplemental artifacts.

This keeps storage bounded while making the final paper evidence stronger.

## Completion Gates

The benchmark is not claimable as an ACL main result until all gates pass:

- At least 30 paired episodes are completed for pilot-main evidence; 100+ paired
  episodes are preferred for a stronger ACL submission.
- At least five distinct scenes are represented; 10+ scenes are preferred.
- Original and modified conditions use the same episode IDs and instructions.
- Aggregate metrics include `SR`, `SPL`, `NE`, `TL`, `OS`, `StR`, `FR`, and
  `Count`.
- Per-episode paired metrics are available for every completed pair.
- Failure cases are classified by condition and paired outcome.
- A video manifest identifies 6-10 representative cases without storing all
  batch frames.
- The ACL paper clearly states whether the result supports degradation,
  behavior preservation, or behavior sensitivity; it must not claim that
  ConvertAsset improves navigation unless the paired evidence proves it.

## Artifact Layout

Repository artifacts:

- `paper/shared/evidence/experiments/07_internnav_vln_downstream/`
  - preparation, collection, statistics, and video-manifest scripts
- `paper/shared/evidence/raw/internnav_vln_downstream/`
  - small JSON/JSONL/YAML evidence files committed to git
- `paper/shared/figures/`
  - final trajectory or metric figures used by the paper
- `docs/records/`
  - dated run records and interpretation notes

External large artifacts:

- `/cpfs/user/zhuzihou/assets/internnav_vln_downstream_work_YYYYMMDD/`
  - datasets, scene links, generated configs, temporary run manifests
- `/cpfs/user/zhuzihou/dev/InternNav/logs/`
  - InternNav logs, LMDB outputs, progress logs, and optional video traces
- `/cpfs/user/zhuzihou/assets/internnav_vln_downstream_videos_YYYYMMDD/`
  - compressed side-by-side clips and source frame caches if needed

## Storage Policy

Metric batch runs must keep `vis_output=False` and `vis_debug=False`. Video runs
must be rerun on selected episodes only. Raw frame directories are temporary;
the paper evidence should keep compressed clips, manifests, and hashes.

## Main Risks

- InternNav aggregate `result.json` is insufficient for paired statistics; the
  LMDB result store must be extracted or the evaluator must emit per-episode
  JSONL.
- InternNav `vis_output=True` may produce large outputs and may require
  additional visualization dependencies.
- If both conditions fail most episodes, the paper story should focus on
  behavior sensitivity, trajectory divergence, and reproducibility risk rather
  than success-rate improvement.
- The clean GRScenes source tree must remain read-only. ConvertAsset modified
  scenes must live in a scratch tree.

## Approval State

The user explicitly requested autonomous progress under the using-superpowers
workflow and approved proceeding without repeated questions. This design records
the chosen direction for auditability.
