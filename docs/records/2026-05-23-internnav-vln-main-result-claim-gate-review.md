# 2026-05-23 InternNav VLN Main-Result Claim Gate Review

## Context

The active ACL goal is to turn the InternNav / DualVLN downstream route into a
main-result-level experiment, not just a protocol smoke test. This review
records the current claim boundary, the evidence required to promote the result,
and the video policy for paper-quality qualitative comparisons.

## Current Story

ConvertAsset is not only an asset conversion tool in the paper story. The ACL
question is whether a material/texture conversion that preserves scene geometry
still preserves the visual conditions that embodied language agents rely on.

The current VLM grounding results support the first half of that story:
target-centered image pairs can remain task-readable while still exposing
material and coordinate-protocol sensitivity. InternNav extends the same concern
to embodied downstream behavior: for the same scene, instruction, start, and
goal, changing the material representation may change how the navigation agent
acts.

The one-episode InternNav smoke already proves the route is executable and
produces real embodied metrics. It does not yet prove a statistically stable
navigation-performance claim.

## Current Gate Status

The main-result gate is not open yet.

The repository currently has:

- one real paired InternNav smoke episode;
- a prepared `acl_main_pilot30` dataset with 30 episodes across six ready
  scenes;
- an original-side `acl_main_pilot30` run in progress;
- no modified-side `acl_main_pilot30` result yet;
- no pilot30 per-episode JSONL extraction or paired analysis yet;
- no paper video frames or mp4 artifacts yet.

The current one-episode smoke supports only a downstream sensitivity example:
both original and no-MDL failed with `SR=0` and `SPL=0`, while the no-MDL run had
larger `TL` and `NE`. That can be written as a failure-case seed, not as a broad
benchmark conclusion.

## Promotion Criteria

Minimum pilot-main criteria:

- at least 30 paired episodes;
- at least five scenes;
- completed original and modified aggregate `result.json` files;
- per-episode JSONL for both conditions;
- paired statistics with SR/SPL/NE/TL/OS/StR/FR deltas;
- failure-pair taxonomy;
- selected-case video reruns or a documented reason that video failed;
- manifest-level proof that original and modified conditions share the same
  instruction, start, goal, and navigation geometry.

Preferred ACL main-result criteria:

- 100+ paired episodes;
- 10+ scenes;
- repeat or seed-control check for representative episodes;
- representative qualitative videos covering multiple case types;
- explicit limitations if success metrics remain all-zero.

If pilot30 still has nearly all failures, the paper claim should be phrased as
embodied trajectory/failure sensitivity, not as a success-rate or SPL benchmark.

## Video Policy

Metric runs should keep video disabled:

```text
eval_settings["vis_output"] = False
agent.model_settings["vis_debug"] = False
```

This keeps 30+ episode runs storage-bounded and avoids requiring video codecs in
the main metric loop.

Paper videos should be produced only after metrics identify representative
cases. The selected rerun configs should use a new task name and enable:

```text
eval_settings["vis_output"] = True
agent.model_settings["vis_debug"] = False
```

InternNav's visualization path is expected to write under:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/frames/*.png
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/<trajectory_id>.mp4
```

Side-by-side paper videos should be created from matched original and modified
selected reruns, then stacked with `ffmpeg`. Different episode lengths must be
handled explicitly by truncating, padding, or leaving a visible blank segment.

The video should show the same instruction, scene id, episode id, terminal
metrics, failure reason, and a synchronized first-person/top-down view when
available. It should emphasize behavior changes such as the first divergent
turn, a stuck loop, moving away from the goal, or reaching a different terminal
state.

## Case Checklist

Try to cover these case types in the final video set:

- original-only success;
- modified-only success;
- both-success but trajectory-divergent;
- both-failure and trajectory-divergent;
- neutral control with similar behavior.

If one of these case types does not appear in the completed batch, record that
absence instead of forcing a hand-picked example.

## Render Boundary

Do not migrate the separate `render-usd` runtime wholesale. ConvertAsset already
has the relevant local render capabilities for static paper figures:

- target-centered render manifests and camera-stage authoring under
  `paper/shared/evidence/experiments/06_grscenes_vlm_grounding/`;
- authored-camera viewport capture through
  `scripts/render_with_viewport_capture.py`;
- single-object render callouts through `convert_asset/render/single.py`.

Use InternNav `vis_output=True` for navigation videos. Use the existing
ConvertAsset target-centered render pipeline for static close-ups, bbox
projection QA, and paper figures. Keep no-MDL generation in scratch trees, not
inside `/cpfs/user/zhuzihou/assets/zzh-grscenes`.

## Current Runtime Observation

As of the review, the original `acl_main_pilot30` run was still active. The
progress log had reached seven completed episodes and the eighth had started.
The aggregate partial metrics at `Count=7` were:

```json
{
  "TL": 21.8069,
  "NE": 11.2418,
  "FR": 0.0,
  "StR": 0.0,
  "OS": 0.2857,
  "SR": 0.0,
  "SPL": 0.0,
  "Count": 7
}
```

This is an in-progress original-only artifact and must not be used as final
paper evidence.

## Next Work

1. Let the original pilot30 run finish.
2. Inspect the final original result and logs.
3. Run the modified pilot30 counterpart with stdout redirected to a log file.
4. Extract aggregate and per-episode metrics for both conditions.
5. Run paired analysis and select video cases.
6. Generate selected-only video reruns and side-by-side mp4s.
7. Update the ACL paper only after the claim gate records real paired results.

