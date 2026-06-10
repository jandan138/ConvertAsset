# 2026-05-30 ACL Fig.3 Provenance Caption Hardening

## Scope

This record documents a targeted ACL manuscript edit after the user-reported
concern that Figure 3's `Original MDL` material cells might be confused with
the historical red-material fallback issue.

## Change

Updated `paper/venues/acl27/sections/results.tex` so the Figure 3 caption now
states that the original-MDL cells passed a **log-checked clean
rerender/provenance gate**.

The accepted wording keeps the claim narrow: Figure 3 is still selected
qualitative material-effect evidence only. It does not expand the NVIDIA
baseline comparison, claim population-level failure rates, or certify
mechanism-level MDL preservation.

## Visual Iteration

A longer caption sentence was first tested that explicitly said every promoted
original cell had a checked render log with no MDL-resolution error signal.
Local rendered-PDF review rejected that draft because it moved Figure 4 to page
10 and left page 9 with a large blank column. The final compact wording
preserves the provenance signal while keeping the page-8/page-9 layout stable.

Targeted visual review record:

```text
paper/shared/evidence/raw/acl27_visual_review/fig3_provenance_caption_visual_review_20260530.json
```

## Current Candidate

The full pre-upload gate restaged the candidate packet after the caption
hardening:

```text
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=d6b74efc377ed51ca502d55d3d785cc43101e259bbce022388088e06c910432e
bytes=4066557
pages=11
created=Sat May 30 19:01:27 2026 CST
```

The build and staged PDFs are byte-identical. The adjacent ignored checksum
sidecar is:

```text
paper/submissions/acl27_arr_candidate_20260526.sha256
sha256=f95a2feb524657182e849720c829a243765cf765d12153aa58627868ad1043d4
```

## Verification

Commands:

```bash
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
make -C paper acl27
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Results:

- Material-effect clean provenance: `ok=true`,
  `status=clean_material_effect_panel_ready`,
  `checked_original_mdl_log_count=4`,
  `original_mdl_error_signal_count=0`.
- Claim-boundary check: `ok=true`.
- Metadata consistency: `ok=true`, abstract remains 183 words.
- Final-integrity fingerprint: `ok=true`, source count now 57.
- Clean ACL build: pass, 11-page A4 PDF 1.5.
- Full pre-upload gate: pass; 93 focused tests passed, clean build/staging,
  packet inventory, checksum sidecar, private-token scan, acknowledgment scan,
  `pdfinfo`, `pdf_profile`, and `pdftotext` section checks all passed.

Remaining blockers are unchanged and human-only: target route confirmation,
private author-gate completion, OpenReview form copy, and runtime/AI/media
approvals.
