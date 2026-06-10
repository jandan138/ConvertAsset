# 2026-06-07 ACL Main Related Page2 Embodied Simulation Linebreak Polish

## Scope

Round 67 of the ACL main-paper visual/prose review polished the page-2 Related
Work right column. The final source change is in:

- `paper/venues/acl27/sections/related.tex`

## Issue

The rendered Related Work paragraph for embodied simulation had a visible
proper-name and compound-word split cluster:

- `AI plat- / forms`
- `Three- / DWorld`
- `GRScenes ex- / tend`
- `general- / robot`

Earlier attempts were rejected because they traded the target cluster for new
defects: `AI2- / THOR`, `ThreeD- / World`, `mate- / rial`, a large
post-citation justification gap, `ren- / dering`, `sim- / ulation`,
`GRU- / topia`, `Intern- / Nav`, and `leader- / boards`.

## Change

The accepted rewrite shortens the embodied-simulation paragraph and keeps the
related systems as context rather than ranking targets. Habitat, AI2-THOR, and
ThreeDWorld are now introduced as interactive testbeds for agents using vision
and language. Isaac Sim and Isaac Lab are framed as a USD/RTX/MDL robotics
stack. GRUtopia/GRScenes and InternNav/DualVLN are then named as city-scene and
VLN context systems.

The final KuJiaLe sentence now states the boundary directly: the official
KuJiaLe sanity check is stack entry evidence over matched source/noMDL scenes,
not a broad navigation claim.

## Visual Evidence

- Before visual review directory:
  `tmp/acl_main_visual_iter_20260607_round67_current`
- After visual review directory:
  `tmp/acl_main_visual_iter_20260607_round67_after`
- Before PDF SHA-256:
  `2dda5c1f787115f15d5b75424d416b2568c865541bc7c8219f9df425bb3c09c6`
- After PDF SHA-256:
  `ce7e409bef671cdec2d0e79574be20443e0f27e0a03b3d44fb6c44bf3c818dda`
- After page-2 right-column crop:
  `tmp/acl_main_visual_iter_20260607_round67_after/page2_right.png`
- After contact sheet:
  `tmp/acl_main_visual_iter_20260607_round67_after/contact_sheet.png`
- Evidence manifest:
  `paper/shared/evidence/raw/acl27_visual_review/main_round67_related_page2_embodied_sim_linebreak_polish_20260607.json`

The accepted page-2 text scan has no remaining target-region splits for the
embodied-simulation paragraph. The inherited left-column `coordinate-` and
`embodied-` splits are outside this round. Page 3 was checked for reflow; the
right-column Claim Registry opener now has a low-priority `ta- / ble` split at
the page bottom, which is recorded as the next-round candidate rather than
mixed into this Related Work edit.

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
