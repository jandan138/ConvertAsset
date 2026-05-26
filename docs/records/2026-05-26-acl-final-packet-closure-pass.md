# ACL Final Packet Closure Pass

Date: 2026-05-26.

## Purpose

Continue the ACL/ARR-ready goal after the citation/provenance pass by turning
the remaining Responsible NLP C1/C2/C4 and upload-boundary risks into concrete
submission packet documents.

## Changes

- Added `paper/venues/acl27/COMPUTE_RUNTIME_SUMMARY_DRAFT.md`.
- Added `paper/venues/acl27/FINAL_SUBMISSION_PACKET_CHECKLIST.md`.
- Updated ACL readiness/provenance/checklist docs to point at these files.
- Downgraded the old `grscene_startup` entry in `paper/shared/evidence/claims.yaml`
  from an active speedup-style claim to a legacy diagnostic with explicit ACL
  non-use boundaries.
- Refreshed ACL status docs so the next large goal is submission-packet
  packaging and anonymization, not more core experiment collection.

## Evidence Checked

- Current GPU probe: NVIDIA GeForce RTX 4090, 46068 MiB memory, driver
  570.153.02.
- Isaac Sim version files under `/isaac-sim`: `4.5.0-rc.36` package build with
  commit `f59b30053cf43dfdddc273a3f850424942a33e0c`.
- Isaac wrapper Python: Python 3.10.15, `usd-core` 26.5, NumPy 2.2.6.
- Gemma4 VLM interpreter: Python 3.10.15, Torch 2.10.0, Transformers
  5.8.0.dev0, Unsloth 2026.4.8, Accelerate 1.13.0, BitsAndBytes 0.49.2,
  Pillow 11.3.0.
- Qwen2.5-VL interpreter: Python 3.13.11, Torch 2.10.0, Transformers 5.2.0,
  Accelerate 1.12.0, Pillow 12.1.1, `qwen-vl-utils` 0.0.14.
- InternNav local checkout: commit `7a5c624`.
- Official-scene closure package: 18/18 required original/noMDL fresh-process
  runs succeeded, with overlapping ready-time intervals.

## Remaining Gates

- Annual ACL 2027 public CFP/author kit remains unavailable in checked public
  sources.
- Gemma4 local quantized checkpoint still needs exact public page/commit/hash
  matching.
- InteriorAgent/KuJiaLe full terms and preferred citation still need final
  author/legal review.
- A concrete upload directory/archive has not yet been assembled or scanned for
  anonymization leaks.
