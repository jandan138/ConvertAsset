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
