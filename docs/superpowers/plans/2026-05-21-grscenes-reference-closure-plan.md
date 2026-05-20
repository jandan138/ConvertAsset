# GRScenes Reference Closure Planner Implementation Plan

Date: 2026-05-21

Status: executed. Implementation results and review findings are recorded in
`docs/records/2026-05-21-grscenes-reference-closure-plan.md`; this file remains
the workflow plan and design rationale.

## Goal

Replace the next risky scaling step, full split-level GRScenes mirroring, with a
small planner that derives the target/reference closure from existing manifests.
The planner must be storage-safe by default: it only reads manifests and selected
model roots, then writes a small JSON plan.

## Scope

- Add a pure-Python planner under
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/`.
- Add tests for deduplication, source/scratch containment, and material symlink
  gap reporting.
- Generate the real planning artifact at
  `paper/shared/evidence/raw/grscene_vlm_grounding/reference_closure_plan.json`.
- Update the experiment README and records so the storage pitfall is hard to
  miss.

## Non-Goals

- Do not copy, hardlink, or delete any GRScenes asset files.
- Do not run no-MDL conversion.
- Do not import `pxr`, `omni`, or Isaac Sim.
- Do not claim the closure is runnable until split-level material dependencies
  are resolved.

## Implementation Steps

1. Write failing tests for the planner contract.
2. Implement `plan_reference_closure.py` with pure Python filesystem checks.
3. Run the planner on the current source/target manifests.
4. Document the result and the remaining material dependency gap.
5. Run full verification, request review, then commit and push.

## Design Decisions

- Unique spatial targets are deduplicated by
  `(source_scene_id, object_instance_id, target_prim_path)`, matching
  `prepare_render_manifest.py`.
- Unique model actions are deduplicated by
  `Path(resolved_model_path).resolve().parent`, because multiple episode
  records or targets can point to one model root.
- The planner reports model-internal symlink targets that are not covered by
  the selected scene/model actions. This makes the split-level `Materials/`
  dependency explicit instead of accidentally remirroring the whole split.
- The planner also classifies each selected model root's `Materials` entry as
  `symlink`, `pointer_file`, `missing`, `dir`, or `file`, because GRScenes uses
  more than one pattern and symlink-only checks underreport the closure risk.
- All source and destination paths are containment-checked against manifest
  source and scratch roots.

## Expected Output

The current real plan should remain small: tens of target model files, not
hundreds of thousands of split-level files. It is allowed to report
`material_closure_status=requires_material_dependency_resolution`; that status
is the evidence needed for the next, narrower material dependency planner.

Execution note: the implemented planner now reports
`model_root_only_materialization_safe=false` for the current pilot. See the
dated record for the exact generated counts.
