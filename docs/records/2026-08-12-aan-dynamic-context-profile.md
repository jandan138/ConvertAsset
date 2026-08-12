# 2026-08-12 AAN Dynamic Context Profile

## Purpose

Scenario Forge needs physically present tabletop dressing that is loaded from a
ConvertAsset-owned package but does not participate in task semantics or
metrics. Reusing a full interaction profile works for already-qualified assets,
but forcing every decorative vessel or rack to declare grasp frames and task
readiness overstates the producer claim.

## Contract

`normalize-asset` now accepts `--context-profile` for `--asset-role dynamic`.
It is mutually exclusive with `--interaction-profile` and uses the same
package-owned rigid-root, collider, physics-profile, dependency-closure, and
runtime-gate machinery.

The input schema is `aan.dynamic_context_profile.v1`. The manifest projects a
passing `aan.dynamic_context_contract.v1` containing the identity entry prim,
rigid root, colliders, and support frame. The package also stores the immutable
input at `context/profile.json`.

The narrow contract intentionally does not publish task named frames, grasp
readiness, scoring participation, or benchmark success. A downstream consumer
may still use a stronger `aan.interaction_contract.v1` asset as context, but it
must not infer new task claims from that use.

## Example

```bash
./scripts/isaac_python.sh ./main.py normalize-asset source.usd \
  --out outputs/example_context \
  --asset-id example_context \
  --asset-class rigid \
  --asset-role dynamic \
  --asset-scope-prim /World/Example \
  --physics-profile profiles/physics/example.json \
  --context-profile profiles/context/example.json \
  --target-benchmark scenario-forge \
  --gates static,runtime
```

## Verification

The regression tests cover dynamic-only admission, mutual exclusion with the
interaction profile, package layout, manifest projection, and the absence of
task/grasp claims. Real runtime qualification remains asset-specific; this
contract addition does not retroactively qualify any source asset.
