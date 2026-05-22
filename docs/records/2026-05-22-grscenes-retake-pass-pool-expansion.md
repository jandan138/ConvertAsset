# 2026-05-22 GRScenes Retake and Zoom Evidence Expansion

## Context

The ACL-oriented GRScenes VLM grounding story needs two related but distinct
evidence pools:

- a clean original/no-MDL paired-render pool before canonical final VLM scoring
  can be claimed;
- a material-shift stress pool where the target is visible and the A/B view is
  fair, but the no-MDL conversion visibly changes color, texture, lighting, or
  material appearance.

The existing canonical manifest had four PASS pairs and explicitly blocked
final benchmark claims because the configured final gate requires at least 20
visual-QA PASS pairs.

## Decision

Retakes must be generated as separate artifacts, not by overwriting the existing
render manifest or render tree. The retake route uses:

- `retake_render_manifest.json`
- `retake_renders/`
- `retake_visibility_preflight_report.json`
- `retake_camera_stage_authoring_report.json`
- `retake_paired_render_reports/`
- `retake_render_logs/`
- `retake_paired_render_summary.json`
- `retake_target_projection_qa_report.json`
- `retake_visual_review_batch.json`

The retake manifest uses `--view-id-prefix retake --view-index-offset 8`, so
pair ids become `<target_id>.retake_008` and later instead of reusing the
original `<target_id>.view_000` names.

Zoom retakes use a second non-overwriting namespace:

- `retake_zoom_render_manifest.json`
- `retake_zoom_renders/`
- `retake_zoom_visibility_preflight_report.json`
- `retake_zoom_camera_stage_authoring_report.json`
- `retake_zoom_paired_render_reports/`
- `retake_zoom_render_logs/`
- `retake_zoom_paired_render_summary.json`
- `retake_zoom_target_projection_qa_report.json`
- `retake_zoom_visual_review_batch.json`

The zoom manifest uses `--view-id-prefix zoom --view-index-offset 16` plus
`--focal-length-mm 18.0`, so pair ids become `<target_id>.zoom_016` and later.
This keeps all camera, render, and review evidence separate from the earlier
orbit views.

## Ordinary Retake Result

The ordinary retake review now covers 40 explicit pairs. All 40 passed render
smoke: both original and converted commands exited successfully and both PNGs
exist.

Projection QA marked 39 pairs `projection_ok`; the only projection blocker was
`90e105daa7e6ff59da38.retake_014`, which was already a visual-QA FAIL and
therefore does not affect the PASS pool.

Independent clean-room visual QA marked the first batch:

- PASS: 11
- WARN: 23
- FAIL: 6

Combined with the earlier four canonical PASS pairs, the clean preservation
pool is 15 PASS pairs. This is useful progress, but the final benchmark gate
remains closed until the clean PASS pool reaches at least 20 pairs and
canonical predictions plus score summary are regenerated from that final
manifest.

## Zoom Retake Result

The zoom pass rendered all 14 visibility-preflight recommended pairs. All 14
passed render smoke and all 14 passed projection QA, producing 28 scoring-record
skeletons.

Independent clean-room visual QA marked the zoom set:

- PASS: 2
- WARN: 12
- FAIL: 0

The two PASS pairs are `f35ef3d86c42446b7ddf.zoom_018` and
`f35ef3d86c42446b7ddf.zoom_019`. These are strong VLM grounding candidates:
the clock is visible, identifiable, and framed comparably in the original and
converted images.

However, zoom did not solve the clean-preservation gate. Most zoom pairs are
WARN because the target is easy to see but the original-vs-converted material
or lighting shift is large. Treat the zoom PASS/WARN pool as material-shift
stress evidence for the ACL story, not as proof that the conversion preserves
appearance.

## Operational Notes

Original-condition renders still emit many MDL/KooPbr failures in Isaac logs.
That is expected for the original GRScenes material stack and is part of why the
paper studies no-MDL conversion. Do not treat those stderr lines as render-smoke
failure if the command exits 0 and the image hash/non-dark pixel checks pass.

Several WARN pairs are visually useful diagnostics for material/color shift but
are not clean enough for final PASS scoring. In particular, some cup, plate, and
faucet retakes are identifiable while showing large original-vs-converted color
or exposure differences. Keep those as qualitative caution examples unless a
later reviewer explicitly promotes them.

The next paper step should stop blindly adding the same orbit views. The
ordinary orbit route had low marginal yield, while zoom confirmed that material
shift is a real stress factor. The practical route is:

1. keep the 15-pair clean preservation pool separate from the zoom stress pool;
2. run real VLM probes on the target-visible stress pool to measure whether
   grounding changes when materials shift;
3. only reopen clean PASS expansion if the paper still needs a final benchmark
   claim rather than a pilot/stress-study claim.

Storage note for this round: retake PNG/camera outputs are about 26M, zoom
outputs about 10M, retake logs about 56M, and zoom logs about 19M. The evidence
is small enough to keep, but future scaling should continue to use explicit
pair-id subsets instead of rendering every planned camera.

Provenance note: the GRScenes experiment scripts now omit per-file untracked
paths from `git_status_porcelain` and record a compact untracked-file count
instead. The older `--untracked-files=all` behavior made generated JSON grow
with every rendered PNG, camera wrapper, and log path before those artifacts
were staged.

Git hygiene note: `paper/shared/evidence/raw/grscene_vlm_grounding/*render_logs/**/*.txt`
is marked as `-text -diff` in `.gitattributes`. These files are raw Isaac/Kit
logs whose exact bytes are hashed by paired render reports; do not trim trailing
spaces or normalize them after report generation.
