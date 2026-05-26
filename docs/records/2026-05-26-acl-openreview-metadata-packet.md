# ACL OpenReview Metadata Packet

Date: 2026-05-26

## Purpose

Prepare copy-ready OpenReview metadata for the current ACL/ARR candidate and
close an ACLPUB formatting issue found during metadata extraction: the previous
abstract was about 218 words, above the 200-word ACLPUB guidance.

## Changes

- Shortened `paper/venues/acl27/sections/abstract.tex` to 184 plain-text words
  while preserving the same claim boundary and evidence numbers.
- Added `paper/venues/acl27/OPENREVIEW_METADATA_PACKET.md` with copy-ready
  title, abstract, ARR area recommendation, suggested keywords, and author-only
  fields.
- Updated `paper/venues/acl27/scripts/stage_submission_packet.py` so the local
  staging packet copies the metadata source as `openreview/METADATA.md`.
- Added staging test coverage for the metadata file.

## Findings

- Recommended primary ARR area: `Multimodality and Language Grounding to Vision,
  Robotics and Beyond`.
- Secondary fit: `Resources and Evaluation`.
- `LLM agents` should not be primary unless the final paper is rewritten around
  agent planning or environment interaction.
- The metadata packet still cannot fill author list/order, OpenReview profiles,
  reviewer-registration commitment, dual-submission/resubmission status,
  preprint status, final route, or optional media approval.

## Verification

Run after this pass:

```bash
python -m pytest -q tests/test_acl_submission_staging.py tests/test_paper_layout.py
make -C paper acl27
python paper/venues/acl27/scripts/stage_submission_packet.py --force
```
