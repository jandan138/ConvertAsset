# 2026-05-28 ACL v18 Full-PDF Visual Review

## Purpose

Record the current ACL candidate PDF visual review after the Figure 1 v18
imagegen schematic promotion. The older full-PDF review file still points to a
v16 PDF hash, so this pass preserves a current-hash review without rewriting
the historical evidence.

## Reviewed Artifact

```text
paper/venues/acl27/build/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
pages=11
bytes=4066538
created=Thu May 28 23:22:53 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
note=staged after the Figure 1 caption polish and final pre-upload gate rerun
```

The review rendered all 11 pages at 150 DPI under:

```text
/tmp/convertasset_acl27_current_visual_review_2322/
contact_sheet_sha256=54071ded4baf34679d4bb373252fda445e22d749724ac3cef0b0de1d78cbbf70
```

Durable review record:

```text
paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_v18_20260528.json
```

## Visual Verdict

Overall verdict: `PASS_WITH_MINOR_QUALITATIVE_CAVEATS`.

No blocking visual failure was found in the current PDF. The 11-page contact
sheet showed no blank page, detached figure caption, raw LaTeX artifact,
obvious table/float overlap, or visible page-level clipping.

The abstract point-hit wording explicitly states the direction as `27/30
original versus 29/30 converted`, and the Figure 1 caption now starts with
`Evidence-chain overview` instead of the earlier internal-sounding
`Figure-driven overview`; visual review of pages 1-2 found no resulting
title/abstract/figure-caption overlap, clipping, or page-flow regression.

Main figure status:

- Figure 1: v18 imagegen schematic is readable at page scale; `Target: box`,
  `VLM Checks`, and `SR/SPL/NE` are visible. It remains schematic roadmap art,
  not empirical evidence.
- Figure 2: real render evidence is usable for orientation. The top proxy row
  is a cropped detail by design, and the caption discloses that boundary.
- Figure 3: material-effect panel has no visible historical red MDL fallback
  in the `Original MDL` column; the caption keeps the evidence selected and
  qualitative.
- Figure 4: selected InternNav path panel keeps the image and caption together,
  with distinguishable purple executed paths and green reference paths. After
  the label-readability polish, the case IDs and `SR O/N` labels are easier to
  scan, though the caption and main text must still carry the claim boundary.

## Decision

No imagegen replacement was made in this pass. The current v18 PDF does not
justify another Figure 1 iteration: Figure 1 is already accepted for
schematic-roadmap use, and regenerating it without a specific visual failure
would add text-accuracy risk.

The concrete visual follow-up was the Figure 4 label-readability polish:
`paper/shared/figures/gen_internnav_main_readable.py` now preserves the same
overall figure size while widening the left label column and increasing the row
label fonts. This changes readability, not the selected-video evidence scope.

## Verification

Commands run:

```bash
pdftoppm -png -r 150 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_current_visual_review_2322/page
pdfinfo paper/venues/acl27/build/main.pdf
pdfimages -list paper/venues/acl27/build/main.pdf
pdftotext -layout paper/venues/acl27/build/main.pdf - | rg -n "Figure 1:|Figure 2:|Figure 3:|Figure 4:|Table 5|Material and Embodied"
sha256sum /tmp/convertasset_acl27_current_visual_review_2322/contact_sheet.png /tmp/convertasset_acl27_current_visual_review_2322/page-*.png
```

Notes:

- This was a local pure-visual review using the `render-visual-reviewer`
  rubric. It was not an independent delegated review because this environment's
  multi-agent tool policy permits spawning only when the user explicitly asks
  for sub-agents.
- `imagegen` was not invoked in this pass because the current review found no
  concrete Figure 1 replacement need. The v18 generated asset and prompt remain
  the current promoted method-chain schematic.
