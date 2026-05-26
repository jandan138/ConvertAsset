# OpenReview Metadata Packet

Checked: 2026-05-26.

This packet provides copy-ready metadata for an ARR/OpenReview submission using
the current ACL-facing PDF. It is not the official form. Re-check and update it
after any manuscript edit, target-route change, or final venue instruction
update.

## Title

Material Perturbations in Synthetic Scenes for Vision-Language Grounding
Evaluation

Plain-text metadata title:

```text
Material Perturbations in Synthetic Scenes for Vision-Language Grounding Evaluation
```

## Abstract

The PDF abstract was shortened on 2026-05-26 to satisfy the ACLPUB guidance
that abstracts should be no longer than 200 words. Current plain-text count:
184 words.

```text
Synthetic 3D scenes are increasingly used to evaluate vision-language and embodied agents, yet their assets often undergo material conversion before rendering, sharing, or reuse in downstream toolchains. We study MDL-to-UsdPreviewSurface conversion as a controlled within-simulation perturbation for vision-language grounding and embodied-data reliability. ConvertAsset preserves USD composition while replacing MDL shader networks with PreviewSurface approximations, enabling matched original/converted evidence. On four Isaac Sim assets, proxy metrics remain high (PSNR 35.52 dB, SSIM 0.990, LPIPS 0.020, CLIP 0.925, DINOv2 0.872), but these proxies do not determine grounding behavior. We therefore evaluate GRScenes with a 15-pair clean visual-QA pilot and a frozen 30-pair target-centered material-shift stress set. Gemma4 preserves 30/30 target-category answers in both material conditions and scores 27/30 versus 29/30 normalized-1000 point hits; Qwen2.5-VL exposes a different coordinate preference, scoring better in raw pixel space than under the requested normalized-coordinate contract. We further add a selected NVIDIA-baseline material-effect audit and a scoped 99-episode official InternNav sanity run. The result is a claim-bounded ACL protocol: visual similarity, grounding, material-effect risk, and embodied-data sanity should be reported as separate gates before converted synthetic scenes support downstream robustness claims.
```

## ARR Track Recommendation

Recommended primary ARR area:

```text
Multimodality and Language Grounding to Vision, Robotics and Beyond
```

Reason: the paper's central contribution is a VLM grounding and embodied-data
reliability protocol under 3D material perturbations. The current ARR area page
explicitly includes vision-language navigation, speech and vision, multimodal
applications, multimodality, and grounding-related topics in this area.

Reasonable secondary fit if OpenReview allows an additional area or keywords:

```text
Resources and Evaluation
```

Reason: the paper is also an evaluation methodology and evidence-gate paper,
with frozen stress pools, descriptive uncertainty, artifact provenance, and
claim-bound reporting.

Do not choose `LLM agents` as the primary area unless the final abstract is
rewritten around agent planning or environment interaction. It is relevant only
as a secondary reviewer-matching cue because the embodied stack uses an
official navigation agent.

## Suggested Keywords

Use only the keywords that the final OpenReview form accepts.

```text
vision-language grounding
multimodal evaluation
embodied AI
vision-language navigation
synthetic 3D scenes
material perturbation
USD assets
Isaac Sim
domain randomization
benchmark reliability
```

## Submission-Type Notes

- Submit as a regular ARR long paper if the authors choose EACL 2027 via ARR.
- Do not submit as a system demonstration track through ARR; ARR author
  guidance says system demonstrations have separate review processes, while ARR
  reviews regular main-conference long/short papers.
- Do not label this packet as Annual ACL 2027 final-ready until Annual ACL 2027
  publishes its official CFP, author kit, and venue-specific policy.

## Fields Still Requiring Author Input

- Author list and order.
- Author OpenReview profiles.
- Reviewer-registration commitment for all submitting authors.
- Dual-submission and resubmission status.
- OpenReview preprint-status answer.
- Final target route.
- Optional media decision.

## Sources

- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/areas`
- `https://aclrollingreview.org/dates`
- `https://2027.eacl.org/`
- `https://2027.eacl.org/calls/papers/`
