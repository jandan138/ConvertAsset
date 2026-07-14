# 2026-07-14 AAN Object Interaction Profile

## Purpose

Scenario consumers need one stable state prim for a manipulable object.  The
LabUtopia vessel sources instead place `RigidBodyAPI` and `MassAPI` on a child
mesh, while task semantics refer to the enclosing object Xform.  A consumer-side
patch would make runtime identity asset-name-specific and would split ownership
between ConvertAsset, Scenario Forge, and GenManip.

This change adds a source-bound, package-owned interaction contract.  It does
not change raw LabUtopia USD and does not change the semantics of
`aan.physics_profile.v1`.

## Investigation

The existing AAN dynamic path was inspected through:

- `usd_closure.py`: owns `asset.usd`, scoped source extraction, and sublayer order;
- `role_normalization.py`: verifies dynamic visual preservation before physics;
- `physics_profile.py` and `physics_authoring.py`: resolve and author a complete
  mass bundle for every composed active rigid body;
- `physics_checks.py`: admits composed collision and mass semantics;
- `evidence_manifest.py`: publishes the downstream machine-readable evidence.

The key integration constraint is ordering.  Physics profile resolution uses
the currently composed active rigid bodies.  Therefore rigid topology must be
normalized before the unchanged mass profile is resolved.

## Design decisions

### Separate versioned profile

`aan.object_interaction_profile.v1` owns:

- source SHA-256 and stage-metric binding;
- one `asset_entry_prim`, equal to the package's first declared asset scope;
- dynamic/kinematic root intent and mandatory descendant RigidBody/Mass removal;
- exact coverage of source collision prims plus optional authored colliders;
- optional Mesh collision approximation override, including `sdf`;
- exact authoritative named frames `opening`, `grasp`, and `support`;
- open-top declaration and runtime gate requirements.

It contains no mass, inertia, COM, or principal-axis values.  Those remain in
`aan.physics_profile.v1`.

### Package composition and authoring

The package entry layer composes, strongest first:

1. `overlays/physics_profile.usda`;
2. `overlays/interaction.usda`;
3. `deps/usd/scoped_source.usda`.

The pipeline authors the interaction layer first.  It applies RigidBodyAPI to
`asset_entry_prim`, deletes descendant RigidBodyAPI/MassAPI opinions in the
strong layer, explicitly disables descendant rigid-body attributes, preserves
or authors declared colliders, and authors body-local frame Xforms.  It then
reopens the composed stage and requires exactly one active rigid body at the
entry prim before physics profile resolution begins.

### Claim boundary

`interaction_contract.status == pass` is a static contract result.  It proves
schema/readback and package closure only.  It does not prove:

- that an `sdf` or other collider leaves the vessel aperture physically open;
- that the runtime state UID moves the qualified rigid root;
- that support is stable;
- that the gripper creates the required contacts.

Accordingly, open-top remains `declared`, and root-motion, stable-support, and
gripper-collision gates remain `not_run` until runtime evidence is merged.

### Closure integrity

The manifest publishes both:

- `contract_payload_sha256`: SHA-256 of canonical JSON containing schema,
  entry prim, runtime identity, disabled bodies, colliders, open-top declaration,
  and named frames;
- `runtime_tree_sha256`: SHA-256 of the canonical, path-sorted artifact list.

The runtime artifact list includes `asset.usd`, `deps/**`, `overlays/**`,
`interaction/**`, and `physics/**`.  Each item has a bare lowercase SHA-256.
`evidence/**` is excluded to avoid a self-referential manifest digest.

## Code changes

- `object_interaction_profile.py`: versioned parsing, source binding, exact
  collider coverage, frame/open-top/runtime-gate validation;
- `interaction_authoring.py`: package overlay authoring, readback, machine
  contract, canonical payload and runtime-tree closure hashes;
- `model.py`, `cli.py`, `package_layout.py`: request/CLI/package paths;
- `usd_closure.py`: interaction layer creation and composition order;
- `pipeline.py`: interaction-before-physics orchestration and fail-closed stage;
- `evidence_manifest.py`: manifest contract and command provenance;
- `test_asset_application_normalizer_object_interaction_profile.py`: TDD fixtures
  and static package/readback coverage.

## Testing

The tests were written first and initially failed because
`NormalizeAssetRequest` did not accept `interaction_profile`.  After the minimal
implementation, the following passed:

```text
./scripts/isaac_python.sh -m pytest -q \
  tests/test_asset_application_normalizer_object_interaction_profile.py \
  tests/test_asset_application_normalizer_dynamic_physics_profile.py
# 14 passed

./scripts/isaac_python.sh -m pytest -q tests/test_asset_application_normalizer*.py
# 82 passed, 1 skipped
```

Coverage includes unique root composition, descendant schema removal, preserve
and author collider modes, `sdf` approximation readback, exact named frames,
interaction-before-mass ordering, immutable profile copy, source binding,
collider exact coverage, CLI projection, per-file hashes, and runtime-tree hash
recomputation.

## Open issues and next evidence

The generic contract implementation is followed by the real-source
[LabUtopia vessel static package record](2026-07-14-aan-labutopia-vessel-static-packages.md).
That follow-up creates source-bound profiles and static packages for both
vessels. Isaac dynamic probes still must run, in order:

1. composed-stage unique-root and collider readback;
2. reset and at-least-5-cm root-motion/UID parity probe;
3. open-top aperture probe for the selected collision approximation;
4. stable-support and gripper-contact probes;
5. final manifest refresh with runtime gate evidence.

If `sdf` is unsupported or unstable in the target Isaac 4.1 runtime, publish a
new profile revision with another package-owned collision approximation or
proxy.  Do not repair it in Scenario Forge or GenManip.
