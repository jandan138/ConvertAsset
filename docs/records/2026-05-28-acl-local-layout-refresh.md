# 2026-05-28 ACL Local Layout Refresh

## Scope

This record captures a local ACL manuscript layout pass after a pure visual
review found that the checked PDF was stale relative to the current source.

The stale build was:

```text
paper/venues/acl27/build/main.pdf
sha256=4fb42c74a889f5ee2ad094305196d0fd2f62309549ad7579beb0d6c705484b06
pages=11
size=3,010,349 bytes
created=2026-05-28 11:59:21 CST
```

It still showed a large page-8 blank right column because it had not absorbed
the current `main.tex` flow after removing the forced post-Conclusion page
break.

## Changes

- Rebuilt the ACL PDF from the current source. The local build now has 10 pages
  and no stale page-8 blank-column defect.
- Kept Tables 5 and 6 as single-column floats so the material-effect and
  official-scene evidence stay near the Results text rather than moving after
  Discussion/Conclusion.
- Added a local `\tabcolsep` setting to
  `paper/shared/tables/tab_official_scene_performance_summary.tex` to remove the
  Table 6 overfull hbox.
- Mirrored that Table 6 setting in
  `paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py`
  so regenerated official-scene packages keep the same layout.
- Added local `hypcap=false` before the Figure 3 `\captionof{figure}` command in
  `paper/venues/acl27/sections/limitations.tex` to remove the harmless caption
  package warning caused by the minipage caption.

## Visual Review

Local pure visual review, following the `render-visual-reviewer` rubric, checked
the rebuilt PDF and focused pages 7--9:

```text
tmp/acl27_rebuild_visual_20260528/contact_sheet.png
tmp/acl27_rebuild_visual_20260528/page_after_tablefix-07.png
tmp/acl27_rebuild_visual_20260528/page_after_tablefix-08.png
tmp/acl27_rebuild_visual_20260528/page_after_tablefix-09.png
```

Findings:

- Page 7 keeps Tables 3, 4, 5, and 6 readable without overlap.
- Page 8 now carries Discussion, Conclusion, and Limitations text instead of a
  mostly blank right column.
- Page 9 keeps Figure 3 attached to its caption, starts References in the right
  column, and keeps Ethical Considerations readable in the left column.
- Figure 3 remains the selected InternNav rollout panel with purple/green
  navigation overlays; no red material fallback is visible.

The durable visual-review summary is:

```text
paper/shared/evidence/raw/acl27_visual_review/layout_refresh_visual_review_20260528.json
```

## Verification

Local build:

```bash
make -C paper acl27
```

Result:

```text
paper/venues/acl27/build/main.pdf
sha256=1a3fed80730e648dec0fc989b1215f84bb78be3907289799c06ded2ebd82c78f
pages=10
size=3,009,971 bytes
created=2026-05-28 12:40:50 CST
```

Focused log scan:

```bash
grep -n "Overfull\|Package .*Warning\|LaTeX Warning\|undefined\|Error" \
  paper/venues/acl27/build/main.log
```

Result: `0` matches after the Table 6 and Figure 3 caption fixes.

## Boundary

This is a local layout refresh, not a new staged submission candidate. The full
pre-upload gate, integrity fingerprint refresh, packet scans, staging audit, and
OpenReview/upload gates still need to be rerun before this local 10-page PDF can
replace the last staged candidate.

## Follow-up Full Pre-upload Gate

The consolidated pre-upload gate was rerun after this local layout refresh and
the follow-up `pdftotext` two-column guard update:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result:

```text
ok=true
focused_pytest=88 passed
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=b4d43ce170073bdc864354ba62c5056f92fae3272ae309b8a025c2ce145ad65b
pages=10
size=3,009,971 bytes
created=2026-05-28 12:58:38 CST
```

The build and staged PDFs are byte-identical. The gate passed claim-boundary,
target-policy, metadata, checklist, citation, evidence-number,
final-integrity-fingerprint, blocker/goal-report, clean-build, log-scan,
staging, packet inventory/checksum, private-token, acknowledgment, PDF profile,
and `pdftotext` checks.

The old boundary note above therefore applies only to the initial local refresh
moment. The current 10-page PDF has now replaced the previous 11-page staged
candidate at the repository-side pre-upload rehearsal level. Final upload still
depends on human route lock, OpenReview form copy, runtime/AI/media approvals,
and final upload decision.
