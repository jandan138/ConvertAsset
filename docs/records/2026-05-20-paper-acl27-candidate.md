# 2026-05-20 Paper ACL 2027 Candidate Venue

## Summary

Added `paper/venues/acl27/` as a candidate venue wrapper for the user's intended Annual ACL 2027 Japan route.

## Source Check

Public checks on 2026-05-20 found:

- An ACL Executive Committee resolution saying the 2027 conference will be branded as `ACL 2027` without IJCNLP/AFNLP co-branding.
- Official ACL style-file guidance pointing authors to `acl.sty` and `acl_natbib.bst`.
- No public ACL 2027 CFP or official city/date page in the checked sources.

Because the public CFP is not available, `paper/venues/acl27/STATUS.md` records Japan as the user-requested route and leaves the official city/date/deadline checks open.

## Changes

- Registered `acl27` in `paper/Makefile`.
- Added ACL template checks for `acl.sty` and `acl_natbib.bst`.
- Added an ACL wrapper that reuses `paper/shared/sections/` and adds local `Limitations` and `Ethical Considerations` sections.
- Updated `paper/README.md`, `docs/superpowers/README.md`, and `tests/test_paper_layout.py`.

## Fit Assessment

The ACL version should not reuse the workshop narrative unchanged. The current manuscript is about synthetic-data asset conversion and renderer/material trade-offs. For ACL, the paper needs a stronger computational-linguistics hook, preferably through multimodal language grounding, VLM evaluation, embodied agent perception, synthetic scene captions/questions/instructions, or language-grounded failure analysis.

AAAI 2027 remains the stronger primary target until those ACL-specific experiments and narrative changes exist.
