# Official InteriorNav / KuJiaLe Val-Unseen 99-Episode Pair

This directory stores lightweight combined evidence for the official InteriorAgent / KuJiaLe `val_unseen` InternNav run completed on 2026-05-25.

Scenes: `kujiale_0031`, `kujiale_0036`, `kujiale_0066`. Each scene
contributes 33 official `val_unseen` episodes, for 99 paired
original-vs-noMDL episodes total. Metric runs used `vis_output=False`;
selected video reruns are stored separately as qualitative evidence.

## Quick Result

| Metric | Original | noMDL | noMDL - original | Direction |
| --- | ---: | ---: | ---: | --- |
| `SR` | `0.5253` | `0.4848` | `-0.0404` | lower |
| `SPL` | `0.4739` | `0.4298` | `-0.0441` | lower |
| `NE` | `3.6798` | `3.6306` | `-0.0492` | lower is better |
| `TL` | `6.9754` | `7.0598` | `0.0844` | higher |
| `OS` | `0.6667` | `0.6162` | `-0.0505` | lower |

Per-scene behavior is mixed: 0031 improves on `SR/SPL`, 0036 drops on
`SR/SPL`, and 0066 is roughly flat to slightly better on `SR/SPL/NE` but
longer on `TL`.

## Key Files

- `combined_original_episodes.jsonl` and `combined_nomdl_episodes.jsonl`: per-episode rows with `scene_id` and `split_data_type`.
- `paired_99_summary.json`: paired metric deltas, paired outcome counts, failure transition counts, and official claim gate.
- `per_scene_aggregate_summary.json`: original/noMDL aggregate metrics per scene and overall paired means.
- `paired_episode_transitions.json` and `.csv`: one row per paired trajectory.
- `nomdl_static_gate_0036_0066.json`: static USD gate for the newly converted 0036/0066 noMDL scratch scenes.
- `official_val_unseen_prep_manifest.json`: split/config preparation provenance.
- `interioragent_scene_download_report.json`: official 0036/0066 scene download provenance.

Selected qualitative media lives in:

```text
paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/
```

That directory contains curated compressed mp4s, stills, contact sheets, QA,
and manifests for both the earlier `kujiale0031` selected rerun and the new
combined `kujiale0036_0066` selected rerun.

Combined paired means: original/noMDL `SR=0.5253/0.4848`,
`SPL=0.4739/0.4298`, `NE=3.6798/3.6306`, and `TL=6.9754/7.0598`.

Claim boundary: this completes the local official KuJiaLe `val_unseen` subset, but it is still not a broad GRScenes, R2R, MP3D, or all-InteriorNav benchmark.
