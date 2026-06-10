# 2026-06-05 ACL Main Discussion/Conclusion Single-Column Closure

## Scope

Continued the ACL main-paper visual and prose iteration on
`paper/venues/acl27/build/main.pdf`, focusing on the late-paper rhythm across
Discussion, Conclusion, Limitations, Figure 4, Ethical Considerations, and
References.

The prior rendered PDF kept the shortened Conclusion but let its final sentence
continue into the top of the right column before the Limitations heading. This
pass tightened the story close so the Conclusion now fits entirely at the bottom
of the left column on page 9, while Limitations starts cleanly at the top of the
right column.

## Changes

- Replaced the Discussion lead labels with a more ACL-style claim narrative:
  `Protocol, not leaderboard.`, `Contracts before deltas.`, and
  `Boundaries as method.`
- Shortened the Conclusion into a single burden-of-proof paragraph while
  preserving the required source marker
  `This paper treats synthetic-scene material conversion`.
- Kept the claim boundary unchanged: the paper still rejects converter ranking,
  speedup, and broad robustness claims.

## Visual Finding

The final rendered page 9 has the intended rhythm:

- Left column: Discussion plus the complete short Conclusion.
- Right column: Limitations starts at the top, without leftover Conclusion text
  above it.
- Page 10 remains stable: Figure 4, caption, Ethical Considerations, and
  References are readable and non-overlapping.

## Visual Evidence

- Before round-9 render:
  `tmp/acl_main_visual_iter_20260605_round9_current/pages_180/page-09.png`
- Final page renders:
  - `tmp/acl_main_visual_iter_20260605_round9_after_r2/pages_180/page-09.png`
  - `tmp/acl_main_visual_iter_20260605_round9_after_r2/pages_180/page-10.png`
- Final late-page contact sheet:
  `tmp/acl_main_visual_iter_20260605_round9_after_r2/contact_sheets/main_pages_08_11_after_r2.png`
- Final text extraction:
  `tmp/acl_main_visual_iter_20260605_round9_after_r2/text/main_layout.txt`

## Verification

- `make -C paper acl27` passed and produced an 11-page A4 PDF.
- Final `main.pdf` SHA-256:
  `275ef0c4690c5d9339b71745c6f75544820dc9d75c94fdd98bec9b615e61ee5f`
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.
- LaTeX log blocker scan for overfull boxes, float sizing warnings, undefined
  references, rerun warnings, and label warnings returned no matches.
- `python -m pytest -q tests/test_acl_preupload_gate.py` passed:
  17 passed.
- Targeted layout pytest passed:
  `4 passed, 81 deselected`.

## Known Gate Status

`python paper/venues/acl27/scripts/run_preupload_gate.py` still stops at
`check_integrity_fingerprint.py` because the current worktree fingerprint is
stale relative to multiple paper/figure/table files. This pass did not refresh
the integrity fingerprint because doing so would bless many existing dirty
paper artifacts outside this narrow Discussion/Conclusion iteration.

## Residual Risk

This pass improves the page-9 prose and rendered rhythm, but it is not a full
final-submission completion audit for the persistent ACL PDF goal. The goal
should remain active for further visual/prose passes and, eventually, an
explicit decision about fingerprint refresh or final upload staging.
