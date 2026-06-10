# 2026-05-28 ACL Figure 4 Caption Polish

## Scope

This record closes a small page-9 visual-polish pass on the ACL main paper. It
changes the Figure 4 caption wording in `paper/venues/acl27/sections/limitations.tex`
without changing the selected InternNav image, the 99-episode metrics, the
official-scene load/render table, or the claim boundary.

No image generation was used in this pass: the current issue was caption
line-breaking in a narrow ACL column, not a missing or unsuitable visual asset.

## Problem

Local rendered-PDF visual review of page 9 found that the Figure 4 caption was
usable but opened with an awkward line break:

```text
Figure 4: Selected qualitative InternNav roll-
out panel.
```

The hyphenation made the selected qualitative panel look less polished at
submission scale. The same page otherwise remained structurally sound:
Limitations, Figure 4, Ethical Considerations, and the AI-assistance disclosure
all stayed visible without overlap.

## Test-First Guard

Before editing the LaTeX source, a focused regression test was added:

```text
tests/test_internnav_rollout_figure.py::test_internnav_caption_avoids_rollout_linebreak_hotspot
```

The test first failed against the previous source because the expected compact
caption opening was not present:

```text
AssertionError: assert 'Selected InternNav path panel.' in ...
```

## Change

The prose now uses a shorter, less hyphenation-prone wording:

```text
The selected path panels are qualitative evidence only...

Figure 4: Selected InternNav path panel.
```

The caption still states that purple paths/action arrows and green reference
paths are orientation overlays, and that quantitative embodied-data claims
remain tied to the 99-episode paired run and official-scene load/render checks.

## Visual Review

The current page-9 render after the change is:

```text
/tmp/convertasset_acl27_fig4_caption_polish/page-09.png
sha256=67566ff56fa342707a7173e91fb46ebf71bca8a8f77e4df55a076c7cae30679a
```

`pdftotext -layout` now extracts the caption opening as:

```text
Figure 4: Selected InternNav path panel. This
selected official KuJiaLe example shows ...
```

No `roll-` / `out panel` break remains in the Figure 4 caption.

Durable visual-review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/figure4_caption_polish_review_20260528.json
```

## Verification

Commands run:

```bash
python -m pytest -q tests/test_internnav_rollout_figure.py::test_internnav_caption_avoids_rollout_linebreak_hotspot
python -m pytest -q tests/test_internnav_rollout_figure.py
make -C paper acl27
pdftotext -f 9 -l 9 -layout paper/venues/acl27/build/main.pdf - | rg -n "roll-|rollout|path panel|Figure 4:"
```

Observed results:

```text
1 failed before the source edit
4 passed in 2.80s after the source edit
ACL PDF build succeeded
pdftotext reports "Figure 4: Selected InternNav path panel" and no "roll-" caption break
```

The inspected build PDF before final staging refresh was:

```text
paper/venues/acl27/build/main.pdf
sha256=3edb09ae2e1652d88bf3ad3e479a383c3a18b31338d1f52c2790dfe54d40c4b7
pages=11
bytes=3625276
created=Thu May 28 16:50:59 2026 CST
```

The final-integrity fingerprint and staged candidate must be refreshed after
this protected-source edit.
