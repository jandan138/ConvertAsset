# 2026-05-21 GRScenes Full no-MDL Apply

## Summary

Ran the guarded full-route no-MDL conversion on the materialized GRScenes
scratch tree and verified the result.

Plain version: the first ACL evidence gate is now complete. The immutable
source dataset stayed clean, and the converted scratch dataset is ready for the
next render-manifest plus USD/render smoke-validation gate.

## Inputs

- Source benchmark root:
  `/cpfs/user/zhuzihou/assets/zzh-grscenes`
- Scratch root:
  `/cpfs/user/zhuzihou/assets/zzh-grscenes_nomdl_full_work_20260521`
- Runner:
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py`
- Closure gate:
  `paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json`
- Materialization gate:
  `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json`

## Apply Command

```bash
PYTHONDONTWRITEBYTECODE=1 ./scripts/isaac_python.sh \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py \
  --closure-report paper/shared/evidence/raw/grscene_vlm_grounding/full_dependency_closure_report.json \
  --materialization-report paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_materialization_report.json \
  --apply
```

Result:

- `elapsed_seconds=6627`.
- `status=0`.
- Output report:
  `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_multi_root_run_report.json`.

## Current Evidence

The final runner report records:

- `dry_run=false`.
- `apply_ready=true`.
- 99 planned jobs.
- 99 conversion results.
- `processor_done_count=89583`.
- `source_usd_missing_count=0`.
- `scratch_input_missing_count=0`.
- `top_level_output_collision_count=0`.

The post-apply verifier:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/verify_full_nomdl_apply.py
```

Result:

- Output report:
  `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_apply_verification_report.json`.
- `passed=true`.
- `blockers=[]`.
- 99 expected top-level no-MDL outputs exist.
- 0 source `_noMDL` USD sidecars were found under the immutable source root.
- The verifier does not open USD stages, inspect residual MDL, or validate
  rendered pixels.

## Implementation Notes

- The runner must add the project root to `sys.path` before importing
  `convert_asset.no_mdl`; otherwise Isaac wrapper path execution starts from
  the experiment directory and cannot import the repository package.
- The post-apply verifier is pure Python and does not open USD stages. It is a
  fast gate before the render stage, not a visual or VLM result.
- The converted scratch tree was produced from hardlinked inputs. This remains
  acceptable only because no-MDL writes sibling sidecar USD files rather than
  mutating existing inputs in place.

## Next Gate

Move to paired rendering:

- regenerate or update the render manifest with the converted-input gate;
- run a small USD-open/render smoke validation on representative original and
  no-MDL scene pairs;
- render original and no-MDL pairs for the selected 23 unique targets and 4
  views each;
- run the clean-room `render-visual-reviewer` pass before VLM scoring.
