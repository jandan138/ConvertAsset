# 2026-05-25 InternNav Official Selected Qualitative Videos

## Context

After the official three-scene KuJiaLe `val_unseen` run reached 99 paired
metric episodes, we added selected qualitative videos for the newly included
`kujiale_0036` and `kujiale_0066` scenes. The storage policy was also changed:
selected qualitative deliverables now live in the repo, while heavy runtime
scratch remains external.

## Repo-Normalized Media Package

Canonical repo media path:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/
```

This package contains:

- `24` compressed selected-rollout mp4 files: `12` for `kujiale0031` and `12`
  for `kujiale0036_0066`;
- start/mid/end stills extracted from each compressed video;
- paired contact sheets under `contact_sheets/`;
- per-group case manifests, selected-rerun result JSONs, QA reports, and asset
  manifests under `manifests/`.

The package size after migration is about `124M`. The largest file is
`18.8M`, so no single selected media file crosses the usual `100M` git-hosting
limit. `.gitattributes` marks these mp4/png files as binary and no-diff.

Do not sync InternNav raw `frames/` directories, LMDBs, runtime logs, generated
configs, scene data, or scratch USD assets into git.

## 0036/0066 Selection

The 0036/0066 selected cases were chosen from the full 99-run per-episode
metrics, not from the later visual rerun outcomes.

| Episode | Scene | Selection type | Full-run original SR | Full-run noMDL SR |
| --- | --- | --- | ---: | ---: |
| `898_898` | `kujiale_0066` | `original_only_success` | `1.0` | `0.0` |
| `919_919` | `kujiale_0066` | `modified_only_success` | `0.0` | `1.0` |
| `895_895` | `kujiale_0066` | `both_failure_divergent` | `0.0` | `0.0` |
| `597_597` | `kujiale_0036` | `both_success_divergent` | `1.0` | `1.0` |
| `891_891` | `kujiale_0066` | `both_failure_neutral` | `0.0` | `0.0` |
| `598_598` | `kujiale_0036` | `both_success_neutral` | `1.0` | `1.0` |

Selected-rerun aggregate metrics:

| Selected rerun | Count | SR | SPL | NE | TL |
| --- | ---: | ---: | ---: | ---: | ---: |
| original | `6` | `0.1667` | `0.1637` | `5.5435` | `9.0561` |
| noMDL | `6` | `0.3333` | `0.2979` | `6.5204` | `7.2966` |

These selected metrics are qualitative context only. The quantitative claim
remains the video-free 99-episode run:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/paired_99_summary.json
```

## Figure Copies

The 0036/0066 contact sheets were also copied into `paper/shared/figures/`:

```text
paper/shared/figures/fig_internnav_rollout_0036_0066_main3.png
paper/shared/figures/fig_internnav_rollout_0036_0066_selected6_supp.png
```

Source-of-truth media and hashes remain in:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/manifests/kujiale0036_0066_video_asset_manifest.json
```

## QA

Both migrated groups passed basic OpenCV/nonblank QA:

| Group | Videos | QA pass |
| --- | ---: | ---: |
| `kujiale0031` | `12` | `12` |
| `kujiale0036_0066` | `12` | `12` |

Checks:

- file exists;
- size is greater than `100000` bytes;
- OpenCV can open the mp4;
- frame count is nonzero;
- sampled start/mid/end frames are nonblank;
- start/mid/end stills were written.

## Claim Boundary

Allowed use:

```text
Selected videos and still frames illustrate qualitative original-vs-noMDL
rollout behavior on official KuJiaLe InternNav episodes.
```

Disallowed use:

- replacing the full 99-episode quantitative metrics;
- claiming deterministic selected-case outcome preservation;
- claiming broad GRScenes, R2R, MP3D, or all-InteriorNav benchmark coverage.
