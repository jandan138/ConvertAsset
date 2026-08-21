# Produce a qualified GPU-PBD liquid start

Use this operation through Scenario Forge for normal delivery. The low-level commands remain
available for producer diagnostics.

## Inspect

```bash
./scripts/isaac_python.sh ./main.py liquid-inspect scene.usd \
  --out inspection.json
```

The report suggests prim paths; it does not choose one for the caller. Pass the exact intended
container path to the request.

## Produce

Create an `aan.gpu_pbd_autofill_request.v1` JSON and run:

```bash
./scripts/isaac_python.sh ./main.py liquid-autofill \
  --request request.json \
  --out producer_package \
  --isaac-python "$EEOS_ISAACSIM41_PYTHON"
```

`--isaac-python` is the authority for the three runtime observations. ConvertAsset removes any
temporary wrapper paths before launching it so a 4.5 static-USD process cannot contaminate 4.1
evidence. Set `EEOS_ISAACSIM41_PYTHON` to the managed EOS environment; do not create an ad-hoc
environment.

On pass, consume `manifest.json`, `producer_overlay.usda`, `analysis.json`, `recipe.json`, and
`evidence/runtime_qualification/report.json` together. On block, retain the directory only as
diagnostics.

For a standalone dynamic vessel, the request may include:

```json
{
  "validation_fixture": {
    "container_motion": "kinematic",
    "scope": "evidence_only"
  },
  "collision_profile": "task02_visual_mesh_convex_decomposition_v1",
  "initial_particle_count": 731
}
```

This profile preserves the source SDF, adds the invisible Task-02-derived PBD
proxy, and uses the measured inner-radius curve for particle layers and
containment. `initial_particle_count` must be 1–10,000 and is accepted only with
this profile. Temporary fixed-container USD layers must never enter the final
closure or ZIP.

The observer is a process-isolated worker. It writes and `fsync`s its observation
before a controlled process exit, so use the JSON `overall_status` and the parent
command exit code—not Kit plugin-unload output—as the qualification result.

## Package a source closure

Scenario Forge calls the existing dependency-closure implementation through:

```bash
./scripts/isaac_python.sh ./main.py package-usd-closure scene.usd \
  --scope /World --out source_closure
```

This is packaging, not asset conversion or role normalization.
