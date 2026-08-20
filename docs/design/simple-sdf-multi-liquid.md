# Simple-SDF multi-liquid producer

This producer implements a narrow, source-bound route for containers whose
liquid behavior can be stabilized by using one reviewed visual mesh as an SDF
collider. It is intentionally separate from the more general fluid-interaction
asset producer.

## Collision contract

`aan.simple_sdf_collision_spec.v1` identifies an exact container prim and
visual `Mesh`. The producer copies the scene dependency closure, disables prior
colliders within the named scope, and authors SDF collision on that exact mesh.
The source USD is not modified.

An invisible convex Cube bottom plug is allowed only with explicit YAML fields
for size and parent-local translation plus `approved: true`. The proposal
command may suggest a Cube for pointed tubes, but the build command rejects an
unapproved suggestion.

## Particle contract

`aan.multi_liquid_sample_request.v1` uses closed sampler meshes as producer-time
volumes. A deterministic interior lattice is baked into USD `Points`; it is not
runtime PhysX sampling and the sampler mesh need not ship in the final scene.

Every sampler produces exactly one independent ParticleSet with a unique
`particleGroup`. All sets bind to the one canonical
`/__ScenarioForgeFluid/ParticleSystem`. A small-container request selects the
small recipe for the whole shared system, avoiding incompatible particle
scales in one PhysX system.

`aan.multi_liquid_sample_request.v2` adds reviewed automatic cylindrical
samplers. The producer analyzes an upright axial hollow mesh, recovers its
inner opening and cavity floor, and supports two modes:

- `inside_fill` suspends a short column inside the upper cavity so it can
  settle without starting on the SDF floor or wall;
- `mouth_drop` authors a narrower column above the detected opening and
  calibrates its discrete lattice count from the requested liquid volume.

`fill_ratio` is constrained to 0.10 through 0.80. The generated sampler USD is
evidence under `/__ScenarioForgeAutoSamplers`; only baked ParticleSets compose
into the runtime scene. Every container still receives its own ParticleSet and
all sets still share one ParticleSystem. Version 1 explicit meshes remain
supported unchanged.

## Package preservation

When liquid is added to a passed `aan.simple_sdf_collision_result.v1` package,
the producer copies the whole package and composes its entrypoint. Re-running a
generic dependency closure is forbidden here because it can discard the
strong collision overlay or an approved bottom plug. The new strongest entry
layer also authors the source `metersPerUnit` and `upAxis`.

## Validation

Quick mode runs one cold Isaac Sim 4.1 process for three seconds. Qualified mode
runs three cold processes for eight seconds each. Acceptance is per set: at
least 99% retention, zero particles below the initial set floor, and no hard
runtime errors. Version 2 additionally checks settled liquid height against
the requested ratio with a ±0.05 tolerance. Runtime validation freezes the named containers only in an
ephemeral evidence fixture; it does not alter the delivered source-bound
package.

The strongest possible claims are `provisional_gpu_pbd_loaded_start` and
`qualified_gpu_pbd_loaded_start`. Neither covers robot policy, pouring, metrics,
or benchmark success.
