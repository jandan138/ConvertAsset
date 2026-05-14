# 2026-05-14 Workshop Review Ingestion For AAAI 2027

## Source

The official workshop reviewer feedback was provided in:

```text
docs/tmp/reviewer_opnion.md
```

It has been copied into the paper evidence tree:

```text
paper/shared/evidence/reviews/2026-05-workshop-official-reviews-raw.md
```

## Structured Output

The parsed revision roadmap is:

```text
paper/shared/evidence/reviews/2026-05-workshop-to-aaai27-revision-roadmap.md
```

## Main Finding

The workshop acceptance validates that the problem is practical and useful, but
the reviews do not support a simple venue-format conversion into AAAI 2027.
The AAAI version needs a larger empirical study, downstream task validation,
material-effect analysis, and baseline comparisons with official NVIDIA tools.

## Highest-Priority Revision Themes

1. Expand beyond four chest-of-drawers assets.
2. Add real downstream task validation or remove "AI Task Performance" claims.
3. Compare against NVIDIA MDL Distill/Bake or Asset Converter where possible.
4. Analyze which MDL effects cause conversion degradation.
5. Reframe guidelines as evidence-bounded and validate them at larger scale.
6. Expand GRScenes startup/performance evidence beyond one scene and three runs.

## Documentation Changes

- Added a raw official review archive under `paper/shared/evidence/reviews/`.
- Added a structured workshop-to-AAAI revision roadmap.
- Added `paper/shared/evidence/reviews/README.md`.
- Updated `paper/shared/evidence/results_manifest.yaml` with review evidence.
- Updated `paper/venues/aaai27/STATUS.md` with review-driven requirements.
