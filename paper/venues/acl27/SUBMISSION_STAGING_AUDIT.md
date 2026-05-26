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
paper/submissions/acl27_arr_candidate_20260526/openreview/METADATA.md
paper/submissions/acl27_arr_candidate_20260526/openreview/RESPONSIBLE_NLP_CHECKLIST.md
paper/submissions/acl27_arr_candidate_20260526/supplemental/README.md
paper/submissions/acl27_arr_candidate_20260526/supplemental/manifest.json
```

`paper/submissions/` is ignored by `paper/.gitignore`, so this candidate packet
does not enter the tracked repository.

## Packet Boundary

Included:

- `main.pdf`: anonymous ACL-facing review manuscript.
- `openreview/METADATA.md`: copy-ready title, abstract, ARR area, and keyword
  source material for OpenReview metadata fields.
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
| `make -C paper clean-acl27 && make -C paper acl27` | Pass; clean rebuild wrote `build/main.pdf`. |
| `python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py tests/test_reviewer_closure_package.py tests/test_official_scene_submission_closure.py` | Pass; 29 tests passed; staging tests require the OpenReview checklist form source. |
| Staged file inventory | Pass; the PDF, OpenReview metadata source, OpenReview checklist source, supplemental README, and supplemental manifest were present. |
| Local path / username / private-repo scan over staged directory | Pass; no matches. |
| Acknowledgment scan over staged directory | Pass; no matches. |
| `pdfinfo` | Pass; 11 pages, A4 page size, PDF version 1.5. |
| `pdftotext` section scan | Pass; anonymous header plus `Limitations`, `Ethical Considerations`, and `References` were found. |

The staged manifest records
`claim_boundary=selected_media_excluded_by_default_pending_explicit_media_approval`
and `include_media=false`. It also records
`openreview/METADATA.md` as an `openreview_metadata_form_source` file and
`openreview/RESPONSIBLE_NLP_CHECKLIST.md` as an
`openreview_responsible_nlp_form_source` file. The manifest's remaining gates
are now final selected-venue policy lock, final author/runtime confirmation,
optional selected-media legal approval, and final OpenReview form completion.

## Refresh After Author-Gate Worksheet

After adding `OPENREVIEW_AUTHOR_GATE_WORKSHEET.md`, the staging smoke was rerun
from the current repository state on 2026-05-26.

| Check | Result |
| --- | --- |
| `python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py` | Pass; 11 tests passed. |
| Abstract count | Pass; 183 tokens by the current conservative metadata tokenizer, still under the ACLPUB 200-word guidance. |
| `make -C paper clean-acl27 && make -C paper acl27` | Pass; clean rebuild wrote `venues/acl27/build/main.pdf`. |
| Final `main.log` undefined citation/reference scan | Pass; no matches. |
| `stage_submission_packet.py --force` | Pass; regenerated the default candidate packet. |
| Staged file inventory | Pass; still exactly `main.pdf`, `openreview/METADATA.md`, `openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and `supplemental/manifest.json`. |
| Local path / username / private-repo scan | Pass; no matches. |
| Acknowledgment scan | Pass; no matches. |
| `pdfinfo` | Pass; 11 pages, A4 page size, PDF version 1.5, file size 299407 bytes. |
| `pdftotext` section scan | Pass; anonymous header plus `Limitations`, `Ethical Considerations`, and `References` were found. |

The author-gate worksheet stays repository-side only. Filled local copies are
ignored by `.gitignore` and are not part of the staged packet.

## Refresh After First-Page ACL-Fit Hardening

After the title and abstract were refreshed to reduce tool-first wording, the
build and staging smoke was rerun from the current repository state on
2026-05-26.

| Check | Result |
| --- | --- |
| Abstract count | Pass; 189 words by the repository's conservative plain-text tokenizer, still under the ACLPUB 200-word guidance. |
| `python -m pytest -q tests/test_paper_layout.py tests/test_acl_submission_staging.py` | Pass; 11 tests passed. |
| `make -C paper clean-acl27 && make -C paper acl27` | Pass; clean rebuild wrote `venues/acl27/build/main.pdf`. |
| Final `main.log` undefined citation/reference scan | Pass; no matches. |
| `stage_submission_packet.py --force` | Pass; regenerated the default candidate packet. |
| Staged file inventory | Pass; still exactly `main.pdf`, `openreview/METADATA.md`, `openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and `supplemental/manifest.json`. |
| Local path / username / private-repo scan | Pass; no matches. |
| Acknowledgment scan | Pass; no matches. |
| `pdfinfo` | Pass; 11 pages, A4 page size, PDF version 1.5, file size 299433 bytes. |
| `pdftotext` title/section scan | Pass; new title plus anonymous header, `Limitations`, `Ethical Considerations`, and `References` were found. |

## Refresh Via Consolidated Pre-Upload Gate

After adding the consolidated runner and later adding the evidence-number
checker, the full repository-side pre-upload gate was executed from the current
repository state on 2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

| Check | Result |
| --- | --- |
| Claim-boundary checker | Pass; no unsupported broad embodied, official-scene speedup, NVIDIA official-scene performance, procedural-texture success, selected-video-as-quantitative, or learned-classifier claim was found. |
| OpenReview metadata consistency | Pass; title and 189-word abstract match the LaTeX sources and remain under the 200-word abstract guidance. |
| Evidence-number consistency | Pass; local CSV/JSON evidence produced the current proxy, VLM, InternNav, official-scene, and coordinate-baseline snapshot, and manuscript/OpenReview text markers matched with no violations. |
| Focused pytest gate | Pass; 20 tests passed across staging, layout, metadata, claim-boundary, evidence-number, and pre-upload runner checks. |
| Clean ACL build | Pass; `make -C paper clean-acl27 acl27` rebuilt the PDF. |
| Final LaTeX log scan | Pass; no unresolved citation/reference or missing bibliography markers were found. |
| Candidate packet staging | Pass; regenerated `paper/submissions/acl27_arr_candidate_20260526/`. |
| Staged file inventory | Pass; still exactly `main.pdf`, `openreview/METADATA.md`, `openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and `supplemental/manifest.json`. |
| Local path / username / private-repo scan | Pass; no matches. |
| Acknowledgment scan | Pass; no matches. |
| `pdfinfo` | Pass; 11 pages, A4 page size, PDF version 1.5, file size 299433 bytes. |
| `pdftotext` title/header/section scan | Pass; found the ACL title, anonymous header, `Limitations`, `Ethical Considerations`, and `References`. |

## Remaining Gates

- Re-run the staging command and scans immediately before any real ARR or ACL
  upload.
- Lock the selected venue policy: Annual ACL 2027 remains unavailable in checked
  official sources, while EACL 2027 is public but its complete CFP is still
  forthcoming.
- Confirm final author/runtime details and keep optional scene-derived media
  out unless a separate terms/anonymization path is approved.
- Fill the final OpenReview Responsible NLP checklist with section, page, or
  line references.
- Add selected qualitative videos only after an explicit license,
  redistribution, and anonymization pass.
