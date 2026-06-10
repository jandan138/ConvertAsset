# 2026-06-02 ACL Supplement Layout Polish

## Summary

The first supplement scaffold built correctly, but the visual review found a
real layout problem: many InternNav pages looked like loose image blocks with
short captions and large blank areas. The root cause was the `\suppfig` macro:
each selected navigation case was emitted as its own floating figure page with a
forced `\clearpage`.

This pass keeps the selected navigation evidence but groups it into paired
evidence pages. The supplement now reads more like a formal ACL supplement and
less like a raw evidence dump.

## Changes

- Added `\suppcasepair` in `paper/venues/acl27/supplement.tex`.
- Replaced 12 standalone InternNav case pages in
  `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex` with
  6 paired evidence pages.
- Tightened selected6 crop boxes in
  `paper/shared/figures/gen_acl_supplement_navigation_crops.py` so case titles
  are complete and top-edge artifacts are removed.
- Added panel-level trim/contain processing for 0036/0066 crops so low-density
  neutral cases no longer carry large source-sheet margins.
- Added layout tests in `tests/test_paper_layout.py` to prevent regression to
  per-case standalone pages and unreadable 0036/0066 crop density.

## Verification

Build:

```bash
make -C paper acl27-supplement
```

PDF profile:

- artifact: `paper/venues/acl27/build/supplement.pdf`
- pages: 34
- page size: A4
- file size: 6,219,146 bytes
- SHA-256: `44592ce8724f77445be3ce1f60c1470b5068a8f811623a8af3df3e1b49e40981`

Tests:

```bash
python -m pytest -q tests/test_paper_layout.py
```

Result: `19 passed`.

Privacy scan:

```bash
pdftotext -layout paper/venues/acl27/build/supplement.pdf /tmp/acl27_supplement.txt
rg -n "/cpfs|/home/|/root/|zhuzihou|jandan138|github\\.com/jandan138|ConvertAsset\\.git" /tmp/acl27_supplement.txt
```

The `rg` command returned no matches.

Visual review:

- record:
  `paper/shared/evidence/raw/acl27_visual_review/supplement_layout_polish_review_20260602.json`
- verdict: `PASS_WITH_NOTES`
- remaining note: the final neutral 0036/0066 cases remain visually thin due to
  the source still composition, but they are now grouped and trimmed rather than
  scattered standalone pages.

## Remaining Work

The supplement is now a stronger layout candidate, but final polish can still
improve the non-InternNav sections:

- reduce some hard `\clearpage` usage around diagnostic tables
- decide whether the two overview index sheets should remain in the PDF or move
  to the media bundle
- run an independent blind visual review before final upload
