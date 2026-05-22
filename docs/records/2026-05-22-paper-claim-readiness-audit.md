# 2026-05-22 Paper Claim Readiness Audit

## Scope

This pass audited the current ACL/AAAI paper state after the 15-pair clean
GRScenes VLM pilot, the 14-pair zoom-stress pilot, the qualitative grounding
figure, the coordinate ablation, and the failure taxonomy were integrated.

The goal was not to claim that the paper is submission-ready. The goal was to
make the evidence ledger honest enough that future writing cannot accidentally
turn pilot diagnostics into final benchmark claims.

## Independent Review Summary

Two independent read-only reviewers reached the same main conclusion:

- The ACL version still reads partly like a simulation/tool paper. To become a
  stronger ACL submission, the main story should pivot toward VLM grounding
  protocol reliability under material/texture/rendering perturbations.
- The current VLM evidence is real-model evidence, but it is not final
  benchmark evidence. The clean pool has 15 PASS pairs, below the configured
  20-pair final gate, and `canonical_vlm_run_manifest.json` still records
  `claim_status=pilot_only` and `final_benchmark_claimable=false`.
- The stronger current ACL angle is: material conversion is a controlled
  perturbation that exposes model and coordinate-protocol sensitivity. The
  clean PASS pool is a control; the zoom-stress pool and coordinate ablation are
  the more interesting ACL-facing evidence.

## Changes Made

- Added claim-registry entries for:
  - `grscenes_vlm_clean_pool_pass15_pilot`
  - `grscenes_vlm_zoom_stress_pilot`
  - `grscenes_vlm_coordinate_ablation`
  - `grscenes_vlm_failure_taxonomy`
- Added review requirements that keep these records scoped as pilot,
  stress-test, coordinate-diagnostic, or illustrative-taxonomy evidence.
- Added GRUtopia/GRScenes and InternNav/DualVLN references to the paper
  bibliography, then cited them where GRScenes and downstream navigation are
  introduced.
- Added a 2026-05-22 addendum to the reference verification report for the new
  GRUtopia/GRScenes and InternNav/DualVLN BibTeX entries.
- Updated venue status files:
  - ACL 2027 remains candidate-only. Official ACL resolutions confirm the
    `ACL 2027` branding but do not confirm CFP, city/date, or Japan.
  - AAAI-27 now records the official date/location: Montréal, Québec, Canada,
    February 16-23, 2027.

## Source Checks

- ACL official source checked on 2026-05-22:
  https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions
- AAAI official source checked on 2026-05-22:
  https://aaai.org/conference/aaai/
- GRUtopia/GRScenes source:
  https://arxiv.org/abs/2407.10943
- InternNav/DualVLN source:
  https://github.com/InternRobotics/InternNav and
  https://arxiv.org/abs/2512.08186

## Current Plain-Language Status

The paper is no longer blocked by "we have no real VLM evidence." It now has
small but real Gemma4 and Qwen2.5-VL evidence.

The paper is still blocked by "the evidence is not yet strong enough for final
claims." The clean set is too small for a final benchmark claim, and Qwen shows
that coordinate interpretation itself is a major variable. This is why the next
scientific move should be to make the ACL story about stress testing and
protocol reliability, then expand that stress-test evidence in a controlled
way.

## Next Work

1. Rewrite the ACL-facing title/abstract/intro around conversion-induced
   perturbations in VLM grounding evaluation.
2. Decide the final VLM gate for the stress framing: fixed material-shift bins,
   target categories, coordinate protocol, and sample count.
3. Produce canonical root `predictions.jsonl` and `score_summary.json` only
   after the manifest is final-claimable.
4. Keep InternNav/VL-LN as a downstream extension, not as a claim inferred from
   image-level VLM probes.
