# 2026-05-30 ACL InternNav Scope Wording Polish

## Scope

Ran a focused reviewer-style pass on the Limitations page after the candidate
PDF was already repository-side gate clean. The issue found was a wording and
guardrail problem, not a missing experiment: `all-InteriorNav` was awkward and
less precise than the intended claim boundary.

## Change

- Updated `paper/venues/acl27/sections/limitations.tex` to say the 99-episode
  route is not evidence for all InternNav or InteriorAgent settings, R2R/MP3D,
  manipulation, or broad GRScenes robustness.
- Shortened the repeated Figure 4 sentence to: Figure 4 is qualitative
  orientation evidence only.
- Extended `check_claim_boundaries.py` so the automated guard catches natural
  broad-scope variants such as `all InternNav` and `all InteriorAgent`, not only
  hyphenated forms.
- Updated the claim audit, OpenReview checklist copy source, tests, and current
  claim registry wording to match.

## Imagegen And Visual Review

No imagegen iteration was run. The issue was text/scope wording plus page-9
flow, and the accepted Figure 1 v18 schematic remains the active generated
image.

The final staged PDF page 9 was rendered at 150 DPI under:

```text
/tmp/convertasset_acl27_visual_20260530_internnav_scope_guard_final/
```

The rendered page-9 SHA-256 is:

```text
c102b28d3ca1b6d01713bebd110481c0178f80fa206376cfc23d4eed636f4496
```

Local pure-visual review verdict: `PASS`. Figure 4, its caption, Limitations,
and Ethical Considerations remain readable with no overlap or clipping.

Durable visual evidence:

```text
paper/shared/evidence/raw/acl27_visual_review/internnav_scope_guard_visual_review_20260530.json
```

## Final Candidate

The consolidated pre-upload gate rebuilt and restaged the candidate:

```text
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=137370b33b567ebc55ab6f88ef5d6e6860b6e61debf133e8077b14a22b454c98
pages=11
bytes=4066626
created=Sat May 30 20:43:58 2026 CST
```

The build and staged PDFs are byte-identical. The adjacent ignored checksum
sidecar is `paper/submissions/acl27_arr_candidate_20260526.sha256` with
SHA-256:

```text
0439826be4d8dd283dc82b277a8a206f6964e031d43bee0f3cadaf2bbf7fb86c
```

## Verification

Commands run:

```bash
python -m pytest -q tests/test_acl_claim_boundaries.py tests/test_acl_openreview_checklist.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_openreview_checklist.py
python paper/venues/acl27/scripts/check_integrity_fingerprint.py --write
python paper/venues/acl27/scripts/check_integrity_fingerprint.py
python paper/venues/acl27/scripts/run_preupload_gate.py
pdftotext paper/submissions/acl27_arr_candidate_20260526/main.pdf - | rg -n "all InternNav|InteriorAgent settings|qualitative orientation evidence|Figure 4|Limitations|Ethical Considerations|References|undefined|\\?\\?"
```

Results: 13 focused claim/checklist tests passed, the claim-boundary and
OpenReview-checklist gates passed, the final-integrity fingerprint passed over
57 sources, the consolidated pre-upload gate passed including 93 focused tests
and clean ACL rebuild, and the text guard found the revised scope wording with
no `undefined` or `??` markers.

## Remaining Gate

The repository-side packet is still candidate-ready but not final-upload
complete. Remaining blockers are human-only: final route lock, private
OpenReview author-gate completion, official OpenReview form copy,
runtime/AI/media/license approval, and final upload decision.
