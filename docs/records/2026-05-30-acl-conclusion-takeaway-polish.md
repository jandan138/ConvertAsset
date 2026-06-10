# 2026-05-30 ACL Conclusion Takeaway Polish

## Scope

Ran a reviewer-style manuscript iteration after the figure-forward ACL draft was
already candidate-ready. The main issue found was not a missing experiment or a
visual defect; the conclusion still read too much like a state summary and did
not make the paper's practical takeaway explicit enough for ACL reviewers.

## Change

Updated `paper/venues/acl27/sections/conclusion.tex` so the conclusion states
the supported claim as an evidence gate: converted-asset benchmarks should
expose matched renders, projection QA, prompt and coordinate contracts,
material-risk bins, and embodied smoke gates before using converted synthetic
scenes for downstream reliability claims.

The change keeps the same claim boundary:

- no broad robustness claim;
- no speedup claim;
- no universal MDL-preservation claim;
- no population-level NVIDIA failure-rate claim.

## Author Identity Note

The private author-gate worksheet was refreshed after user confirmation on
2026-05-30 that the submitter is Zihou Zhu, sole independent author, using the
public OpenReview profile `https://openreview.net/profile?id=~Zihou_Zhu1`.
This is intentionally kept in the ignored local worksheet and not in the
anonymous manuscript PDF.

## Imagegen And Visual Review

No new imagegen iteration was run. The accepted Figure 1 v18 schematic remains
the active generated image because the post-gate visual review did not reveal a
specific defect that another generated bitmap would solve.

The final staged PDF was rendered at 150 DPI under
`/tmp/convertasset_acl27_visual_20260530_final/`. The contact sheet SHA-256 is
`9f7cd7533396d9f258f4bf437b13fe7f41682d5018d4339b3d9587a6f7cb2598`.
Page 8 contains Figure 3 and the strengthened conclusion without visible
overlap or red-material recurrence; page 9 keeps Figure 4, Limitations, and
Ethical Considerations visually coherent.

## Final Candidate

The consolidated pre-upload gate rebuilt and restaged the candidate:

```text
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=a66a67324f267ab7e41b4fb75993efef6969129148fc3ee95156bcdd6f5488ed
pages=11
bytes=4066669
created=Sat May 30 20:12:12 2026 CST
```

The build and staged PDFs are byte-identical. The adjacent ignored checksum
sidecar is `paper/submissions/acl27_arr_candidate_20260526.sha256` with SHA-256
`e1d953e6f8b05211405da1ec38c1b73e215ae9871e562b818eff949b3490eb3c`.

## Verification

Commands run after the conclusion polish:

```bash
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/run_preupload_gate.py
pdftotext paper/submissions/acl27_arr_candidate_20260526/main.pdf - | rg -n "Figure 1|Table 1|Figure 2|Table 2|Table 3|Table 4|Table 5|Table 6|Figure 3|Figure 4|Limitations|Ethical Considerations|References|undefined|\\?\\?"
```

Results: integrity fingerprint passed over 57 sources, claim-boundary and
metadata checks passed, the consolidated pre-upload gate passed including 93
focused tests and clean ACL rebuild, the staged packet was regenerated, and the
PDF text guard found all expected anchors with no `undefined` or `??` markers.

## Remaining Gate

The repository-side packet is candidate-ready. Final upload remains
`human_blocked`: the author must lock the final ACL-family route, finish the
private OpenReview author gate, copy metadata/checklist text into OpenReview,
approve runtime/AI/media/license wording, and make the final upload decision.
