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

## Refresh After Evidence-Gate Table

After adding Table `tab:acl_evidence_gate_registry` to the ACL method section,
the consolidated pre-upload gate was rerun from the current repository state on
2026-05-26:

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
| `pdfinfo` | Pass; 12 pages, A4 page size, PDF version 1.5, file size 306187 bytes. |
| PDF profile guard | Pass; staged PDF is within the current candidate cap of 12 total pages, uses A4, and is PDF 1.5. |
| `pdftotext` title/header/section scan | Pass; found the ACL title, anonymous header, `Limitations`, `Ethical Considerations`, and `References`. |

## Refresh After PDF Profile Gate

After adding the explicit PDF profile guard to `run_preupload_gate.py`, the
focused runner tests were rerun from the current repository state on
2026-05-26:

```bash
python -m pytest -q tests/test_acl_preupload_gate.py
```

Result: 6 tests passed. The new tests cover the `pdf_profile` plan step, the
current 12-page A4/PDF 1.5 candidate profile, rejection of unreviewed page
growth, and section-order rejection when `References` appears before
`Limitations` and `Ethical Considerations`.

The full consolidated gate was then rerun:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The completed step list now includes `pdf_profile` between
`pdfinfo` and `pdftotext_sections`; the focused suite passed 23 tests; `pdfinfo`
reported 12 pages, A4 page size, PDF 1.5, and 306187 bytes; the staged packet
still contained exactly the five safe files and passed the private-token and
acknowledgment scans.

## Refresh After Gate-Status Documentation Sync

After synchronizing the active ACL status/checklist documents to the current
`pdf_profile` gate vocabulary, the full consolidated gate was rerun from a
clean `main` checkout on 2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, OpenReview metadata
consistency, evidence-number consistency, 23-test focused pytest, clean ACL
build, final LaTeX log scan, candidate packet staging, inventory, local
path/private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`, and
`pdftotext_sections`. `pdfinfo` reported 12 pages, A4 page size, PDF 1.5, and
306187 bytes. The staged packet still contained exactly the five safe files:
`main.pdf`, `openreview/METADATA.md`,
`openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and
`supplemental/manifest.json`.

## Refresh After Author-Gate Checker

After adding `check_author_gate.py` and its focused tests, the private
author-gate logic was kept separate from the default anonymous packet gate:
`run_preupload_gate.py` includes the author-gate unit tests, but it does not
require the private `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` file to exist.
That private checker is a final human-upload gate and is expected to fail until
the authors create and fill the ignored local worksheet.

The full consolidated gate was rerun from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, OpenReview metadata
consistency, evidence-number consistency, 27-test focused pytest, clean ACL
build, final LaTeX log scan, candidate packet staging, inventory, local
path/private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`, and
`pdftotext_sections`. `pdfinfo` reported 12 pages, A4 page size, PDF 1.5, and
306187 bytes. The staged packet still contained exactly the five safe files:
`main.pdf`, `openreview/METADATA.md`,
`openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and
`supplemental/manifest.json`.

## Refresh After Citation-Inventory Checker

After adding `check_citation_inventory.py`, the repository-side gate now checks
the ACL wrapper's citation inventory before rebuilding and staging. The checker
parses ACL section citations plus the shared appendix, verifies that every
cited key exists in `paper/shared/references.bib`, requires each cited entry to
carry DOI or URL metadata, and checks exact key coverage against the 2026-05-26
web-trail addendum in
`paper/shared/evidence/references/verification_report.md`.

The full consolidated gate was rerun from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, OpenReview metadata
consistency, citation-inventory consistency, evidence-number consistency,
31-test focused pytest, clean ACL build, final LaTeX log scan, candidate packet
staging, inventory, adjacent checksum-sidecar validation,
local path/private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`,
and `pdftotext_sections`. The citation-inventory report covered 20 unique cited
keys with no missing BibTeX entry, no cited key without DOI/URL, no missing
web-trail key, and no uncited web-trail key. `pdfinfo` reported 12 pages, A4
page size, PDF 1.5, and 306187 bytes. The staged packet still contained exactly
the five safe files: `main.pdf`, `openreview/METADATA.md`,
`openreview/RESPONSIBLE_NLP_CHECKLIST.md`, `supplemental/README.md`, and
`supplemental/manifest.json`.

## Refresh After Packet Checksum Sidecar

After adding the adjacent checksum sidecar, the staging script still keeps the
anonymous review packet at the same five-file boundary. It now also writes the
ignored local sidecar:

```text
paper/submissions/acl27_arr_candidate_20260526.sha256
```

That sidecar is outside `paper/submissions/acl27_arr_candidate_20260526/`, so it
is not part of the upload packet. It records SHA-256 digests for exactly the five
staged files. `run_preupload_gate.py` validates the sidecar immediately after
the exact packet-inventory check and before private-token and acknowledgment
scans. The refreshed full gate on 2026-05-26 passed with 31 focused tests, the
same five packet files, a valid checksum sidecar, a 12-page A4 PDF 1.5, and
306187 bytes.

## Refresh After Final-Integrity Fingerprint Gate

After adding the source-freshness fingerprint for the final integrity audit,
the consolidated runner was executed again from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, OpenReview metadata
consistency, citation-inventory, evidence-number, final-integrity fingerprint,
34-test focused pytest, clean ACL build, final LaTeX log scan, candidate packet
staging, exact packet inventory, adjacent checksum-sidecar validation,
private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`, and
`pdftotext_sections`. The fingerprint check validated 41 current source files
before build/staging. The rebuilt staged PDF is still 12 A4 pages, PDF 1.5,
and 306187 bytes, and the staged packet still contains exactly the five safe
files plus the adjacent ignored checksum sidecar outside the packet.

## Refresh After Final Blocker Report Gate

After adding the privacy-preserving final upload blocker report, the
consolidated runner was executed again from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, OpenReview metadata
consistency, citation-inventory, evidence-number, final-integrity fingerprint,
final blocker report, 37-test focused pytest, clean ACL build, final LaTeX log
scan, candidate packet staging, exact packet inventory, adjacent
checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`.

The blocker report itself is an upload handoff aid rather than an upload
authorization. Its current status is `human_blocked`: `repo_blockers=[]`, while
the missing private author worksheet, target-route author confirmation,
official OpenReview form copy, and author/runtime/AI/media approval remain
human-only blockers. The rebuilt staged PDF is still 12 A4 pages, PDF 1.5, and
306187 bytes. The staged packet still contains exactly the five safe files plus
the adjacent ignored checksum sidecar outside the packet.

## Refresh After OpenReview Checklist Gate

After adding the OpenReview Responsible NLP checklist copy-readiness gate, the
consolidated runner was executed again from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, OpenReview metadata
consistency, OpenReview checklist copy-readiness, citation-inventory,
evidence-number, final-integrity fingerprint, final blocker report, 41-test
focused pytest, clean ACL build, final LaTeX log scan, candidate packet
staging, exact packet inventory, adjacent checksum-sidecar validation,
private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`, and
`pdftotext_sections`.

The checklist report validated 17 expected ARR checklist questions, official
policy URLs, current PDF anchors, no placeholder text, no bare yes/no/N/A
answers, and anonymous-review AI-assistance wording. The rebuilt staged PDF is
still 12 A4 pages, PDF 1.5, and 306187 bytes. The staged packet still contains
exactly the five safe files plus the adjacent ignored checksum sidecar outside
the packet.

## Refresh After Target-Policy Gate

After adding the ACL/ARR target-policy consistency gate, the consolidated
runner was executed again from the current repository state on 2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, 45-test focused pytest, clean ACL build, final LaTeX log scan, candidate packet
staging, exact packet inventory, adjacent checksum-sidecar validation,
private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`, and
`pdftotext_sections`.

The target-policy report validated that the notes remain an ACL/ARR candidate
packet: `route_status=acl_arr_candidate`, `annual_acl_final_ready=false`,
`eacl_arr_public_route=true`, no missing official URLs, no missing required
route markers, and no unsupported Annual ACL 2027 final-ready wording. The
rebuilt staged PDF is still 12 A4 pages, PDF 1.5, and 306187 bytes. The staged
packet still contains exactly the five safe files plus the adjacent ignored
checksum sidecar outside the packet.

## Refresh After Final-Blocker Clearance Gate

After making the final blocker report clearable by a complete private author
worksheet, the consolidated runner was executed again from the current
repository state on 2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, 46-test focused pytest, clean ACL build, final LaTeX log scan,
candidate packet staging, exact packet inventory, adjacent checksum-sidecar
validation, private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`,
and `pdftotext_sections`.

The current real repository report remains `status=human_blocked` with
`repo_blockers=[]` because the private author worksheet is not filled. A
complete ignored private worksheet can now clear the human blockers without
printing private values. The rebuilt staged PDF is still 12 A4 pages, PDF 1.5,
and 306187 bytes. The staged packet still contains exactly the five safe files
plus the adjacent ignored checksum sidecar outside the packet.

## Refresh After Private Author-Gate Semantic Check

After hardening `check_author_gate.py` so filled private rows also need
positive approval/pass/upload semantics, the consolidated runner was executed
again from the current repository state on 2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, 48-test focused pytest, clean ACL build, final LaTeX log scan,
candidate packet staging, exact packet inventory, adjacent checksum-sidecar
validation, private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`,
and `pdftotext_sections`.

The current real repository report remains `status=human_blocked` with
`repo_blockers=[]` because the private author worksheet is not filled. A future
filled private worksheet must now use positive confirmation wording for
high-risk fields; failed scans or `do not upload` keep the gate incomplete
without leaking private values. The rebuilt staged PDF is still 12 A4 pages,
PDF 1.5, and 306187 bytes.

## Earlier Refresh Via Consolidated Pre-Upload Gate

After adding the consolidated runner and later adding the evidence-number
checker, the full repository-side pre-upload gate was executed from the
then-current repository state on 2026-05-26, before the evidence-gate table
refresh:

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
