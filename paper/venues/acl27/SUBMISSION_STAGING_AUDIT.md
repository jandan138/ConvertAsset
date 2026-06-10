# ACL/ARR Submission Staging Audit

Checked: 2026-05-30.

This audit records the first concrete candidate upload staging directory for the
ACL/ARR review draft. The staged directory is intentionally ignored by git and
is not a final archive; it is a local smoke target for upload-boundary,
anonymization, and PDF sanity checks.

Latest refresh on 2026-05-30: after the InternNav/InteriorAgent scope wording
polish in the Limitations section, the full pre-upload gate rebuilt and
restaged the candidate. The current build and staged PDFs are byte-identical as
an 11-page A4 PDF 1.5 candidate, 4,066,626 bytes
(`sha256=137370b33b567ebc55ab6f88ef5d6e6860b6e61debf133e8077b14a22b454c98`,
created 2026-05-30 20:43:58 CST). The adjacent ignored checksum sidecar is
`paper/submissions/acl27_arr_candidate_20260526.sha256`
(`sha256=0439826be4d8dd283dc82b277a8a206f6964e031d43bee0f3cadaf2bbf7fb86c`).
The gate passed claim boundaries, target policy, metadata consistency,
OpenReview checklist, citation inventory, evidence-number checks, the
57-source final-integrity fingerprint, blocker/goal reports, 93 focused tests,
clean ACL rebuild, LaTeX log scan, packet staging,
inventory/checksum/private-token/acknowledgment scans, PDF profile checks, and
ordered text-section checks. Page 9 was rerendered at 150 DPI and passed local
visual review with Figure 4, Limitations, and Ethical Considerations readable
and non-overlapping.

Previous same-day refresh on 2026-05-30: after the Figure 3 provenance-caption hardening,
conclusion takeaway polish, and removal of the manual Introduction page break,
the full pre-upload gate rebuilt and restaged the candidate. The current build
and staged PDFs are byte-identical as an 11-page A4 PDF 1.5 candidate,
4,066,770 bytes
(`sha256=177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356`,
created 2026-05-30 20:25:01 CST). The adjacent ignored checksum sidecar is
`paper/submissions/acl27_arr_candidate_20260526.sha256`
(`sha256=4a39e9ce663abac3c31b266272173acb047f7ea7cbd28c868dec5d4d0e18a4ad`).
The accepted caption says the selected `Original MDL` cells passed a
log-checked clean rerender/provenance gate. A longer draft was rejected after
rendered-page review because it pushed Figure 4 to page 10 and left page 9
with a large blank column; the compact final wording keeps Figure 4 on page 9.
The conclusion now states the paper's practical outcome as an evidence gate,
and the contribution list now flows after Figure 1 without a manual
`\newpage`, without changing the packet boundary. The gate passed claim
boundaries, target policy, metadata consistency, OpenReview checklist, citation
inventory, evidence-number checks, the 57-source final-integrity fingerprint,
blocker/goal reports, 93 focused tests, clean ACL rebuild, LaTeX log scan,
packet staging, inventory/checksum/private-token/acknowledgment scans, PDF
profile checks, and ordered text-section checks.

Previous refresh on 2026-05-28: after the material-effect covered-bin clean
rerender/provenance pass, main-panel promotion, Figure 2 visual-first
readability polish, Figure 3 readable-label polish/red-material recheck, Table
6 caption compacting, the Figure 4 wide InternNav panel upgrade, the Figure 4
label-readability polish, page-9 Limitations tail polish, page-7 official-scene
hyphenation polish, Figure 1 v17 rejected-candidate audit plus v18 promotion,
the abstract point-hit direction clarity update, the Figure 1 caption polish,
and the final pre-upload gate rerun, the current build and staged PDFs are
byte-identical as an 11-page A4 PDF 1.5 candidate,
4,066,538 bytes
(`sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7`,
created 2026-05-28 23:22:53 CST).
The material-effect qualitative panel is now main-paper Figure 3 on page 8;
the material-effect result is still table-bounded, and the caption/prose state
that it is selected qualitative evidence rather than a population-level NVIDIA
failure rate or a mechanism-level MDL preservation certificate. Figure 4 is now
the wide three-case official KuJiaLe InternNav path panel on page 9. The PDF
text guard requires both `Figure 3:` and `Figure 4:`, allows this top-of-page
Figure 4 float before the Limitations heading, and still rejects a float-only
material-table page immediately before Limitations. The staged
packet boundary is still the same five files plus an adjacent checksum sidecar
outside the packet.

Table 6 keeps the same official-scene aggregate metrics but now has a compact
main-paper caption. Local page-7/page-8 review records `pass_with_caveat`: the
page is dense, but Table 6 fits without overlap and keeps the NVIDIA
official-scene omission explicit.

Follow-up local visual review of the staged PDF rendered the Figure 3 page and
found no red-material signal: both the source
`fig_material_effect_baseline_qualitative.png`, the rendered page-8 image, and
the extracted embedded PDF image had zero strong-red pixels, and the four
selected original-MDL logs contain no `KooPbr`, module, or MDL shade-node error
terms. Figure 3 now uses larger row-level target/effect labels; the source
figure hash is
`e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a`,
and the rendered page-8 hash is
`e8cf7110e83bfe8b44d7674dd29cee26d7a4917aea70dc783db07ee3e18c7f90`.
The source Figure 4 wide InternNav panel has hash
`818525fcc0a5fd0b4e692ddd9d2738e673eb3b70a2b2dd90895cab7dd0d51a6e`, the
rendered page-9 hash is
`cb7fbc9efb13ff560646189e2f39067e5c720abb446ce85958ca12e31e4fde10`, and both
have zero strong-red pixels after overlay recoloring. Page 9 now starts the
right text column at `Ethical Considerations`, not with a dangling Limitations
continuation; the left case-ID and `SR O/N` labels are widened for page-scale
scanning without changing the selected still evidence.
The page-7 official-scene stability paragraph now starts after the page break
with `complete successfully in fresh processes...`, not a broken
`nal/noMDL`, `process official-scene`, or `scene runs` fragment.
Figure 2 remains an orientation panel, now with a larger visual-first
real-render layout and a
rendered page-6 hash
`c4bcad2fb1e5f47037e2c7c7cf3a7a6ea4879a6f3160ca7a690e2f4396d75ca2`; its
caption and main text correctly keep task claims tied to frozen tables rather
than to the qualitative image.
Figure 1 now uses the promoted v18 imagegen schematic
`fig_acl_method_chain_imagegen_v18.png`
(`sha256=be576fdaaa35f4977f500af32c5208e9abcf730e6975bc8961774ad6b8ec1a45`);
local page-2 visual review confirms the exact `Target: box` label, readable
`VLM Checks` title, the polished `Evidence-chain overview` caption opening,
and schematic-only claim boundary.

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
make -C paper acl27
python - <<'PY'
import importlib.util
from pathlib import Path
script = Path("paper/venues/acl27/scripts/run_preupload_gate.py")
spec = importlib.util.spec_from_file_location("gate", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.check_pdf_text(Path("paper/venues/acl27/build/main.pdf"))
print("pdf text/page-budget check ok")
PY
```

| Check | Result |
| --- | --- |
| Claim-boundary checker | Pass; no unsupported broad embodied, official-scene speedup, NVIDIA official-scene performance, procedural-texture success, selected-video-as-quantitative, or learned-classifier claim was found. |
| OpenReview metadata consistency | Pass; title and 181-word abstract match the LaTeX sources and remain under the 200-word abstract guidance. |
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

## Refresh After Final Blocker Handoff Details

After adding `human_blocker_details` to `report_final_blockers.py`, the
consolidated runner was executed again from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report with structured human handoff details, 49-test focused pytest, clean ACL
build, final LaTeX log scan, candidate packet staging, exact packet inventory,
adjacent checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`.

The current real repository report remains `status=human_blocked` with
`repo_blockers=[]` because the private author worksheet is not filled. The
details now point each human blocker to required actions, worksheet field names,
tracked copy-source files, and done conditions without printing private values.
The rebuilt staged PDF is still 12 A4 pages, PDF 1.5, and 306187 bytes.

## Refresh After OpenReview Upload Runbook

After adding `OPENREVIEW_UPLOAD_RUNBOOK.md` and including its coverage test in
the consolidated focused pytest step, the runner was executed again from the
current repository state on 2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, 50-test focused pytest including
`tests/test_acl_openreview_upload_runbook.py`, clean ACL build, final LaTeX log
scan, candidate packet staging, exact packet inventory, adjacent
checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`.

The current real repository report remains `status=human_blocked` with
`repo_blockers=[]` because the private author worksheet is not filled. The
upload runbook narrows the last-mile OpenReview operation to the private
worksheet, route lock, metadata/checklist copy, author/runtime/AI/license/media
approval, final gates, and stop conditions. The rebuilt staged PDF is still 12
A4 pages, PDF 1.5, and 306187 bytes.

## Refresh After Author-Gate Initializer

After adding `init_author_gate.py`, the private author worksheet creation path
was moved from a manual copy into a guarded local initializer. The initializer
creates `OPENREVIEW_AUTHOR_GATE_FILLED.local.md` from the blank template,
refuses to overwrite an existing private file, verifies the path is git-ignored,
and reports only path/status metadata. The blank worksheet, filling guide, and
OpenReview upload runbook now all point to the initializer as the preferred
first author-side action.

The OpenReview upload runbook and filling guide now point authors to:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
```

The full consolidated gate was rerun from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, 53-test focused pytest including
`tests/test_acl_author_gate_init.py`, clean ACL build, final LaTeX log scan,
candidate packet staging, exact packet inventory, adjacent checksum-sidecar
validation, private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`,
and `pdftotext_sections`. `pdfinfo` reported 12 pages, A4 page size, PDF 1.5,
and 306187 bytes.

The real repository report remains `status=human_blocked` with
`repo_blockers=[]` because the private author worksheet is not filled. The
initializer only creates the ignored local copy; it does not fill private
author, route, OpenReview, runtime, AI-assistance, license, media, scan, or
upload-decision values.

## Refresh After Final-Blocker Required Commands

After aligning `report_final_blockers.py` with the author-side runbook, the
report's `required_commands` list now gives the complete final handoff order:

```bash
python paper/venues/acl27/scripts/init_author_gate.py
python paper/venues/acl27/scripts/prefill_author_gate.py --apply
python paper/venues/acl27/scripts/check_author_gate.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

This is a reporting change, not an automated packet-staging behavior change.
The consolidated pre-upload gate still does not run `init_author_gate.py` or
`prefill_author_gate.py`; private author worksheet creation, repo-verifiable
prefill, and human filling remain explicit local author actions. The refreshed
focused tests and full gate passed with 53 focused ACL tests, a 12-page A4 PDF
1.5 staged packet, and 306187 bytes.

## Refresh After Target-Policy Source Refresh

After reopening the official ARR, EACL, and ACLPUB target-policy sources, the
route state remained unchanged: EACL 2027 via ARR is still the concrete public
2027 ACL-family route, while Annual ACL 2027 still lacks an official CFP/author
kit in checked official sources. Updating
`TARGET_CALL_POLICY_AUDIT.md` and `TARGET_LOCK_OPENREVIEW_REHEARSAL.md`
changed protected final-integrity sources, so the 41-source fingerprint was
refreshed before rerunning the consolidated gate.

```bash
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, 53-test focused pytest, clean ACL build, final LaTeX log scan,
candidate packet staging, exact packet inventory, adjacent checksum-sidecar
validation, private-token scan, acknowledgment scan, `pdfinfo`, `pdf_profile`,
and `pdftotext_sections`. The final blocker report remained
`status=human_blocked` with `repo_blockers=[]`; the staged PDF remained 12 A4
pages, PDF 1.5, and 306187 bytes.

## Refresh After Goal-Completion Reporter

After adding `report_goal_completion.py`, the consolidated runner now executes
a machine-readable goal-completion report after the final blocker report and
before focused pytest/build/staging. The reporter is intentionally lighter than
the full gate and reports the current state as
`candidate_ready_human_blocked`, not complete:

```text
repo_static_ready=true
candidate_ready_for_human_gate=true
repo_requirement_failures=[]
final_goal_complete=false
```

The full consolidated gate was rerun from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, goal-completion report, 60-test focused pytest, clean ACL build, final
LaTeX log scan, candidate packet staging, exact packet inventory, adjacent
checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`. The staged PDF remained 12
A4 pages, PDF 1.5, and 306187 bytes.

After adding `prefill_author_gate.py`, the full gate was rerun again. The
focused pytest suite now includes `tests/test_acl_author_gate_prefill.py`, and
the final blocker handoff recommends the prefill helper before manual
completion of `OPENREVIEW_AUTHOR_GATE_FILLED.local.md`. The local ignored
worksheet was prefilled for the eight repo-verifiable final-evidence rows, but
the final blocker report correctly remains `status=human_blocked` because route,
author, OpenReview form-copy, approval, optional-media, and final upload rows
remain human decisions.

## Refresh After Figure-Driven Main-Paper Rewrite

After adding the AI-generated method-chain schematic, the cleaner follow-up
method-chain imagegen v3 figure, the real render and material-effect panels, the
oblique-view single-object render-pair refresh, retaining selected InternNav
qualitative media for supplemental/rebuttal use, and later removing the main-text
InternNav rollout panel to protect the eight-page counted-content boundary, the
candidate was rebuilt from the current repository state on 2026-05-27:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, goal-completion report, 65-test focused pytest, clean ACL build, final
LaTeX log scan, candidate packet staging, exact packet inventory, adjacent
checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`. The final blocker report
remained `status=human_blocked` with `repo_blockers=[]`. A later Fig.3
red-material mitigation and layout-polish pass rebuilt the staged PDF as 11 A4
pages, PDF 1.5, and 3,337,110 bytes. A later Figure 2 proxy-row readability
pass rebuilt and staged the ACL PDF as 11 A4 pages, PDF 1.5, and 3,330,780
bytes. A subsequent v8 method-chain imagegen pass rebuilt and staged the ACL
PDF as 11 A4 pages, PDF 1.5, and 3,361,922 bytes. A later reviewer-risk
Discussion pass reran the full gate and staged the current ACL PDF as 11 A4
pages, PDF 1.5, and 3,362,820 bytes, with `Limitations` on page 8,
`Ethical Considerations` on page 9, selected InternNav Figure 3 on page 9, and
`References` starting on page 9. Local visual review found no overlap or
clipped text after replacing the broad pre-Limitations `\clearpage` with
targeted page breaks.
Subsequent reference-layout, Fig.3 overlay-color, page-8 table layout, and v9
method-chain imagegen passes preserved the candidate at 10 A4 pages. The latest
full gate stages a PDF 1.5 file of 3,313,612 bytes with the v9 Figure 1
schematic on page 2 and selected InternNav Figure 3 still on page 9.
Later all-page visual review also fixed the page-4 Method opening word spacing
and the page-5 `expanded30` prose token without changing experimental claims.
Another Figure 2 pass regenerated the real-render panel with cropped display
views for the white single-object proxy row, then shortened the caption and
nearby prose to avoid a page-6 orphan line while preserving the claim boundary.
The latest Figure 2 display pass keeps the same render sources but uses
cover-fit cropped display cells for the top proxy row, so the white objects are
larger and the gray side bands are mostly removed in the integrated PDF. A
follow-up readability pass keeps the same raw proxy-render pool but replaces
the nearly blank `#0004` display example with the more legible `#0023` pair and
adds a focused pytest guard for minimum top-row contrast; the consolidated
preupload gate now runs that guard as part of its 68-test focused suite.
The latest navigation visual pass keeps the selected official KuJiaLe rollout
panel as the full-width readable Figure 3 on page 9; it remains qualitative
orientation only and does not enter the safe staged media packet. The accepted
layout keeps the candidate under the 12-page cap and avoids a float-only
material-table page before Limitations.
The latest Figure 2 sample refresh switches the representative proxy row to the
same `#0023` asset's recorded full-object back view (`A_back.png`/`B_back.png`)
after a local visual review found the previous front-view crop too low-detail
at PDF scale. This remains deterministic empirical render evidence, not image
generation or a new experiment. The consolidated preupload gate now runs the
selected-proxy contrast guard as part of its 72-test focused suite and stages a
10-page A4 PDF 1.5 file of 3,487,597 bytes. A rendered staged page-6 spot check
shows Figure 2 and the following table without overlap.
A subsequent rendered-PDF spot check found that the back-view proxy still read
like a low-detail gray slab in the integrated page. The current front-detail
pass switches the representative proxy row to the recorded `#0011` front-view
pair (`A_front.png`/`B_front.png`) from the same proxy render pool and replaces
the selected-proxy contrast guard with a front-detail edge-density guard that
rejects back-only representative views. The full preupload gate passed again
with 72 focused tests, a 53-source fingerprint, clean build/staging, scans, PDF
profile checks, and ordered text-section checks. The staged candidate is now a
10-page A4 PDF 1.5 file of 3,493,873 bytes; rendered page 6 shows the front
drawer/handle details, Figure 2 caption, and Table 2 without overlap.
A follow-up pure visual review found that the flat front-view row was usable
but still visually weaker than an angled object render. The current Figure 2
proxy row therefore uses the recorded `#0011` top-front-right pair
(`A_top_front_right.png`/`B_top_front_right.png`) from the same empirical render
pool. The selected-proxy guard now requires a front/front-angled path plus both
minimum edge density and contrast. The full preupload gate passed again with 72
focused tests, a 53-source fingerprint, clean build/staging, scans, PDF profile
checks, and ordered text-section checks. The staged candidate is now a 10-page
A4 PDF 1.5 file of 3,514,678 bytes; rendered page 6 shows the angled proxy
object, Figure 2 caption, and Table 2 without overlap.
The follow-up sublabel precision pass keeps the same `#0011` top-front-right
render files but changes the proxy-cell sublabel from `#0011 full object view`
to `#0011 top-front-right object view`. The full preupload gate passed again
with 73 focused tests, a 53-source fingerprint, clean build/staging, scans, PDF
profile checks, and ordered text-section checks. The staged candidate is now a
10-page A4 PDF 1.5 file of 3,515,110 bytes, identical to the build PDF with
SHA-256 `2800402b662904faf83862cd1f5fd1374e9d81fa6bdd8768f72e0a59458fa794`;
rendered staged page 6 shows the angled proxy object, Figure 2 caption, and
Table 2 without overlap.
After the gate, `prefill_author_gate.py --apply --overwrite` refreshed only the
repo-verifiable private worksheet rows; `check_author_gate.py` still reports 19
human-only TODO fields.

A later visual/diagnostic pass rechecked the user-reported Fig.3 red-material
concern and confirmed that the staged Figure 3 is still the selected InternNav
rollout panel. The retired material-effect contact sheet remains excluded and
blocked by clean provenance because its original-MDL cells reuse stale
pre-rerender PNGs with `KooPbr`/`KooPbr_maps` stderr signals. The same pass
removed a narrow-column monospace evidence path from the page-4 Claim Registry
paragraph and added a layout regression guard. The refreshed full preupload
gate passed with 74 focused tests, a 53-source fingerprint, clean
build/staging, scans, PDF profile checks, and ordered text-section checks. The
staged candidate is now a 10-page A4 PDF 1.5 file of 3,513,952 bytes,
identical to the build PDF with SHA-256
`81acd09574094b915097cc23fa8687f7822ed5dcd976f9d0ea9587faca2a8177`; rendered
staged page 4 and page 9 checks show the Claim Registry typography and
InternNav Figure 3 without overlap.

A follow-up page-6 visual pass improved the same real Figure 2 proxy evidence
without introducing new data: the selected `#0011` top-front-right Original
MDL/noMDL render pair now uses deterministic crop `(140, 40, 780, 720)` and the
cell sublabel discloses `#0011 cropped top-front-right object view`. The
selected-proxy guard now includes a crop contrast-improvement check. The full
preupload gate passed again with 75 focused tests, a 53-source fingerprint,
clean build/staging, scans, PDF profile checks, and ordered text-section
checks. The staged candidate is now a 10-page A4 PDF 1.5 file of 3,553,091
bytes, identical to the build PDF with SHA-256
`7fed84db45e19f2e2ed56a67452d27ea04d0e4ffcf9a582e6a591a9e254163fe`; rendered
staged page 6 shows the cropped proxy object, Figure 2 caption, and Table 2
without overlap.

## Refresh After Qualitative VLM Panel Exclusion

After the render-log audit showed that the ACL qualitative VLM panel still lacks
clean original-condition render provenance, the ACL main paper stopped including
`fig_vlm_grounding_cases`. The claim-boundary checker now rejects reintroducing
that unsafe panel before clean render/overlay provenance exists.

The full consolidated gate was rerun from the current repository state on
2026-05-26:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy consistency,
OpenReview metadata consistency, OpenReview checklist copy-readiness,
citation-inventory, evidence-number, final-integrity fingerprint, final blocker
report, goal-completion report, 63-test focused pytest, clean ACL build, final
LaTeX log scan, candidate packet staging, exact packet inventory, adjacent
checksum-sidecar validation, private-token scan, acknowledgment scan,
`pdfinfo`, `pdf_profile`, and `pdftotext_sections`. The final blocker report
remained `status=human_blocked` with `repo_blockers=[]`; the staged PDF is now
11 A4 pages, PDF 1.5, and 215253 bytes.

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
| OpenReview metadata consistency | Pass; title and 181-word abstract match the LaTeX sources and remain under the 200-word abstract guidance. |
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
