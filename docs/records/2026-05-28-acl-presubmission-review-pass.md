# 2026-05-28 ACL Presubmission Review Pass

## Scope

This record captures a focused ACL-style presubmission review pass on the
current `paper/venues/acl27/build/main.pdf` candidate. The pass used the
academic-paper-reviewer workflow locally and did not dispatch independent
subagents.

## Finding

The strongest remaining reviewer-facing weakness was not a figure issue. The
current paper already has the v15 schematic, clean render-evidence panel,
single-column InternNav Figure 3, and a full-PDF visual review record. The
remaining textual risk was model-backend provenance in the VLM grounding
protocol: the Results section reports Gemma4 and Qwen2.5-VL numbers, but the
Method section did not explicitly state the public checkpoint IDs or their
roles.

## Change

`paper/venues/acl27/sections/method.tex` now states that:

- `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` is the canonical Gemma4 local run;
- `Qwen/Qwen2.5-VL-7B-Instruct` is a second-model diagnostic under the same
  manifest;
- these backends are measurement probes, not a model leaderboard.

This uses provenance already recorded in
`paper/venues/acl27/MODEL_AND_ASSET_LICENSE_AUDIT.md`. It does not change any
model outputs, evidence counts, tables, figures, or claim boundaries.

Follow-up typography pass: the same public checkpoint IDs are now typeset as
breakable inline monospace text instead of unbreakable `\path{...}` paths. This
keeps the exact public model IDs visible while avoiding a narrow-column
badness-10000 line break in the Method protocol paragraph.

Conclusion polish: the practical reporting-pattern takeaway was moved out of
the Discussion and compressed into the Conclusion. This keeps Discussion focused
on interpretation, gives the paper a stronger closing action item, and preserves
the 11-page candidate layout without creating a blank tail page.

## Verification

After the provenance edit, Fig.3/checklist anchor sync, checkpoint-ID typography
pass, conclusion polish, final Method/Fig.3 wording polish, and a follow-up
Figure 3 minipage layout fix, the full repository-side pre-upload gate was
rerun:

```bash
python paper/venues/acl27/scripts/run_preupload_gate.py
```

Result: pass. The runner completed claim-boundary, target-policy, metadata,
OpenReview checklist, citation-inventory, evidence-number, final-integrity
fingerprint, final blocker, goal-completion, focused pytest, clean ACL build,
LaTeX log, staging, packet inventory/checksum/private-token/acknowledgment
scans, `pdfinfo`, PDF profile, and `pdftotext` section-order checks. Focused
pytest reports `83 passed`.

The current build and staged packet are byte-identical:

```text
paper/venues/acl27/build/main.pdf
paper/submissions/acl27_arr_candidate_20260526/main.pdf
sha256=5028f38ebc5ac398e3e99980ca00d909abfd4a8e6a61bcf2fb148b6ff5e3857c
size=3,072,456 bytes
pages=11
pdf=1.5 A4
created=2026-05-28 06:34:38 CST
```

`pdftotext -layout -f 9 -l 9` places `Limitations`, Figure 3, Ethical
Considerations, and the start of References on page 9, in that order. The
Figure 3 image and caption are now wrapped together in a `\columnwidth`
minipage, so the two-column layout no longer splits the caption away from the
image. The OpenReview checklist anchors were updated accordingly.

The final LaTeX log still contains ordinary underfull boxes from bibliography
names and narrow ACL columns, but the prior badness-10000 Method checkpoint-ID
line is gone; the only remaining badness-10000 match is in the bibliography
entry for Oquab et al.

Follow-up Method/Fig.3 wording pass: the Method opening now keeps the
non-flattening conversion description in a complete page-3 sentence, and the
main-text Figure 3 caption now says `Selected qualitative InternNav rollout
panel` instead of `Supplemental qualitative InternNav rollout panel`. This
wording pass did not change experiments, figure sources, evidence counts, or
claim boundaries. The subsequent visual spot check confirmed that rendered page
9 still has zero strong-red pixels and that Figure 3 remains the selected
InternNav rollout panel.

Follow-up Figure 1 imagegen iteration: v15 was generated through the imagegen
workflow, copied to `paper/shared/figures/fig_acl_method_chain_imagegen_v15.png`
with prompt provenance in
`paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v15.prompt.txt`,
and promoted over v14 after local pure-visual review. It preserves the same
schematic-only role while improving page-scale balance in the VLM and InternNav
blocks.

Current pure-visual full-PDF spot check: the rebuilt PDF was rendered at 150 DPI
to `tmp/acl27_current_visual_review_final_20260528/`; the contact sheet has
SHA-256 `98657124bda63ec313d534793ee2b76202bf0401952e86839a825ed35dcc75d0`.
Local visual review of the contact sheet found no page-level overlap, blank
page, detached Figure 3 caption, or reintroduced material-effect Figure 3.
The 180-DPI page-9 render has SHA-256
`d1f855fe8be5a85d2f3bfb47cd04b1403ac9b9c43c0381472d4b72b98ebd110e`;
strong-red checks report zero pixels on rendered page 9, the Figure 3 source
PNG, and the regenerated material-effect contact sheet, so the earlier
red-material concern does not recur in the current Figure 3.
The v15 Figure 1 page-2 render has SHA-256
`9a2dd5115956c9d1a028ceec02a8d79e52c7120c04250bdae80a780000a013c1` at
180 DPI and keeps the method-chain roadmap readable at page scale.
