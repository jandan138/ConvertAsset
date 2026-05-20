# GRScenes Material Dependency Closure Planner Implementation Plan

## Goal

Plan the exact split-level `home_scenes/Materials` subset needed by the 23
selected GRScenes VLM target model roots. The planner must stay read-only and
must not scale the earlier one-scene split-level mirror.

## Scope

- Add `plan_material_dependency_closure.py` beside the existing GRScenes VLM
  experiment scripts.
- Add tests for pxr-lazy import behavior, text-backend recovery, deduplication,
  missing-material reporting, and source/scratch path safety.
- Generate
  `paper/shared/evidence/raw/grscene_vlm_grounding/material_dependency_closure_plan.json`.
- Update experiment READMEs and records so the next materializer can proceed
  without rediscovering the split-level Materials trap.

## Design

- Default backend is pxr: use `UsdUtils.ComputeAllDependencies(str(instance_usd))`.
- The script imports `pxr` only inside the pxr backend function.
- The test backend scans `@asset@` references in small fake USD/MDL text files.
- Resolved material paths are normalized through real paths so model-root
  `Materials` symlinks deduplicate against split-level `home_scenes/Materials`.
- Unresolved paths are only recoverable when their lexical tail is under
  `model_root/Materials/<tail>` and `split_root/Materials/<tail>` exists.
- Material actions are file-level hardlink plans, not directory mirrors.
- Pointer-file and missing model-root `Materials` entries produce separate
  scratch-side repair actions. The 68 material files alone are not enough to run
  no-MDL.

## Verification Plan

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_material_dependency_closure.py
./scripts/isaac_python.sh paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_material_dependency_closure.py --dependency-backend pxr
python -m json.tool paper/shared/evidence/raw/grscene_vlm_grounding/material_dependency_closure_plan.json >/tmp/material_dependency_json_check.out
```

After code review, run the full pytest suite and a dry-run regeneration to a
temporary output path.
