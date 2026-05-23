# Video Material

Optional paper videos and submission-ready video notes should be added here after the venue policy is verified.

## InternNav / DualVLN Side-By-Side Videos

The InternNav videos should be generated only from selected reruns, not from the
full metric batch. The full metric batch keeps `vis_output=False` to avoid large
frame/mp4 output. After paired metrics are available, select representative
cases with:

```text
paper/shared/evidence/raw/internnav_vln_downstream/video_case_manifest.json
```

Then rerun only those cases with `eval_settings["vis_output"] = True` and a new
task name. InternNav is expected to write frames and mp4s under:

```text
/cpfs/user/zhuzihou/dev/InternNav/logs/<task>/video/<trajectory_id>/
```

Submission-ready clips should be side-by-side original vs no-MDL, with matching
scene, instruction, start, target, terminal metrics, failure reason, and step
count. Keep the clip list traceable to the video case manifest and paired metric
rows.
