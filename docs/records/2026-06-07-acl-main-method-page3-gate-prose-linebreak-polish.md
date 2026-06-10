# 2026-06-07 ACL Main Method Page3 Gate Prose Linebreak Polish

## Scope

Round 62 of the ACL main-paper visual/prose review polished the page-3 Method
right column. The source change is in:

- `paper/venues/acl27/sections/method.tex`

## Issue

The rendered page-3 right column still had a reader-visible linebreak cluster
across Material Conversion and the Evidence Gates opener:

- `flat- / tening`
- `metal- / lic`
- `similar- / ity`
- `DINOv2 sim- / ilarity`
- `ren- / dered`
- `Vi- / sual`
- `target-visible PASS/WARN material- / shift`
- `target- / category`
- `pixel- / space`

During iteration, shorter wording briefly introduced replacement splits such as
`furni- / ture`, `pre- / serves`, `con- / trolled`, `met- / alness`,
`ConvertAs- / set`, `con- / tract`, `tar- / get`, and `un- / der`. The accepted
version removes the target cluster without changing the evidence boundary.

## Change

The Material Conversion subsection now states the same non-flattening
intervention with shorter sentences: the tool discovers referenced layers and
writes sibling noMDL assets while composition arcs stay intact and source files
do not change.

The material-channel paragraph now describes PreviewSurface as a core-channel
model and keeps unsupported MDL mechanisms as audit risk labels, not fidelity
promises.

Gate 1 now describes the proxy screen with the same metric set while avoiding
repeated `similarity` wording in the narrow column.

Gate 2 now describes the GRScenes protocol as a structured schema with Gemma4
as the canonical backend and Qwen2.5-VL as a second probe. The metric wording is
kept scoped to answer agreement, box inclusion, and raw pixel diagnostics; it
does not become a model ranking claim.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round62_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round62_after`
- Before PDF SHA-256:
  `d7219ef76e9da3bd6956592b5d54f73798001ea44152ed870060a531f764a5d2`
- After PDF SHA-256:
  `b8b950c3b9a87357f6adc0a2d34d1282159793d1657112ea2f11dfb6207776c6`
- After page-3 right-column crop:
  `tmp/acl_main_visual_iter_20260607_round62_after/page3_right.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round62_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round62_method_page3_gate_prose_linebreak_polish_20260607.json`

The Round62 baseline directory does not contain a copied `main.pdf`, but its
baseline PDF hash is the accepted Round61 final hash above. The baseline text
and page-3 render artifacts are present in the Round62 baseline directory.

The final page-3 crop removes the targeted Method right-column split cluster.
The full contact sheet remains 11 pages with no obvious float, table, or
blank-page regression.

## Verification

- `make -C paper acl27` exited 0.
- Log blocker scan for overfull boxes, undefined references, rerun warnings,
  multiply-defined labels, and `lineno` warnings returned no matches.
- `python -m pytest -q tests/test_paper_layout.py tests/test_acl_preupload_gate.py tests/test_acl_metadata_consistency.py`
  passed with `104 passed`.
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` returned
  `"ok": true`.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` returned
  `"ok": true` with a 168-word abstract.
