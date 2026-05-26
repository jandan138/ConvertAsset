# 2026-05-26 Paper Story Progress Snapshot

## Purpose

This record summarizes the current paper story after the GRScenes VLM route,
official InternNav / KuJiaLe downstream runs, material-effect NVIDIA baseline,
reviewer-closure package, and official-scene submission-closure package.

It is not a new experiment record. It is the paper-level progress ledger:
what the evidence now supports, what remains bounded, and what should be done
next before the target submission route is finalized.

## Current Story

The paper should no longer be framed as only:

```text
We built an MDL-to-UsdPreviewSurface converter and the converted assets look
similar.
```

The stronger current story is:

```text
Material conversion is a controlled perturbation in synthetic 3D data
pipelines. Visual similarity alone is not enough, so ConvertAsset evaluates
whether no-MDL conversion preserves usable evidence across visual/material
diagnostics, VLM grounding, downstream InternNav sanity checks, and
official-scene load/render stability.
```

For an ACL/ARR route, the defensible framing is:

```text
VLM grounding and embodied-agent data reliability under 3D material
perturbations, with scoped official InternNav sanity evidence.
```

For a broader AI/simulation route, the defensible framing is:

```text
A claim-bounded conversion and evaluation pipeline for Isaac Sim / USD
synthetic assets, including material-effect risk analysis and downstream
sanity checks.
```

The work is now past the early "tool exists" stage. It is in a
submission-closure stage for a scoped story, but it is not a completed broad
embodied benchmark paper.

## Evidence Blocks

### Core Conversion Tool

ConvertAsset provides a composition-preserving MDL-to-UsdPreviewSurface route:
it avoids flattening the USD scene graph, keeps references/payloads/variants as
first-class composition, and writes no-MDL sidecar assets for downstream use.

This supports the method section and the claim that the intervention is a
controlled material conversion rather than an arbitrary scene rewrite.

### Single-Asset Visual And Feature Evidence

The original paper evidence includes single-object Isaac Sim renders and
image/feature metrics. This remains useful as a first visual-fidelity layer,
but it is no longer the main answer to reviewer concerns because reviewers
asked for downstream task impact, broader material effects, and official-tool
baselines.

### GRScenes VLM Grounding Evidence

The GRScenes route now contains:

- a clean 15-pair pilot branch;
- a frozen expanded30 target-centered stress set;
- Gemma4 and Qwen2.5-VL model probes;
- coordinate-only sanity baselines;
- paired bootstrap confidence intervals in the reviewer-closure package.

This supports a scoped VLM-grounding reliability story. It does not support a
broad "all GRScenes VLM robustness" claim because the set is frozen and
target-centered, not a population sample over all scenes and views.

### Official InternNav / KuJiaLe Downstream Evidence

The official InteriorAgent / KuJiaLe route now contains 99 paired `val_unseen`
episodes across three official scenes: `kujiale_0031`, `kujiale_0036`, and
`kujiale_0066`.

This addresses the "proxy-only AI task" concern much better than image-only
metrics. It supports a scoped downstream sanity claim: ConvertAsset noMDL has
been exercised inside a real InternNav / InternVLA-N1 evaluation route over
official scenes and episodes.

It does not support a broad embodied-navigation benchmark claim over all
InteriorNav, GRScenes, R2R, or MP3D.

### Selected Qualitative Videos

The repository contains the selected official qualitative video package:

- 24 compressed rollout videos;
- 76 still/contact-sheet images;
- 12 manifest JSON files;
- 24/24 QA-passing videos.

These are paper-figure and rebuttal-inspection evidence. They should be used to
show concrete cases, not as quantitative evidence.

### Material-Effect And NVIDIA Baseline Evidence

The material-effect package compares three conditions where available:

- original MDL;
- ConvertAsset noMDL;
- NVIDIA Asset Converter preview/bake route, with the current main route using
  the smoke-validated `usd_to_usd_preview` outputs for the selected GRScenes
  pool.

The GRScenes-covered bins are:

- opacity/transparency;
- emission;
- normal/bump;
- displacement/height.

For these four bins, all three conditions have bounded static evidence and
selected qualitative panels. This can be written as a covered-bin comparison,
not as a universal visual-quality win.

Supplemental cases remain claim-bounded:

- clearcoat: ConvertAsset retains the target as a PreviewSurface
  approximation, while the selected NVIDIA case loses the target; this is a
  selected NVIDIA failure case, not a population-level failure rate.
- procedural texture: both ConvertAsset and NVIDIA conversions fail to preserve
  the checker/procedural evidence reliably; this is a limitation or
  investigation case, not a success case.

### Official-Scene Load/Render Stability

The official-scene submission-closure package adds repeated load/render timing
on three official KuJiaLe scenes for original MDL and ConvertAsset noMDL.

Current result:

| Condition | Scenes | Successful runs | Failed runs | Aggregate ready time |
| --- | ---: | ---: | ---: | --- |
| original MDL | 3 | 9 | 0 | 13.95 s, 95% CI [11.64, 16.28] |
| ConvertAsset noMDL | 3 | 9 | 0 | 14.12 s, 95% CI [12.31, 16.24] |

This supports official-scene loadability/stability. It does not support an
official-scene speedup claim because the intervals overlap.

The NVIDIA official-scene baseline is not available until matching
official-scene NVIDIA converted USDs are generated and smoke-gated.

## Reviewer Concern Status

| Reviewer concern | Current status | Plain interpretation |
| --- | --- | --- |
| Only visual/proxy evaluation | Largely improved | We now have VLM grounding and official InternNav downstream sanity evidence. |
| No NVIDIA baseline | Partially fixed | NVIDIA is included for selected material-effect cases, but not for official-scene performance. |
| No material-effect breakdown | Fixed for the selected/risk-matrix scope | Four GRScenes-covered bins are compared; clearcoat/procedural are bounded supplemental cases. |
| Performance evidence too narrow | Partially fixed | Official 3-scene repeated original/noMDL load/render statistics exist, but not broad all-scene or NVIDIA official-scene statistics. |
| Overbroad conversion guidelines | Addressed by claim boundaries | The paper should now use evidence-gated, scoped language. |
| Need qualitative videos | Fixed for selected official cases | The selected 0031/0036/0066 videos are repo-resident and QA-passing. |
| Need automatic recommender | Partially fixed | A rule-based safe-conversion table exists; a learned material-risk classifier remains future work. |

## What Can Be Claimed Now

The paper can claim:

- ConvertAsset implements a composition-preserving no-MDL material conversion
  route for USD / Isaac Sim assets.
- Single-object visual metrics are supplemented by VLM grounding, InternNav
  downstream sanity, material-effect diagnostics, and official-scene
  load/render stability.
- On the GRScenes-covered material-effect bins, original MDL, ConvertAsset
  noMDL, and the NVIDIA baseline can be compared with bounded static and
  selected qualitative evidence.
- Clearcoat and procedural textures are correctly treated as risk cases rather
  than automatic successes.
- Official KuJiaLe `val_unseen` InternNav evidence covers 99 paired episodes
  across three official scenes.
- Official-scene original/noMDL load/render runs succeeded 18/18, with
  overlapping ready-time confidence intervals.

## What Must Not Be Claimed

The paper must not claim:

- broad embodied-navigation benchmark completion;
- all-InteriorNav, all-GRScenes, R2R, or MP3D robustness;
- official-scene noMDL speedup;
- NVIDIA official-scene performance comparison;
- population-level NVIDIA failure rate from the selected clearcoat case;
- procedural texture preservation success;
- selected qualitative videos as quantitative metric evidence;
- learned automatic material-risk prediction beyond the current rule table.

## Current Submission Readiness

The evidence package is now rebuttal/submission-closure level for the current
scoped story.

For ACL/ARR, the paper still needs a final venue-facing rewrite pass:

- foreground VLM grounding reliability and embodied data reliability;
- expand ACL/VLM related work;
- verify venue/citation/provenance requirements;
- make the title, abstract, introduction, and limitations match the bounded
  evidence.

For a broader AI/simulation venue, the remaining optional strengthening work is:

- add NVIDIA official-scene converted USDs and smoke-gated performance numbers
  if a three-way official-scene performance table is desired;
- or broaden material/object diversity if the paper wants stronger
  population-level material-effect claims.

Do not start a new experiment unless it directly supports a missing claim in
the target paper story.

## Recommended Next Goal

The next major goal should be:

```text
Finalize the target-submission manuscript story: perform a venue-specific
writing, citation, and claim-boundary audit that turns the completed evidence
packages into a coherent ACL/ARR-or-AAAI-ready paper draft, without adding
unsupported new claims.
```

Success criteria:

- choose the target route explicitly: ACL/ARR VLM-grounding reliability, or
  broader AI/simulation conversion-evaluation paper;
- update title, abstract, introduction, experiments, discussion, limitations,
  and appendix so the same scoped story is repeated consistently;
- ensure every major claim points to an existing manifest, table, figure, or
  record;
- remove or soften any unsupported broad claims;
- run the paper build and citation/provenance checks for the chosen route.

Optional extension after that:

```text
If the paper needs a three-way official-scene performance comparison, generate
and smoke-gate NVIDIA official-scene conversions for 0031/0036/0066, then rerun
the official-scene performance package.
```

This is useful but not required for the current scoped two-condition
official-scene stability claim.

## Verification

This docs-only snapshot should be verified with:

```bash
rg -n "Paper Story Progress Snapshot|Current Story|Recommended Next Goal" docs/index.md docs/records/README.md docs/records/2026-05-26-paper-story-progress-snapshot.md
git diff --check
```
