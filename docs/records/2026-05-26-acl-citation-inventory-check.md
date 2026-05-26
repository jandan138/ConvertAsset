# ACL Citation-Inventory Check

Date: 2026-05-26

## Context

The ACL wrapper already had a 20-reference web-trail audit and a manual final
integrity delta, but the pre-upload gate did not automatically detect citation
inventory drift. A later manuscript edit could add a citation key without a
BibTeX entry, remove a citation while leaving stale web-trail coverage, or cite
a key whose BibTeX entry lacks DOI/URL metadata.

## Change

- Added `paper/venues/acl27/scripts/check_citation_inventory.py`.
- Added `tests/test_acl_citation_inventory.py`.
- Added the checker as a pre-build step in
  `paper/venues/acl27/scripts/run_preupload_gate.py`.
- Added the citation-inventory tests to the focused ACL pytest suite.
- Updated the ACL status, checklist, readiness, staging, next-goal, and docs
  index records.

## Behavior

The checker parses citations from:

- `paper/venues/acl27/sections/*.tex`;
- `paper/shared/sections/appendix.tex`.

It then checks:

- every cited key exists in `paper/shared/references.bib`;
- every cited BibTeX entry has a DOI or URL field;
- every cited key appears in the 2026-05-26 ACL wrapper web-trail addendum in
  `paper/shared/evidence/references/verification_report.md`;
- the web-trail addendum has no extra key that is no longer cited by the ACL
  wrapper.

This is an inventory and metadata drift gate. It does not replace source-level
citation-context review, bibliographic field verification, or originality
screening.

## Verification

TDD red checks were run before implementation:

```bash
python -m pytest -q tests/test_acl_citation_inventory.py tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
```

After implementation:

```bash
python -m pytest -q tests/test_acl_citation_inventory.py tests/test_acl_preupload_gate.py::test_preupload_plan_orders_checks_before_staging
python paper/venues/acl27/scripts/check_citation_inventory.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Current citation inventory result:

- 20 unique cited keys;
- no missing BibTeX key;
- no cited key lacking DOI/URL metadata;
- no missing web-trail key;
- no uncited web-trail key.

The full consolidated pre-upload gate now includes citation-inventory
consistency. At the time of this change the focused ACL pytest suite contained
30 tests; a later packet-checksum sidecar gate moved the current focused-suite
count to 31 tests.

## Remaining Gate

Rerun this checker after any manuscript citation edit, bibliography edit, or
web-trail audit update. It proves citation inventory consistency; it does not
prove that each cited sentence accurately represents the source.
