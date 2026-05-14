# 2026-05-14 Scene Target Capture Implementation

## Investigation

Multi-agent review found that the existing `thumbnails` pipeline collects every
`Mesh` under its scope. On GRScenes layouts this splits logical assets into mesh
parts. The reviewed GRScenes hierarchy places furniture objects under:

```text
/Root/Meshes/Furnitures/<category>/model_<hash>_<n>
```

Many `model_*` roots are empty, so discovery must require at least one mesh
descendant.

## Design Decisions

- Keep `thumbnails` compatible and add new commands.
- Default to object-level targets for GRScenes.
- Keep mesh-level and category-level modes for debugging and overview captures.
- Keep Isaac imports lazy so regular CLI help and unit tests do not require a
  renderer.
- Use a manifest per capture scene to preserve reproducibility for paper work.
- Defer dataset-level batching until the single-scene API has been validated.
- Compute capture bboxes from accepted `UsdGeom.Boundable` descendants, not
  from ancestor aggregate bounds, so ignored environment children cannot leak
  into object extents.
- Wait for Isaac's `get_stage_loading_status()[2]` during `open_stage()`.

## Code Changes

Created:

- `convert_asset/capture/targets.py`
- `convert_asset/capture/manifest.py`
- `convert_asset/capture/pipeline.py`
- `convert_asset/camera/bounds.py`
- `convert_asset/camera/poses.py`
- `convert_asset/render/viewport.py`
- `convert_asset/datasets/grscenes.py`
- `tests/capture/test_targets.py`
- `tests/capture/test_poses_manifest.py`
- `tests/capture/test_pipeline.py`
- `tests/capture/test_bounds.py`

Modified:

- `convert_asset/cli.py`
- `docs/index.md`
- `docs/design/README.md`
- `docs/operations/README.md`
- `docs/records/README.md`
- `docs/superpowers/README.md`

## Validation

Initial full baseline in the worktree:

```text
python -m pytest tests -q
```

Result: 10 passed, 2 failed. The failing tests are pre-existing GLB hierarchy
tests that reference missing worktree assets under
`assets/usd/chestofdrawers_nomdl/.../instance_noMDL.usd`.

Final full-suite check after adding target-capture tests:

```text
python -m pytest tests -q
```

Result: 27 passed, 2 failed. The same two GLB hierarchy tests still fail
because those `chestofdrawers_nomdl` USD fixtures are absent from this
worktree.

Target-capture focused tests:

```text
python -m pytest tests/capture -q
```

Result after implementation and review fixes: 14 passed.

Result after second review fixes for bbox filtering, stage-load waiting, and
async viewport capture result handling: 17 passed.

Compile and CLI help checks were run after CLI wiring:

```text
python -m py_compile convert_asset/capture/targets.py convert_asset/capture/manifest.py convert_asset/capture/pipeline.py convert_asset/camera/bounds.py convert_asset/camera/poses.py convert_asset/render/viewport.py convert_asset/datasets/grscenes.py convert_asset/cli.py
python ./main.py --help
```

Both exited 0, and help showed `target-list` and `target-capture`.

Additional review-driven checks:

```text
python - <<'PY'
import sys
import convert_asset.cli
print([m for m in sys.modules if m == "pxr" or m.startswith("pxr.")])
PY
```

Result: `[]`. This confirms CLI import no longer loads `pxr` before
`SimulationApp`.

GRScenes target listing smoke:

```text
./scripts/isaac_python.sh ./main.py target-list \
  /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd \
  --target-level object \
  --limit 5 \
  --out /tmp/convertasset-targets-review-fixed-2.json
```

Result: exited 0, resolved `/Root/Meshes/Furnitures`, and wrote 5 bounded
object targets.

The first `target-capture` smoke exposed an eager-`pxr` import path through
`convert_asset.cli`; after moving those imports inside subcommands, Kit started
cleanly. A later smoke showed the command could stay in Isaac stage loading,
which led to the `get_stage_loading_status()[2]` wait fix above.

Final low-resolution Isaac smoke:

```text
./scripts/isaac_python.sh ./main.py target-capture \
  /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes100/home/MV7J6NIKTKJZ2AABAAAAADQ8_usd/layout.usd \
  --target-level object \
  --limit 1 \
  --views 2 \
  --width 64 \
  --height 64 \
  --wait-frames 1 \
  --out /tmp/convertasset-target-capture-smoke
```

Result: exited 0, wrote `targets.json`, `manifest.jsonl`, and two PNG files.
Both manifest records had `status="ok"`. The run also showed that Isaac may
spend several minutes loading/rendering even for a tiny smoke scene.

## Follow-up

- Add dataset-level `dataset-capture` once single-scene capture is validated on
  representative GRScenes samples.
- Consider migrating `thumbnails`, `camera/orbit.py`, and `camera/fit.py` onto
  the shared bbox and pose helpers after behavior parity is documented.
- Add a low-resolution headless render smoke test in an environment with a
  working Isaac renderer.
