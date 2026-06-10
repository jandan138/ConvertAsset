# 2026-06-06 ACL Main Page 8 Caption Density Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 8 where Tables 2--6 form
the densest result-table stack in the main paper.

The fresh round-23 contact sheet showed no hard crop or float displacement. The
selected issue was reader load: several adjacent captions repeated audit-style
boundary prose, making the result page feel like a verification log rather than a
compact ACL result narrative.

## Changes

- Condensed the Table 2 clean-pool caption while preserving the 15 PASS pairs,
  O/C convention, structured-text prompt, and benchmark-gate boundary.
- Condensed the Table 3 frozen stress-set caption and made Gemma4/Qwen2.5-VL
  roles read as canonical versus coordinate-format diagnostic.
- Rephrased the Table 4 caption from `Reviewer-closure` to a reader-facing
  paired-CI claim-boundary description.
- Synchronized the Table 3 and Table 4 generator scripts with the checked-in
  table captions.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Tables 2--6 remain together on page 8.
- No table, caption, or page number is clipped.
- Table 6 still fits above the page number after the caption rewrite.
- The page reads more directly as a result-summary stack: clean-pool control,
  frozen stress set, paired intervals, material-effect boundary, and
  official-stack stability.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round23_current/contact_sheet.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round23_current/page-08.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round23_after/page-08.png`
- Accepted before/after comparison:
  `tmp/acl_main_visual_iter_20260606_round23_after/page08_before_after.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round23_after/contact_sheet.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round23_page8_caption_density_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=7cef09b4ffd907d129f5f16b65c077dbcc8d0eecc1bf4db3ab02c77403561572
pages=11
bytes=5188958
created=Sat Jun 6 11:30:51 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py
python -m py_compile paper/shared/tables/gen_vlm_stress_expanded30.py paper/shared/evidence/experiments/09_reviewer_closure_package/build_reviewer_closure_package.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
pdftotext paper/venues/acl27/build/main.pdf tmp/acl_main_visual_iter_20260606_round23_after/main.txt && rg -n "Table 2: Clean-pool GRScenes VLM grounding pilot on 15|Table 3: Frozen 30-pair GRScenes material-shift stress set|Table 4: Paired bootstrap confidence intervals for the frozen VLM" tmp/acl_main_visual_iter_20260606_round23_after/main.txt
```

Results: the ACL build passed with an 11-page A4 PDF, the final LaTeX blocker
scan returned no matches, `tests/test_paper_layout.py` plus
`tests/test_acl_preupload_gate.py` passed with 102 tests, and the synchronized
generator scripts compiled. Both ACL claim-boundary and metadata-consistency
checks returned `ok`; the metadata check still reports `abstract_word_count=169`.
The extracted-PDF caption scan found the new Table 2, Table 3, and Table 4
caption openings.

## Residual Risk

This pass is a focused page-8 main-paper caption-density polish. It is not a
supplement-wide wording cleanup, full final-upload audit, target-policy refresh,
or regeneration of every experiment package.
