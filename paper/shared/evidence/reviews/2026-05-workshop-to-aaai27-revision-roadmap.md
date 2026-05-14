# Workshop Reviews to AAAI 2027 Revision Roadmap

Date: 2026-05-14

Source: official workshop feedback copied from
`docs/tmp/reviewer_opnion.md` into
`paper/shared/evidence/reviews/2026-05-workshop-official-reviews-raw.md`.

## Decision Context

The workshop version was accepted, but the official reviews are split. One
reviewer recommended marginal acceptance, while two reviewers recommended
rejection. The acceptance should be treated as validation that the topic is
useful for the workshop audience, not as evidence that the paper is ready for
AAAI 2027.

| Reviewer | Rating | Confidence | Core Position |
|---|---:|---:|---|
| o7vM | 6 | 3 | Clear and useful; claims need more caution because scope is limited. |
| CiLc | 4 | 4 | Useful technical utility, but empirical scale and downstream validation are insufficient. |
| cb7X | 4 | 3 | Meaningful problem, but evaluation depth and practical contribution are too shallow. |

## What Reviewers Liked

- The paper targets a real Isaac Sim interoperability problem.
- The MDL-to-UsdPreviewSurface pipeline is clearly described.
- Composition-preserving USD traversal is viewed as technically appropriate for
  professional digital-twin workflows.
- The multi-level diagnostic setup is appreciated: pixel metrics, performance,
  CLIP/DINOv2 feature alignment, and large-scene startup timing.
- Reviewers see practical value in understanding the within-simulation material
  gap.

## Cross-Reviewer Failure Themes

### P1 Must Fix For AAAI

| ID | Theme | Reviewer Evidence | Required AAAI Action |
|---|---|---|---|
| P1-1 | Empirical scope is too small | All reviewers mention four same-category furniture assets and 24 matched pairs. | Expand to multiple object categories and material types, including transparent/translucent, highly specular, organic/fabric, metal/glass, and procedural or layered materials. |
| P1-2 | Downstream task claims are unsupported | CiLc rejects the "AI Task Performance" framing because only feature proxies were used. | Add real downstream task validation, or remove/rename all task-performance claims. Preferred: train/test or evaluate detectors/segmenters across MDL and converted renders. |
| P1-3 | Missing comparison to existing NVIDIA tools | CiLc explicitly asks for comparison with MDL Distill and Bake / Asset Converter. | Add a baseline comparison against NVIDIA conversion paths, or clearly define why this toolkit targets a different production constraint. |
| P1-4 | No material-effect analysis | cb7X asks for finer-grained degradation analysis by MDL effect. | Add per-effect or per-material-family analysis for clearcoat, anisotropy, procedural textures, transparency, emission, opacity, displacement, and layered materials. |
| P1-5 | General guidelines are overclaimed | o7vM and CiLc both question generality. | Reframe guidelines as evidence-bounded rules, or validate them on a larger held-out set. |
| P1-6 | Large-scene benchmark is too narrow | o7vM notes one GRScenes interior and three runs per version. | Run multiple scenes and more repeated trials; report variance and confidence intervals. |

### P2 Strongly Recommended

| ID | Theme | Reviewer Evidence | Suggested Action |
|---|---|---|---|
| P2-1 | Practical contribution needs automation | cb7X suggests an automatic detector/recommender for safe conversion. | Add a material-risk classifier or rule-based recommender that predicts whether conversion is safe from MDL features and asset metadata. |
| P2-2 | Originality is only moderate | CiLc says the implementation overlaps with existing industrial tooling. | Position novelty around risk assessment, benchmark protocol, production-preserving traversal, and validated decision support rather than channel mapping alone. |
| P2-3 | Feature similarity is only a proxy | CiLc calls CLIP/DINOv2 useful but insufficient. | Keep CLIP/DINOv2 as diagnostics, but connect them to downstream task results or present them explicitly as proxy-only. |
| P2-4 | Statistical support is weak | Scope and run-count concerns appear across reviews. | Add paired tests, bootstrap confidence intervals, and per-category aggregation. |
| P2-5 | Title/abstract overpromise | "AI Task Performance" is criticized when no actual task is tested. | Change the AAAI title/abstract unless real downstream tasks are added. |

### P3 Writing And Framing

| ID | Theme | Suggested Action |
|---|---|---|
| P3-1 | Use more cautious language | Replace broad "safe conversion" claims with scope-limited claims tied to asset/material classes. |
| P3-2 | Preserve the strongest conceptual hook | Keep "within-simulation rendering gap" as the paper's core framing. |
| P3-3 | Separate workshop contribution from AAAI contribution | The workshop paper is a useful case study; the AAAI paper needs scale, baselines, and task validation. |

## Recommended AAAI 2027 Pivot

The AAAI version should not be a lightly edited workshop paper. It should become
a broader study of **material simplification risk assessment for simulation data
pipelines**.

Recommended framing:

1. **Problem**: simulation assets often need material simplification for
   interoperability and throughput, but the impact on visual quality, feature
   representations, and downstream perception tasks is poorly understood.
2. **Method**: a composition-preserving conversion pipeline plus a target-aware
   capture and evaluation protocol.
3. **Benchmark**: multiple asset categories, material families, and full scenes.
4. **Baselines**: original MDL, ConvertAsset conversion, and official NVIDIA
   conversion/distillation paths when available.
5. **Decision support**: a material-risk score or recommender that flags assets
   needing MDL preservation or manual review.
6. **Tasks**: at least one real downstream task beyond feature-space proxies.

## Concrete Revision Order

1. **Scope expansion first**: build a larger asset/material matrix and select
   representative GRScenes layouts.
2. **Capture pipeline**: use the target-level capture workflow to collect
   object-level render evidence instead of only four single-object assets.
3. **Baseline comparison**: define NVIDIA baseline commands and compare outputs,
   runtime, and structural preservation.
4. **Downstream task**: choose one measurable task and define train/test splits.
5. **Material-effect analysis**: annotate or infer MDL features and report which
   effects drive degradation.
6. **Paper rewrite**: update title, abstract, introduction, method, experiments,
   and limitations after the evidence is in place.

## Response Strategy If Writing A Revision Letter

- Acknowledge that the workshop study was intentionally narrow.
- Emphasize that the AAAI version expands beyond case-study evidence.
- Explicitly state which reviewer concerns are addressed by new experiments:
  scale, material diversity, downstream tasks, baselines, and automation.
- Avoid defending proxy-only "AI task performance" claims unless supported by
  new task evidence.
