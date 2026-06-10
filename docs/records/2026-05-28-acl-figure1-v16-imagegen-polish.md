# 2026-05-28 ACL Figure 1 v16 Imagegen Polish

## Scope

This record documents the follow-up Figure 1 schematic iteration for the ACL
candidate paper. The work used the image-generation workflow for the schematic
bitmap and the local render-visual-reviewer rubric for page-scale visual QA.
No independent delegated visual-review subagent was used.

## Change

The ACL intro figure now references:

```text
paper/shared/figures/fig_acl_method_chain_imagegen_v16.png
```

The generated candidate and preserved prompt are:

```text
paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v16_candidate.png
paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v16.prompt.txt
```

v16 keeps the same four-stage roadmap as v15:

- `USD / MDL`
- `noMDL`
- `VLM Evidence`
- `InternNav`

It preserves `Original`, `Converted`, `Target: box`, and neutral `SR` / `SPL`
/ `NE` metric tiles, while removing the v15 footer text. The claim boundary is
therefore carried by the Figure 1 caption and the ethics disclosure rather than
by small in-image microtext.

## Visual Review

Rendered page 2 of the rebuilt ACL PDF shows the v16 schematic as readable at
page scale. The four stage labels, stage arrows, VLM target block, and
InternNav metric tiles remain legible. The figure still acts only as roadmap
art; empirical visual evidence remains in the real-render and navigation
figures.

Durable review records:

```text
paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v16_visual_review_20260528.json
paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260528.json
```

Key hashes:

```text
fig_acl_method_chain_imagegen_v16.png sha256=3859ea26536da733c0a2a57937661566e4a1291d1909886f18829ef35af392d3
fig_acl_method_chain_gpt_image2_v16.prompt.txt sha256=218f23ab1b063584508a4536a7ec666f1d52988ca89da666786f356050db9d08
page-2 render, 150 DPI sha256=9f38319fed9ecf3ce694b896341602804300388bf5003a376c0e6c3a5562e000
page-2 render, 180 DPI sha256=39db4d6724b7f38e9e43a64e64b94f773db732452d3f616c51cdb6f76d47f24f
```

## Verification

Focused checks passed before refreshing the fingerprint:

```bash
python -m pytest -q \
  tests/test_paper_layout.py::test_acl_intro_uses_latest_low_text_method_chain_schematic \
  tests/test_acl_integrity_fingerprint.py::test_integrity_fingerprint_tracks_expected_current_sources \
  tests/test_internnav_rollout_figure.py \
  tests/test_render_scene_evidence_figure.py
```

Result:

```text
11 passed in 2.76s
```

The rebuilt PDF profile before final pre-upload staging:

```text
paper/venues/acl27/build/main.pdf
pages=11
size=3,010,470 bytes
sha256=30b248b970aa586ce83f0c0f011d1576eee0af24b0eef6859124021bdc3b7e34
```

## Claim Boundary

Figure 1 remains AI-generated schematic roadmap art. It must not be cited as
measured render evidence, material-effect evidence, VLM output, or navigation
evidence. Quantitative claims continue to come from the frozen tables and
recorded project artifacts.
