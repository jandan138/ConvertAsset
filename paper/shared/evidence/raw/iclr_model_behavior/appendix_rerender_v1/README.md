# Repaired appendix target views

This versioned directory holds qualitative rerenders for ICLR Figures 14 and 15.
It is **not** a replacement inference dataset. Historical images, model responses,
and numerical results remain in their original locations.

The five Original images previously shown in these figures were recorded before
the GRScenes MDL dependency repair. Their historical logs contain missing MDL
modules and failed shade-node creation. The current scene dependencies have the
repaired relative KooPbr imports. New captures use the saved cameras and both
material conditions, without pixel recoloring or replacement materials.

- `manifest.json`: commands, old/new image hashes, log paths/hashes, material
  diagnostics and per-image visual review. A pending review is not approved output.
- `preserved_inputs.json`: hashes of historical predictions and referenced images.
- `runtime_sources.json`: camera layers, scene entry layers, renderer and MDL
  library fingerprint used for this run.
- `unchanged_manuscript_inputs.json`: numerical tables, submission CSV and Figure 1
  source hashes captured before the repair.

Reproduction, from the repository root:

```bash
python paper/shared/evidence/experiments/11_iclr_model_behavior/rerender_appendix.py \
  --out paper/shared/evidence/raw/iclr_model_behavior/appendix_rerender_v2 \
  --work /cpfs/user/zhuzihou/assets/convertasset_research/experiments/grscenes/appendix_rerender_v2
```

Each capture invokes Isaac Sim separately and writes a new output. The default
timeout is 900 seconds per capture. Failures are retained for diagnosis. Do not
delete a failed record to make it appear successful; use a fresh output directory
for a corrected run. Completed captures can be resumed, but their hashes must
still match. Review all output images before setting a visual `PASS` verdict.

The initial backpack Original capture was validated separately, then copied
byte-for-byte into this directory; its manifest preserves the actual smoke
command, original output location and log. Remaining captures use the batch runner.

The ICLR figure loader requires exactly five approved pairs and rejects old red
image hashes, absent files, changed images and failed material diagnostics.
Historical readout scores include rendering-failure inputs; the appendix explains
that those scores describe the recorded rendering conditions and do not transfer
to these repaired images.
