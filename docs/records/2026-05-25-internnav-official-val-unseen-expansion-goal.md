# 2026-05-25 InternNav Official Val-Unseen Expansion Goal

## Context

The current repository has one completed official InteriorAgent / KuJiaLe
paired downstream sanity result:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_kujiale0031_33/
```

That result covers `kujiale_0031` with `33` official `val_unseen` episodes.
The next lowest-risk expansion should stay on InternNav's official InteriorNav
/ KuJiaLe route rather than immediately returning to custom GRScenes episodes.
The reason is attribution: the GRScenes route has already exposed reset,
height-filter, and warm-up compatibility failures that are hard to separate
from material-conversion effects. Official KuJiaLe episodes avoid that custom
episode-construction confound.

## Official Data Inventory

The locally downloaded official InteriorAgent_Nav splits contain:

| Split | Episodes | Unique KuJiaLe scenes |
| --- | ---: | ---: |
| `train` | `649` | `21` |
| `val_seen` | `44` | `18` |
| `val_unseen` | `99` | `3` |

The `val_unseen` split is exactly balanced over three scenes:

| Scene | Episodes | Current status |
| --- | ---: | --- |
| `kujiale_0031` | `33` | completed original/noMDL pair |
| `kujiale_0036` | `33` | not downloaded / not converted / not run |
| `kujiale_0066` | `33` | not downloaded / not converted / not run |

Public references checked on 2026-05-25:

- `https://huggingface.co/datasets/InternRobotics/IROS-2025-Challenge-Nav`
  records InteriorNav trajectory counts, including `val_unseen=99`.
- `https://github.com/InternRobotics/InternNav` describes InternNav as an
  Isaac Sim / Habitat embodied-navigation toolbox with VLN-PE and InteriorNav
  evaluation support.
- `spatialverse/InteriorAgent` hosts the KuJiaLe scene asset directories.

## Storage Budget

User-reported quota at 2026-05-25 15:15:02:

```text
total = 1600.0 GiB
used = 1124.3109893798828 GiB
free = 475.6890106201172 GiB
file quota total = 100000000
file quota used = 2675539
file quota free = 97324461
```

Measured `kujiale_0031` local footprint:

| Item | Size |
| --- | ---: |
| official original scene | `496M` |
| noMDL scratch scene | `596M` |
| ordinary original metric log | `755K` |
| ordinary noMDL metric log | `1.1M` |
| selected original video rerun log | `218M` |
| selected noMDL video rerun log | `221M` |
| selected rerun workspace manifests/assets | `29M` |

Estimated additional footprint for `kujiale_0036` and `kujiale_0066`:

| Scope | Estimated added space |
| --- | ---: |
| metric-only original/noMDL runs | `2.1-2.5 GiB` |
| metric runs plus selected videos | `3.0-4.0 GiB` |
| conservative budget including logs/cache | `6-8 GiB` |

Conclusion: storage is not the bottleneck. The main risks are runtime duration,
scene download integrity, noMDL conversion correctness, and avoiding unbounded
video/frame output.

## External Workspace Layout

The canonical external root for new ConvertAsset research assets is now:

```text
/cpfs/user/zhuzihou/assets/convertasset_research
```

Historical top-level paths under `/cpfs/user/zhuzihou/assets` remain as
compatibility symlinks. New official InternNav expansion outputs should use:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525
```

The layout policy is recorded in
`../operations/research-asset-layout.md` and the migration record is
`2026-05-25-research-asset-layout-normalization.md`.

## Goal

Upgrade the official InternNav downstream evidence from:

```text
1 official KuJiaLe scene / 33 episodes
```

to:

```text
3 official KuJiaLe val_unseen scenes / 99 episodes
```

by completing paired original-vs-noMDL runs for:

- `kujiale_0031` (already done)
- `kujiale_0036`
- `kujiale_0066`

## Execution Plan

1. Download official scene assets for `kujiale_0036` and `kujiale_0066` from
   `spatialverse/InteriorAgent` into the canonical official InteriorNav
   workspace under `convertasset_research/experiments/internnav/official/`.
2. Split the local `val_unseen` JSON into per-scene 33-episode datasets for
   `kujiale_0036` and `kujiale_0066`.
3. Run original-scene baselines first with `vis_output=False`.
4. Gate each scene on:
   - `Count=33`
   - no fatal runtime signature
   - no unresolved evaluation process
   - preferably non-zero `SR` and `SPL`
5. Copy each scene into a noMDL scratch workspace and convert with
   ConvertAsset's no-MDL pipeline.
6. Gate each noMDL scene on static USD checks:
   - stage opens
   - active MDL shader ID count is zero
   - active MDL source asset count is zero
   - UsdPreviewSurface shaders exist
7. Run the noMDL 33-episode evaluations with `vis_output=False`.
8. Extract per-episode LMDB metrics and generate:
   - per-scene paired summaries
   - combined 99-episode paired summary
   - transition tables
   - claim gate report
9. Select a small number of representative cases for video rerun only after
   metric runs are complete.
10. Sync only lightweight repository evidence:
    - JSON / JSONL / CSV summaries
    - QA reports
    - selected contact-sheet figures
    - documentation records

## Claim Boundary

If all three scenes complete, the manuscript can upgrade the current wording
from:

```text
one official KuJiaLe scene sanity check
```

to:

```text
three official InteriorNav / KuJiaLe val_unseen scenes covering 99 paired
episodes
```

This still must not be framed as:

- a broad GRScenes benchmark
- an R2R / MP3D reproduction
- proof of deterministic per-episode preservation
- proof of all-scene downstream robustness

## Completion Update

The 2026-05-25 run completed this goal. `kujiale_0036` and `kujiale_0066`
were downloaded, converted in scratch, statically gated, and evaluated for both
original and noMDL conditions. Combined with the existing `kujiale_0031` pair,
the repository now has 99 paired official `val_unseen` episodes under:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/
```

See `2026-05-25-internnav-official-val-unseen-99-results.md` for the final
numbers and claim boundary.
