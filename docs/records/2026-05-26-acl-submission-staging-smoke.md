# 2026-05-26 ACL/ARR Submission Staging Smoke

## Purpose

Turn the ACL/ARR-ready paper goal from a documentation-only checklist into a
repeatable local staging gate. The target is a minimal anonymous review packet
that can be inspected before upload without redistributing source scenes,
scratch assets, local checkpoints, raw InternNav outputs, or selected videos.

## Changes

- Added `paper/venues/acl27/scripts/stage_submission_packet.py`.
- Added `tests/test_acl_submission_staging.py`.
- Generated an ignored candidate packet under
  `paper/submissions/acl27_arr_candidate_20260526/`.
- Added `paper/venues/acl27/SUBMISSION_STAGING_AUDIT.md` as the tracked audit
  record for this smoke pass.

## Design Decisions

- The default packet is PDF-first: `main.pdf`, supplemental README, and
  supplemental manifest only.
- Selected qualitative videos are deliberately refused by the staging script
  until license, terms-of-use, and anonymization review are complete.
- The manifest records the upload boundary explicitly, including excluded raw
  scene trees, scratch no-MDL USD trees, InternNav raw outputs, and local model
  checkpoints.
- The staged directory remains under `paper/submissions/`, which is ignored by
  `paper/.gitignore`.

## Verification

Commands run:

```bash
python -m pytest -q tests/test_acl_submission_staging.py
make -C paper acl27
python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py
python paper/venues/acl27/scripts/stage_submission_packet.py --force
find paper/submissions/acl27_arr_candidate_20260526 -maxdepth 3 -type f -print | sort
pdfinfo paper/submissions/acl27_arr_candidate_20260526/main.pdf
pdftotext paper/submissions/acl27_arr_candidate_20260526/main.pdf - | rg -n "Anonymous ACL submission|Anonymous ACL 2027 Submission|Limitations|Ethical Considerations|References"
```

Results:

- Initial TDD red check failed because the staging script did not exist.
- The staging test then passed with 3 tests.
- The combined staging/layout test passed with 11 tests.
- The ACL PDF build target was up to date.
- The staged packet contained only the PDF, supplemental README, and
  supplemental manifest.
- Local path / username / private-repo scans and acknowledgment scans over the
  staged directory returned no matches.
- `pdfinfo` reported 11 pages and A4 page size.
- `pdftotext` found the anonymous header, `Limitations`, `Ethical
  Considerations`, and `References`.

## Open Issues

- This is not yet a final upload archive.
- The final Annual ACL or ARR target-call policy is still external.
- Gemma-family public checkpoint identity and InteriorAgent / KuJiaLe terms
  still need final confirmation before submission.
- Selected qualitative videos remain useful for rebuttal and figures, but are
  not part of the safe minimal review packet yet.
