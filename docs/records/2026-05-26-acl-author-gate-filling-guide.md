# ACL Author-Gate Filling Guide

Date: 2026-05-26.

## Summary

Added a tracked, privacy-safe guide for filling the ignored
`OPENREVIEW_AUTHOR_GATE_FILLED.local.md` worksheet before a real ARR/OpenReview
submission.

New file:

- `paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLING_GUIDE.md`

The guide turns the remaining author-only gate into an explicit workflow:
choose route, fill author/OpenReview readiness, fill submission-history fields,
approve form-copy text, decide optional media, run the final pre-upload gate,
copy final evidence into the private worksheet, and verify the filled worksheet
is ignored.

## Why This Matters

The repository can already rebuild and stage the anonymous candidate packet, but
it cannot know real author order, OpenReview profiles, reviewer-registration
commitment, dual-submission status, preprint status, runtime approval, or media
legal approval. The new guide keeps those decisions out of tracked files while
making the required fill order and stop conditions concrete.

## Sources Rechecked

- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/authorchecklist`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://2027.eacl.org/calls/papers/`

The route state remains unchanged: EACL 2027 via ARR is the concrete public
2027 ACL-family route, while Annual ACL 2027 still lacks a public official
CFP/author kit in checked sources.

## Verification

Run after this documentation pass:

```bash
git diff --check
git check-ignore -v paper/venues/acl27/OPENREVIEW_AUTHOR_GATE_FILLED.local.md
python paper/venues/acl27/scripts/run_preupload_gate.py
```

The full goal remains open because the authors still need to fill the private
worksheet and copy final metadata/checklist answers into the official
OpenReview form.
