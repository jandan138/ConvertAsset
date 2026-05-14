# Scene Target Capture Design

Date: 2026-05-14

## Purpose

Scene target capture locates logical assets inside a composed USD scene and
captures multi-view images around each asset with Isaac Sim. It is intended for
GRScenes-style `layout.usd` files and for paper-quality evidence where target
inventory, camera views, and output images must be reproducible.

The existing `thumbnails` command remains a compatibility path. The new feature
uses `target-list` and `target-capture`.

## Target Granularity

The default target level is `object`.

For GRScenes, an object target is usually:

```text
/Root/Meshes/Furnitures/<category>/model_<hash>_<n>
```

When the same scene is referenced under `/World/scene`, the equivalent path is:

```text
/World/scene/Meshes/Furnitures/<category>/model_<hash>_<n>
```

This avoids the legacy mesh-level problem where a single chair can be split into
chair back, chair seat, chair legs, and other mesh leaves.

Supported levels:

- `object`: non-empty logical object roots, recommended default;
- `mesh`: every mesh leaf under the scope, useful for debugging;
- `category`: direct category scopes such as `chair` or `table`, useful for
  overview captures.

## Scope Resolution

`--target-scope auto` checks common GRScenes and legacy locations in order:

1. `/World/scene/Meshes/Furnitures`
2. `/Root/Meshes/Furnitures`
3. `/World/scene/Instances`
4. `/Root/Instances`
5. `/World/scene`
6. `/Root`

Explicit relative scopes are resolved under `/World`, as absolute paths, under
`/World/scene`, and under the stage default prim.

## Module Boundaries

```text
convert_asset/capture/targets.py
```

Owns `TargetConfig`, `TargetSpec`, target-scope resolution, and target listing.
It uses a small duck-typed USD surface so tests can run without loading real
USD files.

```text
convert_asset/camera/bounds.py
```

Owns `Bounds3D` and lazy-`pxr` world bbox computation. It filters common
environment shells, light prims, empty ranges, non-finite ranges, and
pathological extents. Bounds are merged from accepted `UsdGeom.Boundable`
descendants instead of ancestor aggregate bboxes, so ignored environment
children such as `__default_setting/HDR_Sphere` cannot inflate an object target.

```text
convert_asset/camera/poses.py
```

Owns pure-Python orbit pose planning. It rounds view counts up to an even
number and splits views between positive and negative elevation.

```text
convert_asset/capture/manifest.py
```

Owns JSON-safe target and capture records. It writes `targets.json` and
`manifest.jsonl`.

```text
convert_asset/capture/pipeline.py
```

Owns `run_target_list` and `run_target_capture`.

```text
convert_asset/render/viewport.py
```

Owns Isaac Sim viewport helpers. All Isaac imports stay inside functions so CLI
help and unit tests do not require a renderer. Stage opening waits on
`get_stage_loading_status()[2]` when available, matching Isaac's own async
loading status API.

```text
convert_asset/datasets/grscenes.py
```

Owns `layout.usd` discovery helpers for later dataset-level batching.

## Output Contract

Default image layout:

```text
<out>/<scene_id>/<category>/<target_id>/view_000.png
<out>/<scene_id>/<category>/<target_id>/view_001.png
<out>/<scene_id>/targets.json
<out>/<scene_id>/manifest.jsonl
```

`targets.json` records target paths, IDs, categories, levels, mesh counts, and
bounds when bbox computation succeeds.

`manifest.jsonl` records one line per planned capture view. Each record includes
the scene path, target metadata, bbox, camera pose, output path, status, and
error message when present.

## Failure Model

Target listing fails fast when the scene cannot be opened or an explicit scope
does not exist. Individual targets with invalid bboxes are skipped or marked as
failed in the manifest during capture.

Capture uses one Isaac `SimulationApp`, one opened stage, one viewport, and one
reused camera prim. Per-view failures are recorded in `manifest.jsonl`; the
command returns non-zero if any requested target view fails.
