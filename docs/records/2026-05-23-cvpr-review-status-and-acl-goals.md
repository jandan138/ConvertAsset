# 2026-05-23 CVPR Review Status And ACL Goals

## Scope

This record updates the paper status after the expanded30 GRScenes material-shift
VLM grounding run was integrated into the ACL 2027 route.

It is a status and target ledger, not a new experimental claim. The purpose is
to keep the workshop-review response, ACL story, and next work aligned before
more writing or experiments happen.

## Source Documents

- `paper/shared/evidence/reviews/2026-05-workshop-official-reviews-raw.md`
- `paper/shared/evidence/reviews/2026-05-workshop-to-aaai27-revision-roadmap.md`
- `paper/venues/acl27/STATUS.md`
- `paper/EXPERIMENT_CHECKLIST.md`

## Current Plain-Language Status

通俗版本：现在论文已经不再是“只有 CLIP/DINOv2 proxy，硬说 AI task
performance”。我们已经有了真实 VLM 的 image-level grounding 证据：Gemma4
canonical run 和 Qwen2.5-VL diagnostic run，基于 frozen 30-pair GRScenes
target-centered material-shift stress set。

但这不等于论文已经可以稳妥投 ACL main。它解决的是“材质/纹理扰动会不会影响
VLM 看图定位”这一层；它还没有证明 InternNav、VLN、manipulation 或真实导航任务
会受同样影响。

## Workshop Reviewer Carry-Over

| Reviewer Concern | Status On 2026-05-23 | Meaning |
|---|---|---|
| Experiments too small | Partially mitigated | The ACL route now has a 30-pair GRScenes stress set with more target categories than the workshop furniture-only examples, but it is not a full material-family benchmark. |
| Unsupported "AI Task Performance" | Partially fixed | Real Gemma4/Qwen VLM grounding replaces proxy-only evidence for the ACL story. Embodied downstream tasks are still open. |
| Missing NVIDIA official-tool baseline | Open | No head-to-head MDL Distill/Bake or Asset Converter comparison has been run yet. |
| Missing per-material-effect analysis | Open | The current stress set is not yet grouped by clearcoat, anisotropy, procedural texture, transparency, emission, opacity, displacement, or similar MDL effects. |
| Overbroad guideline claims | Addressed for ACL wording | Current claims are narrowed to the frozen target-centered stress set and do not assert broad downstream robustness. |
| Large-scene performance too narrow | Open | No multi-scene, multi-run performance statistics with variance or confidence intervals yet. |
| Missing safe-conversion recommender | Open | No material-risk classifier or rule-based recommender has been implemented. |

## ACL Story After This Update

The ACL-facing story should be:

> USD material conversion creates controlled visual perturbations. These
> perturbations are useful for stress-testing whether VLM grounding evaluations
> remain reliable after realistic 3D asset pipeline changes.

The ACL-facing story should not be:

> ConvertAsset is already proven to improve or preserve all downstream embodied
> AI tasks.

The evidence currently supports a VLM grounding reliability diagnostic. A
stronger main-conference version needs broader VLM/material-effect coverage,
official-tool baselines, or a real embodied downstream task.

## Next Targets

Priority order:

1. Add point baselines and coordinate ablations: random point, bbox center,
   target center, prompt variants, and normalized coordinate parsing checks.
2. Expand ACL/NLP related work and run citation/integrity audit so the paper is
   positioned as multimodal evaluation and VLM grounding reliability, not only
   asset conversion engineering.
3. Decide the downstream strategy: either run a real InternNav/VLN/manipulation
   experiment, or explicitly mark downstream embodied transfer as future work.
4. Add NVIDIA baseline comparison or document the boundary clearly: ConvertAsset
   preserves composition and batch evidence manifests, while official tools may
   target different conversion objectives.
5. Add per-material-effect attribution so the paper can explain which MDL
   material features are risky, not only report aggregate before/after scores.

## Documentation Changes Made

- Updated `paper/EXPERIMENT_CHECKLIST.md` with a reviewer concern closure table
  and next ACL targets.
- Updated `paper/venues/acl27/STATUS.md` with the expanded30 interpretation and
  explicit downstream boundary.
- Updated
  `paper/shared/evidence/reviews/2026-05-workshop-to-aaai27-revision-roadmap.md`
  with ACL-route status by reviewer theme.

## Verification

This is a docs-only status update. The expected verification is:

```bash
rg -n "CVPR Workshop Reviewer 意见闭环状态|2026-05-23 Status Update For ACL Route|CVPR workshop reviewer carry-over|NVIDIA official-tool baselines|下一阶段 ACL 投稿目标" \
  paper/EXPERIMENT_CHECKLIST.md \
  paper/venues/acl27/STATUS.md \
  paper/shared/evidence/reviews/2026-05-workshop-to-aaai27-revision-roadmap.md \
  docs/records/2026-05-23-cvpr-review-status-and-acl-goals.md \
  docs/records/README.md \
  docs/index.md
git diff --check
```
