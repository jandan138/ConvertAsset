# Build a Canonical Task-Object Facade

Use this workflow when a reviewed USD object has a non-canonical axis, scale,
support origin, or entry transform and a downstream task needs a direct identity
entry prim.

```bash
python main.py build-facade \
  --src <immutable-source.usd> \
  --out <facade-output-directory> \
  --object-profile <source-bound-facade-profile.json>
```

The profile schema is `aan.object_facade_profile.v1`. It binds:

- source SHA-256, source prim, up axis, and metres-per-unit;
- direct `/World/<Object>` entry prim and visual child name;
- reviewed axis rotation, uniform scale, and support-plane height;
- the geometry claim and its basis.

The output contains `facade.usda` and `facade_provenance.json`. The source is
referenced under `<entry>/Visual/Source`; the entry itself must remain identity.
Run the normal dynamic `normalize-asset` admission and Isaac 4.1 interaction
qualification after building the facade. A facade result alone is not a
physics-ready asset.

For non-vessel objects, use `aan.object_interaction_profile.v2` and list only the
authoritative semantic frames under `required_named_frames`. Do not use v2 to
omit a frame that the task or runtime probe actually requires.
