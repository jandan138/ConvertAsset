# 2026-05-28 ACL Figure 1 v17 Imagegen Rejected Candidate

## Scope

This record documents one additional Figure 1 image-generation iteration after
the v16 schematic was already active in the ACL candidate.

## Candidate

The v17 candidate was generated with the imagegen workflow and saved as:

```text
paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v17_candidate.png
sha256=c6deac6d01b914c1b395be945471c738a861f989d600f3c820655f7d383e9197
```

Prompt:

```text
paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v17.prompt.txt
```

## Visual Review

Local visual review rejected v17 for main-paper use. The candidate preserves
the intended four-panel roadmap and readable stage labels, but the VLM target
label is wrong: it visibly reads `Target: boy` instead of the required
`Target: box`.

The active main-paper Figure 1 therefore remains:

```text
paper/shared/figures/fig_acl_method_chain_imagegen_v16.png
sha256=3859ea26536da733c0a2a57937661566e4a1291d1909886f18829ef35af392d3
```

Durable review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v17_candidate_review_20260528.json
```

## Claim Boundary

The rejected candidate is an image-generation audit artifact only. It is not
empirical render evidence, material-effect evidence, VLM output evidence, or
navigation evidence.
