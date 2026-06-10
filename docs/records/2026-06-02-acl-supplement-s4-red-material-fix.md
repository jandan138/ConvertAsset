# 2026-06-02 ACL Supplement S4 Red-Material Fix

## Scope

This record fixes the ACL supplement Figure S4 issue where the supplement
reintroduced `fig_vlm_grounding_cases.png`, an older diagnostic VLM panel that
contained abnormal red material from the pre-repair GRScenes MDL render stack.

## Root Cause

The old S4 panel mixed selected VLM point overlays with original-condition
renders whose MDL/KooPbr dependencies had previously failed. The earlier
2026-05-26 root-cause record already marked that panel as unsafe for clean
qualitative evidence unless the exact images were rerendered and the VLM
predictions were rerun or revalidated. The supplement render atlas accidentally
reintroduced that panel and added a caption saying the red material was part of
the diagnostic probe evidence.

That caption was not evidence-safe. The red surfaces were render-stack fallback
artifacts, not a clean material phenomenon to preserve in the supplement.

## Fix

- Added `paper/shared/figures/gen_supplement_vlm_clean_rerender_panel.py`.
- Generated `paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png`.
- Registered the new panel in `paper/shared/figures/sources.yaml`.
- Replaced the supplement S4 include in
  `paper/venues/acl27/sections/supplement/01a_render_atlas.tex`.
- Removed the unsafe caption language about red material being part of probe
  evidence.
- Added regression checks in `tests/test_paper_layout.py` so the supplement
  cannot silently re-include `fig_vlm_grounding_cases.png` or the old caption.

The replacement S4 panel uses four clean rerender reports:

- `47aa36277a54f6ca90cc.zoom_018.clean_rerender_20260528.json`
- `f35ef3d86c42446b7ddf.zoom_018.clean_rerender_20260528.json`
- `c27086f557d316584264.zoom_018.clean_rerender_20260528.json`
- `e2ec085d524d5df4455d.zoom_020.clean_rerender_20260528.json`

All four reports have `both_commands_exit_zero=true`,
`both_images_exist=true`, `original_mdl_error_signal=0`, and
`converted_mdl_error_signal=0`.

## Claim Boundary

The new S4 is not a VLM prediction overlay. It shows post-repair GRScenes
target-view renders and registered target boxes only. This avoids binding the
2026-05-23 frozen VLM prediction outputs to 2026-05-28 clean rerender images.
The VLM evidence remains table-level unless predictions are rerun or revalidated
on the exact clean images.

## Related Visual Iteration

During the same pass, the material and navigation intro strips were regenerated
from cleaner crops:

- `fig_supplement_material_intro_strip.png` no longer includes clipped source
  labels and shows covered-bin, clearcoat, and procedural-texture crops.
- `fig_supplement_navigation_intro_strip.png` uses denser metric/still/route
  crops and avoids clipped metric-axis labels.

The rendered PDF pages for these strips remain visually sparse because the
strips are currently placed inside one ACL column. This is acceptable for the
S4 fix but remains a layout-polish opportunity if we want these previews to be
full-width floats.

## Verification

Commands:

```bash
python paper/shared/figures/gen_supplement_vlm_clean_rerender_panel.py
python paper/shared/figures/gen_supplement_task_media_atlases.py
python -m pytest -q tests/test_paper_layout.py
make -C paper acl27-supplement
pdftoppm -f 8 -l 8 -r 170 -png paper/venues/acl27/build/supplement.pdf tmp/acl27_supplement_visual_check/page
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n "Red material|registered diagnostic figure|fig_vlm_grounding_cases|Post-repair GRScenes target-view|No VLM point marker" -S
```

Results:

- `tests/test_paper_layout.py`: `27 passed`.
- `make -C paper acl27-supplement`: passed; output PDF has 40 pages.
- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `ef8c0115a9fd30ee9baa4dcf9ca20516ea0bd461f8147635730fa12c800126ef`.
- `fig_supplement_vlm_clean_rerender_panel.png` SHA-256:
  `b430f20f9cdffc78a002f891587b00977186d27999b8bdab830bd44c521e75ce`.
- Text scan no longer finds the unsafe red-material caption or
  `fig_vlm_grounding_cases`; it finds the new post-repair S4 caption.
- Local render visual review of page 8: PASS. No large red material fallback is
  visible.

Structured visual-review evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/supplement_s4_clean_rerender_fix_20260602.json
```

## Follow-Up Shared-Source Cleanup

After rechecking the user-visible Figure S4 caption, I also found a separate
residual reference in `paper/shared/sections/experiments.tex`: the shared
results section still included `fig_vlm_grounding_cases.pdf`. The current ACL
`main.pdf` and `supplement.pdf` did not contain the old red-material caption,
but leaving that shared reference in place was unsafe because a future venue
wrapper could re-import the old qualitative panel.

The shared results section now keeps the VLM evidence table-first and states
that the earlier selected point-overlay panel is not used because it came from
pre-repair GRScenes diagnostic renders. A regression test was added so
`paper/shared/sections/experiments.tex` cannot silently reintroduce
`fig_vlm_grounding_cases` or the old red-material caption language.

Additional verification:

```bash
python -m pytest -q tests/test_paper_layout.py -k "shared_experiments_excludes_unsafe_vlm_red_material_panel or acl_supplement_excludes_unsafe_vlm_red_material_panel"
python -m pytest -q tests/test_paper_layout.py tests/test_acl_claim_boundaries.py
make -C paper acl27-supplement
make -C paper acl27
pdftotext paper/venues/acl27/build/supplement.pdf - | rg -n "Red material|registered diagnostic figure|Selected VLM grounding cases|fig_vlm_grounding_cases" -S
pdftotext paper/venues/acl27/build/main.pdf - | rg -n "Red material|registered diagnostic figure|Selected VLM grounding cases|fig_vlm_grounding_cases" -S
```

Results:

- Targeted red-material exclusion tests: `2 passed, 32 deselected`.
- Layout and claim-boundary tests: `43 passed`.
- `make -C paper acl27-supplement`: passed/up-to-date.
- `make -C paper acl27`: passed/up-to-date.
- Both PDF text scans returned no old red-material caption or unsafe figure
  reference.
- Rendered supplement page 8 was visually checked locally: current S4 is the
  post-repair target-view rerender panel with green boxes and no large red
  fallback-material artifact.

## 2026-06-02 Recheck After User Report

The user re-reported a Figure S4 caption that framed red material as selected
diagnostic evidence. I rechecked the current source and rebuilt supplement PDF.
The old caption is not present in the current PDF. The current Figure S4 text is:

```text
Figure S4: Post-repair GRScenes target-view render panel for the VLM evidence chain.
```

Current verification:

- `paper/venues/acl27/build/supplement.pdf` SHA-256:
  `a7cb640814ab086dd5f0e3810a741367bc2f166d92d7c39151dd737541718fbb`.
- Output PDF page count: 39.
- Current S4 rendered page red fraction: `0.0`.
- Current S4 source figure red fraction: `0.0`.
- Legacy `fig_vlm_grounding_cases.png` red fraction: `0.051321`; it remains
  excluded from the supplement and shared experiments section.
- Text scan found the current post-repair S4 caption and did not find
  `Red material`, `Selected VLM grounding cases`,
  `registered diagnostic figure`, or `fig_vlm_grounding_cases`.

Structured evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/supplement_material_decision_map_20260602.json
```

## 2026-06-02 Recheck After Later Supplement Insertions

The user reported the old caption again:

```text
Figure S4: Selected VLM grounding cases ... Red material in these diagnostic cases ...
```

Current root-cause status remains unchanged: that caption belongs to the old
unsafe `fig_vlm_grounding_cases` panel. The red material in that panel is not
intentional evidence; it is the earlier MDL/KooPbr fallback artifact from the
pre-repair render stack. The current ACL supplement source excludes
`fig_vlm_grounding_cases` and uses the clean rerender panel
`fig_supplement_vlm_clean_rerender_panel.png`.

Because later supplement visual iterations inserted new figures before the VLM
panel, the numbering has shifted:

- Current Figure S4 is `fig_render_scene_evidence_wide.png`, captioned as a
  wide render evidence view.
- Current Figure S6 is `fig_supplement_vlm_clean_rerender_panel.png`, the
  post-repair GRScenes target-view render panel.

Current verification against `paper/venues/acl27/build/supplement.pdf`:

- PDF SHA-256:
  `028ecdf152c4b870920a13d6e633bdc915af98b0f4723373fd756091a93e701b`.
- Output PDF page count: `41`.
- Rendered page 8 / current Figure S4 red fraction: `0.000000`.
- Rendered page 10 / current Figure S6 red fraction: `0.000000`.
- Legacy `fig_vlm_grounding_cases.png` red fraction: `0.055537`; it remains
  excluded from the ACL supplement and shared results source.
- `pdftotext` finds the current Figure S4 and Figure S6 captions, and does not
  find `Red material`, `Selected VLM grounding cases`,
  `registered diagnostic figure`, or `fig_vlm_grounding_cases` in the current
  supplement.
- Targeted regression tests:
  `python -m pytest -q tests/test_paper_layout.py -k "unsafe_vlm_red_material_panel or vlm_clean_rerender"`
  returned `3 passed, 43 deselected`.

Structured evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/supplement_s4_red_material_user_recheck_20260602.json
```
