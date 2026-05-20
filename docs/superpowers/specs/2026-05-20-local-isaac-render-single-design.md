# Local Isaac Render Single Design

## Goal

Move the useful, stable parts of `render-usd` into ConvertAsset so this repository can render USD assets through the local Isaac Sim runtime exposed by `./scripts/isaac_python.sh`, without depending on `/cpfs/shared/simulation/zhuzihou/dev/render-usd` or its independent conda environment.

## Problem

ConvertAsset already has rendering code, but the current CLI path is not a reliable paper rendering backend. The `thumbnails` command is routed through `main.py -> convert_asset/cli.py`, and `convert_asset/cli.py` imports modules that can load `pxr` before `SimulationApp` starts. Isaac Sim requires `SimulationApp` to be initialized before `omni` and often before `pxr`-backed extension modules are imported. A smoke run on 2026-05-20 reproduced this as extension startup errors followed by a segmentation fault.

`render-usd` has a working single-asset renderer, but it assumes its own `render-usd` Python environment, package layout, DLC scripts, default dataset roots, and historical batch output conventions. Those assumptions should not be copied into ConvertAsset.

## Recommended Approach

Implement a narrow local renderer in ConvertAsset:

1. Keep `convert_asset.cli` safe to import for render commands by removing top-level `pxr` imports from the CLI import path.
2. Add a new `render-single` CLI command for one USD file and four fixed orbit views.
3. Keep all `isaacsim`, `omni`, and `pxr` imports inside the runtime function after `SimulationApp` is created.
4. Port the render-usd practices that are directly useful: `SimulationApp` first, headless PathTracing defaults, environment fallback lighting, bbox validation, camera orbit from object bbox, view-name output, overwrite/skip behavior, explicit cleanup before `kit.close()`.
5. Leave ACL `render_manifest.json` execution as the next layer. It should call the same local runtime after the single-file path is verified.

## Non-Goals

- Do not vendor the `render-usd` package or use its conda environment.
- Do not add DLC job submission in this step.
- Do not mutate benchmark datasets in place.
- Do not claim VLM or ACL experiment results from this renderer smoke test.
- Do not make `thumbnails` the paper renderer. It remains a legacy scene-instance thumbnail tool.

## New User Flow

```bash
./scripts/isaac_python.sh ./main.py render-single \
  /abs/path/to/asset.usd \
  --out /tmp/render-single-smoke \
  --naming-style view \
  --overwrite
```

Expected output for default four views:

```text
/tmp/render-single-smoke/<asset_stem>/front.png
/tmp/render-single-smoke/<asset_stem>/left.png
/tmp/render-single-smoke/<asset_stem>/back.png
/tmp/render-single-smoke/<asset_stem>/right.png
```

## Architecture

- `convert_asset/render/single.py`: local Isaac renderer entrypoint and pure helpers.
- `convert_asset/cli.py`: lazy dispatch for `render-single`; avoid importing `pxr` on CLI import.
- `tests/test_render_single.py`: pure-Python tests for import isolation, output planning, and command wiring. Runtime image generation is verified by an explicit smoke command, not unit tests.
- `docs/operations/local-rendering.md`: runbook for local Isaac rendering and known limitations.
- `docs/records/2026-05-20-local-isaac-render-single.md`: dated implementation record.

## Error Handling

- Missing USD input returns code `2`.
- Missing Isaac Sim runtime returns code `3`.
- Invalid bbox returns a nonzero code and no partial success claim.
- Existing outputs are skipped unless `--overwrite` is set.
- Runtime cleanup must clear camera resources, delete the transient `/World/Show` prim, force garbage collection, and close `SimulationApp`.

## Testing

Automated tests cover behavior that does not require Isaac Sim:

- importing `convert_asset.cli` does not load any `pxr` module;
- importing `convert_asset.render.single` does not load `isaacsim`, `omni`, or `pxr`;
- view-name planning is deterministic;
- unsafe or missing input paths fail clearly.

Runtime verification uses local Isaac Sim:

```bash
./scripts/isaac_python.sh ./main.py render-single \
  assets/usd/chestofdrawers_nomdl/chestofdrawers_0011/instance.usd \
  --out /tmp/convertasset-render-single-smoke \
  --naming-style view \
  --overwrite
```

The smoke pass requires four nonempty RGB PNG files.
