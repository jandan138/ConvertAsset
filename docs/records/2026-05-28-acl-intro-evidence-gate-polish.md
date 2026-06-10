# 2026-05-28 ACL Intro Evidence-Gate Polish

## Scope

This record documents a focused ACL manuscript polish pass after the Figure 1
imagegen v16 and full-PDF visual-review iterations. The goal was to strengthen
the introduction's paper story without changing experiments, evidence counts,
figures, tables, or claim boundaries.

## Change

`paper/venues/acl27/sections/intro.tex` now makes the central answer more
explicit:

- material conversion is treated as an evidence-gated perturbation rather than
  a binary safe/unsafe operation;
- proxy similarity, grounding coordinates, material mechanisms, and embodied
  metrics are framed as separate reliability questions;
- the Figure 1 reference is shorter and keeps the schematic separate from the
  empirical render/navigation panels later in the paper.

The first two introduction paragraphs were compressed after the initial wording
pass pushed Figure 1 too late in the two-column float order. The final layout
keeps Figure 1 at the top of page 2 and starts Related Work cleanly on page 3.

## Visual Review

Rendered pages from the current ACL build were inspected locally using the
render-visual-reviewer rubric:

```text
tmp/acl27_current_visual_review_20260528/page-01.png
tmp/acl27_current_visual_review_20260528/page-02.png
tmp/acl27_current_visual_review_20260528/page-06.png
tmp/acl27_current_visual_review_20260528/page-09.png
```

The review found no page-level overlap, blank-page defect, detached caption, or
red-material signal. Page 2 keeps the accepted Figure 1 imagegen v16 schematic
readable at page scale. Page 6 keeps Figure 2 as real render orientation
evidence, with the caption still tying claims to frozen tables. Page 9 keeps
Figure 3 as the selected InternNav rollout panel with purple/green navigation
overlays rather than a material-effect contact sheet.

No new image-generation call was made in this pass. The accepted project-bound
asset remains:

```text
paper/shared/figures/fig_acl_method_chain_imagegen_v16.png
sha256=3859ea26536da733c0a2a57937661566e4a1291d1909886f18829ef35af392d3
```

## Verification

Focused checks after the intro polish:

```bash
make -C paper acl27
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/check_evidence_numbers.py
python -m pytest -q \
  tests/test_paper_layout.py \
  tests/test_acl_claim_boundaries.py \
  tests/test_acl_metadata_consistency.py \
  tests/test_acl_evidence_numbers.py
```

Results:

```text
make: pass
claim-boundary check: pass
metadata consistency: pass
evidence-number check: pass
pytest: 25 passed
```

Pre-fingerprint PDF profile before restaging:

```text
paper/venues/acl27/build/main.pdf
pages=10
size=3,010,017 bytes
sha256=f72294e50546948392ec74f2be3f26f7a0563b7aa69420dcb042eb57ef372d33
created=2026-05-28 13:28:25 CST
```

## Boundary

This pass is a manuscript-story and layout polish only. It does not add new
experiments, does not expand the supported population, does not change the
material-effect/NVIDIA claim boundary, and does not clear human OpenReview
gates. Because `intro.tex` changed, the final-integrity fingerprint and staged
packet must be refreshed before this build can become the current repository
candidate.

## Post-gate Refresh

After refreshing the final-integrity fingerprint, the full pre-upload gate was
rerun:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The gate completed claim-boundary, target-policy, metadata,
OpenReview checklist, citation-inventory, evidence-number, final-integrity
fingerprint, final blocker, goal-completion, focused pytest, clean ACL build,
LaTeX log, staging, packet inventory/checksum/private-token/acknowledgment
scans, PDF profile, and `pdftotext` section-order checks. Focused pytest
reports:

```text
88 passed
```

The refreshed build and staged packet are byte-identical:

```text
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
pages=10
size=3,010,017 bytes
sha256=4f04c57047e395e2afc86e0adbd247fcf257a9e730e03e0c34a4846521d62250
created=2026-05-28 13:47:21 CST
```

The post-gate rendered page hashes match the pre-gate visual review renders for
the focused pages, so the content-level visual judgment is unchanged. A fresh
page-9 red-pixel check reports zero red or red/orange pixels in the rendered
Figure 3 page, the Figure 3 source PNG, and the material-effect contact sheet.
