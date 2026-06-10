# 2026-05-28 ACL Abstract Boundary Tightening

## Scope

This record documents a manuscript and metadata revision to align the ACL
abstract with the paper's claim-bounded story.

## Problem

The previous abstract said:

```text
proxy fidelity does not determine grounding behavior
```

That sentence was directionally aligned with the paper, but it could be read as
a broad causal statement. The rest of the manuscript is more precise: proxy
metrics are useful screening evidence, but they are insufficient by themselves
for downstream grounding or embodied-data claims.

## Change

The abstract now says:

```text
proxy fidelity alone is insufficient for downstream grounding claims
```

The same plain-text abstract was copied into:

```text
paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md
```

The metadata checker reports a conservative abstract count of 181 words, below
the 200-word limit used by the current ACL/ARR packet guard.

## Guard

Added a regression test:

```text
tests/test_acl_metadata_consistency.py::test_acl_abstract_uses_bounded_proxy_fidelity_wording
```

The test rejects the old broad wording and requires the bounded proxy-fidelity
wording in both the manuscript abstract and OpenReview metadata copy source.

## Verification

Commands run after the edit:

```bash
python -m pytest -q tests/test_acl_metadata_consistency.py
python paper/venues/acl27/scripts/check_metadata_consistency.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
python paper/venues/acl27/scripts/check_openreview_checklist.py
```

Observed result:

```text
tests/test_acl_metadata_consistency.py: 2 passed
metadata_consistency: ok=true, abstract_word_count=181
claim_boundaries: ok=true
openreview_checklist: ok=true
```

The final packet hash must be refreshed by rerunning the full pre-upload gate
after the final-integrity fingerprint is updated.

## Full Gate Closure

After refreshing the final-integrity fingerprint, the full repository-side
pre-upload gate was rerun:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Observed result:

```text
ok=true
focused_pytest=85 passed in 1.89s
pages=11
size=3,073,082 bytes
sha256=021ad97eab2e78701ba8327750b28e36741446f3c5039396cc8c8dba572c48a6
```

The build PDF and staged packet PDF are byte-identical. The ignored private
author-gate worksheet was then refreshed with:

```bash
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
```

Local rendered-PDF visual review of the 150-DPI contact sheet
`tmp/acl27_post_abstract_gate_visual_20260528/contact_sheet.png`
(`sha256=f176fe5bab9af02a36e6296ff2a393ee694a8cad92ac390c1eb13379b17b21bd`)
found no page-level overlap, blank page, detached caption, or Fig.3
red-material regression after the abstract wording change.

## Follow-up: Point-Hit Direction Clarity

A later quick academic-review pass found that the abstract phrase
`27/30 versus 29/30 normalized-1000 point hits` was numerically correct but
forced readers to infer which value belonged to original or converted renders.
The abstract and OpenReview metadata copy source now state:

```text
27/30 original versus 29/30 converted normalized-1000 point hits
```

The metadata checker now reports `abstract_word_count=183`, still below the
200-word packet guard. This edit changes result readability only; the evidence
numbers and claim boundary are unchanged.

Follow-up current-PDF sync: the current build and staged PDFs after this
direction-clarity edit are byte-identical:

```text
paper/venues/acl27/build/main.pdf
sha256=4936611aa9aafc4795365ee2aa9892280b151a40e5994f69580bf5ee4dfb40bc
pages=11
bytes=4066563
created=Thu May 28 22:50:25 2026 CST

paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=4936611aa9aafc4795365ee2aa9892280b151a40e5994f69580bf5ee4dfb40bc
```

The page-1 visual review in
`paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_v18_20260528.json`
found no title/abstract overlap, clipping, or page-flow regression from the
extra `original` / `converted` wording.
