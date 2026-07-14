# 2026-07-14 AAN Vessel Entry-reference Material Closure

## Problem and investigation

Scenario Forge consumes a dynamic object by referencing the package's declared
`asset_entry_prim`, not by importing all siblings below `/World`. The first
integrated render showed that both vessel packages opened correctly as complete
stages, while the same entry-prim reference lost its material. USD reported that
the binding target was outside the reference scope and ignored it. The source
meshes were under each object prim, but their effective materials lived under the
sibling `/World/Looks` scope.

This was an upstream package-closure defect. Rebinding material in Scenario Forge
would have duplicated ConvertAsset logic and, for the cylinder, risked replacing
the qualified Isaac 4.1 OmniGlass root with the incompatible source root. The raw
LabUtopia USD remained unchanged throughout; its SHA-256 is
`b3861b5a17945abe401062a04125969c3a63b0f8a0a5ce0026a461dbdfc935f2`.

## Design

For interaction-profile packages only, scoped extraction now finds effective
materials bound to render prims inside `asset_entry_prim` and moves those material
subtrees below `<asset_entry_prim>/__aan_materials/`. A fresh
`Usd.NamespaceEditor` operation moves each material and retargets its bindings and
internal shader connections. The moved material stores its immutable source prim
path in `aan:sourceMaterialPrim`; material closure and visual-preservation checks
use that identity instead of treating the package-local path as a visual change.

The public `aan.interaction_contract.v1` shape is unchanged. Additive provenance is
published at `dependency_closure.scope_extraction`:

- `reference_scope_material_relocations` records source and package material paths;
- `entry_reference_qualification` records a nested arbitrary-path reference probe.

The build fails closed for a reserved target-scope collision, duplicate material
leaf, external shader-network connection, invalid material target, or loss of the
unique rigid root after reference. This logic is generic to entry-prim interaction
packages and has no vessel-name branches.

## Code and evidence changes

- `usd_closure.py` owns relocation, provenance, and the independent reference probe;
- `material_closure.py` maps relocated materials back to source dependency records;
- `role_normalization.py` canonicalizes relocated material identity for visual
  preservation;
- `interaction_authoring.py` verifies that the composed entry reference still has
  exactly one active rigid root;
- object-interaction tests cover all-purpose and preview bindings, GeomSubset
  bindings, nested references, reserved scope, external connections, and name
  collisions;
- real-source tests require a valid referenced material, retained unique rigid root,
  correct Isaac 4.1 OmniGlass bytes, and unchanged source SHA.

Both retained packages and their conventional/runtime-interaction evidence were
rebuilt. Conventional runtime and all four interaction probes pass for each asset.
The current runtime logs contain no `outside the scope of the reference`, ignored
material-binding, missing asset, MDLC, or USD_MDL failure signal. External and
embedded manifests are byte-identical.

## Verification

The final focused regression passed:

```text
./scripts/isaac_python.sh -m pytest -q \
  tests/test_asset_application_normalizer_object_interaction_profile.py \
  tests/test_asset_application_normalizer_labutopia_vessel_profiles.py

./scripts/isaac_python.sh -m pytest -q tests/test_asset_application_normalizer*.py
```

Ruff lint, `git diff --check`, manifest/report hash closure, and the exact source
hash were checked after the rebuild. Final package and report hashes are in
the updated [runtime qualification record](2026-07-14-aan-labutopia-vessel-runtime-qualification.md).

## Visual and claim boundary

An image-only review of the eight rebuilt asset views remains `WARN`: the conical
bottle is recognizable, while the cylinder has no clearly readable graduation
marks and both transparent assets have low-contrast soft edges. The source evidence
does not establish readable markings, so ConvertAsset does not invent them. This
is not a material-closure blocker, but it forbids a readable-scale or polished
product-render claim.

The repaired package interface proves reference-closed material composition and
retains the prior collider/support/root-motion evidence. It still does not prove a
real robot grasp, force closure, liquid transfer, a five-stage trajectory, or task
success.
