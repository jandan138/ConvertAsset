# 2026-05-28 ACL Table 6 Caption Polish

## Scope

This record closes a layout-only polish pass on the ACL main-paper official
scene performance table. The pass changes the generated Table 6 caption and
does not change the underlying official-scene experiment rows, InternNav
metrics, material-effect evidence, or NVIDIA claim boundary.

No image generation was used for this pass because the issue was table-caption
density, not missing schematic or empirical imagery.

## Problem

Local PDF review found that page 7 remained readable but dense: Tables 3--6 all
land on the same page, and the previous Table 6 caption made the right column
look like a small table followed by a large explanatory block. The table already
used the correct aggregate layout, but the caption was longer than needed for
main-paper scanning.

## Change

`paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py`
now emits a compact Table 6 caption:

```text
Official KuJiaLe / InteriorAgent scene load/render stability. Aggregate original/noMDL rows only; intervals are bootstrap 95% CIs. NVIDIA official-scene baseline is omitted until matching conversions pass smoke gates.
```

The generated table remains:

```text
paper/shared/tables/tab_official_scene_performance_summary.tex
paper/shared/tables/official_scene_performance_summary.csv
```

The CSV remains the machine-readable source for per-scene detail. The main-paper
LaTeX table stays aggregate-only to preserve readability.

## Test-First Guard

Before changing the generator, a focused regression test was added:

```text
tests/test_official_scene_submission_closure.py::test_performance_summary_caption_stays_compact_for_main_pdf
```

The new test first failed on the old caption with:

```text
AssertionError: assert 51 <= 30
```

After the generator change and table rebuild, the focused tests passed.

## Visual Review

Local visual review rendered the current PDF pages 7--8 at 150 DPI:

```text
/tmp/convertasset_acl27_current_visual/page-07.png
sha256=df90adf076d30284b4452e20da306177a28de6eb34e7e7d4e16954c1da4b9123

/tmp/convertasset_acl27_current_visual/page-08.png
sha256=ba29e98a331afea7af10458120af6f0968599bbc38547129c0ea2ffc919d42a2
```

The review verdict is `pass_with_caveat`: Table 6 fits in the right column on
page 7, has no visible overlap with Table 5, body text, or margins, and keeps
the NVIDIA official-scene baseline omission explicit. The caveat is that page 7
remains dense because Tables 3--6 share the page, but this is not a blocking
layout defect.

Durable review summary:

```text
paper/shared/evidence/raw/acl27_visual_review/table6_caption_compact_review_20260528.json
```

## Verification

Commands run:

```bash
python -m pytest -q \
  tests/test_official_scene_submission_closure.py::test_performance_summary_caption_stays_compact_for_main_pdf \
  tests/test_official_scene_submission_closure.py::test_write_performance_summary_table_includes_failure_counts

python paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py

python -m pytest -q \
  tests/test_official_scene_submission_closure.py \
  tests/test_acl_claim_boundaries.py \
  tests/test_acl_preupload_gate.py

make -C paper acl27
```

Observed results:

```text
2 passed in 0.10s
Submission closure complete: True
38 passed in 0.21s
ACL PDF build succeeded
```

The build PDF inspected in this record is:

```text
paper/venues/acl27/build/main.pdf
sha256=91cb9d3c248596f2356324e30a369fecbd267d80bc25f40fa33adb350e2f66de
pages=11
bytes=3625282
created=Thu May 28 16:32:03 2026 CST
```

The final-integrity fingerprint was refreshed after the table source changed,
and the consolidated pre-upload gate was rerun. The build and staged candidate
PDFs are now byte-identical:

```text
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=91cb9d3c248596f2356324e30a369fecbd267d80bc25f40fa33adb350e2f66de
```

The gate passed claim boundaries, target policy, metadata consistency,
OpenReview checklist, citation inventory, evidence-number checks,
final-integrity fingerprint, blocker/goal reports, 89 focused tests, clean ACL
rebuild, LaTeX log scan, packet staging, packet inventory/checksum/private-token
and acknowledgment scans, PDF profile checks, and ordered `pdftotext` section
checks.
