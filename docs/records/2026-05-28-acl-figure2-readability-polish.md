# 2026-05-28 ACL Figure 2 Readability Polish

## Scope

This record documents a deterministic layout-only refresh of the ACL main-paper
Figure 2 render-evidence panel:

```text
paper/shared/figures/gen_render_scene_evidence_wide.py
paper/shared/figures/fig_render_scene_evidence_wide.png
paper/shared/figures/fig_render_scene_evidence_wide.pdf
tests/test_render_scene_evidence_figure.py
```

No new experiment was run and no generated imagery was introduced. The update
uses the same recorded real render sources and changes only the panel
composition for PDF-scale readability.

## Change

The proxy-object row now uses the same near-full text width as the GRScenes
scene row:

```text
OBJECT_CELL_W = CELL_W
OBJECT_H = 340
```

The figure still shows the selected `#0011` top-front-right cropped object
detail pair and the representative GRScenes commercial-interior scene pair.
The caption and sublabels continue to disclose that the top row is a cropped
proxy detail view and that quantitative claims remain table-bound.

Follow-up visual-first polish on the same day keeps the same recorded real
render sources, but removes internal title/subtitle/footer microcopy from the
bitmap and gives that space back to the panels. The LaTeX caption now carries
the explanation and claim boundary, while the bitmap keeps only row labels and
condition labels.

```text
TITLE_H = 0
SUBTITLE_H = 0
ROW_FOOTER_H = 0
OBJECT_H = 380
SCENE_H = 360
```

This keeps Figure 2 as real render evidence, not generated imagery, and does
not change any metric or task evidence.

## Guard

Added and exercised a focused readability guard:

```text
tests/test_render_scene_evidence_figure.py::test_proxy_object_row_uses_near_full_text_width_for_pdf_readability
tests/test_render_scene_evidence_figure.py::test_render_scene_panel_uses_visual_first_layout_without_microcopy
```

The test first failed on the old narrow layout:

```text
OBJECT_CELL_W=620
CELL_W=853
assert 620 >= 810
```

After the layout update, the full Figure 2 test file passes. The older selected
proxy detail test now checks absolute strong-edge pixels rather than edge ratio,
because the enlarged cell increases visual area while preserving or increasing
detail pixels.

The visual-first guard first failed against the older microcopy-heavy layout:

```text
assert module.TITLE_H == 0
E AssertionError: assert 34 == 0
```

After the update, the full Figure 2 test file reports `7 passed`.

## Visual Review

Local rendered-PDF visual review at page scale found:

- Figure 2 remains on page 6.
- The updated proxy row is larger and readable as a drawer/handle detail pair,
  with less internal microcopy competing for space.
- Figure 2, its caption, Table 2, and the following body text do not overlap.
- The main caveat remains qualitative: the top row is a cropped detail view,
  not an uncropped full-object view; this is disclosed in the figure text.

Durable visual-review summary for the follow-up polish:

```text
paper/shared/evidence/raw/acl27_visual_review/figure2_visual_first_layout_review_20260528.json
```

Rendered full-PDF contact sheet:

```text
tmp/acl27_fig2_readability_full_visual_20260528/contact_sheet.png
sha256=06502d3fc295d79af3050dd8ab0c4cc2197c84c4099a0ada1e972cc73586d8b8
```

## Verification

Commands run:

```bash
python -m pytest -q tests/test_render_scene_evidence_figure.py
python paper/shared/figures/gen_render_scene_evidence_wide.py
python -m pytest -q tests/test_render_scene_evidence_figure.py tests/test_paper_layout.py
make -C paper acl27
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Observed results:

```text
tests/test_render_scene_evidence_figure.py: 7 passed
tests/test_render_scene_evidence_figure.py tests/test_paper_layout.py: 19 passed
run_preupload_gate.py: ok=true
focused_pytest=89 passed in 1.96s
pages=11
size=3,615,704 bytes
sha256=1a7e3be4f3fea42f5fc8ec3359522a828e0ab2d71f8190054ee8357f81afbf24
created=2026-05-28 15:34:05 CST
rendered_page_6_sha256=c4bcad2fb1e5f47037e2c7c7cf3a7a6ea4879a6f3160ca7a690e2f4396d75ca2
```

The build PDF and staged packet PDF are byte-identical. The final blocker state
remains human-gated, not repo-blocked.
