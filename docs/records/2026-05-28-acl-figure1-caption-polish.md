# 2026-05-28 ACL Figure 1 Caption Polish

## Scope

This record documents the final small Figure 1 caption polish after the v18
imagegen method-chain schematic had already passed local visual review and was
promoted into the ACL main paper.

## Change

The Figure 1 caption now starts with:

```text
Evidence-chain overview.
```

instead of:

```text
Figure-driven overview of the paper's evidence chain.
```

The edit is wording-only. It makes the caption sound like a paper-facing ACL
caption rather than an internal production label. No experimental number,
figure source, image pixels, claim boundary, citation, or table content changed.

## Imagegen / Visual Review Decision

No new imagegen candidate was generated in this pass. The existing v18
schematic remained the safer choice because prior visual review already checked
the exact `Target: box` text, the `VLM Checks` stage title, the four-stage
method-chain structure, and page-scale readability. Regenerating without a
specific visual failure would have added unnecessary text-accuracy risk.

The current PDF was rerendered with the pure visual-review workflow at 150 DPI:

```text
paper/venues/acl27/build/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7
pages=11
bytes=4066538
created=Thu May 28 23:22:53 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=59636b2dbd5b43f90c49ddcf72649a018005790254f26558724f1c15fd2cb6b7

/tmp/convertasset_acl27_current_visual_review_2322/contact_sheet.png
sha256=54071ded4baf34679d4bb373252fda445e22d749724ac3cef0b0de1d78cbbf70

/tmp/convertasset_acl27_current_visual_review_2322/page-02.png
sha256=5badba8aa60021957cbc93b3213b56abeacab9db6a941548ba460fada1fe56a8
```

Local page-2 visual review found that the v18 schematic remains readable at
page scale, the caption stays attached, the new `Evidence-chain overview`
opening is visible in extracted PDF text, and the first contribution page has
no visible overlap or clipping.

## Verification

Commands run:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
sha256sum paper/venues/acl27/build/main.pdf paper/submissions/acl27_arr_candidate_20260526/main.pdf
pdftoppm -png -r 150 paper/venues/acl27/build/main.pdf /tmp/convertasset_acl27_current_visual_review_2322/page
pdftotext -layout paper/venues/acl27/build/main.pdf - | rg -n "Figure 1:|Evidence-chain overview|Figure-driven overview"
rg -n "Undefined|undefined|Citation .* undefined|Reference .* undefined|multiply defined|Overfull" paper/venues/acl27/build/main.log
```

`run_preupload_gate.py` completed all configured checks, including 91 focused
tests, clean ACL rebuild, LaTeX log scan, packet staging, packet inventory,
checksum/private-token/acknowledgment scans, PDF profile checks, and ordered
text-section checks.

## Remaining Boundary

The full paper goal is still not final-upload complete. The repository-side
candidate is ready, but the author still needs to lock the final ACL-family
route, copy the OpenReview form fields, approve runtime/AI/media/license
wording, complete the private author worksheet, and make the final upload
decision.
