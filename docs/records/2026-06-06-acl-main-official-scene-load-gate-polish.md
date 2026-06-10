# 2026-06-06 ACL Main Official-Scene Load Gate Polish

## Scope

Round 39 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The target was the page 6 Results paragraph
that follows Table 6, where the old official-scene infrastructure sentence
produced several conspicuous narrow-column splits.

## Change

- Recast the Table 6 paragraph as a `load gate` for the same three official
  scenes.
- Preserved the layout guard phrase `18 required paired runs` while replacing the
  page-break-prone original/noMDL/fresh-process phrasing with `fresh launches`
  and `both asset families`.
- Kept the claim boundary explicit: the gate checks load/run stability only, not
  speed, and the NVIDIA row remains omitted until matching scene conversions have
  been generated and smoke-gated.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round39_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round39_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round39_after/focus_before_after_p6.png`
- Pages 5-6 focus sheet: `tmp/acl_main_visual_iter_20260606_round39_after/focus_p5_p6_after.png`

Observed result: the page 6 target paragraph no longer renders the old `same
three offi-` / `cial scenes`, `load-` / `stability`, `be-` / `cause`, or
`gen-` / `erated` splits in the official-scene Table 6 prose. The final PDF keeps
the same 11-page structure, Figure 3 position, and neighboring page flow. An
intermediate wording failed the layout test because it removed the exact
`18 required paired runs` guard phrase; the final wording restores that phrase
without reintroducing the older forbidden fresh-process phrases.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, float blockers, rerun warnings, label
  warnings, undefined references, multiply defined labels, and lineno warnings
  returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.39s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.
- The focused regression
  `tests/test_paper_layout.py::test_acl_results_avoids_page_break_prone_original_nomdl_phrase`
  passed after restoring the exact `18 required paired runs` phrase.

Final PDF identity:

- SHA256: `b1487fc02e01915254908d2fc368882089526843e27f563c5aab1501efa0c562`
- Pages: 11
- Size: 5,188,328 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round39_official_scene_load_gate_polish_20260606.json`
