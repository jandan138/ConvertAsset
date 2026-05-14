# Target Capture Operations

Date: 2026-05-14

## Purpose

Use `target-list` to inspect which logical scene assets will be captured. Use
`target-capture` to render multi-view images around those assets in Isaac Sim.

Run commands through Isaac Sim Python for real USD scenes:

```bash
./scripts/isaac_python.sh ./main.py target-list /path/to/layout.usd
```

## List Targets

Dry-run one GRScenes layout:

```bash
./scripts/isaac_python.sh ./main.py target-list \
  /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd \
  --target-scope auto \
  --target-level object \
  --limit 10 \
  --out /tmp/convertasset-targets.json
```

Useful options:

- `--target-scope auto`: resolve GRScenes furniture scope automatically.
- `--target-level object`: list full object roots such as
  `Furnitures/chair/model_*`.
- `--target-level mesh`: list mesh leaves for debugging.
- `--target-level category`: list category scopes for overview captures.
- `--limit N`: inspect a small prefix before a long run.
- `--out path.json`: write machine-readable target metadata.

## Capture Targets

Capture one scene:

```bash
./scripts/isaac_python.sh ./main.py target-capture \
  /path/to/layout.usd \
  --target-scope auto \
  --target-level object \
  --views 8 \
  --width 1024 \
  --height 768 \
  --out /tmp/grscene_target_capture
```

Smoke-test a small render first:

```bash
./scripts/isaac_python.sh ./main.py target-capture \
  /path/to/layout.usd \
  --target-level object \
  --limit 2 \
  --views 2 \
  --width 320 \
  --height 240 \
  --out /tmp/grscene_target_capture_smoke
```

The command writes:

```text
<out>/<scene_id>/targets.json
<out>/<scene_id>/manifest.jsonl
<out>/<scene_id>/<category>/<target_id>/view_000.png
```

## Renderer Notes

`target-capture` keeps one `SimulationApp`, one stage, one viewport, and one
camera prim alive for the whole scene. This avoids per-target startup cost.

Default renderer:

```text
RayTracedLighting
```

Use `--renderer PathTracing` only when runtime budget allows it. Indoor scenes
can produce occluded views when the orbit camera lands behind walls or furniture;
that is recorded as capture failure or low-quality output, not as proof that the
target does not exist.

## Resume Behavior

By default, existing non-empty images are skipped and recorded as `skipped` in
the manifest. The manifest is regenerated for each command run so downstream
readers see one record per planned view in the current run. Use `--no-resume` to
recapture existing images instead of skipping them.

## Validation Commands

Fast tests:

```bash
python -m pytest tests/capture -q
```

Compile checks:

```bash
python -m py_compile \
  convert_asset/capture/targets.py \
  convert_asset/capture/manifest.py \
  convert_asset/capture/pipeline.py \
  convert_asset/camera/bounds.py \
  convert_asset/camera/poses.py \
  convert_asset/render/viewport.py \
  convert_asset/datasets/grscenes.py \
  convert_asset/cli.py
```

No-RTX validation can prove target discovery, bbox math, camera pose planning,
CLI wiring, and manifest output. It cannot prove final material appearance,
occlusion behavior, RTX convergence, or pixel quality.

## Runtime Caveats

`target-capture` must be run as a fresh Isaac Sim Python process. Importing
`pxr`, `omni.*`, or viewport modules before `SimulationApp` starts can crash or
deadlock Kit startup.

The command waits for Isaac's async USD loading status before it starts target
discovery. Large scenes or missing remote assets can therefore spend visible
time in the `opening stage` phase before capture begins or before the
`max_wait_frames` timeout is reached.
