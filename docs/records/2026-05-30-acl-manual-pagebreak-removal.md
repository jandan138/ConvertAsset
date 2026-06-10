# 2026-05-30 ACL Manual Page-Break Removal

## Scope

Ran another reviewer-style layout pass on the ACL candidate after the
conclusion takeaway polish. The issue found was small but submission-facing:
`paper/venues/acl27/sections/intro.tex` still contained a manual `\newpage`
before the contribution list. This was a layout artifact, not a scientific
requirement, and could look like hand-tuned pagination in a review PDF.

## Change

Removed the manual page break before `We make four contributions:`. The first
two pages now flow naturally:

- page 1 keeps the title, abstract, and opening framing;
- page 2 starts with Figure 1, then the evidence-gate paragraph, contribution
  list, and Related Work heading;
- no figure or table was regenerated.

## Imagegen And Visual Review

No new imagegen iteration was run. The accepted Figure 1 v18 schematic remains
the active generated image because the rendered page-2 check still preserves
the exact `Target: box` label and no visual defect called for another generated
candidate.

The staged PDF was rendered at 150 DPI under
`/tmp/convertasset_acl27_visual_20260530_no_manual_break_final/`. Contact sheet
SHA-256:

```text
895062a4428ec572e908db2643077474339171ee459455c0a4bae816d79c20a1
```

Visual verdict: pass with minor qualitative caveats. Page 2, page 7, page 8,
and page 9 were checked directly. The change does not introduce blank pages,
detached headings, figure/table overlap, red-material recurrence, or Figure 4
movement.

## Final Candidate

The consolidated pre-upload gate rebuilt and restaged the candidate:

```text
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356
pages=11
bytes=4066770
created=Sat May 30 20:25:01 2026 CST
```

The build and staged PDFs are byte-identical. The adjacent ignored checksum
sidecar is `paper/submissions/acl27_arr_candidate_20260526.sha256` with SHA-256
`4a39e9ce663abac3c31b266272173acb047f7ea7cbd28c868dec5d4d0e18a4ad`.

## Verification

Commands run:

```bash
rg -n -F '\newpage' paper/venues/acl27/sections paper/venues/acl27/main.tex paper/venues/acl27/preamble.tex
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/run_preupload_gate.py
pdftotext paper/submissions/acl27_arr_candidate_20260526/main.pdf - | rg -n "Figure 1|We make four contributions|Related Work|Figure 2|Figure 3|Figure 4|Limitations|Ethical Considerations|References|undefined|\\?\\?"
```

Results: no remaining `\newpage` / `\clearpage` / `\pagebreak` /
`\enlargethispage` controls were found in the ACL wrapper sources checked,
the final-integrity fingerprint passed over 57 sources, the consolidated
pre-upload gate passed including 93 focused tests and clean ACL rebuild, and
the staged PDF text guard found the expected anchors with no `undefined` or
`??` markers.

## Remaining Gate

This is a repository-side polish only. Final upload remains human-gated by
route lock, private author gate completion, OpenReview form copy,
runtime/AI/license/media approvals, and final upload decision.
