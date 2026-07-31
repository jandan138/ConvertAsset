# 2026-07-31 AAN Scientific Workbench Rigid-Object Packages

## Scope

Prepare the currently needed rigid objects for Feishu-aligned Scenario Forge
layout prototypes without downstream asset-specific scale or physics patches.

Output root:

```text
outputs/scientific_workbench_task_assets_20260731/
```

## Source selection

The source archive is:

```text
/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/valid_with_json_by_final_category_usd.zip
SHA-256 89f7248e223588fe0a584bdb5033b3b30ff4e055227ec1f40fa03d2531d0f5ea
```

Selected members:

- beaker: `beaker/data_buy_BCI762450811977342-6.usd`;
- funnel: `funnel/data_buy_EEG3939408195047-3.usd`.

The user authorized these assets for public redistribution under
`LicenseRef-Team-Owned-Public-Redistribution` on 2026-07-31.

Two archive candidates labelled magnetic stirrer were not admitted. Visual
screening identified a laboratory scale and a stand-mounted heating apparatus,
not a credible magnetic stirrer work surface.

## Implementation

`aan.object_facade_profile.v1` now produces a direct identity entry prim while
keeping axis conversion, uniform scale, XY recentering, and support-plane
alignment below its visual child. The original source USD is not modified.
The `generic_usd` source-runtime label is accepted for profiled USD assets that
do not claim an Isaac- or Blender-specific producer runtime; normal dynamic
physics requirements remain unchanged.

`aan.object_interaction_profile.v2` allows each profile to declare the exact
required named frames. The funnel uses this contract so its through-opening is
not forced through the closed-vessel cooked-bottom probe. That probe is
`not_applicable` for this profile; this is not a flow or insertion-success claim.

The existing graduated-cylinder r3 and conical-bottle r1 visual lineages were
re-exposed through identity-entry canonical facades. Their prior producer-owned
physics semantics remain the basis; Scenario Forge adds no scale, collider,
mass, inertia, or warning-suppression patch.

A scoped-source reload was added after dependency-path rewriting. This prevents
USD's process-wide layer cache from producing a false missing-material result
when a just-written nested material layer is reopened during admission.

## Delivered packages

| Object | Package | Entry prim | Result |
|---|---|---|---|
| Beaker | `beaker/package` | `/World/Beaker` | pass |
| Funnel | `funnel/package` | `/World/Funnel` | pass |
| Graduated cylinder | `graduated_cylinder_identity/package` | `/World/graduated_cylinder_03` | pass |
| Conical flask | `conical_bottle_identity/package` | `/World/conical_bottle03` | pass |

Each manifest reports `overall_status: pass`, `blocked_reasons: []`, a dynamic
role, an identity entry prim, runtime smoke evidence, and an Isaac 4.1
interaction-runtime qualification report with `status: pass`.

Repository verification:

```text
python -m pytest -q
782 passed, 4 skipped

python -m ruff check <changed Python files>
All checks passed

git diff --check
pass
```

## Claim boundary

The evidence covers the package's declared collider and interaction runtime
gates. It does not establish robot policy success, collision-free bimanual
motion, physical liquid flow, benchmark success, or complete task success. The
funnel result does not establish liquid-flow fidelity or insertion success.
