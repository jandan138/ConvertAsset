# 2026-06-06 ACL Main VLM Stress Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on the Results 4.2 stress-set
story around page 5.

The fresh round-14 contact sheet did not show a new table crop or hard float
failure. The highest-value local issue was rhetorical: the expanded GRScenes
stress-set result still read like a metric inventory, even though this is the
main place where the paper explains why proxy similarity is not enough.

## Changes

- Recast the expanded stress set as a stronger prompt-contract question:
  when target visibility is retained but material appearance can move, does the
  same prompt contract still bind the model to the same object?
- Replaced "Qwen2.5-VL is different" / "comfortable in raw pixel space" wording
  with a tighter claim-boundary contrast between Gemma4 and Qwen2.5-VL.
- Reframed the paragraph conclusion as a measurement-interface finding rather
  than a model-ranking result.
- Replaced internal-artifact language with `contract-auditable, not
  figure-driven` evidence language.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 4 still introduces Results 4.2 without displacing the clean-pool table.
- Page 5 now carries the stress-set story as a reader-facing question and
  measurement-interface finding.
- An intermediate underfull short line, "Table 3 gives the main stress result.",
  was removed by changing the opener to "Table 3 gives the main result for this
  frozen stress test."
- Page 6 and the later table/Discussion pages remain in the same visual
  structure on the full contact sheet.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round14_current/contact_sheets/main_pages_01_11_current.png`
- Before page renders:
  - `tmp/acl_main_visual_iter_20260606_round14_current/pages_180/main-04.png`
  - `tmp/acl_main_visual_iter_20260606_round14_current/pages_180/main-05.png`
  - `tmp/acl_main_visual_iter_20260606_round14_current/pages_180/main-06.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round14_after2/pages_180/main-04.png`
  - `tmp/acl_main_visual_iter_20260606_round14_after2/pages_180/main-05.png`
  - `tmp/acl_main_visual_iter_20260606_round14_after2/pages_180/main-06.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round14_after2/contact_sheets/main_pages_01_11_after2.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round14_vlm_stress_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=7212bddbe930984bf3338dd9a1eba1290998914dc897065c9eb278cc9cae23fd
pages=11
bytes=5189474
created=Sat Jun 6 10:01:42 2026 CST
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
ACL claim-boundary and metadata-consistency checks returned `ok`. The metadata
check still reports `abstract_word_count=169`.

## Residual Risk

This pass is a focused Results 4.2 story and page-5 visual iteration. It is not
a complete final-upload audit, broad full-PDF completion proof, or
integrity-fingerprint refresh.
