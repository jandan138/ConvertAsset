# Official KuJiaLe 0036 33-Episode noMDL Pair

This directory stores lightweight repository-side evidence for the official
InteriorAgent / KuJiaLe `kujiale_0036` paired InternNav run completed on
2026-05-25.

Files:

- `original_result.json`: original MDL aggregate InternNav result.
- `nomdl_result.json`: ConvertAsset noMDL aggregate InternNav result.
- `original_episodes.jsonl`: per-episode original MDL metrics.
- `nomdl_episodes.jsonl`: per-episode noMDL metrics.
- `paired_33_summary.json`: paired aggregate summary and claim gate.

The metric runs used `vis_output=False`. Large scene assets, runtime logs,
generated configs, and LMDB outputs remain outside git under:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/internnav/official/internnav_official_val_unseen_20260525
```
