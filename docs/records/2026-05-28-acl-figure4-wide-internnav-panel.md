# 2026-05-28 ACL Figure 4 Wide InternNav Panel

## Scope

This record upgrades main-paper Figure 4 from one selected single-column
InternNav rollout panel to the recorded three-case official KuJiaLe InternNav
path panel.

## Change

- `paper/venues/acl27/sections/limitations.tex` now places a two-column
  `figure*` before the Limitations text and uses
  `paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png`.
- The caption now starts with `Selected InternNav path panels.` and keeps the
  orientation-only boundary: quantitative claims remain tied to the
  99-episode paired run and official-scene load/render checks.
- `tests/test_internnav_rollout_figure.py` now guards the wide figure source,
  plural caption, placement before `Limitations`, and the claim-boundary
  wording.

## Visual Review

Local visual review reports `PASS_WITH_BOUNDARY`. The wide panel makes the real
navigation evidence more visible than the old single-column panel, keeps the
purple executed paths/action arrows and green reference paths readable, and
does not add pages or visible overlap. It is still only selected qualitative
evidence for reader orientation.

Current checked artifacts:

```text
paper/venues/acl27/build/main.pdf
sha256=36b2f0fae8ead9955016466227ef9936fa0f454427577aefb48b53c523116711
pages=11
bytes=3991259
created=Thu May 28 19:33:56 2026 CST

paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png
sha256=4d8881fd4833c32c039d8d5e72036570503a4bb6d08c1dec0d250fc4f398fe2e
size=1748x806
strong_red_pixels=0

/tmp/convertasset_acl27_limitations_tail_final/page-09.png
sha256=d120edde228dd31e50540c5d0e51761ccd9695826f0d0a1e0675ed48d999129e
size=1489x2105
strong_red_pixels=0
```

Durable review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/figure4_wide_internnav_review_20260528.json
```

## Claim Boundary

Figure 4 can support a concrete, reader-visible example of the official
InternNav evidence route. It must not be used as a population-level embodied
robustness result, an official-scene speedup claim, or an NVIDIA official-scene
baseline.

## Verification

Commands run before this record:

```bash
python -m pytest -q tests/test_internnav_rollout_figure.py
make -C paper acl27
pdftoppm -f 9 -l 9 -png -r 180 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_wide_internnav_final/page
pdftotext -f 9 -l 9 -layout paper/venues/acl27/build/main.pdf -
```

Focused result: `tests/test_internnav_rollout_figure.py` reports `5 passed`.
The follow-up consolidated pre-upload gate reports `ok=true` with 91 focused
tests and a staged PDF hash matching the build PDF.

## Follow-up Page-9 Tail Polish

The first wide-panel build made the page-9 right column begin with a short
continuation of the Limitations paragraph before `Ethical Considerations`.
`paper/venues/acl27/sections/limitations.tex` was tightened so the section
transition starts cleanly while keeping the same claim boundary: the selected
path panels are orientation evidence only, and official-scene load/render
closure supports stability only, not speedup.

The follow-up durable review record is:

```text
paper/shared/evidence/raw/acl27_visual_review/limitations_page9_tail_polish_review_20260528.json
```
