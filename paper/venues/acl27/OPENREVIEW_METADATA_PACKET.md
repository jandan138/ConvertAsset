# OpenReview Metadata Packet

Checked: 2026-05-30.

This packet provides copy-ready metadata for an ARR/OpenReview submission using
the current anonymous PDF. It is not the official form. Re-check and update it
after any manuscript edit, target-route change, or final venue instruction
update.

Route-policy note checked on 2026-05-30: EACL 2027 via ARR remains the concrete
public 2027 ACL-family route for this packet; the EACL complete CFP is still
forthcoming, and Annual ACL 2027 still lacks a public official CFP/author kit
in the checked official sources.

## Title

Material Conversion as a Controlled Perturbation for Vision-Language Grounding
in Synthetic 3D Scenes

Plain-text metadata title:

```text
Material Conversion as a Controlled Perturbation for Vision-Language Grounding in Synthetic 3D Scenes
```

## Abstract

The PDF abstract was refreshed on 2026-06-10 to satisfy the ACLPUB guidance
that abstracts should be no longer than 200 words while keeping the first-page
story focused on measurement reliability for language grounding rather than a
tool-first framing. Current plain-text count by the repository's conservative
tokenizer: 172 words.

```text
Synthetic 3D benchmarks increasingly use rendered USD scenes to test VLM and embodied agents, yet the material step that makes scenes portable is treated as quiet infrastructure. We treat MDL conversion as a controlled test of the measurement layer. Our path rewrites MDL shader networks as portable USD materials and keeps paired USD evidence. On four Isaac Sim assets, proxy similarity is high (PSNR 35.52 dB, SSIM 0.990, LPIPS 0.020, CLIP 0.925, DINOv2 0.872), while grounding behavior still requires task-level checks. We evaluate GRScenes with a 15-pair clean visual-QA pilot and a frozen stress set of 30 target-centered pairs. Gemma4 keeps all 30 target answers in both versions and scores 27/30 original versus 29/30 converted normalized-1000 point hits; Qwen2.5-VL exposes a raw-coordinate preference with the same coordinate-prompt format in paired runs. One NVIDIA baseline material audit and an official InternNav stack-entry check over 99 episodes define the evaluation scope. Keeping these checks separate prevents visual match, grounding, material effects, and stack behavior from being collapsed into one task result.
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

Reason: the paper is also an evaluation-methodology paper, with frozen stress
pools, descriptive uncertainty, artifact provenance, and explicitly scoped
reporting.

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
