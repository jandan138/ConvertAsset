# 2026-05-26 ACL Fig.1 Red-Material Root Cause

## Scope

This record investigates the abnormal red materials visible in the previously
included ACL qualitative VLM panel, which was generated from
`paper/shared/figures/fig_vlm_grounding_cases.pdf`.

## Finding

The panel should not be treated as final qualitative evidence. Its "Original
MDL render" columns were rendered from an original-condition GRScenes scratch
tree whose MDL dependencies failed to compile in Isaac Sim. The visible red
material is therefore a render-stack artifact, not a clean representation of
the intended original MDL appearance.

The figure generator selects four cases in
`paper/shared/figures/gen_vlm_grounding_cases.py`:

| Pair | Target | Original MDL error signal | Converted MDL error signal | Original mean RGB | Converted mean RGB |
| --- | --- | ---: | ---: | --- | --- |
| `21dde4a14ca93f539a47.retake_008` | pillow | 1556 | 0 | `[131.5, 20.3, 18.9]` | `[26.8, 25.8, 24.4]` |
| `c27086f557d316584264.view_001` | bottle | 1556 | 0 | `[76.3, 44.0, 41.8]` | `[80.9, 77.0, 73.0]` |
| `47aa36277a54f6ca90cc.zoom_018` | backpack | 988 | 0 | `[159.8, 58.0, 57.2]` | `[98.7, 97.5, 95.5]` |
| `c8ee4b66274b05d242c2.zoom_017` | faucet | 1588 | 0 | `[179.9, 116.4, 114.9]` | `[212.1, 211.3, 210.2]` |

The underlying reports are:

- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_paired_render_reports/21dde4a14ca93f539a47.retake_008.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/paired_render_smoke_report.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/47aa36277a54f6ca90cc.zoom_018.json`
- `paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/c8ee4b66274b05d242c2.zoom_017.json`

## MDL Import Evidence

The corresponding original render logs contain compiler errors such as:

```text
C120 could not find module '::KooPbr' in module path
C120 could not find module '::KooPbr_maps' in module path
```

The referenced `.mdl` files in the scratch GRScenes tree still use absolute
imports, for example:

```text
import ::KooPbr::KooMtl;
import ::KooPbr_maps::KooPbr_alpha_source;
import ::KooPbr_maps::KooPbr_bitmap;
```

This matches the known failure mode where Isaac Sim renders fallback/error
materials when the GRScenes `KooPbr` / `KooPbr_maps` modules are not resolved.

## Historical-Fix Audit

The user-provided historical fix description points to:

- `docs/records/changes/2026-03-16_mdl_import_fix.md`
- `scripts/fix_mdl_absolute_imports.py`
- commit `d2ee86e`

These paths and that commit are not present in the current repo history. A
read-only check of `/cpfs/shared/simulation/zhuzihou/dev/ConvertAsset` also did
not find those files or commit. The historical fix may have lived in another
clone, branch, or uncommitted working copy, but it is not currently part of the
reproducible ACL evidence chain.

## Repair Applied On 2026-05-26

The ACL/VLM scratch asset tree was repaired in place under:

```text
/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521/scenes/GRScenes-100/home_scenes
```

The official source tree under `/cpfs/user/zhuzihou/assets/zzh-grscenes` was
not intentionally modified. Spot checks confirmed that hardlinked scratch MDL
files were split by atomic replacement and that source-side pointer entries
remained unchanged.

Applied repairs:

| Repair | Report | Result |
| --- | --- | --- |
| Generated MDL import rewrite | `paper/shared/evidence/raw/grscene_vlm_grounding/mdl_import_fix_apply_20260526.json` | `1566` changed `.mdl` files, `3683` import replacements, `0` errors |
| Existing GRScenes pointer files to symlinks | `paper/shared/evidence/raw/grscene_vlm_grounding/pointer_entry_repair_apply_20260526.json` | `23141` `Materials` / `models` pointer files repaired, `0` errors |
| Missing `Materials` entries for render-log-referenced models | `paper/shared/evidence/raw/grscene_vlm_grounding/pointer_entry_missing_materials_render_log_apply_20260526.json` | `51` new scratch-local `Materials` symlinks among `1703` render-log-referenced model instances, `0` errors |

Why the third repair was needed: after the `KooPbr` imports were fixed, Isaac
started resolving deeper per-model MDL assets and exposed paths like
`./Materials/Num5dd77cea7d6a630001bffad3.mdl` in model directories that lacked a
`Materials` entry. The initial byte-string scan reported zero candidates because
many `instance.usd` files are binary USD; the render-log-scoped repair was
therefore driven by actual `model_<hash>` references seen in the VLM render
logs, mapped back to scratch `instance.usd` paths.

Targeted PXR checks on the previously failing tray, bottle, and cup model
instances showed local `./Materials/*.mdl` asset references resolving after the
repair:

| Model hash | Local MDL assets checked | Unresolved after repair |
| --- | ---: | ---: |
| `fd9cdb64d2f8ac3d3c9c576344a03ecb` | 27 | 0 |
| `9a3c34d5068f8864e0a3e187f8a898a1` | 2 | 0 |
| `ca60d4ce35e12df089354aabad307f01` | 1 | 0 |

## Remaining Render Blocker

After the asset repair, the selected
`c27086f557d316584264.view_001` original-condition rerender no longer emitted
`KooPbr`, `KooPbr_maps`, `could not find module`, or `Failed to create MDL shade
node` in the checked stderr log. However, the headless viewport capture command
timed out at 1800 seconds after opening the stage and binding the camera.

A direct isolation probe reproduced the issue:

- original MDL camera USD: opened the stage and bound the camera, but timed out
  after 300 seconds before saving a frame.
- converted/noMDL camera USD for the same view: saved a frame in about 226
  seconds.

Interpretation: the red-material MDL resolution failure has been repaired for
the scratch asset paths exercised so far, but the cleaned original MDL scene is
too slow or hangs in the current headless viewport-capture path. The panel is
therefore still not final-upload safe until the original-condition image is
rerendered with a reliable capture path, replaced by clean-log cases, or removed.

## ACL Main-Paper Mitigation

The ACL main results section now removes
`figures/fig_vlm_grounding_cases.pdf` instead of relying on a selected
qualitative panel with blocked render provenance. The VLM grounding result is
kept in tabular and metric-auditable form, and selected qualitative panels are
treated as internal inspection artifacts until their exact render logs and VLM
overlay provenance are clean.

`paper/venues/acl27/scripts/check_claim_boundaries.py` now includes an
`unsafe_vlm_grounding_qualitative_panel` guard so the ACL main text cannot
silently re-include `fig_vlm_grounding_cases` before that evidence is repaired.

## Paper Impact

The current VLM numerical tables remain usable as frozen pilot/stress evidence
only under their already documented limitations, because they are tied to the
rendered images used for the VLM probes. However, the removed qualitative panel
is not a safe representative visual panel for final submission:

- It can support an internal diagnostic statement that the original GRScenes
  MDL stack fails in this Isaac render environment.
- It must not be used as a clean "original MDL versus noMDL" qualitative
  appearance comparison.
- Replacing the images without rerunning or revalidating VLM predictions would
  break the point-overlay provenance.

## Required Fix Path

Before final upload, use one of these evidence-safe routes:

1. Finish a reliable original-condition render path for the repaired scratch
   assets, rerender the selected original images, rerun or revalidate VLM
   predictions for those exact images, regenerate the panel, and rerun visual QA.
2. Replace the panel with cases whose original render logs have zero
   `KooPbr` / `KooPbr_maps` / `Failed to create MDL shade node` signal, then
   regenerate the figure from the matching prediction and scoring records.
3. Keep the current qualitative panel out of the ACL main paper and use the
   red-material examples only as internal diagnostic notes until clean evidence
   is available. This is the active ACL mitigation as of this record update.

## Verification Commands

Commands run during this investigation:

```bash
pdfimages -list paper/venues/acl27/build/main.pdf
pdftoppm -f 7 -l 7 -png -r 180 paper/venues/acl27/build/main.pdf /tmp/acl27_fig_page
rg -n "fig_vlm_grounding_cases|includegraphics" paper/venues/acl27 paper/shared
git show --stat --oneline d2ee86e
git -C /cpfs/shared/simulation/zhuzihou/dev/ConvertAsset show --stat --oneline d2ee86e
rg --files | rg "fix_mdl_absolute_imports\\.py|2026-03-16_mdl_import_fix\\.md"
python -m pytest -q tests/test_fix_mdl_absolute_imports.py tests/test_repair_grscenes_pointer_entries.py -q
```

Structured report parsing confirmed the per-pair MDL error counts and RGB
means shown above.
