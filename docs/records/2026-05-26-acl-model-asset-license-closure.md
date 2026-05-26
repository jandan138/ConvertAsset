# ACL Model And Asset License Closure

Date: 2026-05-26

## Scope

This pass closed the ACL/ARR submission-facing provenance questions for the VLM
models and scene assets. It did not add new experiments; it converted previously
open review-packet risks into explicit public IDs, terms, and upload boundaries.

## Findings

- Gemma4 primary VLM is now tied to public model ID
  `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` and revision
  `9746c23553347b443ebdc1caba1d41b52223d0c8`. The checked metadata reports
  Apache-2.0 and base `google/gemma-4-E4B-it`.
- Qwen2.5-VL diagnostic VLM is now tied to public model ID
  `Qwen/Qwen2.5-VL-7B-Instruct`; the checked public `main` revision is
  `cc594898137f460bfe9f0759e9844b3ce807cfb5`, with Apache-2.0 metadata.
- GRScenes public metadata resolves to `InternRobotics/GRScenes` at revision
  `4760b9031881c985e3582075cb2d8dbde1530a68` and reports CC BY-NC-SA 4.0.
- InteriorAgent / KuJiaLe public metadata resolves to
  `spatialverse/InteriorAgent` at revision
  `ac599fe2d2285ed0ddfafb70ba56e489462e0650`. Its terms are no longer an
  unknown: safe default is no raw scene redistribution and no optional selected
  scene-derived media in the ACL packet.

## Changes

- Added `paper/venues/acl27/MODEL_AND_ASSET_LICENSE_AUDIT.md`.
- Updated `ARTIFACT_PROVENANCE_DRAFT.md`,
  `COMPUTE_RUNTIME_SUMMARY_DRAFT.md`,
  `RESPONSIBLE_NLP_CHECKLIST_DRAFT.md`,
  `OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md`,
  `FINAL_SUBMISSION_PACKET_CHECKLIST.md`,
  `SUBMISSION_READINESS_AUDIT.md`, and `SUBMISSION_STAGING_AUDIT.md`.
- Updated the staging script so its generated manifest no longer lists Gemma
  public-ID discovery or InteriorAgent terms discovery as open gates.

## Claim Boundary

The ACL paper can now say the model and asset provenance for the candidate
packet has been checked to public IDs/terms. It still cannot upload raw scenes,
local model checkpoints, scratch USD trees, raw InternNav logs, or optional
selected scene-derived videos by default.

The remaining large gates are final Annual ACL/ARR target-call verification,
final OpenReview form copy, author confirmation of runtime details, and final
author/legal approval if optional media is ever added.
