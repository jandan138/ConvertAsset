# 2026-05-21 GRScenes Full no-MDL Scratch Plan

## Summary

Added a read-only planner for the "can we no-MDL the whole
`zzh-grscenes` tree first?" route. The answer is: yes in principle, but the
safe engineering path is not direct in-place conversion and not a naive loop of
99 or 297 independent CLI runs.

## Files Added

- `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py`
- `paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_plan.json`
- `tests/test_grscenes_vlm_full_nomdl_scratch_plan.py`
- `docs/superpowers/plans/2026-05-21-grscenes-full-nomdl-scratch-plan.md`

## Design Notes

- The planner is pure Python and imports no `pxr`.
- It reads only bounded scene-directory structure under
  `/cpfs/user/zhuzihou/assets/zzh-grscenes/scenes/GRScenes-100`.
- It does not copy, hardlink, convert, render, or create scratch directories.
- It defaults to `start_result_raw.usd`, because raw covers the current ACL/VLM
  grounding story while avoiding immediate 3x recursive conversion risk.
- It inventories all three scene USD variants so the plan can later be expanded
  to `raw/navigation/interaction` with `--all-scene-usds`.
- It emits scratch-side actions for:
  - 99 scene directories.
  - 4 split-level resource roots: home/commercial `models` and `Materials`.
  - 138 home scene pointer-file repairs for `models` and `Materials`.
  - 99 preview no-MDL jobs.
- Preview jobs include structured `argv` fields for a later runner. The
  human-readable `command` string is not the runner contract.
- Commercial scene `models` and `Materials` entries are already relative
  symlinks; the planner records 60 projectable symlink entries and does not
  repair them.
- The CLI refuses `--out` paths inside either the immutable source root or the
  scratch root, so the planner report cannot be accidentally written into an
  asset tree.

## Current Output

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py
```

Output:

```text
paper/shared/evidence/raw/grscene_vlm_grounding/full_nomdl_scratch_plan.json
```

Current checked-in summary:

- 99 scenes: 69 home and 30 commercial.
- 99 planned `start_result_raw.usd` inputs.
- All 297 scene-entry USDs exist: 99 raw, 99 navigation, 99 interaction.
- 340 total planned actions.
- 0 existing source-side raw `_noMDL` sidecars at the scene-entry layer.
- `planner_only=true`.
- `safe_to_apply=false`.

## Important Limitation

Plain version: the plan is a map, not a green button.

ConvertAsset no-MDL writes `*_noMDL.usd` beside every USD it processes, including
recursive dependencies. `--only-new-usd` suppresses summary/audit sidecars, but
it does not suppress recursive dependency USD sidecars. If 99 scene roots are
converted as 99 independent CLI processes, shared dependencies can be converted
again and can produce timestamped outputs because `ALLOW_OVERWRITE=False`.

Therefore the preview commands in the plan are intentionally marked as blocked.
The next implementation step should be a single-process multi-root runner that
reuses one `Processor.done` map, plus a dependency/output collision scan before
any scratch conversion is allowed.

## Storage Notes

The planner intentionally avoids a deep walk of split-level `models/` and
`Materials/`. A previous one-scene split-level hardlink mirror exposed about
104G through `du` and 141,082 visible files, so full resource-tree work needs
strict staging. Hardlink mode can control physical bytes, but it does not remove
file-count, inode, recursive sidecar, or timestamp-output risk.

Do not switch this to `copy` mode under the current 1.6 TiB quota unless a
separate storage estimate proves it fits.

## Verification

Fresh checks run during implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_grscenes_vlm_full_nomdl_scratch_plan.py
PYTHONDONTWRITEBYTECODE=1 python paper/shared/evidence/experiments/06_grscenes_vlm_grounding/plan_full_nomdl_scratch.py
```

The full planner tests report 7 passing tests. Full-repo verification is
tracked in the final commit notes for this change.
