# Simple-SDF and multi-liquid CLI

All commands run through Isaac Sim Python:

```bash
./scripts/isaac_python.sh ./main.py simple-sdf-propose SOURCE_USD \
  --container /World/obj_tube15 \
  --visual-mesh /World/obj_tube15/Visual/Mesh \
  --particle-scale small_required \
  --out /abs/path/review
```

Review `review/proposal.yaml`. If a bottom Cube is suggested, verify its local
pose and size before setting `approved: true`.

```bash
./scripts/isaac_python.sh ./main.py simple-sdf-build \
  --spec /abs/path/review/proposal.yaml \
  --out /abs/path/collision_package
```

The liquid request lists one set per sampler mesh. Multiple sets share one
ParticleSystem but retain independent identities, groups, counts, and evidence.

To infer a sampler from a reviewed upright hollow container, use request v2:

```yaml
schema_version: aan.multi_liquid_sample_request.v2
scene: /abs/path/collision_package/asset.usda
validation: quick
sets:
  - id: bottle_liquid
    container_prim: /World/obj_reagent_bottle
    sampler:
      mode: mouth_drop
      fill_ratio: 0.40
      visual_mesh_prim: /World/obj_reagent_bottle/Visual/HollowMesh
    particle_scale: task02_compatible
  - id: tube_liquid
    container_prim: /World/obj_tube15
    sampler:
      mode: inside_fill
      fill_ratio: 0.40
    particle_scale: small_required
```

Use `mouth_drop` when the opening admits the selected effective particle
radius. Use `inside_fill` for narrow vessels such as the qualified 15 mL tube.
The producer rejects ambiguous hollow geometry, tilted containers, unsupported
openings, or particle budgets above the recipe limit. It never changes the
particle recipe merely to force a pass.

```bash
./scripts/isaac_python.sh ./main.py multi-liquid-sample \
  --request /abs/path/liquid.yaml \
  --out /abs/path/liquid_package \
  --isaac-python /path/to/eos-managed-isaac41/python
```

Use `validation: quick` for a one-run provisional check and
`validation: qualified` for the three-run qualification. Read `manifest.json`
and `evidence/runtime_validation/report.json`; never infer robot or benchmark
success from either result.

For an editable liquid package use request v3 with
`delivery_mode: dual_editable_frozen` and `editable_axis: height_z` on every
automatic sampler. Open `scene_liquid_edit.usda`, change only the sampler
root's Z scale, run and save, then publish a new immutable candidate with:

```bash
./scripts/isaac_python.sh ./main.py multi-liquid-freeze \
  --package /abs/path/editable_package --out /abs/path/new_frozen_package \
  --isaac-python /path/to/eos-managed-isaac41/python
```
