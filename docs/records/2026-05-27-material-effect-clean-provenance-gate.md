# 2026-05-27 Material-Effect Clean-Provenance Gate

## Scope

This record documents a small guard added for the material-effect qualitative
panel:

```text
paper/shared/figures/fig_material_effect_baseline_qualitative.png
```

The panel is currently retained as an internal artifact, but it must not be used
as clean ACL main-paper evidence until the original-MDL cells have clean
render-log provenance.

## Change

Added a machine-checkable provenance gate:

```text
paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py
tests/test_material_effect_qualitative_clean_provenance.py
```

The checker requires every selected material-effect case to have ready images
for:

```text
original_MDL
existing_noMDL
nvidia_asset_converter_preview_or_bake
```

It then requires an original-MDL stderr log for each selected case and blocks the
panel if that log contains MDL-resolution failure terms:

```text
C108
C120
Failed to create MDL shade node
KooPbr
KooPbr_maps
could not find module
```

The checker is intentionally stricter than image existence. A stale PNG can look
ready to the contact-sheet generator while still carrying old red-material
fallback provenance.

## Current Result

The current material-effect qualitative manifest has all 4 selected cases and
all 12 condition images ready, but it is blocked for ACL main-paper reuse:

```text
selected_case_count: 4
complete_case_count: 4
checked_original_mdl_log_count: 4
missing_original_mdl_log_count: 0
original_mdl_error_signal_count: 4
blockers: original_mdl_error_signal
```

This means the May 26 import repair may be present in the scratch asset tree, but
the material-effect contact sheet still reuses older original-condition PNGs and
their old stderr logs.

## Decision

Do not reintroduce `fig_material_effect_baseline_qualitative.png` into the ACL
main text until either:

1. the four original-MDL cells are rerendered from repaired assets and pass this
   checker, or
2. the panel is rebuilt from replacement selected cases whose original-MDL
   stderr logs are clean.

This is a provenance gate for real render evidence. It is separate from the
image-generation work used for schematic method-chain figures.

## Verification

Commands run:

```bash
python -m pytest -q tests/test_material_effect_qualitative_clean_provenance.py
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py --report-only
```

Observed result:

```text
2 passed
blocked_material_effect_panel
original_mdl_error_signal_count: 4
```

## 2026-05-28 Update

After the clean original-MDL rerender pass, the same gate now reports the
selected material-effect contact sheet as clean:

```text
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py
```

Observed result:

```text
ok: true
status: clean_material_effect_panel_ready
selected_case_count: 4
complete_case_count: 4
checked_original_mdl_log_count: 4
missing_original_mdl_log_count: 0
original_mdl_error_signal_count: 0
blockers: []
```

The current contact sheet also has `0` saturated strong-red pixels under the
project spot check. This updates the status of the contact sheet from
`blocked_material_effect_panel` to `clean_material_effect_panel_ready`.

The ACL main PDF still keeps the material-effect evidence table-bounded rather
than reintroducing this contact sheet as a main figure. It remains available for
selected supplemental/rebuttal inspection, subject to the existing claim-boundary
and artifact-redistribution constraints.
