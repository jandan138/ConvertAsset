# 2026-05-25 InternNav Official Val-Unseen 99 Results

## Summary

The official InteriorAgent / KuJiaLe `val_unseen` downstream run is now
complete for all three local official scenes:

| Scene | Episodes | Original SR/SPL | noMDL SR/SPL |
| --- | ---: | ---: | ---: |
| `kujiale_0031` | 33 | `0.5152 / 0.4793` | `0.5758 / 0.4955` |
| `kujiale_0036` | 33 | `0.8182 / 0.7002` | `0.6061 / 0.5503` |
| `kujiale_0066` | 33 | `0.2424 / 0.2422` | `0.2727 / 0.2435` |

Combined paired means over 99 episodes:

| Metric | Original | noMDL | noMDL - original |
| --- | ---: | ---: | ---: |
| `SR` | `0.5253` | `0.4848` | `-0.0404` |
| `SPL` | `0.4739` | `0.4298` | `-0.0441` |
| `NE` | `3.6798` | `3.6306` | `-0.0492` |
| `TL` | `6.9754` | `7.0598` | `0.0844` |
| `OS` | `0.6667` | `0.6162` | `-0.0505` |

Plain interpretation:

- noMDL did not break the official InternNav evaluation pipeline; all paired
  runs completed with `Count=33` per scene and `Count=99` combined.
- The aggregate result is slightly worse on success-style metrics:
  `SR -0.0404`, `SPL -0.0441`, `OS -0.0505`.
- The aggregate final navigation error is slightly better: `NE -0.0492`
  because lower `NE` is better.
- The trajectory length is almost unchanged but slightly longer:
  `TL +0.0844`.
- The direction is scene-dependent: 0031 improves on `SR/SPL`, 0036 drops
  clearly on `SR/SPL`, and 0066 is roughly flat to slightly better on
  `SR/SPL/NE` but longer on `TL`.

The correct conclusion is not "noMDL always preserves behavior." The stronger
and defensible conclusion is: ConvertAsset noMDL can be evaluated end-to-end on
official InteriorNav / KuJiaLe VLN episodes, and the observed downstream effect
is small in aggregate but not uniform across scenes.

## Evidence

Repository-side lightweight evidence:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_kujiale0031_33/
paper/shared/evidence/raw/internnav_vln_downstream/official_kujiale0036_33/
paper/shared/evidence/raw/internnav_vln_downstream/official_kujiale0066_33/
paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/
paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/
```

External heavy workspace:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525
```

Metric runs used `vis_output=False`. Selected-video reruns are stored in the
separate qualitative media package and are not included in the combined
99-episode metric evidence.

Heavy artifacts intentionally left outside git:

| Artifact class | Location |
| --- | --- |
| Official scene downloads | `.../interiornav_data/scene_data/` |
| noMDL scratch scenes | `.../scene_data_nomdl/` |
| Generated configs | `.../configs/` |
| Runtime logs | `.../logs/` |
| InternNav aggregates | `/cpfs/user/zhuzihou/dev/InternNav/logs/official_kujiale*_33_valunseen_*_20260525/` |
| InternNav LMDBs | `/cpfs/user/zhuzihou/dev/InternNav/data/sample_episodes/official_kujiale*_33_valunseen_*_20260525/` |

The repository copy contains only small evidence files needed for paper tables,
audit, and reproducibility notes.

## noMDL Gate

The 0036/0066 noMDL scratch scenes passed the static USD gate:

| Scene | Active MDL shaders | Active MDL source assets | UsdPreviewSurface |
| --- | ---: | ---: | ---: |
| `kujiale_0036` | 0 | 0 | 2439 |
| `kujiale_0066` | 0 | 0 | 1788 |

The 0031 noMDL gate was recorded in the earlier official pair result.

## Per-Scene Details

`kujiale_0031`:

- Original: `SR=0.5152`, `SPL=0.4793`, `NE=3.0653`, `TL=6.0970`.
- noMDL: `SR=0.5758`, `SPL=0.4955`, `NE=3.1024`, `TL=5.8050`.
- Read as: noMDL wins on `SR/SPL/TL`, but slightly loses on `NE`.

`kujiale_0036`:

- Original: `SR=0.8182`, `SPL=0.7002`, `NE=2.0924`, `TL=7.9190`.
- noMDL: `SR=0.6061`, `SPL=0.5503`, `NE=2.8459`, `TL=6.7922`.
- Read as: noMDL clearly loses on `SR/SPL/NE`, while producing shorter
  trajectories.

`kujiale_0066`:

- Original: `SR=0.2424`, `SPL=0.2422`, `NE=5.8817`, `TL=6.9102`.
- noMDL: `SR=0.2727`, `SPL=0.2435`, `NE=4.9436`, `TL=8.5823`.
- Read as: noMDL is slightly better on `SR/SPL/NE`, but trajectories are
  longer.

## Reviewer-Response Mapping

This result helps with these prior reviewer concerns:

| Concern | Status after this run |
| --- | --- |
| "AI task performance is proxy-only" | Partially fixed: there is now a real InternNav / InternVLA-N1 embodied downstream metric run. |
| "Experiment scale is too small" | Partially fixed for the official KuJiaLe route: from one official scene / 33 episodes to three scenes / 99 episodes. |
| "Claims are too broad" | Fixed in documentation: the claim is explicitly scoped to official KuJiaLe val-unseen sanity evidence. |
| "Evidence organization is unclear" | Improved: heavy artifacts live under `convertasset_research`; repo stores bounded evidence plus curated selected-video deliverables. |

Still open:

- no NVIDIA official-tool baseline;
- no per-MDL-effect attribution;
- no broad GRScenes embodied runtime result;
- no 100+ episode / 5+ scene downstream evidence gate.

## Claim Boundary

This result supports the scoped statement:

```text
ConvertAsset noMDL was evaluated on all three local official InteriorNav /
KuJiaLe val_unseen scenes, covering 99 paired InternNav episodes.
```

It still does not support a broad GRScenes, R2R, MP3D, all-InteriorNav, or
general embodied-navigation benchmark claim. It is also one episode short of
the old 100+ episode ACL preference gate and has only three official scenes, so
the paper should present it as a controlled official downstream sanity result.

## Follow-Up Options

Reasonable next steps, in priority order:

1. Add a fourth or fifth official scene only if another official split can be
   justified without changing the claim boundary.
2. Return to GRScenes expanded30 runtime only after accepting that it tests a
   different, custom-episode route.
3. Add NVIDIA baseline or material-effect attribution if the paper needs a
   stronger conversion-method comparison rather than more InternNav rows.
