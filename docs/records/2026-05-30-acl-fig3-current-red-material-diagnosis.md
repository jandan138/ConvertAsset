# 2026-05-30 ACL Fig.3 Current Red-Material Diagnosis

## Scope

This record diagnoses the user-reported concern that
`paper/venues/acl27/build/main.pdf` Figure 3 still shows abnormal red material
in the `Original MDL` column, despite the earlier GRScenes MDL import repair.

## Current Artifact

The checked PDF is the current local build:

```text
paper/venues/acl27/build/main.pdf
sha256=d6b74efc377ed51ca502d55d3d785cc43101e259bbce022388088e06c910432e
pages=11
bytes=4066557
created=Sat May 30 19:01:27 2026 CST
```

The staged candidate is byte-identical:

```text
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=d6b74efc377ed51ca502d55d3d785cc43101e259bbce022388088e06c910432e
```

Figure 3 is sourced from:

```text
paper/shared/figures/fig_material_effect_baseline_qualitative.png
sha256=e0cea32c186661ce2efcf736fd7fb0f714f7d78b411364b029374e0e473e187a
size=1124x672
```

## Visual And Pixel Diagnosis

Rendering page 8 at 220 DPI and extracting the embedded image from the PDF did
not reproduce saturated or dominant red material:

```text
/tmp/convertasset_fig3_red_diag_20260530/page-08.png
sha256=dbe212cc7cb3a38fedc5b53749dcdda0547959205bc1d6361bd64d4313601cd8
strong_red_pixels=0
reddish_pixels=0
warm_red_dominant_pixels=0

/tmp/convertasset_fig3_red_diag_20260530/extracted/img-000.png
sha256=86f29b67e14a1f271abfa157134da887c5bf4a7a5c7cdc7c1a13e58b9b11402a
size=1124x672
strong_red_pixels=0
reddish_pixels=0
warm_red_dominant_pixels=0

paper/shared/figures/fig_material_effect_baseline_qualitative.png
strong_red_pixels=0
reddish_pixels=0
warm_red_dominant_pixels=0
```

The extracted embedded PDF image is pixel-identical to the source Figure 3 PNG.
Therefore the current PDF is not embedding an older red fallback panel.

Per-record checks over all 12 source cells in the current Figure 3 manifest also
reported zero `strong_red`, `reddish`, and `warm_red_dominant` pixels. The
visible `Original MDL` cells are bottle, clock, cup, and backpack. The cup row
has a light warm tabletop/background, but it does not match the prior saturated
red MDL fallback failure mode.

## MDL Import Repair Coverage

The two selected GRScenes scene directories used by Figure 3 link their
`Materials` directories to the shared GRScenes material root:

```text
/cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/nomdl_full/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/Materials
```

That material root contains 1677 `.mdl` files. Running the import repair script
in dry-run mode over this root found no remaining absolute KooPbr imports to
repair:

```text
python scripts/fix_mdl_absolute_imports.py --dry-run \
  --report /tmp/convertasset_fig3_red_diag_20260530/mdl_import_materials_dryrun.json \
  /cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/nomdl_full/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/Materials

candidate_files=1566
changed_files=0
total_replacements=0
errors=0
```

This supports that the earlier `.mdl` import repair is present for the material
set feeding the current Figure 3 scenes.

## Render-Provenance Gate

The current clean-provenance gate also passes:

```text
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py \
  --manifest paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json

ok=true
status=clean_material_effect_panel_ready
selected_case_count=4
complete_case_count=4
checked_original_mdl_log_count=4
missing_original_mdl_log_count=0
original_mdl_error_signal_count=0
blockers=[]
```

The four checked `Original MDL` stderr logs contain only the known Isaac
extension dependency warning line, not `KooPbr`, `KooPbr_maps`, `could not find
module`, `Failed to create MDL shade node`, `C108`, or `C120` material-resolution
signals.

## Diagnosis

The current `build/main.pdf` does not contain the historical red `Original MDL`
fallback. The likely explanations if red is still visible in a viewer are:

1. The viewer is showing a cached copy of an older PDF with the same file name.
2. A different PDF or older exported image is being inspected.
3. The light warm tabletop/background in the cup row is being interpreted as the
   old red-material failure, but it is not the saturated fallback signal.

No source, embedded-image, rendered-page, render-log, or MDL-import evidence from
the current artifact indicates that the previous MDL import issue has recurred.

## Verification Commands

```text
pdfinfo paper/venues/acl27/build/main.pdf
sha256sum paper/venues/acl27/build/main.pdf paper/submissions/acl27_arr_candidate_20260526/main.pdf
pdfimages -list -f 8 -l 8 paper/venues/acl27/build/main.pdf
pdfimages -png -f 8 -l 8 paper/venues/acl27/build/main.pdf /tmp/convertasset_fig3_red_diag_20260530/extracted/img
pdftoppm -f 8 -l 8 -r 220 -png paper/venues/acl27/build/main.pdf /tmp/convertasset_fig3_red_diag_20260530/page
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py --manifest paper/shared/evidence/raw/material_effect_baseline/qualitative_render_manifest.json
python scripts/fix_mdl_absolute_imports.py --dry-run --report /tmp/convertasset_fig3_red_diag_20260530/mdl_import_materials_dryrun.json /cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/nomdl_full/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes/Materials
```
