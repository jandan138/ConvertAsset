# 2026-06-07 ACL Main Method Page3 Conversion/Probe Linebreak Polish

## Scope

Round 65 of the ACL main-paper visual/prose review polished the page-3 Method
right column around Material Conversion and the Gate 2 VLM probe protocol. The
source change is in:

- `paper/venues/acl27/sections/method.tex`

## Issue

The rendered page-3 right column contained a dense Method split cluster:

- `se- / mantic`
- `in- / puts`
- `ef- / fects`
- `emis- / sion`
- `la- / bels`
- `struc- / tured`
- line pressure around `box inclusion`

During iteration, first-pass rewrites removed the original cluster but introduced
replacement splits such as `chan- / nels`, `de- / faults`, `box in- / clusion`,
`coordinate se- / mantics`, `net- / work`, `em- / ulate`, `val- / ues`,
`coor- / dinate`, `canoni- / cal`, `raw- / pixel`, and `an- / swer`. The
accepted version removes the target cluster by shortening the prose rather than
boxing or hiding line breaks.

## Change

The Material Conversion paragraph now states the intervention in shorter
concrete units: each processed file swaps MDL shaders for PreviewSurface; the
rewrite covers base color, roughness, metal, normal maps, and texture paths; it
uses the declaring layer when paths exist and fixed values otherwise; it is not
full MDL semantics. The audit-risk list keeps clearcoat, procedural cues,
height/displacement, opacity, emission, and related features out of fidelity
promises.

The Gate 2 probe wording now keeps Gemma4 as the primary probe and Qwen2.5-VL as
the second probe, then records label agreement, normalized-1000 point hits, and
raw pixel point hits. The raw-pixel check remains a coordinate-use diagnostic,
and the paragraph still says the probes test a contract, not a model ranking.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round65_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round65_after`
- Before PDF SHA-256:
  `554fcf8d46aa9c39385c36d7945aa01a66ffa75b4f3fa8edda90812bd781745e`
- After PDF SHA-256:
  `9f764b2b764055a0675ab2eaa24c12ed8f07e9f94d0e924eae28b3bc003c0034`
- After page-3 right-column crop:
  `tmp/acl_main_visual_iter_20260607_round65_after/page3_right.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round65_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round65_method_page3_conversion_probe_linebreak_polish_20260607.json`

The final page-3 crop removes the targeted conversion/probe split cluster. The
full contact sheet remains 11 pages with no obvious float, table, or blank-page
regression.

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
