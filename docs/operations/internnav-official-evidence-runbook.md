# InternNav Official Evidence Runbook

This runbook describes the current preferred path for producing paper evidence
from official InternNav / InteriorNav KuJiaLe scenes.

## When To Use This Route

Use this route when the goal is to test whether ConvertAsset noMDL conversion
changes a real embodied VLN downstream metric while avoiding custom GRScenes
episode-construction confounds.

Prefer this route over GRScenes runtime experiments when:

- the paper needs official public-scene downstream evidence;
- the question is original MDL vs ConvertAsset noMDL under the same episodes;
- metric stability is more important than broad scene diversity;
- video output is not needed for the quantitative run.

Do not use this route to claim a broad GRScenes, R2R, MP3D, or all-InteriorNav
benchmark. The completed 2026-05-25 run covers the local official KuJiaLe
`val_unseen` subset only: three scenes and 99 paired episodes.

## Canonical Workspace

Heavy runtime assets live outside git:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525
```

Lightweight repository evidence lives in:

```text
paper/shared/evidence/raw/internnav_vln_downstream/
```

The important evidence directories are:

| Directory | Purpose |
| --- | --- |
| `official_kujiale0031_33/` | 33-episode original/noMDL pair plus historical selected-rerun manifests |
| `official_kujiale0036_33/` | 33-episode original/noMDL metric pair |
| `official_kujiale0066_33/` | 33-episode original/noMDL metric pair |
| `official_val_unseen_99/` | Combined 3-scene / 99-episode paired metric evidence |
| `official_selected_qualitative_videos/` | Curated repo-resident selected mp4/still/contact-sheet evidence for 0031 and 0036/0066 |

## Metric-Run Rules

- Keep quantitative metric runs video-free: `vis_output=False`.
- Run original scenes before noMDL scenes.
- Use the same official split rows for original and noMDL so per-episode
  pairing is exact.
- Copy official scenes into scratch before noMDL conversion. Do not write
  `_noMDL` outputs into official source directories.
- Store raw logs, generated configs, LMDBs, and scene assets outside git.
- Sync only JSON, JSONL, CSV, YAML, QA reports, small figures, and dated docs.

## Selected Video Rules

- Keep full quantitative metric runs video-free.
- Rerun only selected qualitative cases with `vis_output=True`.
- Keep InternNav raw `video/<path_key>/frames/` directories outside git.
- Sync the curated compressed mp4s, start/mid/end stills, contact sheets, QA,
  and manifests into
  `paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/`.
- Treat selected-video rerun metrics as qualitative context only; the
  `official_val_unseen_99` full-run metrics remain authoritative.

## noMDL Static Gate

Before running InternNav on a noMDL scratch scene, open the USD stage with
Isaac/PXR and record:

- stage opens successfully;
- active MDL shader count is zero;
- active MDL source asset count is zero;
- `UsdPreviewSurface` shader count is greater than zero.

For the 2026-05-25 `kujiale_0036` and `kujiale_0066` run, this gate is stored
at:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/nomdl_static_gate_0036_0066.json
```

## Result Files

For each scene-level pair, keep:

- `original_result.json`
- `nomdl_result.json`
- `original_episodes.jsonl`
- `nomdl_episodes.jsonl`
- `paired_33_summary.json`

For the combined official val-unseen result, keep:

- `combined_original_episodes.jsonl`
- `combined_nomdl_episodes.jsonl`
- `paired_99_summary.json`
- `per_scene_aggregate_summary.json`
- `paired_episode_transitions.json`
- `paired_episode_transitions.csv`

The combined summary adds `official_scene_count` because the generic analyzer's
legacy `scene_count` field expects GRScenes-style `*_usd` path keys. Official
KuJiaLe LMDB keys are trajectory IDs such as `462_462`, so `scene_count=0` is
not meaningful for this route.

## Paper Wording

Allowed wording:

```text
We evaluate ConvertAsset noMDL on all three local official InteriorNav /
KuJiaLe val_unseen scenes, covering 99 paired InternNav episodes.
```

Disallowed wording:

```text
We complete a broad GRScenes embodied-navigation benchmark.
We reproduce R2R/MP3D downstream results.
noMDL preserves every navigation outcome.
noMDL is generally safe for all InteriorNav scenes.
```

The current interpretation is scoped: noMDL completed all paired metric runs,
with a small aggregate SR/SPL drop, a small aggregate NE improvement, and
scene-dependent behavior.
