# 2026-06-04 ACL supplement navigation media boundary v3

## Summary

Reworked the ACL supplement page-37 navigation media boundary figure so the page is less sparse while respecting the updated AI-slot anti-cropping rule.

## Changes

- Generated `paper/shared/figures/ai_slots/fig_supplement_navigation_media_package_v3_ai_slot.png` from a new media-package gate prompt with explicit no-crop, no-edge-contact, and no-critical-text constraints.
- Post-processed only the generated slot whitespace using a conservative crop box plus a 64 px safety border, then placed it with `_fit(..., cover=False)`.
- Rebuilt `paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png` as a `2000x2240` board with larger real still/route panels and deterministic mini evidence rows in the bottom boundary cards.
- Raised the ACL supplement include from `0.66\textheight` to `0.74\textheight`.
- Changed downstream reuse of `NAVIGATION_MEDIA_BOUNDARY_OUT` from cover to contain to avoid cropping the updated figure when it appears in a later media card.

## Visual Review

- Raw v3 project slot: PASS, no visible object clipped after whitespace trim and safety border.
- Standalone composed figure: PASS, title bars, still panels, route panels, AI gate, cards, and footer are contained.
- PDF page 37: PASS, no caption collision or page spill; pages 36 and 38 remain visually intact.
- Dense crops reviewed:
  - `tmp/acl_supplement_page37_navigation_media_boundary_v3_20260604/crops/page37_bottom_gate_cards.png`
  - `tmp/acl_supplement_page37_navigation_media_boundary_v3_20260604/crops/page37_caption_area.png`
  - `tmp/acl_supplement_page37_navigation_media_boundary_v3_20260604/crops/standalone_bottom_gate_cards.png`

## Metrics

- Page 37 active245 at 90 dpi: `0.183632574` -> `0.224922083` (`+0.041289508`).
- Page 37 full-document density rank after the pass: `31/45` by active245 ascending.
- Standalone figure active238: `0.363080804`.
- Figure size: `2000x2240`.
- Supplement page count after rebuild: `45`.

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_media_boundary_strip'`
- `python -m pytest -q tests/test_paper_layout.py -k 'navigation_media_boundary_strip or acl_supplement_uses_visual_pages'`
- `python -m pytest -q tests/test_paper_layout.py` (`77 passed`)
- `make -C paper acl27-supplement`
- `pdfinfo paper/venues/acl27/build/supplement.pdf | rg '^Pages:'` (`45`)

Evidence record:

- `paper/shared/evidence/raw/acl27_visual_review/supplement_navigation_media_boundary_v3_20260604.json`
