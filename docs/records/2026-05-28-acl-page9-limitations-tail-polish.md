# 2026-05-28 ACL Page 9 Limitations Tail Polish

## Scope

This record documents the page-9 layout polish after the main paper promoted
Figure 4 to a wide InternNav qualitative panel.

## Finding

The wide Figure 4 was visually useful, but the first build left a short
Limitations continuation at the top of the right column before
`Ethical Considerations`. That looked like an accidental dangling tail rather
than a clean section transition.

The manuscript text now tightens the final InternNav limitation sentence in:

```text
paper/venues/acl27/sections/limitations.tex
```

The claim boundary did not change: the official-scene checks support stability
only, not speedup, and the selected path panels remain qualitative orientation
evidence only.

## Visual Review

Current local artifacts at the time of this polish:

```text
paper/venues/acl27/build/main.pdf
sha256=36b2f0fae8ead9955016466227ef9936fa0f454427577aefb48b53c523116711
pages=11
bytes=3991259
created=Thu May 28 19:33:56 2026 CST

/tmp/convertasset_acl27_limitations_tail_final/page-09.png
sha256=d120edde228dd31e50540c5d0e51761ccd9695826f0d0a1e0675ed48d999129e
size=1489x2105
strong_red_pixels=0

paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png
sha256=4d8881fd4833c32c039d8d5e72036570503a4bb6d08c1dec0d250fc4f398fe2e
size=1748x806
strong_red_pixels=0
```

The rendered page now keeps Figure 4 at the top and starts the right column
cleanly with `Ethical Considerations`.

Durable review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/limitations_page9_tail_polish_review_20260528.json
```

## Verification

Commands run for this polish:

```bash
python -m pytest -q tests/test_internnav_rollout_figure.py -k caption_avoids_rollout_linebreak_hotspot
python -m pytest -q tests/test_internnav_rollout_figure.py
make -C paper acl27
pdftotext -f 9 -l 9 -layout paper/venues/acl27/build/main.pdf -
pdftoppm -f 9 -l 9 -png -r 180 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_limitations_tail_final/page
```

Focused result: `tests/test_internnav_rollout_figure.py` reports `5 passed`.
The follow-up consolidated pre-upload gate reports `ok=true` with 91 focused
tests and a staged PDF hash matching the build PDF.
