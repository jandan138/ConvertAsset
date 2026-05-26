# ACL Author-Gate Checker

Date: 2026-05-26

## Context

The ACL/ARR candidate already had a tracked blank author-gate worksheet and a
filling guide, but the final private OpenReview gate still depended on manual
inspection. That is risky because route choice, author order, OpenReview
profiles, reviewer-registration commitment, submission history, runtime wording,
AI-assistance wording, and final upload evidence are intentionally not part of
the anonymous repository-side packet.

## Change

- Added `paper/venues/acl27/scripts/check_author_gate.py`.
- Added `tests/test_acl_author_gate.py`.
- Added the new author-gate tests to the focused pytest step inside
  `paper/venues/acl27/scripts/run_preupload_gate.py`.
- Tightened `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md` so optional media has an
  explicit local decision row.
- Updated the author filling guide, next-large-goal handoff, final packet
  checklist, status page, goal-completion audit, and staging audit.

## Behavior

The checker expects the ignored local file
`paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md`.

It verifies:

- the private worksheet exists;
- all TODO-bearing table rows in the tracked worksheet are covered by required
  field validation;
- required author/OpenReview/final-evidence fields are present;
- required field values are not blank and do not contain
  `TODO`, `TBD`, `UNKNOWN`, or `UNDECIDED`;
- the private worksheet is ignored by git;
- the private worksheet is not tracked by git.

The JSON report lists field names and status booleans only. It does not print
private worksheet values, author names, emails, OpenReview IDs, or submission
history.

`run_preupload_gate.py` deliberately does not require the private worksheet to
exist. The repository-side anonymous packet gate can still pass before the
authors fill private data. The private checker must be run separately as the
final human-upload gate.

## Verification

TDD red checks were run before implementation:

```bash
python -m pytest -q tests/test_acl_author_gate.py
python -m pytest -q tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
```

After implementation:

```bash
python -m pytest -q tests/test_acl_author_gate.py
python -m pytest -q tests/test_acl_author_gate.py tests/test_acl_preupload_gate.py
python paper/venues/acl27/scripts/check_author_gate.py --no-git-check
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Expected local author-gate status before authors fill private data:
`check_author_gate.py --no-git-check` exits nonzero and reports missing
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md`.

The full consolidated pre-upload gate passes with the author-gate unit tests in
the focused suite. At the time of this author-gate change, the focused suite
contained 27 tests and the staged ACL candidate remained a 12-page A4 PDF 1.5
packet with exactly five safe files. A later citation-inventory gate moved the
focused-suite count to 30 tests, and a later packet-checksum sidecar gate moved
the current focused-suite count to 31 tests.

## Remaining Gate

The private checker cannot pass until the authors create and fill
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md`. That is intentional and remains a
human/upload gate, not a repository failure.
