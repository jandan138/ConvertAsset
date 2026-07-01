# 2026-06-30 EBench-01 AAN Consumer Handoff

## Context

AAN-07 produces a benchmark handoff package for DryingBox-style USD assets.
The next consumer is EOS BPL / EBench adapter, not another ConvertAsset repair
stage.

## Decision

EBench-01 will consume the AAN package as-is:

```text
asset.usd
task/task_config.yaml
task/required_prims.yaml
task/evaluator.yaml
manifest.json or evidence/manifest.json
```

ConvertAsset remains the owner of dependency closure, remote URI handling,
MDL/texture mirror, PreviewSurface fallback, physics/articulation checks,
runtime smoke, and AAN manifest evidence. EOS BPL / EBench adapter owns package
ingestion, task-contract evidence, claim boundary, and later runtime/score
integration.

## Consumer Contract

The consumer may rely on AAN-07 only when:

```text
AAN-07-benchmark-contract is present and pass
benchmark_contract.status=pass
task/task_config.yaml exists
task/required_prims.yaml exists
task/evaluator.yaml exists
required prim mappings match packaged asset.usd
blocked_reasons is empty for required closure
claims_forbidden is propagated
```

Current AAN evidence may use `overall_status=pass`; consumers must still check
the explicit AAN-07 benchmark gate before declaring task handoff readiness.

## Forbidden Downstream Behavior

EBench-01 must not:

```text
patch DryingBox USD paths
patch MDL or texture paths
patch articulation or joint paths
invent required prims
invent evaluator entrypoints
infer success predicates
hide AAN waivers
treat AAN runtime smoke as EBench score eligibility
```

## Claim Boundary

AAN-07 plus EBench-01 may claim only:

```text
EOS/EBench can read the normalized AAN package and task handoff contract.
```

It does not claim:

```text
official EBench reproduction
leaderboard comparability
real EBench episode execution
task success
standard_model_score
full material parity
full physics parity
backend parity
```

## Related EOS Documents

```text
/cpfs/user/zhuzihou/dev/embodied-eval-os/docs/operations/ebench01-aan-package-consumer-acceptance.md
/cpfs/user/zhuzihou/dev/embodied-eval-os/docs/records/2026-06-30-ebench01-aan-package-consumer-planning.md
```
