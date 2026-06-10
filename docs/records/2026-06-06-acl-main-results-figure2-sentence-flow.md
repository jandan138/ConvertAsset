# 2026-06-06 ACL Main Results Figure 2 Sentence Flow

## Scope

Continued the ACL main-paper visual and language review on
`paper/venues/acl27/build/main.pdf`, focusing on the Results text immediately
before and after full-width Figure 2.

The rendered PDF had a reader-visible sentence-flow problem: page 4 ended with
the opening of the Qwen2.5-VL clean-pool diagnostic, while page 5 resumed after
Figure 2 and its caption with the continuation of that same sentence. The
reader had to cross a full-width figure to recover the sentence.

## Changes

- Tightened the clean GRScenes pool description while preserving the 15-pair
  pilot-control boundary.
- Compressed the clean-pool Gemma4/Qwen2.5-VL diagnostic sentence so the Qwen
  sentence now finishes before Figure 2.
- Preserved the reported values: Gemma4 8/15 and 6/15 normalized-1000 hits,
  Qwen2.5-VL 23/30 scorable answer rows, 5/14 and 5/15 raw point hits, and zero
  normalized-1000 hits in both conditions.
- Kept Figure 2 framed as orientation evidence tied to frozen tables, not as
  qualitative proof of VLM equivalence.

## Visual Finding

The accepted render keeps the same page count and local float structure:

- Page 4 now ends with a complete clean-pool diagnostic sentence.
- Figure 2 remains at the top of page 5.
- Page 5 post-figure text begins with the next full paragraph, "The expanded
  stress set...", rather than a stranded sentence continuation.
- There is no Figure 2 caption collision, text overlap, or visible image crop
  regression in the checked p4/p5 render.

## Visual Evidence

- Before page 4:
  `tmp/acl_main_visual_iter_20260606_round10_current/pages_180/main-04.png`
- Before page 5:
  `tmp/acl_main_visual_iter_20260606_round10_current/pages_180/main-05.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round10_after2/pages_180/main-04.png`
  - `tmp/acl_main_visual_iter_20260606_round10_after2/pages_180/main-05.png`
- Accepted contact sheet:
  `tmp/acl_main_visual_iter_20260606_round10_after2/contact_sheets/main_pages_04_05_after2.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round10_results_figure2_sentence_flow_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=f4d36cec8444c74d285cb9d1fc466ef897ce7786dcd5b1b3cd0410194fd63d57
pages=11
bytes=5189306
created=Sat Jun 6 09:23:46 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
```

Results: ACL build passed with an 11-page A4 PDF, the final LaTeX blocker scan
returned no matches, `tests/test_paper_layout.py` passed with 85 tests, and both
ACL claim-boundary and metadata-consistency checks returned `ok`.

## Residual Risk

This pass is a focused p4/p5 Results sentence-flow iteration. It is not a
complete final-upload audit, broad full-PDF completion proof, or
integrity-fingerprint refresh.
