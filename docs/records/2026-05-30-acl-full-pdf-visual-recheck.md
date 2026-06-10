# 2026-05-30 ACL Full-PDF Visual Recheck

## Scope

Re-rendered the current ACL/ARR candidate PDF after the target-policy refresh,
Figure 3 provenance-caption hardening, conclusion takeaway polish, and final
manual Introduction page-break removal plus pre-upload-gate restaging to
confirm that the paper still has no page-level visual blocker and does not need
a new imagegen iteration.

## Findings

- The current build PDF is the 11-page A4 candidate with SHA-256
  `177466b7d0cf6a557f73f792dc6f718fdae8f42663e7398a54bc2d9252cde356`,
  size `4066770` bytes, created `Sat May 30 20:25:01 2026 CST`.
- The staged candidate at
  `paper/submissions/acl27_arr_candidate_20260526/main.pdf` is byte-identical
  to the build PDF.
- Rendering all pages at 150 DPI produced the contact sheet hash
  `895062a4428ec572e908db2643077474339171ee459455c0a4bae816d79c20a1`
  under `/tmp/convertasset_acl27_visual_20260530_no_manual_break_final/`.
- Pages 6-9 remain visually usable with minor qualitative caveats: Table 3-6
  density is high, Figure 2's top row is a cropped proxy detail by design, and
  Figure 4's selected navigation stills remain small but coherent. Page 8 now
  carries the compact Figure 3 provenance caption without moving Figure 4 off
  page 9.
- Page 2 now lets Figure 1, the contribution list, and the Related Work heading
  flow without the previous manual `\newpage`; no detached heading or overlap
  was observed.
- No blocking visual failures, abnormal red material fallback, detached
  captions, visible overlap, or raw LaTeX artifacts were observed.
- The final visual-rendered page hashes are: page 1
  `811e00d49062b29a37e823b0752332e92abd13a31fb6aa69ad37474dbd1be237`,
  page 2 `980f7931c141e6ae389421da30d5196f2e96a6f28f9b1d06e3c9b1f2bab05874`,
  page 3 `36f88a6686782340fe5436b90b90bc9b09a60894a1816dd80b533160b69eabe1`,
  page 4 `938afe691cb0aa8c9d004c66bdfc3a009a8f142b930894507af854bc36ad6c61`,
  page 5 `540969e84391d3fcfd42611979396ab27f5dc432bee4211615dd6f12d3c87bfb`,
  page 6 `d2e25d28ad445974ed0b79fbd9b10339dcb399958c31085fc192172cbd620057`,
  page 7 `43b24402e5e690e53f021999108946ba8897e57ffcfa47af319d567270d42456`,
  page 8
  `2898ea13de893b98f078971732a2107592dbef3f83cc9816635c7fd794faaf60`,
  page 9 `087ae75467e45fa1fdee6e30c24d0c99c2384e493955bd5d63a5e6846016d481`,
  page 10 `95b2490acdbc31ca40aed496404890a34a7de64fdf3f15701c2c54d00681e79a`,
  and page 11 `66db72d1f17d31627b5a7ecedc2de85a58baa9dea487dc53e44f1fb23d20691f`.

## Imagegen Decision

No new imagegen candidate was generated in this pass. The current Figure 1 v18
schematic has already passed text-accuracy and page-scale visual review, and
the post-gate full-PDF render did not reveal a specific visual defect that a
new generated image would solve. Generating another candidate without a
targeted defect would increase risk of in-image text errors.

## Evidence

```text
paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260530.json
/tmp/convertasset_acl27_visual_20260530_no_manual_break_final/contact_sheet.png
```

## Verification

Verification after recording this visual recheck:

```bash
python -m json.tool paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260530.json
git diff --check -- paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260530.json docs/records/2026-05-30-acl-full-pdf-visual-recheck.md docs/records/README.md
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/report_final_blockers.py
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Results: the JSON parsed successfully, `git diff --check` reported no
whitespace errors, claim-boundary and metadata checks passed, and the
final-blocker report remained `human_blocked` with no repository blockers. The
consolidated pre-upload gate passed, including 93 focused tests, clean ACL
rebuild, packet staging, PDF profile checks, and ordered text-section checks.
