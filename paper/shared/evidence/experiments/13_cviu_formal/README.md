# CVIU formal cross-scene capacity study

Active goal: 30 frozen formal scenes × 8 distinct objects × 2 views = 480 pairs;
Qwen3-VL-8B/32B × two material conditions × three fresh-process repeats = 5,760 predictions.
This is a new campaign, not a relabeling of the completed three-scene pilot.

## Frozen resources

`paper/shared/evidence/raw/cviu_formal/v1/scenes.json` retains the existing 20 home/10
commercial scene IDs and train/validation/test labels; excludes pilot/reserve scenes.
The formal model evaluation uses all 30 scenes; these split labels do not imply model
training. Initial USD entry hashes match the original frozen inventory.
`protocol.json` records the current goal scope and pinned checkpoint revisions.

## Execution status

- `download_model.py`: revision-pinned 32B public checkpoint download, then filename/size checks.
- `prepare_scenes.py`: two CPU workers independently restore each scene, convert, and audit
  its geometry. `restore_pilot.py --splits ...` is reused with explicit split selection.
  Before conversion, all loaded USD layers must belong to the new workspace; shared
  MDL/textures may be read, but source USD references must not be converted in place.
- Status and logs under the formal workspace are authoritative. A failed scene remains
  in the frozen cohort until repaired; no model-outcome-driven or silent scene substitution.

Workspace: `/cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/formal_sources_20261114_v1`.

Still required: target/query selection, batch renderer that reuses loaded scenes across
views, annotation/visual QA, 32B two-GPU BF16 qualification, full inference, statistics,
old-ICLR comparison and final contribution statement. No formal results exist yet.

## Measurement contract

Freeze image/query/mask hashes before inference; both models see identical accepted inputs.
Keep native model processor/version settings explicit and verify their pixel budget before
capacity comparison. Do not equate checkpoint size comparison with a pure causal parameter-count experiment.

Report fixed-denominator mask hits, visible-box auxiliary hits, coordinate coverage, gains,
losses, turnover, repeated-input disagreement and normalized/pixel displacement. Runtime
exceptions are separate from invalid model responses; never count infrastructure failures
as task misses or silently remove them. Report visibility/label exclusions and their rates.

Use 10,000 scene-cluster bootstrap draws (seed 20261114), keeping all objects/views/repeats
of a scene together; report 95% intervals. Preserve the paired structure for model contrasts.
For matched repeats report O/C flips; separately compare independent-run O/C disagreement
with the mean O/O and C/C disagreement baseline. Treat excess disagreement as descriptive,
not a literal causal fraction. Report greedy-repeat stability without claiming coverage of
stochastic decoding. Include center-point and uniform-pixel baselines.

No stopping rule based on significance or discovered flip count. A null result completes
the experiment if the specified coverage and audits pass. Conclusions must state what is
supported, unsupported, and unresolved. Compare new and old ICLR data, conversion revision,
model/readout and sampling protocols explicitly rather than pooling incompatible results.

## Resource closure update

All 30 frozen scene pairs now pass geometry/dependency audits, including five remote-MDL repairs. `ready_scenes.json` binds receipts and target pools. The 240 targets remain provisional. Batch render equivalence is not yet qualified; synchronous-load controls are running.

## Formal visibility population

Unlike pipeline qualification in the pilot, the formal cohort is frozen from valid original
views. Technically valid conversions that remove target visibility remain in the cohort.
Report visible-mask end-to-end success on that fixed denominator, visibility-loss rates,
and a separately named both-visible comparison. Never interpret information loss as
proof of model reasoning failure. Broken renders/annotations remain infrastructure errors
and require repair, not a zero task score. Preserve query/target identity and all exclusions.

## Candidate capture status

Matched ordered batch repeats passed (RGB MAE < 1, masks equal); fresh-per-view
equivalence remains unproven. Use one uniform final O/C sequence and the prescribed
render-repeat controls. Original-only candidate capture now runs over all 30 scenes,
with up to four geometric views per target; the final cohort still requires two
accepted views per target (480 pairs). Proposals and captured frames are not acceptance.


## Frozen cohort inference and complete-output analysis

`run_formal_campaign.py --raw RAW --out RUNS/MODEL --model 8b|32b --checkpoint CHECKPOINT` runs three independent 960-input primary processes and one 96-input render-control process. Reserve one GPU for 8B or two for 32B using CUDA_VISIBLE_DEVICES. Campaigns preserve exclusive outputs and stop on any incomplete run.

`analyze_when_complete.py --raw RAW --runs RUNS --out ANALYSIS` waits for both campaigns to complete, then executes `analyze_formal.py` on exactly six primary JSONL files and `analyze_render_controls.py` on primary repeat0 plus auxiliary predictions. The latter remains a descriptive analysis of three preselected scenes. Analysis completion does not complete manuscript interpretation or the active goal.

Current frozen primary inputs: `raw/cviu_formal/v1/manifest.json`; repeated-render controls: `render_control_manifest.json`. Live run receipts are under the external `formal_model_runs_v1/{8b,32b}` directories, referenced by `formal_campaign_dispatch.json`. Do not edit the frozen protocol/inputs or bound inference runner during a campaign.
