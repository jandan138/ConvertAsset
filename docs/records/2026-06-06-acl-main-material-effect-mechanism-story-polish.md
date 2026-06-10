# 2026-06-06 ACL Main Material-Effect Mechanism Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on page 5 and the section
4.3 transition from VLM grounding stress results into material-effect and
NVIDIA-baseline boundaries.

The fresh round-19 contact sheet showed no hard crop or float displacement. The
selected issue was local: the section had the correct claim boundary, but the
opener did not yet make the mechanism question explicit after the VLM stress
evidence.

## Changes

- Rewrote the section 4.3 opener so the material-effect audit follows from the
  VLM stress result: if render evidence changes, the paper asks which bounded
  material effect moved it.
- Reframed Figure 3 as a visual index for bounded cases, not an error-rate
  sample.
- Clarified that the static material gates localize mechanisms and support
  selected-bin interpretation only.
- Preserved all counts, tables, figure references, and NVIDIA-baseline claim
  boundaries.

## Visual Finding

The accepted render keeps the 11-page A4 structure stable:

- Page 5 now gives section 4.3 a clearer story handoff from VLM stress evidence
  to material-mechanism inspection.
- The new right-column text fits cleanly within the ACL column.
- The page-5/page-6 focus sheet shows no downstream displacement of Figure 3 or
  the embodied-sanity section.
- The after full contact sheet shows no visible displacement of Method, Results,
  figures, tables, Ethical Considerations, or References.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round19_current/contact_sheets/main_pages_01_11_current.png`
- Before page render:
  `tmp/acl_main_visual_iter_20260606_round19_current/pages_180/main-05.png`
- Accepted page render:
  `tmp/acl_main_visual_iter_20260606_round19_after/pages_180/main-05.png`
- Accepted page-5/page-6 focus sheet:
  `tmp/acl_main_visual_iter_20260606_round19_after/contact_sheets/main_pages_05_06_after_focus.png`
- Accepted full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round19_after/contact_sheets/main_pages_01_11_after.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round19_material_effect_mechanism_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=467a711f65485caf81df270dff5a653e0a7dc24cde0f351efb9f0091d998fe88
pages=11
bytes=5189872
created=Sat Jun 6 10:48:02 2026 CST
```

## Verification

```bash
make -C paper acl27
rg -n "Overfull|Float too large|too large|LaTeX Warning: Float|Rerun to get|Warning:.*Label|Undefined references|multiply defined|Package lineno Warning" paper/venues/acl27/build/main.log || true
python -m pytest -q tests/test_paper_layout.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
```

Results: ACL build passed with an 11-page A4 PDF, the final LaTeX blocker scan
returned no matches, `tests/test_paper_layout.py` passed with 85 tests, and both
ACL claim-boundary and metadata-consistency checks returned `ok`. The metadata
check still reports `abstract_word_count=169`.

## Residual Risk

This pass is a focused page-5 material-effect mechanism story polish. It is not
a complete final-upload audit, target-policy refresh, or integrity-fingerprint
refresh.
