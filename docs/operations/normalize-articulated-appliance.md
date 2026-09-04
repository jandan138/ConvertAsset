# Normalize an Articulated Appliance

Run with an Isaac/USD Python environment:

```bash
./scripts/isaac_python.sh ./main.py normalize-articulated source.usd \
  --out outputs/device_identity_candidate \
  --profile profiles/articulated/device_identity.v1.json
```

The command writes `package/asset.usd`, an unchanged package-local source copy,
and `package/evidence/manifest.json`. Its initial status is always
`candidate_runtime_qualification_pending`.

For IKA OVEN 125, the reproducible source-archive adapter and runtime qualifier
are:

```bash
python scripts/build_ika_oven_125_identity_root.py
python scripts/qualify_ika_oven_125_relocatable.py
```

The qualifier exercises canonical, ordinary object, and VR `_scene` namespace
mounts in Isaac Sim 4.1. `--reuse-existing` re-evaluates already recorded
runtime reports without rerunning PhysX; it does not manufacture missing
evidence.

Consumers must read `promotion_receipt.json`. They may reference the declared
asset entry and author transforms on their own `obj_*` root only after the
receipt is promoted. They must not copy joint anchors, bake a table height into
descendants, or rewrite the controller again.

## New VR/eBench fixed-base acceptance

`normalize-articulated` v1 alone produces a relocation candidate. Before a new
VR or eBench task consumes it, an asset-specific producer build must call the
shared Instance/fixed-base authoring helpers and emit a promoted receipt whose
audit proves:

```text
obj_device                         enabled Articulation Root
└── Instance                       identity Xform
    ├── Body                       non-kinematic rigid base
    ├── <all other rigid links>    non-kinematic
    └── Joints/BaseFixed           obj_device -> Instance/Body
```

Use the OVEN 125 r16 builder and qualifier as the maintained example. Runtime
qualification must initialize the public object root as an articulation and
exercise the task-scoped controls under canonical, prefixed, and VR mount paths.

Consumers must not add an articulation root, must not toggle kinematic state,
and must not add or replace `BaseFixed`. A failure in any of those properties is
a producer-side requalification request, not a downstream scene patch.
