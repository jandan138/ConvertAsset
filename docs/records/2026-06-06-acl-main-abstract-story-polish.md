# 2026-06-06 ACL Main Abstract Story Polish

## Scope

Continued the ACL main-paper visual and prose review on
`paper/venues/acl27/build/main.pdf`, focusing on the page-1 abstract after a
fresh front-page and table-page render pass.

The page-8 table area remained complete and readable, so this iteration moved
to the abstract. The previous opening still read more like a report summary
than an ACL story, and an intermediate rewrite created a visible wide gap after
the prompt-contract sentence on page 1.

## Changes

- Rewrote the abstract opener to frame USD material conversion as quiet
  infrastructure that perturbs the measurement interface.
- Compressed the proxy-fidelity paragraph while keeping PSNR, SSIM, LPIPS,
  CLIP, and DINOv2 evidence intact.
- Preserved the separate gates for visual similarity, grounding,
  material-effect risk, and embodied-stack usability.
- Synchronized `OPENREVIEW_METADATA_PACKET.md` with the venue abstract and its
  conservative tokenizer count.

## Visual Finding

The accepted render keeps the same 11-page A4 structure:

- Page 1 now opens with the benchmark-infrastructure story before the metric
  inventory.
- The large page-1 abstract gap from the intermediate prompt-contract sentence
  is gone.
- The earlier disruptive `hid-den infrastructure` split is avoided by using
  `quiet infrastructure`.
- Page 2 remains structurally stable: Figure 1, the contribution list, and the
  start of Related Work are still readable without overlap.

## Visual Evidence

- Before full contact sheet:
  `tmp/acl_main_visual_iter_20260606_round13_current/contact_sheets/main_pages_01_11_current.png`
- Before page renders:
  - `tmp/acl_main_visual_iter_20260606_round13_current/pages_180/main_front-01.png`
  - `tmp/acl_main_visual_iter_20260606_round13_current/pages_180/main_front-02.png`
  - `tmp/acl_main_visual_iter_20260606_round13_current/pages_180/main_tables-07.png`
  - `tmp/acl_main_visual_iter_20260606_round13_current/pages_180/main_tables-08.png`
- Accepted page renders:
  - `tmp/acl_main_visual_iter_20260606_round13_after4/pages_180/main-01.png`
  - `tmp/acl_main_visual_iter_20260606_round13_after4/pages_180/main-02.png`
- Accepted contact sheet:
  `tmp/acl_main_visual_iter_20260606_round13_after4/contact_sheets/main_pages_01_02_after4.png`
- Evidence sidecar:
  `paper/shared/evidence/raw/acl27_visual_review/main_round13_abstract_story_polish_20260606.json`

## Final PDF

```text
paper/venues/acl27/build/main.pdf
sha256=a405dc573e14fb553033da60852a42ce9328dd420cba5f86d2494d9a2f89af8b
pages=11
bytes=5189144
created=Sat Jun 6 09:50:56 2026 CST
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
check reports `abstract_word_count=169`.

## Residual Risk

This pass is a focused page-1/page-2 abstract story and visual iteration. It is
not a complete final-upload audit, broad full-PDF completion proof, or
integrity-fingerprint refresh.
