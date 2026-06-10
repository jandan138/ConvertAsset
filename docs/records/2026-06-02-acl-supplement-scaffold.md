# 2026-06-02 ACL Supplement Scaffold

## Summary

Created a standalone ACL-style supplement entry point for the ACL/ARR candidate.
The supplement is intentionally separate from the 11-page main-paper candidate:
the main paper remains self-contained, while the supplement expands derivations,
diagnostic tables, material-effect examples, InternNav still panels, theory
notes, and reproducibility boundaries.

## Changed Paths

- `paper/venues/acl27/supplement.tex`
- `paper/venues/acl27/sections/supplement/*.tex`
- `paper/Makefile`
- `paper/shared/figures/gen_acl_supplement_navigation_crops.py`
- `paper/shared/figures/supplement/internnav_*_case*.png`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_v0_visual_review_20260602.json`
- `tests/test_paper_layout.py`
- `docs/superpowers/specs/2026-06-02-acl27-supplement-design.md`
- `docs/superpowers/plans/2026-06-02-acl27-supplement.md`

## Content Shape

The supplement has eight appendix sections:

- claim boundary and evidence map
- mathematical definitions and metric derivations
- VLM prompt and coordinate protocol
- GRScenes visual grounding diagnostics
- material-effect and NVIDIA-baseline diagnostics
- InternNav / DualVLN selected navigation stills
- mechanism hypotheses and interpretation
- reproducibility and media-boundary notes

The InternNav section includes two selected overview sheets and 12 per-case
navigation pages. The 0036/0066 rows are reflowed into 2x3 panels so the PDF
does not show them as unreadably thin strips.

## Verification

Build:

```bash
make -C paper acl27-supplement
```

PDF profile:

- artifact: `paper/venues/acl27/build/supplement.pdf`
- pages: 40
- page size: A4
- file size: 6,132,749 bytes
- SHA-256: `47e771514b43915997d5818c9c272a8ce291deab269e4cd17bf8911afab13c11`

Tests:

```bash
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_entrypoint_and_build_target tests/test_paper_layout.py::test_acl_supplement_has_eight_appendix_sections tests/test_paper_layout.py::test_acl_supplement_sources_stay_anonymous
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_navigation_0036_crops_are_readable_panels
```

Privacy scan:

```bash
pdftotext -layout paper/venues/acl27/build/supplement.pdf /tmp/acl27_supplement.txt
rg -n "/cpfs|/home/|/root/|zhuzihou|jandan138|github\\.com/jandan138|ConvertAsset\\.git" /tmp/acl27_supplement.txt
```

The `rg` command returned no matches.

Visual review:

- record: `paper/shared/evidence/raw/acl27_visual_review/supplement_v0_visual_review_20260602.json`
- overall verdict: `PASS_WITH_NOTES`
- note: the overview InternNav sheet is compact, but the per-case navigation
  pages provide the larger still evidence.

## Remaining Work

The supplement PDF is ready as a v0 scaffold, not a final submission packet.
Remaining author-gated work:

- decide whether to upload a separate anonymized media bundle for videos
- run an independent blind visual review if desired
- re-run the full ACL pre-upload gate after any final main-paper or supplement
  edits
- decide whether the final upload route is ARR or a direct ACL 2027 track once
  the live call page is fixed
