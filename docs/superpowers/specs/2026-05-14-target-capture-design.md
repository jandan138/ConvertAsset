# Scene Target Capture Design

Date: 2026-05-14

## Goal

Add a first-class pipeline that can locate logical assets inside a USD scene and
capture multi-view images around each asset in Isaac Sim.

The immediate dataset target is GRScenes-style `layout.usd` files, including:

```text
/Root/Meshes/Furnitures/<category>/model_<hash>_<n>
```

The pipeline must keep the existing `thumbnails` command compatible. New behavior
is exposed through new commands instead of changing legacy defaults.

## Reviewed Alternatives

### Patch `thumbnails`

This is the smallest code change, but it would mix legacy mesh-level behavior,
semantic annotator filtering, GRScenes object discovery, and batch rendering in a
single large function. It also risks breaking existing users of `thumbnails`.

### Add a separate target capture pipeline

This is the selected approach. `thumbnails` remains available, while new modules
own target discovery, camera planning, rendering, and manifests. The new pipeline
can later replace the internals of `thumbnails` once behavior is proven.

### Script-only batch capture

This is useful for quick experiments, but not enough for AAAI 2027 paper support.
The paper needs repeatable target inventory, stable identifiers, and manifests.

## Target Granularity

The default target level is `object`.

For GRScenes furniture scopes, this means:

- find the target scope automatically, preferring `/Root/Meshes/Furnitures` when
  a scene is opened directly and `/World/scene/Meshes/Furnitures` when referenced
  under `/World/scene`;
- list non-empty `model_*` roots under each category;
- compute one world bbox for the full object root;
- write output names from stable path-derived IDs, not leaf mesh names.

Supported levels:

- `object`: logical object roots, default for production capture;
- `mesh`: every mesh leaf, useful for debugging and legacy comparison;
- `category`: direct category scopes, useful for overview images.

Default exclusions:

- actual light prims and `/lights`;
- `/__default_setting` and HDR/environment shells;
- `/Meshes/Base`, `/Meshes/BaseAnimation`, and `/Meshes/Animation` unless the
  caller selects a different scope;
- inactive prims, instance proxies, empty targets, guide/proxy-only targets, and
  targets with invalid bboxes.

Furniture categories named `light` are not excluded by name, because they can be
lamp objects. The exclusion is based on prim type and path role.

## Architecture

```text
convert_asset/
  capture/
    targets.py      # target scope resolution and TargetSpec inventory
    manifest.py     # JSON/JSONL records for targets, views, and images
    pipeline.py     # target-list and target-capture orchestration
  camera/
    bounds.py       # lazy-pxr world bbox utilities
    poses.py        # pure-Python orbit pose planning
  render/
    viewport.py     # lazy Isaac viewport capture helpers
  datasets/
    grscenes.py     # layout.usd discovery for dataset-level follow-up
```

`camera/orbit.py` remains the richer USD camera animation authoring tool. The new
pipeline uses shared bbox and pose utilities so future refactors can make
`orbit.py`, `fit.py`, and `thumbnail.py` depend on the same primitives.

## CLI Design

### `target-list`

Dry-run inventory command.

```bash
./scripts/isaac_python.sh ./main.py target-list /path/to/layout.usd \
  --target-scope auto \
  --target-level object \
  --out /tmp/targets.json
```

It opens the stage with `pxr`, resolves the target scope, lists targets, computes
bounds when possible, prints a concise table, and optionally writes JSON.

### `target-capture`

Single-scene capture command.

```bash
./scripts/isaac_python.sh ./main.py target-capture /path/to/layout.usd \
  --target-scope auto \
  --target-level object \
  --views 8 \
  --width 1024 \
  --height 768 \
  --out /tmp/grscene_target_capture
```

It starts one Isaac `SimulationApp`, opens one stage, reuses one camera and one
viewport, then captures `target x view` images. It writes a `manifest.jsonl`
record for every planned image and records failures per target instead of
aborting the whole batch.

### Follow-up `dataset-capture`

Dataset-level batching is intentionally deferred until the single-scene API is
stable. `convert_asset/datasets/grscenes.py` provides discovery helpers that a
future command can call.

## Output Layout

Default image layout:

```text
<out>/<scene_id>/<category>/<target_id>/view_000.png
<out>/<scene_id>/<category>/<target_id>/view_001.png
<out>/<scene_id>/manifest.jsonl
<out>/<scene_id>/targets.json
```

The manifest records:

- source scene path;
- target path, category, target ID, target level, mesh count;
- bbox center, size, min, max;
- view index, azimuth, elevation, distance, camera position;
- output path;
- capture status and error message when present.

## Error Handling

Target discovery is strict about missing explicit scopes and permissive for
individual bad targets. A missing `--target-scope` path returns a non-zero CLI
status. An invalid or empty object is skipped with a manifest warning.

Rendering errors are isolated per view or per target. The batch runner continues
when possible and returns non-zero if any requested target failed.

## Testing Strategy

The first implementation uses fast unit tests for the non-rendering contract:

- auto scope resolution prefers GRScenes furniture scopes;
- object-level discovery returns non-empty `model_*` roots and skips empty roots;
- mesh-level discovery still returns leaf meshes;
- orbit pose planning returns stable, finite view positions;
- manifest writing produces JSON records with stable path-derived IDs.

Isaac rendering is verified with compile checks and a low-resolution smoke
command when the renderer is available. No test without RTX/GPU is allowed to
claim final render quality.

## Compatibility

Existing `thumbnails` behavior remains available. The new CLI commands do not
change `thumbnails` defaults, output names, or return codes.

