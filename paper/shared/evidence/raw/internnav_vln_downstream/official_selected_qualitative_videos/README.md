# Official InternNav Selected Qualitative Videos

This directory stores repo-resident qualitative media for the official
InteriorNav / KuJiaLe InternNav evidence route.

The package is intentionally curated:

- keep compressed selected `mp4` rollouts;
- keep start/mid/end stills extracted from those compressed videos;
- keep paired contact sheets and machine-readable QA manifests;
- do not keep InternNav raw `frames/`, full stdout logs, LMDBs, generated
  configs, scene data, or scratch USD assets here.

Large runtime workspaces remain outside git, but these selected deliverables are
small enough to keep with the paper evidence. The media files are marked
binary in `.gitattributes`.

## Current Groups

| Group | Selected cases | Videos | QA | Main evidence |
| --- | ---: | ---: | --- | --- |
| `kujiale0031` | `6` | `12` | `12/12` pass | `manifests/kujiale0031_video_asset_manifest.json` |
| `kujiale0036_0066` | `6` | `12` | `12/12` pass | `manifests/kujiale0036_0066_video_asset_manifest.json` |

Package-level index:

```text
package_index.json
```

## Layout

```text
videos/<group>/<condition>/<path_key>.mp4
stills/<group>/<group>_<path_key>_<condition>_<start|mid|end>_<frame>.png
contact_sheets/<group>_main3_paired_contact_sheet.png
contact_sheets/<group>_selected6_paired_contact_sheet.png
manifests/<group>_video_case_manifest.json
manifests/<group>_video_rerun_manifest.json
manifests/<group>_original_result.json
manifests/<group>_nomdl_result.json
manifests/<group>_video_basic_qa.json
manifests/<group>_video_asset_manifest.json
```

## Claim Boundary

Use these files for qualitative rollout examples, paper figure candidates, and
rebuttal inspection. Do not use the selected rerun metrics as the quantitative
downstream result. The authoritative quantitative evidence remains:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_val_unseen_99/paired_99_summary.json
```

The selected reruns set `vis_output=True`, so they are slower and can have
selected-case outcomes that differ from the video-free full metric run.
