# 2026-05-25 InternNav Official noMDL Pair Preparation

## Context

This note records the setup state for the controlled paired InternNav downstream
experiment that follows the official KuJiaLe sanity check in
[2026-05-25-internnav-official-sanity.md](2026-05-25-internnav-official-sanity.md).

The experiment intentionally uses the official public InteriorAgent /
KuJiaLe `kujiale_0031` scene and the same `33` `val_unseen` episodes that
already produced a non-zero original-scene baseline:

| Metric | Original official scene |
| --- | ---: |
| `Count` | `33` |
| `SR` | `0.5152` |
| `SPL` | `0.4793` |
| `OS` | `0.8182` |
| `NE` | `3.0653` |
| `TL` | `6.097` |

The purpose is not to reuse the earlier unverified GRScenes attempts. The
purpose is to create a controlled original-vs-noMDL pair on an official scene
where the original baseline is already known to run successfully.

## Prepared Workspace

Scratch root:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525
```

Copied noMDL scene root:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031
```

Original source scene, left unchanged:

```text
/cpfs/user/zhuzihou/assets/internnav_official_sanity_20260525/interiornav_data/scene_data/kujiale_0031/kujiale_0031.usda
```

The scratch scene keeps the original top-level layer as a backup:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031/kujiale_0031_originalMDL.usda
```

The converted top-level layer is:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031/kujiale_0031_noMDL.usda
```

Because InternNav's KuJiaLe loader resolves
`scene_data_dir/<scan>/<scan>.usda`, the scratch entrypoint was replaced with a
copy of the converted layer:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031/kujiale_0031.usda
```

This replacement is limited to the scratch workspace. The official original
download is not modified.

## Conversion

The scene was converted with the ConvertAsset no-MDL pipeline through the Isaac
Sim Python wrapper:

```bash
./scripts/isaac_python.sh ./main.py no-mdl \
  /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031/kujiale_0031.usda \
  --only-new-usd \
  > /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/logs/kujiale_0031_nomdl_conversion.log 2>&1
```

Observed conversion outputs:

| Check | Value |
| --- | ---: |
| Scene directory size | `838M` |
| Paths matching `*_noMDL*` | `180` |
| Converted mesh dependencies | `179` |
| Converted top-level layer | `kujiale_0031_noMDL.usda` |

The conversion log ends with the expected top-level output:

```text
Top-level new file: /cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl/kujiale_0031/kujiale_0031_noMDL.usda
```

## Static USD Verification

The converted scratch entrypoint was opened through the Isaac Sim wrapper and
checked with `pxr` stage traversal.

Verification log:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/logs/kujiale_0031_nomdl_stage_verify.log
```

Recorded values:

| Check | Value |
| --- | ---: |
| Stage opened | `True` |
| Open time | `0.194` seconds |
| Prim count | `23899` |
| Shader count | `14403` |
| `UsdPreviewSurface` shader count | `2062` |
| Active MDL shader ID count | `0` |
| Active MDL source asset count | `0` |
| MDL-named placeholder properties | `2124` |

The textual USD still contains blocked placeholder properties such as
`outputs:mdl:surface = "__noMDL_placeholder__"`. Those placeholders should not
be treated as active MDL materials. The semantic gate for this experiment is
that the opened stage has zero active MDL shader IDs and zero active MDL source
assets, while retaining `UsdPreviewSurface` shader networks.

## InternNav Inputs

The full paired split was copied into the noMDL scratch workspace:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/raw_data/val_unseen_kujiale0031_33/val_unseen_kujiale0031_33.json.gz
```

A three-episode smoke split was also prepared:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/raw_data/val_unseen_kujiale0031_3_smoke/val_unseen_kujiale0031_3_smoke.json.gz
```

Generated configs:

| Purpose | Config | Task name | Split |
| --- | --- | --- | --- |
| Loader/action smoke | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/configs/internvla_n1_kujiale0031_nomdl_smoke3_eval_cfg.py` | `official_kujiale0031_nomdl_smoke3` | `val_unseen_kujiale0031_3_smoke` |
| Full paired run | `/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/configs/internvla_n1_kujiale0031_nomdl_33_eval_cfg.py` | `official_kujiale0031_nomdl_33` | `val_unseen_kujiale0031_33` |

Both configs point `scene_data_dir` at:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl
```

Both configs point `base_data_dir` at:

```text
/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/raw_data
```

The model path remains the original InternNav checkpoint:

```text
/cpfs/user/zhuzihou/dev/InternNav/checkpoints/InternVLA-N1-DualVLN
```

## Loader Validation

The smoke config passed InternNav evaluation config validation and resolved the
expected three path keys:

```text
Evaluation config validation passed!
{'task': 'official_kujiale0031_nomdl_smoke3', 'scene': '/cpfs/user/zhuzihou/assets/internnav_official_nomdl_pair_20260525/scene_data_nomdl', 'split': ['val_unseen_kujiale0031_3_smoke'], 'size': 3, 'first_keys': ['464_464', '463_463', '462_462']}
```

This validated config wiring and episode loading before the downstream runs.
The final noMDL smoke and full paired evaluation results are recorded in
[2026-05-25-internnav-official-nomdl-pair-results.md](2026-05-25-internnav-official-nomdl-pair-results.md).

## Current Status

Completed:

- the official original baseline exists and has `Count=33`, `SR=0.5152`,
  `SPL=0.4793`
- the official `kujiale_0031` scene has been copied into an isolated scratch
  workspace
- the scratch copy has been converted to noMDL
- the scratch InternNav entrypoint now resolves to the converted noMDL layer
- static USD verification opens the stage and finds zero active MDL shader IDs
  and zero active MDL source assets
- noMDL smoke and full configs have been generated
- the smoke config resolves three expected episodes
- the three-episode noMDL smoke evaluation completed through Isaac Sim reset and
  action execution
- the full `33`-episode noMDL evaluation completed with `Count=33`
- paired aggregate and per-episode transition artifacts were generated

Final results:

```text
docs/records/2026-05-25-internnav-official-nomdl-pair-results.md
```

## Claim Boundary

The preparation-stage evidence supports this limited statement:

```text
The official KuJiaLe `kujiale_0031` scene has been noMDL-converted in a
scratch workspace, the converted USD stage opens, and static inspection finds
zero active MDL shader IDs or source assets.
```

The completed downstream evidence is now documented separately:

```text
docs/records/2026-05-25-internnav-official-nomdl-pair-results.md
```

That result supports a narrow paper-facing controlled sanity claim for one
official KuJiaLe scene with `33` episodes. It still does not validate the
earlier unverified GRScenes InternNav runs or prove navigation preservation
across all converted scenes.
