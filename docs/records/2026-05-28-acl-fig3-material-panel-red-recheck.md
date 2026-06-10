# 2026-05-28 ACL Fig.3 Material Panel Red Recheck

## Scope

This record rechecks the user-reported abnormal red material in
`paper/venues/acl27/build/main.pdf` Figure 3 after the material-effect panel
was promoted back into the ACL main paper.

## Finding

The current build does not reproduce the abnormal red `Original MDL` material.
Current Figure 3 is the selected material-effect qualitative panel on page 8,
sourced from:

```text
paper/shared/figures/fig_material_effect_baseline_qualitative.png
```

The current source figure and rendered PDF page both have zero strong-red pixels
under the spot check:

```text
paper/shared/figures/fig_material_effect_baseline_qualitative.png
  strong_red_pixels=0, redish_pixels=0
/tmp/convertasset_fig3_diag/page-08.png
  strong_red_pixels=0, redish_pixels=0
```

Visual inspection also shows no saturated red fallback in the four
`Original MDL` cells. The visible rows are bottle, clock, cup, and backpack,
with columns `Original MDL`, `ConvertAsset`, and `NVIDIA`.

## Root-Cause Diagnosis

The earlier red `Original MDL` cells were stale render evidence produced before
the clean rerender/provenance pass, not proof that the mounted MDL import repair
failed again. The historical failure mode was consistent with unresolved KooPbr
MDL imports and Isaac Sim MDL shade-node errors. The current selected original
renders pass the clean-provenance guard:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

For the four selected `Original MDL` stderr logs, the checked error terms were
absent:

```text
C108
C120
Failed to create MDL shade node
KooPbr
KooPbr_maps
could not find module
```

## Current Artifacts

```text
paper/venues/acl27/build/main.pdf
sha256=e0de91499b4f4f9120da4a133811985698c7cc5dcd1aa391f81fa016764bb844
pages=11
bytes=3625276
created=Thu May 28 16:56:47 2026 CST

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
```

The staged candidate PDF is byte-identical to the build PDF:

```text
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=e0de91499b4f4f9120da4a133811985698c7cc5dcd1aa391f81fa016764bb844
```

## Follow-up Recheck: Current Build Path

After the user reported seeing abnormal red material in Figure 3 again, the
current on-disk build was re-rendered from:

```text
paper/venues/acl27/build/main.pdf
sha256=99507373a15a835dd9da181a6432dc90e268cd4bf73a9ed339e8c971b7d7437d
pages=11
bytes=3625282
created=Thu May 28 16:13:33 2026 CST

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a

/tmp/convertasset_fig3_user_diag/page-08.png
sha256=c70ebaa34bcb4937862b5904a8d0272154becf59124306208608603715d08c74
```

The rendered build page 8 and the staged-candidate page 8 were visually
identical at the checked resolution. The source figure and rendered PDF page
again reported zero strong-red, reddish, or warm-red-dominant pixels under the
spot-check thresholds:

```text
/tmp/convertasset_fig3_user_diag/page-08.png
  strong_red_pixels=0, reddish_pixels=0, warm_red_dominant_pixels=0

paper/shared/figures/fig_material_effect_baseline_qualitative.png
  strong_red_pixels=0, reddish_pixels=0, warm_red_dominant_pixels=0
```

The clean-provenance gate still passes:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

The checked original-MDL stderr logs remain free of `C108`, `C120`,
`Failed to create MDL shade node`, `KooPbr`, `KooPbr_maps`, and
`could not find module`. The only diagnostic line seen in those logs was an
Isaac extension-resolution warning for `omni.kit.viewport`, not an MDL material
resolution failure. A dry-run of `scripts/fix_mdl_absolute_imports.py` over the
two Fig.3 selected scene roots also found `candidate_files=1566`,
`changed_files=0`, `total_replacements=0`, and `errors=0`, so the repaired MDL
import form is already present in those mounted assets. Therefore the current
reproduced diagnosis is: the active build artifact does not contain the
historical red material fallback; if a viewer still shows red Original-MDL
cells, it is likely displaying a cached or older PDF/image rather than the
current `build/main.pdf`.

## Follow-up Recheck: 16:56 Current Candidate

After the final same-day pre-upload gate, the current build path and staged
packet were checked again:

```text
paper/venues/acl27/build/main.pdf
sha256=e0de91499b4f4f9120da4a133811985698c7cc5dcd1aa391f81fa016764bb844
pages=11
bytes=3625276
created=Thu May 28 16:56:47 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=e0de91499b4f4f9120da4a133811985698c7cc5dcd1aa391f81fa016764bb844

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
size=1124x672

/tmp/convertasset_fig3_diag/page-08.png
sha256=c70ebaa34bcb4937862b5904a8d0272154becf59124306208608603715d08c74

/tmp/convertasset_fig3_diag/extracted/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
size=1124x672
```

The source Figure 3 PNG, the rendered PDF page 8, and the extracted embedded
PDF image all report:

```text
strong_red_pixels=0
redish_pixels=0
```

The four selected `Original MDL` stderr logs are short current rerender logs
and still contain no `KooPbr`, `KooPbr_maps`, `could not find module`,
`Failed to create MDL shade node`, `C120`, or `C108` matches. The only common
diagnostic line is an Isaac extension dependency warning, not an MDL material
resolution failure.

## Claim Boundary

Figure 3 can support only selected qualitative inspection for the four
GRScenes-covered material-effect bins after clean original-MDL rerender
provenance. It must not be used as:

- a population-level NVIDIA failure-rate estimate;
- a mechanism-level MDL preservation certificate;
- a procedural-texture success case;
- an official-scene NVIDIA navigation baseline.

The governing material-effect claim boundary remains Table 5.

## Verification

Commands run:

```bash
pdfinfo paper/venues/acl27/build/main.pdf
pdftotext -layout paper/venues/acl27/build/main.pdf - | rg -n "Figure 3:|Figure 4:|Limitations|References"
pdftoppm -f 8 -l 8 -png -r 220 paper/venues/acl27/build/main.pdf /tmp/convertasset_fig3_diag/page
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py
sha256sum paper/venues/acl27/build/main.pdf paper/submissions/acl27_arr_candidate_20260526/main.pdf paper/shared/figures/fig_material_effect_baseline_qualitative.png
```

Durable visual-review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/material_effect_main_figure_visual_review_20260528.json
```

## Follow-up Recheck: 18:48 Current Build

After the Figure 4 wide-panel manuscript edit, the current build path was
checked again because the user reported seeing abnormal red material in the
`Original MDL` cells:

```text
paper/venues/acl27/build/main.pdf
sha256=36b2f0fae8ead9955016466227ef9936fa0f454427577aefb48b53c523116711
pages=11
bytes=3991259
created=Thu May 28 19:33:56 2026 CST

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a

/tmp/convertasset_fig3_final_recheck/page-08.png
sha256=b5665e17c65837894df30d7848c857a84e5f0175fe05fc96a27474777214a779

/tmp/convertasset_fig3_final_recheck/extracted/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
```

The source Figure 3 PNG, rendered PDF page 8, and extracted embedded PDF image
all report:

```text
strong_red_pixels=0
redish_pixels=0
warm_red_dominant_pixels=0
magenta_fallback_like_pixels=0
```

The clean-provenance checker still reports
`status=clean_material_effect_panel_ready`, `selected_case_count=4`,
`checked_original_mdl_log_count=4`, and
`original_mdl_error_signal_count=0`. A dry-run of
`scripts/fix_mdl_absolute_imports.py` over the two selected scene roots with
`--follow-symlinks` found `candidate_files=1566`, `changed_files=0`,
`total_replacements=0`, and `errors=0`.

Current diagnosis is unchanged after the full pre-upload gate rerun: the active
Fig.3 source and active staged/build PDF do not show the historical red MDL
fallback. If red `Original MDL` material is still visible in a viewer, the
viewer is showing a stale PDF/image/cache or an older pre-rerender artifact, not
the current `build/main.pdf`.

## Follow-up Recheck: User-Reported Current Path

The exact user-reported path was checked again:

```text
paper/venues/acl27/build/main.pdf
sha256=36b2f0fae8ead9955016466227ef9936fa0f454427577aefb48b53c523116711
pages=11
bytes=3991259
created=Thu May 28 19:33:56 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=36b2f0fae8ead9955016466227ef9936fa0f454427577aefb48b53c523116711

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a

/tmp/convertasset_fig3_diag/page-08.png
sha256=ccea54257c62a0e1244c691c24d2576ef36312c8aef9e689519e37eec580cf1e
```

The ACL source still includes Figure 3 through:

```text
paper/venues/acl27/sections/results.tex
  -> figures/fig_material_effect_baseline_qualitative.png
```

`pdfimages -list` reports the embedded page-8 figure image as an RGB
1124-by-672 image, matching the source PNG dimensions. Local visual inspection
of both the source PNG and the rendered page-8 PNG found no saturated red MDL
fallback in the `Original MDL` column. Pixel spot checks on both files reported
zero pixels for the strong-red, dominant-red, broad-reddish, and magenta-red
fallback-like thresholds.

The current clean-provenance guard still passes:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

The four selected `Original MDL` stderr logs contain no matches for `KooPbr`,
`KooPbr_maps`, `could not find module`, `Failed to create MDL shade node`,
`C108`, or `C120`. The only non-empty diagnostic lines are Isaac extension
dependency warnings for `omni.kit.viewport`, which are not material-resolution
fallback signals.

A dry-run over the two selected scene roots again reports that the mounted MDL
files are already repaired:

```text
candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

Diagnosis remains unchanged: the active PDF and active Figure 3 source do not
contain the historical red `Original MDL` material fallback. A viewer that still
shows red material in this figure is most likely displaying an older cached PDF,
an old extracted page image, or a retired pre-rerender contact sheet rather than
the current `paper/venues/acl27/build/main.pdf`.

## Follow-up Recheck: Current v18 PDF Build

After the Figure 1 v18 rebuild, the current user-reported PDF path was checked
again:

```text
paper/venues/acl27/build/main.pdf
sha256=5f0e2d5a54dbe1068c244c427eb4d228c61cce02a785f3477944db8d0f2395e7
pages=11
bytes=4079491
created=Thu May 28 20:32:56 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=5f0e2d5a54dbe1068c244c427eb4d228c61cce02a785f3477944db8d0f2395e7

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a

/tmp/convertasset_acl27_fig3_red_recheck/page-08.png
sha256=e55a17495ef7862d70ea2a6668ac4d52c93d98f52156b20e49a2c199f01b9729
```

`pdfimages -list` still reports the embedded Figure 3 image on page 8 as the
same RGB 1124-by-672 image, matching the source PNG dimensions. Local visual
inspection of the source PNG and the page-8 PDF render found no saturated red
or magenta MDL fallback in the `Original MDL` column.

Pixel checks on the current source PNG and current page-8 render reported zero
strong-red, dominant-red, and magenta-fallback-like pixels. The looser broad-red
threshold counted only 47 pixels in the source PNG and 43 pixels in the rendered
page, with no sampled strong-red or magenta pixels; this is not consistent with
the historical large red material fallback.

The clean-provenance guard still passes:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

A scoped dry-run of `scripts/fix_mdl_absolute_imports.py --dry-run
--follow-symlinks` over the two Figure 3 scene roots reported:

```text
candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

Diagnosis remains unchanged for the v18 PDF build: the active source figure,
the embedded PDF image, and the Fig.3 scene-root MDL files do not reproduce the
historical red fallback. A remaining red view is most likely a stale viewer
cache, stale extracted page image, or older pre-rerender artifact.

## Follow-up Recheck: 22:50 Final-Gate Build

The user-reported path was checked again after the latest ACL build:

```text
paper/venues/acl27/build/main.pdf
sha256=4936611aa9aafc4795365ee2aa9892280b151a40e5994f69580bf5ee4dfb40bc
pages=11
bytes=4066563
created=Thu May 28 22:50:25 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=4936611aa9aafc4795365ee2aa9892280b151a40e5994f69580bf5ee4dfb40bc

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a

/tmp/convertasset_fig3_current_diag/page-08.png
sha256=e8cf7110e83bfe8b44d7674dd29cee26d7a4917aea70dc783db07ee3e18c7f90

/tmp/convertasset_fig3_current_diag/extracted/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
```

Local visual inspection of the source Figure 3 PNG and the rendered page-8 PDF
image found no saturated red or magenta MDL fallback in the `Original MDL`
column. The current source figure, rendered PDF page, and extracted embedded
PDF image all report zero pixels under the strong-red, dominant-red,
broad-reddish, warm-red-dominant, and magenta-fallback-like checks.

The clean-provenance guard still passes:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

The four selected `Original MDL` stderr logs contain no matches for `C108`,
`C120`, `Failed to create MDL shade node`, `KooPbr`, `KooPbr_maps`, or
`could not find module`; their only non-empty diagnostic lines are Isaac
extension dependency warnings for `omni.kit.viewport`. A scoped dry-run of the
MDL import repair over the two Figure 3 scene roots again reports:

```text
candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

Current diagnosis remains unchanged: the active PDF and active Figure 3 source
do not contain the historical red `Original MDL` fallback. The earlier
`.mdl import` repair is still present in the selected mounted scene roots; a
viewer that still shows red material is most likely displaying a stale PDF,
stale extracted page image, or old pre-rerender contact sheet.

## Follow-up Recheck: 23:07 Caption-Polish Build

The user-reported path was checked again after the Figure 1 caption-polish
build. Figure 3 itself is unchanged from the 22:50 final-gate build:

```text
paper/venues/acl27/build/main.pdf
sha256=4ff15035a709700527e42166ee4c5ba30ecf15138128c16f7a5d4de3fab5cebf
pages=11
bytes=4066538
created=Thu May 28 23:07:01 2026 CST

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
size=1124x672

/tmp/convertasset_fig3_diag/page-08.png
sha256=e8cf7110e83bfe8b44d7674dd29cee26d7a4917aea70dc783db07ee3e18c7f90

/tmp/convertasset_fig3_diag/extracted/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
size=1124x672
```

The extracted embedded PDF image is pixel-identical to
`paper/shared/figures/fig_material_effect_baseline_qualitative.png`; the byte
hash differs only because the PNG container metadata differs. The source Figure
3 PNG, rendered page-8 PDF image, and extracted embedded image all report:

```text
strong_red_pixels=0
reddish_pixels=0
warm_red_dominant_pixels=0
magenta_fallback_like_pixels=0
```

The clean-provenance guard still reports
`status=clean_material_effect_panel_ready`, `selected_case_count=4`,
`checked_original_mdl_log_count=4`, and
`original_mdl_error_signal_count=0`. The four selected `Original MDL` stderr
logs still contain no `KooPbr`, `KooPbr_maps`, `could not find module`,
`Failed to create MDL shade node`, `C120`, or `C108` matches; the only
non-empty diagnostic lines remain Isaac extension dependency warnings for
`omni.kit.viewport`. A scoped dry-run of
`scripts/fix_mdl_absolute_imports.py --dry-run --follow-symlinks` over the two
Figure 3 scene roots again found:

```text
candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

Current diagnosis remains unchanged: the active `build/main.pdf` does not
contain the historical red `Original MDL` material fallback. If a PDF viewer
still shows red Figure 3 cells at this path, the likely cause is viewer/file
cache or an older pre-rerender artifact, not a recurrence of the MDL import
repair failure.

## Follow-up Recheck: 23:22 Final-Gate Restage

After the Figure 1 caption-polish build was restaged through the full
pre-upload gate, Figure 3 was checked again:

```text
paper/venues/acl27/build/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
pages=11
bytes=4066538
created=Thu May 28 23:22:53 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7

/tmp/convertasset_fig3_2322_diag/page-08.png
sha256=e8cf7110e83bfe8b44d7674dd29cee26d7a4917aea70dc783db07ee3e18c7f90

/tmp/convertasset_fig3_2322_diag/extracted/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
```

The source Figure 3 PNG, rendered page-8 PDF image, and extracted embedded
PDF image still report zero strong-red, reddish, warm-red-dominant, and
magenta-fallback-like pixels. This confirms that the full restaged candidate
still does not contain the historical red `Original MDL` material fallback.

## Follow-up Recheck: 2026-05-29 User-Reported Build Path

The user-reported path was checked again directly:

```text
paper/venues/acl27/build/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
pages=11
bytes=4066538
created=Thu May 28 23:22:53 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
size=1124x672

/tmp/convertasset_fig3_diag/page-08.png
sha256=e8cf7110e83bfe8b44d7674dd29cee26d7a4917aea70dc783db07ee3e18c7f90

/tmp/convertasset_fig3_diag/extracted_20260529/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
size=1124x672
```

`pdfimages -list` reports one page-8 embedded RGB image at `1124x672`, and
the extracted image is pixel-identical to
`paper/shared/figures/fig_material_effect_baseline_qualitative.png`. The source
Figure 3 PNG and extracted embedded PDF image both report:

```text
strong_red_pixels=0
reddish_pixels=0
warm_red_dominant_pixels=0
magenta_fallback_like_pixels=0
```

The clean-provenance guard still passes:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

The four selected `Original MDL` stderr logs still contain no matches for
`C108`, `C120`, `Failed to create MDL shade node`, `KooPbr`, `KooPbr_maps`, or
`could not find module`. A scoped dry-run of the MDL import repair over the two
Figure 3 source scene roots again reports:

```text
candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

Diagnosis remains unchanged: the active PDF at the reported path does not
contain the historical red `Original MDL` material fallback. The old failure was
stale pre-rerender evidence from unresolved KooPbr imports; the selected
mounted assets now have the import repair, and the current paper uses the clean
rerendered panel. If red cells are visible in a local viewer, the likely source
is a cached PDF/page image or an older pre-rerender artifact with the same
human-facing filename, not a recurrence in the current `build/main.pdf`.

## Follow-up Recheck: 2026-05-30 User-Reported Origin-MDL Concern

The user-reported path was checked again directly:

```text
paper/venues/acl27/build/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
pages=11
bytes=4066538
created=Thu May 28 23:22:53 2026 CST

paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
size=1124x672

/tmp/ca_fig3_diag/page-08.png
sha256=688b89c6e8ab7239bb72f794e781c85059464ddde7a2275b46d8dc642eb02513

/tmp/ca_fig3_current_extract/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
size=1124x672
```

`pdfimages -list` reports the page-8 embedded figure as one RGB image with
dimensions `1124x672`, matching the source Figure 3 PNG. The extracted embedded
image is pixel-identical to
`paper/shared/figures/fig_material_effect_baseline_qualitative.png`.

Pixel spot checks on the source Figure 3 PNG, the rendered page-8 PDF image,
and the extracted embedded image report:

```text
strong_red_pixels=0
dominant_red_pixels=0
magenta_fallback_like_pixels=0
warm_red_pixels=1
```

The single warm-red pixel is isolated and is not visually consistent with the
historical saturated red MDL fallback. The four original-MDL source images used
by Figure 3 also report `strong_red=0`, `redish=0`, and `warm=0`.

The clean-provenance guard still passes:

```text
ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

The checked current original-MDL stderr logs contain no matches for `C108`,
`C120`, `Failed to create MDL shade node`, `KooPbr`, `KooPbr_maps`, or
`could not find module`; the remaining log line is the known
`omni.kit.viewport` extension dependency warning, not a material-resolution
failure.

A scoped dry-run of `scripts/fix_mdl_absolute_imports.py` over the resolved
Figure 3 material root reports:

```text
candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

The scene-local `Materials` entries are symlinks to the shared GRScenes material
root, so the reproducible scoped command should use the resolved `Materials`
directory rather than walking the whole scene tree with unrestricted symlink
following.

Diagnosis remains unchanged on 2026-05-30: the current PDF, the embedded Figure
3 image, the source Figure 3 PNG, the selected original-MDL render logs, and the
selected material root do not show a recurrence of the historical abnormal red
`Original MDL` fallback. A red-looking view is most likely a PDF/image-viewer
cache, an older pre-rerender PDF or contact sheet, or visual interpretation of
normal warm/brown scene colors at small figure scale rather than a failed MDL
import repair.
