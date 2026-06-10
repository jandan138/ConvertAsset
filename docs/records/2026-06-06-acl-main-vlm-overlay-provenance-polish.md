# 2026-06-06 ACL Main VLM Overlay Provenance Polish

## Scope

Round 43 continued the ACL main-paper visual review loop on
`paper/venues/acl27/build/main.pdf`. The accepted target was page 5, in the
VLM-grounding claim-boundary paragraph immediately before
`Material Effects and NVIDIA Baseline Boundaries`. The current render split
`VLM-overlay prove-` / `nance`, which was distracting in a paragraph whose
purpose is to separate qualitative orientation panels from frozen table claims.

## Change

- Replaced `until they have clean render logs and VLM-overlay provenance` with
  `until clean render logs and VLM overlay provenance exist for the exact
  images`.
- Removed the hyphenated `VLM-overlay` construction and made the evidence unit
  explicit: the exact images need clean logs and overlay provenance before
  qualitative panels can support more than orientation.
- Preserved the surrounding claim boundary: VLM answer and point-grounding
  claims remain tied to frozen tables, not figure panels.

Rejected intermediate route: `their image-level render logs and VLM overlay
provenance are clean` removed `prove-` / `nance` but introduced an `image-` /
`level` line break, so it was rebuilt, visually reviewed, and replaced.

## Visual Review

- Current render: `tmp/acl_main_visual_iter_20260606_round43_current/contact_sheet.png`
- After render: `tmp/acl_main_visual_iter_20260606_round43_after/contact_sheet.png`
- Before/after focus sheet: `tmp/acl_main_visual_iter_20260606_round43_after/focus_before_after_p5.png`
- Pages 5-6 focus sheet: `tmp/acl_main_visual_iter_20260606_round43_after/focus_p5_p6.png`

Observed result: page 5 no longer renders `VLM-overlay prove-` / `nance`. The
accepted text now reads `logs and VLM overlay provenance exist for the` /
`exact images`. The page 5 `Material Effects and NVIDIA` heading remains at the
same line-number position, page 6 keeps the embodied-data section and Figure 3
stable, and the PDF remains 11 pages.

## Verification

- `make -C paper acl27` passed.
- Log blocker scan for overfull boxes, label warnings, undefined references,
  multiply defined labels, rerun-to-cross-reference warnings, and lineno
  warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py`
  passed with `102 passed in 15.47s`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `ok=true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `ok=true`; abstract word count remained 169.

Final PDF identity:

- SHA256: `b214f8bbc9d000e40e34c008cd11897ae1b79700e25f29335944c137a2334055`
- Pages: 11
- Size: 5,188,369 bytes

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/main_round43_vlm_overlay_provenance_polish_20260606.json`
