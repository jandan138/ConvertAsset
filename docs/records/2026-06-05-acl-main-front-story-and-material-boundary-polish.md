# 2026-06-05 ACL Main Front Story and Material Boundary Polish

## Scope

Continued the ACL main-paper visual and prose iteration on
`paper/venues/acl27/build/main.pdf`, focusing on two reader-visible issues:

- the first two pages around Figure 1 and the contribution list;
- the page-5/page-6 transition around the material-effect boundary result and
  Figure 3.

This pass also responded to the claim-boundary regression test that required
the results text to state explicitly that static material-effect gates do not
certify preservation of the MDL mechanism itself.

## Changes

- Tightened the Introduction opening so the rendered scene is framed as the
  measurement interface and the conversion step as an unreported intervention.
- Shortened the Figure 1 bridge to a complete sentence at the end of page 1 and
  let page 2 begin with a complete protocol paragraph.
- Reworded the contribution list to foreground the protocol story:
  controlled VLM-grounding perturbation, claim-bounded protocol, GRScenes stress
  instantiation, and shared claim registry.
- Added the explicit material-effect boundary sentence:
  static gates do not certify that the MDL mechanism itself is preserved.
- Shortened the Figure 3 prose bridge so page 5 ends with a complete sentence
  and page 6 begins with the complete boundary paragraph.

## Visual Findings

- Page 1 now ends with the complete sentence
  `Figure 1 gives the schematic roadmap.`
- Page 2 starts with a complete paragraph:
  `The resulting protocol has four gates rather than one conversion score.`
- Figure 1 remains fully visible and non-cropped.
- Page 5 now ends with the complete sentence `Figure 3 aids inspection.`
- Page 6 starts with the complete static-gate boundary sentence.
- Figures 2, 3, and 4 remain fully visible, with no new caption collision,
  clipping, or float overlap in the final full-page review.

## Visual Evidence

- Front-page baseline contact sheet:
  `tmp/acl_main_visual_iter_20260605_round10_front_story/contact_sheets/main_pages_01_04_before.png`
- Final full-page contact sheets:
  - `tmp/acl_main_visual_iter_20260605_round10_front_story/contact_sheets/main_pages_01_04_final_r2.png`
  - `tmp/acl_main_visual_iter_20260605_round10_front_story/contact_sheets/main_pages_05_08_final_r2.png`
  - `tmp/acl_main_visual_iter_20260605_round10_front_story/contact_sheets/main_pages_09_11_final_r2.png`
- Targeted material-effect transition review:
  `tmp/acl_main_visual_iter_20260605_round10_front_story/contact_sheets/main_pages_05_06_material_fix_r2.png`
- Final rendered pages:
  `tmp/acl_main_visual_iter_20260605_round10_front_story/pages_180_final_r2/`
- Final text extraction:
  `tmp/acl_main_visual_iter_20260605_round10_front_story/text_final_r2/main_layout.txt`

## Verification

- `make -C paper acl27` passed and produced an 11-page A4 PDF.
- Final `main.pdf` SHA-256:
  `a4c0b8b7e250dbd761727a93c38b4db11c3fe45c3357c646b2204ceeec7bd874`
- `python paper/venues/acl27/scripts/check_claim_boundaries.py` passed.
- `python paper/venues/acl27/scripts/check_metadata_consistency.py` passed.
- LaTeX log blocker scan for overfull boxes, fatal errors, undefined
  references, and rerun warnings returned no matches.
- `python -m pytest -q tests/test_acl_claim_boundaries.py` passed:
  9 passed.
- `python -m pytest -q tests/test_acl_preupload_gate.py` passed:
  17 passed.
- Targeted layout pytest passed:
  5 passed, 80 deselected.

## Known Gate Status

`python paper/venues/acl27/scripts/run_preupload_gate.py` still stops at
`check_integrity_fingerprint.py`. Earlier preupload stages pass, including claim
boundaries, target policy, metadata consistency, OpenReview checklist, citation
inventory, and evidence-number checks. The fingerprint mismatch lists multiple
existing dirty paper/figure/table files, so this pass did not refresh the
integrity fingerprint.

## Residual Risk

This pass improves the front-story flow, removes two visible page-transition
awkwardnesses, and strengthens material-effect claim boundaries. It is still one
iteration toward the persistent ACL PDF polishing goal, not a full final
submission completion audit or a fingerprint refresh.
