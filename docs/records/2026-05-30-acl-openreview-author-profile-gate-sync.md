# ACL OpenReview Author-Profile Gate Sync

Date: 2026-05-30.

## Context

The author confirmed the current OpenReview profile and sole-author status for
the ACL/ARR candidate, and the public OpenReview profile page was reachable on
2026-05-30. The confirmation belongs in the ignored private author gate
worksheet, not in the anonymous submission packet.

## Changes

- Confirmed that `paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md` is
  git-ignored and untracked.
- Kept private author/profile values out of tracked docs and the staged packet.
- Updated public status docs to say the ignored private worksheet now records
  the author/profile rows, while route, reviewer-registration, OpenReview
  form-copy, runtime/AI/license, optional-media, and final-upload decisions
  remain human-gated.
- Refreshed the repo-verifiable private worksheet rows after the latest full
  pre-upload gate; the current staged PDF is 11-page A4 PDF 1.5,
  4,087,616 bytes, SHA-256
  `d03af3b4554951ccb51c3a224a8fbbd12fb517180dd36bad5672f0fb07006793`.

## Verification

```bash
python paper/venues/acl27/scripts/check_author_gate.py
git status --short --ignored paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
python paper/venues/acl27/scripts/report_final_blockers.py
python -m pytest -q tests/test_acl_author_gate.py tests/test_acl_author_gate_init.py tests/test_acl_author_gate_prefill.py tests/test_acl_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

`check_author_gate.py` still reports `ok=false` because 19 human-only fields
remain TODO, but the worksheet has no missing fields and the filled local copy
is ignored and untracked. The full pre-upload gate passes with 94 focused tests
and no repo blockers; final upload remains human-blocked by route lock,
OpenReview form copy, runtime/AI/media approvals, and final upload decision.
