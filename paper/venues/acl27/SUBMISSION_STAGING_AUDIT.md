# ACL/ARR Submission Staging Audit

Checked: 2026-05-26.

This audit records the first concrete candidate upload staging directory for the
ACL/ARR review draft. The staged directory is intentionally ignored by git and
is not a final archive; it is a local smoke target for upload-boundary,
anonymization, and PDF sanity checks.

## Staging Command

```bash
python paper/venues/acl27/scripts/stage_submission_packet.py --force
```

The command writes the default candidate packet under
`paper/submissions/acl27_arr_candidate_20260526/`.

## Staged Files

```text
paper/submissions/acl27_arr_candidate_20260526/main.pdf
paper/submissions/acl27_arr_candidate_20260526/openreview/RESPONSIBLE_NLP_CHECKLIST.md
paper/submissions/acl27_arr_candidate_20260526/supplemental/README.md
paper/submissions/acl27_arr_candidate_20260526/supplemental/manifest.json
```

`paper/submissions/` is ignored by `paper/.gitignore`, so this candidate packet
does not enter the tracked repository.

## Packet Boundary

Included:

- `main.pdf`: anonymous ACL-facing review manuscript.
- `openreview/RESPONSIBLE_NLP_CHECKLIST.md`: copy-ready source material for
  ARR/OpenReview Responsible NLP checklist fields.
- `supplemental/README.md`: human-readable upload boundary and claim guardrail.
- `supplemental/manifest.json`: machine-readable local staging manifest.

Excluded:

- Raw source scenes.
- Full scratch no-MDL USD trees.
- InternNav raw frame directories, LMDBs, and logs.
- Local model checkpoints.
- Selected qualitative videos.

Selected qualitative media is still excluded because InteriorAgent / KuJiaLe
scene-derived media needs explicit author/legal approval before redistribution.
This candidate packet therefore supports a safe PDF-first ARR upload smoke, not
a final media supplement.

## Scan Results

| Check | Result |
| --- | --- |
| `make -C paper acl27` | Pass; `build/main.pdf` was up to date. |
| `python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py tests/test_reviewer_closure_package.py tests/test_official_scene_submission_closure.py` | Pass; 29 tests passed; staging tests require the OpenReview checklist form source. |
| Staged file inventory | Pass; the PDF, OpenReview checklist source, supplemental README, and supplemental manifest were present. |
| Local path / username / private-repo scan over staged directory | Pass; no matches. |
| Acknowledgment scan over staged directory | Pass; no matches. |
| `pdfinfo` | Pass; 11 pages, A4 page size, PDF version 1.5. |
| `pdftotext` section scan | Pass; anonymous header plus `Limitations`, `Ethical Considerations`, and `References` were found. |

The staged manifest records
`claim_boundary=selected_media_excluded_by_default_pending_explicit_media_approval`
and `include_media=false`. It also records
`openreview/RESPONSIBLE_NLP_CHECKLIST.md` as an
`openreview_responsible_nlp_form_source` file. The manifest's remaining gates
are now final target-call policy, final author/runtime confirmation, optional
selected-media legal approval, and final OpenReview form completion.

## Remaining Gates

- Re-run the staging command and scans immediately before any real ARR or ACL
  upload.
- Complete final target-call policy checks once the selected Annual ACL or ARR
  instructions are public.
- Confirm final author/runtime details and keep optional scene-derived media
  out unless a separate terms/anonymization path is approved.
- Fill the final OpenReview Responsible NLP checklist with section, page, or
  line references.
- Add selected qualitative videos only after an explicit license,
  redistribution, and anonymization pass.
