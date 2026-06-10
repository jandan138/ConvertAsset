# 2026-05-28 ACL Figure 3 Readability Polish

## Scope

This record documents a layout-only refresh of the ACL main-paper material-effect
qualitative panel:

```text
paper/shared/figures/gen_material_effect_qualitative.py
paper/shared/figures/fig_material_effect_baseline_qualitative.png
paper/shared/figures/fig_material_effect_baseline_qualitative.report.json
tests/test_material_effect_baseline_qualitative.py
```

No new experiment was run, and no generated imagery was introduced. The update
uses the same recorded original/noMDL/NVIDIA render sources and changes only the
contact-sheet typography for PDF-scale readability.

## Change

The old Figure 3 contact sheet used small footer text under each row to identify
the target category and covered effects. In the rendered ACL PDF this text was
hard to scan. The generator now places each row's case/effect label at the top
of the row and uses larger bold condition labels:

```text
header_h = 42
caption_h = 0
condition_label_font_size = 18
case_label_font_size = 16
```

Effect identifiers are also rendered as reader-facing labels such as
`opacity/transparency`, `normal/bump`, and `displacement/height` rather than raw
manifest keys.

## Guard

Added a focused regression test:

```text
tests/test_material_effect_baseline_qualitative.py::test_contact_sheet_uses_pdf_readable_row_headers_instead_of_tiny_footers
```

The test first failed against the old footer-heavy layout:

```text
assert layout["caption_h"] == 0
E assert 22 == 0
```

After the generator update, the focused Figure 3 tests pass.

## Visual Review

Local rendered-PDF visual review of page 8 found:

- Figure 3 still appears on page 8.
- The four selected rows now expose target/effect labels at page scale.
- The three condition columns remain aligned as Original MDL, ConvertAsset, and
  NVIDIA.
- The caption and following Discussion/Conclusion text do not overlap.
- The figure remains selected qualitative evidence only; Table 5 remains the
  governing material-effect claim-boundary artifact.

Durable visual-review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/figure3_readable_labels_review_20260528.json
```

## Verification

Commands run:

```bash
python -m pytest -q tests/test_material_effect_baseline_qualitative.py::test_contact_sheet_uses_pdf_readable_row_headers_instead_of_tiny_footers
python -m pytest -q tests/test_material_effect_baseline_qualitative.py::test_contact_sheet_uses_pdf_readable_row_headers_instead_of_tiny_footers tests/test_material_effect_baseline_qualitative.py::test_contact_sheet_writes_three_condition_panel_for_ready_cases
python paper/shared/figures/gen_material_effect_qualitative.py
python -m pytest -q tests/test_material_effect_baseline_qualitative.py tests/test_material_effect_qualitative_clean_provenance.py
make -C paper acl27
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Observed results:

```text
focused red: failed as expected on caption_h=22
focused green: 2 passed
material-effect figure/provenance tests: 10 passed
make -C paper acl27: 11-page PDF built
check_claim_boundaries.py: ok=true
check_integrity_fingerprint.py: ok=true after fingerprint refresh
run_preupload_gate.py: ok=true
focused_pytest=89 passed in 3.51s
pages=11
size=3,625,413 bytes
sha256=cafa41976b46f16760883e0dd70bd69a1a777f16caa7136d8ec5b648a3b64156
created=2026-05-28 15:56:58 CST
rendered_page_8_sha256=ba29e98a331afea7af10458120af6f0968599bbc38547129c0ea2ffc919d42a2
```

Intermediate artifact hashes before the final consolidated pre-upload gate:

```text
fig_material_effect_baseline_qualitative.png sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
fig_material_effect_baseline_qualitative.report.json sha256=1f1c254c90c562921173bba60f5e2132064cedb2b572a834dc12401bda3284df
gen_material_effect_qualitative.py sha256=a42e7a61bb0f7dc3eb046af09e21718b643eb29fa37ef03e64fca107d524fa78
rendered page 8 sha256=ba29e98a331afea7af10458120af6f0968599bbc38547129c0ea2ffc919d42a2
```
