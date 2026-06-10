# 2026-05-28 ACL Figure 4 Label Readability Polish

## Purpose

Improve the main-paper Figure 4 path-panel readability without changing the
selected InternNav still evidence. The previous full-PDF visual review passed
the page but noted that the per-case labels were small at page scale.

## Change

Updated `paper/shared/figures/gen_internnav_main_readable.py`:

- kept the main Figure 4 image at `1748 x 806` px;
- widened the left per-case label column from `230` px to `270` px;
- reduced each evidence frame from `360` px to `350` px to preserve total
  figure width;
- increased row-key/detail fonts to `22` px and `16` px;
- exposed the main-panel layout values in the generator report so tests can
  lock the page-scale readability intent.

Regenerated:

```text
paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png
sha256=818525fcc0a5fd0b4e692ddd9d2738e673eb3b70a2b2dd90895cab7dd0d51a6e

paper/shared/figures/fig_internnav_rollout_0036_0066_column.png
sha256=7ca4fdf99c648d740d64ad27e69fb44e4b6da20a98e58e51996163a65243dfe5
```

After the full pre-upload gate, the build and staged PDFs are byte-identical:

```text
paper/venues/acl27/build/main.pdf
sha256=8d55b5e53f437839d0fe2d59128d91a1c152fb47c2fd925ea92f4fa2318ed352
pages=11
bytes=4066548
created=Thu May 28 21:36:20 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=8d55b5e53f437839d0fe2d59128d91a1c152fb47c2fd925ea92f4fa2318ed352
```

## Visual Review

Durable review record:

```text
paper/shared/evidence/raw/acl27_visual_review/figure4_label_readability_review_20260528.json
```

The page-9 PDF render after the rebuild is:

```text
/tmp/convertasset_acl27_fig4_label_polish/page-09.png
sha256=cb7fbc9efb13ff560646189e2f39067e5c720abb446ce85958ca12e31e4fde10
```

Local visual verdict: `PASS_WITH_MINOR_CAVEAT`.

The case IDs and `SR O/N` labels are easier to scan, the selected original/noMDL
start/end stills are unchanged in meaning, the caption remains attached to the
figure, and the page still starts the two-column text cleanly at `Limitations`
and `Ethical Considerations`.

Pixel spot checks reported `strong_red_pixels=0` for both the source figure and
the rendered page. The source PNG has two magenta-threshold pixels under the
very narrow spot check, but the rendered PDF page has zero; this does not
indicate the historical red-material fallback and does not affect the
InternNav overlay recoloring claim.

## Claim Boundary

Figure 4 remains selected qualitative path-inspection evidence only. The
quantitative navigation claim remains tied to the 99-episode paired InternNav
run and official-scene load/render checks. This polish changes readability, not
the evidence scope.

## Verification

Commands run:

```bash
python -m pytest -q tests/test_internnav_rollout_figure.py::test_internnav_readable_panel_uses_wider_page_scale_row_labels
python paper/shared/figures/gen_internnav_main_readable.py
make -C paper clean-acl27 acl27
pdftoppm -f 9 -l 9 -png -r 180 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_fig4_label_polish/page
pdftoppm -png -r 150 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_current_visual_review_after_fig4_labels/page
pdfinfo paper/venues/acl27/build/main.pdf
pdftotext -layout paper/venues/acl27/build/main.pdf - | rg -n "Figure 4:|Limitations|Ethical Considerations|References"
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/run_preupload_gate.py
python -m pytest -q tests/test_internnav_rollout_figure.py tests/test_acl_integrity_fingerprint.py
```

The full gate passed with 91 focused tests, clean ACL rebuild, packet staging,
PDF profile checks, and ordered text-section checks. The extra Fig4/fingerprint
pytest command passed 9 tests.
