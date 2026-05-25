# Official KuJiaLe 0031 33-Episode noMDL Pair

This directory stores repository-side small-file evidence for the official
InteriorAgent / KuJiaLe `kujiale_0031` paired InternNav run completed on
2026-05-25.

Quantitative full-run artifacts:

- `original_result.json`: original MDL aggregate InternNav result.
- `nomdl_result.json`: noMDL aggregate InternNav result.
- `original_episodes.jsonl`: per-episode original MDL metrics.
- `nomdl_episodes.jsonl`: per-episode noMDL metrics.
- `paired_33_summary.json`: paired aggregate summary and claim gate.
- `paired_episode_transitions.json` and `.csv`: per-episode transition table.

Smoke and selected visual rerun artifacts:

- `nomdl_smoke3_result.json`, `nomdl_smoke3_episodes.jsonl`, and
  `paired_smoke3_summary.json`: three-episode noMDL smoke provenance.
- `video_case_manifest_selected6.json`: selected six qualitative rerun cases.
- `video_rerun_manifest_selected6.json`: selected-only video rerun config
  manifest.
- `original_video_selected6_result.json` and
  `nomdl_video_selected6_result.json`: aggregate selected-rerun results.
- `video_asset_manifest_selected6.json`: historical figure, still, video, and
  QA manifest with external source paths.
- `video_basic_qa_selected6.json`: basic OpenCV/nonblank QA for 12 expected
  selected rerun videos.

The selected compressed videos and stills have also been migrated into the
repo-normalized media package:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/
```

Paper figure copies live in `paper/shared/figures/`:

- `fig_internnav_downstream_panel.png`
- `fig_internnav_rollout_stills.png`
- `fig_internnav_rollout_selected6_supp.png`

The authoritative quantitative claim is the full 33-episode pair. The selected
visual rerun is qualitative only because selected-rerun outcomes can differ
from the full metric run.
