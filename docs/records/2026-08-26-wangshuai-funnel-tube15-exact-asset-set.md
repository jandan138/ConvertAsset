# Wangshuai funnel/tube exact-source asset set

## Investigation

The intake
`scenario-forge/external_artifacts/incoming/from_wangshuai/lixinguan_funnel_liquid.usd`
is one monolithic Isaac scene containing a 15 mL threaded tube body, a separate
threaded closed cap, the small-v2 funnel, one 1,948-particle liquid seed,
ground/light/render fixtures, and two PhysicsScene prims.

The tube mesh is byte/topology-identical to the previously delivered threaded
`shiguan.usd`. The new cap is not byte-identical to the old open sleeve: it
retains the internal thread profile and adds a closed top. The internal-thread
radial histogram correlates `0.9993` with the earlier threaded cap after frame
alignment.

The funnel mesh exactly matches the earlier admitted small-v2 package, but the
new scene also authors a kinematic rigid-body root. Reusing the older
collision-only wrapper would therefore drop source physics semantics.

The source glass shader pointed at a Windows absolute OmniGlass path and the
PP materials used a runtime-relative OmniPBR module. The source tube also has a
dangling physics-material relationship to `/World/PhysicsMaterial`; that prim
does not exist and has no effective material parameters.

## Implementation

`scripts/extract_wangshuai_funnel_tube15_asset_set.py` performs exact subtree
extraction into four identity-root packages:

- `tube15_threaded_liquid_ready`;
- `tube15_threaded_closed_cap`;
- `funnel_small_v2_liquid_ready`;
- `small_v2_liquid_seed_1948`.

Mesh arrays, rigid-body/kinematic state, collision APIs, SDF/convexHull values,
all authored PhysX attributes, and particle arrays/parameters are unchanged.
Only scene placement is removed from each entry root and retained in the
recomposition profile. Cross-subtree material relationships are moved inside
the package, and unchanged Isaac 4.1 OmniGlass/OmniPBR modules are copied to
package-relative paths. No collider, mass, offset, velocity, bottom plug, or
warning-suppression rule is added.

The liquid overlay contains the source sampler, ParticleSystem and ParticleSet
with rewritten internal relationship paths. It intentionally contains no
PhysicsScene; the consumer owns one GPU scene.

Output:

`outputs/wangshuai_funnel_tube15_exact_asset_set_20260826/`

## Runtime qualification

`scripts/qualify_wangshuai_funnel_tube15_asset_set.py` compares one direct
source baseline with three independent package recompositions in the pinned
Isaac Sim 4.1 runtime. The source physical parameters are deliberately not
tuned.

At eight seconds, both source and package recomposition captured
`1653/1948 = 84.856%`; the source recipe has `maxVelocity=0.1 m/s` and flows
slowly. At the source-grounded 16-second acceptance point:

- source baseline: `1948/1948`, capture ratio `1.0`, below-floor `0`;
- three recompositions: each `1948/1948`, capture ratio `1.0`, below-floor `0`;
- non-finite positions: `0`;
- hard CUDA/PhysX/cooking errors: `0`.

`scripts/promote_wangshuai_funnel_tube15_asset_set.py` hash-binds the immutable
build manifest and these four reports before marking every package and the set
`pass`.

## Claim boundary

The delivery proves exact-source independent assets and robot-free
funnel-to-tube liquid recomposition. It does not prove cap tightening, robot
grasping, task completion, policy success, or benchmark success. The dangling
source physics-material target remains semantically ineffective; no replacement
friction values were invented.
