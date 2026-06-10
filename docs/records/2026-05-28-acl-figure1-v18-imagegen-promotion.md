# 2026-05-28 ACL Figure 1 v18 Imagegen Promotion

## Scope

This record documents another image-generation and visual-review iteration for
the ACL candidate's Figure 1 method-chain roadmap. The work used the built-in
image-generation workflow and local render-visual-reviewer rubric. No
independent delegated visual-review subagent was used.

## Change

The ACL intro now references:

```text
paper/shared/figures/fig_acl_method_chain_imagegen_v18.png
```

The generated candidate and preserved prompt are:

```text
paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v18_candidate.png
paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v18.prompt.txt
```

v18 keeps the same four-stage schematic role as v16 while changing the third
stage title to `VLM Checks`. It preserves the exact key labels `USD / MDL`,
`noMDL`, `InternNav`, `Original`, `Converted`, `Target: box`, `SR`, `SPL`, and
`NE`. This directly fixes the v17 rejection mode, where the generated target
label read `Target: boy`.

## Visual Review

Local visual review found v18 acceptable for schematic roadmap use. The four
stage labels are readable, the target label is correct, the VLM and InternNav
blocks are visually balanced, and no red material fallback cue is present.
The figure remains AI-generated schematic art; the manuscript caption and
ethics disclosure still keep empirical claims tied to real render artifacts,
tables, logs, and navigation evidence.

Durable review record:

```text
paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v18_visual_review_20260528.json
```

Key hashes:

```text
fig_acl_method_chain_imagegen_v18.png sha256=be576fdaaa35f4977f500af32c5208e9abcf730e6975bc8961774ad6b8ec1a45
fig_acl_method_chain_imagegen_v18_candidate.png sha256=be576fdaaa35f4977f500af32c5208e9abcf730e6975bc8961774ad6b8ec1a45
fig_acl_method_chain_gpt_image2_v18.prompt.txt sha256=465ea8d40d6fa8c7c5f8bab341dff0196e263c0e76a205afd3aa7f636f0fc94b
```

## Claim Boundary

Figure 1 remains AI-generated schematic roadmap art. It must not be cited as
measured render evidence, material-effect evidence, VLM output, or navigation
evidence. Quantitative and empirical claims continue to come from frozen tables
and recorded project artifacts.
