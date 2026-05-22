# 2026-05-22 ACL27 VLM Story Overrides

## Scope

The ACL 2027 wrapper now has local narrative overrides for the parts of the
paper that define the submission story:

- `paper/venues/acl27/sections/abstract.tex`
- `paper/venues/acl27/sections/intro.tex`
- `paper/venues/acl27/sections/conclusion.tex`

The shared method, experiments, discussion, tables, figures, claims, and
evidence registries remain shared. AAAI and CVPR wrappers are not redirected to
these ACL-specific sections.

## Design Decision

The reviewer-style audits agreed that the current ACL path should not be sold
as a generic asset-conversion paper. The ACL-facing story is now:

> MDL-to-UsdPreviewSurface conversion is a controlled material/rendering
> perturbation, and VLM grounding evaluations need stricter evidence gates than
> pixel or feature similarity before claiming downstream robustness.

This avoids duplicating or rewriting the experimental core while giving ACL a
clearer first-page signal.

## Claim Boundary

The local ACL abstract, introduction, and conclusion keep the GRScenes evidence
at pilot/diagnostic scope:

- 15-pair clean visual-QA pool: preservation control, below final benchmark
  gate.
- 14-pair zoom material-shift pool: stress diagnostic, not clean preservation.
- Coordinate ablation: protocol sensitivity diagnostic.
- Failure taxonomy: qualitative selected cases, not a final distribution.

## Remaining Work

This is a narrative alignment pass, not a completed ACL paper. The next
scientific work is still to define and run a final-claimable stress benchmark
or expand the clean preservation pool, then produce canonical root
`predictions.jsonl` and `score_summary.json` files after the claim gate is
closed.
