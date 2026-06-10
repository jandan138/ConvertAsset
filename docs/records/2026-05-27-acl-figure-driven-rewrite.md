# 2026-05-27 ACL Figure-Driven Rewrite

## Context

The active ACL/ARR goal shifted from a mostly tabular evidence wrapper toward a
figure-driven main-conference narrative. The selected story order is method
chain first: USD/MDL scene assets, ConvertAsset noMDL conversion, matched
rendering plus VLM grounding, and InternNav navigation evidence.

## Changes

- Added a generated schematic method-chain candidate to:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v1.png`
- Replaced the ACL Figure 1 image reference with the cleaner follow-up
  candidate:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v2.png`
- Refreshed the ACL Figure 1 schematic again with the same preserved image2
  prompt after PDF visual review:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v3.png`
- Preserved the requested `gpt-image-2` prompt for reproducibility at:
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2.prompt.txt`
- Generated and preserved a later imagegen/image2 candidate refresh without
  replacing the current paper figure, because the existing v3 schematic remains
  cleaner for PDF use:
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v4_candidate.png`
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v4_candidate.prompt.txt`
- Re-ran the project image-generation workflow on the same image2 prompt after
  the explicit method-chain request, preserving the output as another backup
  candidate while the already-integrated v3 figure remained in the ACL draft at
  that point:
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v5_candidate.png`
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v5_candidate.prompt.txt`
- Re-ran the project image-generation workflow with an updated image2 prompt
  that explicitly forbids red fallback material in the schematic thumbnails.
  This candidate was promoted into the ACL draft:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v6.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v6_candidate.png`
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v6.prompt.txt`
- Re-ran the imagegen/image2 workflow for a lighter PDF-scale Figure 1. The v7
  candidate improved visual density but used the wrong Stage 3 target label;
  the v8 candidate corrected that label and was promoted into the ACL draft:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v8.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v7_candidate.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v8_candidate.png`
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v8.prompt.txt`
- Re-ran the imagegen/image2 workflow again after full-PDF visual review. The
  v9 candidate keeps the exact v8 claim-boundary text and `Target: box` label
  while making the four-stage roadmap less dense at paper scale; it was
  promoted and later superseded by v12:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v9.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v9_candidate.png`
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v9.prompt.txt`
- Re-ran the imagegen workflow for a lower-text Figure 1 after another full-PDF
  visual review. The v10 candidate reduced red trajectory confusion but gave
  the NE metric a misleading green-up cue; the v11 candidate removed direction
  arrows but introduced a generated-text typo; the v12 candidate keeps the
  four-stage structure, `Target: box`, purple/green navigation paths, and
  neutral SR/SPL/NE cards with fewer internal labels. It is now the ACL Figure 1
  source:
  - `paper/shared/figures/fig_acl_method_chain_imagegen_v12.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v10_candidate.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v11_candidate.png`
  - `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v12_candidate.png`
  - `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v12.prompt.txt`
- Added a reviewer-facing Discussion paragraph that turns the evidence gates
  into a reusable reporting pattern for converted synthetic-scene benchmarks:
  source asset tree, conversion workspace, matched render sets, target-projection
  QA, prompt/coordinate contracts, material-mechanism bins, and embodied-stack
  smoke gates remain separately reportable artifacts.
- Added main-text visual evidence panels from existing project artifacts:
  - `fig_render_pairs.pdf` for real single-object MDL/noMDL render pairs,
    refreshed to use oblique matched views for better PDF readability;
  - `fig_grscene_qualitative.pdf` for real GRScenes scene-level renders;
  - `fig_render_scene_evidence_wide.png` as the current ACL main-text Figure 2,
    combining the real single-object proxy pairs and GRScenes scene renders into
    one two-column-wide evidence panel;
  - `fig_material_effect_baseline_qualitative.png` was initially refreshed for
    original/noMDL/NVIDIA selected material-effect comparison, then removed from
    the ACL main PDF after the red-material provenance diagnosis showed stale
    original-MDL cells;
  - `fig_internnav_rollout_0036_0066_main3_readable.png` retained in the
    current ACL PDF as selected official KuJiaLe InternNav start/end rollout
    stills and trajectory overlays for reader orientation only.
- Refined the current ACL Figure 2 representative proxy row after page-level
  visual review. The selected `#0011` top-front-right real render pair now uses
  deterministic crop `(140, 40, 780, 720)` in
  `gen_render_scene_evidence_wide.py`, and the displayed sublabel says
  `#0011 cropped top-front-right object view`. This is not image generation and
  not a new experiment; it improves PDF-scale readability of the existing real
  render evidence. The new regression test checks that the crop improves
  minimum pair contrast over the uncropped view.
- Added a deterministic builder for the readable InternNav retained panel:
  - `paper/shared/figures/gen_internnav_main_readable.py`
- Replaced the ACL main-text Fig.3 use of the full-width InternNav panel with
  the deterministic single-column representative panel:
  - `paper/shared/figures/fig_internnav_rollout_0036_0066_column.png`
  The full-width readable panel remains fingerprinted and available as retained
  supplemental/rebuttal evidence, but the main PDF no longer spends a mostly
  blank standalone page on Fig.3.
- Compacted the official-scene performance Table 6 generated by
  `paper/shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py`
  from a dense condition/scenes table into a main-text aggregate metric table:
  `Metric / Original MDL / noMDL`. The CSV keeps aggregate and per-scene rows;
  the LaTeX table reports only the aggregate rows so the ACL main paper remains
  readable.
- Kept the diagnostic appendix source in `paper/shared/sections/appendix.tex`
  for supplemental reuse, but removed it from the current ACL main PDF so the
  manuscript remains a figure-driven main-conference draft rather than a
  diagnostic table packet.
- Extended the ACL integrity fingerprint source set to include the new
  schematic, the real main-text figure assets, and the artifact-provenance
  draft.

## Visual QA

Local clean-room visual review of the generated schematic:

| Asset | Verdict | Evidence | Risk |
| --- | --- | --- | --- |
| `fig_acl_method_chain_imagegen_v1.png` | WARN/PASS for schematic use | The four-stage flow, arrows, VLM grounding block, navigation map, and footer claim boundary are readable and aligned with the intended paper story. | The scene thumbnails inside the schematic are generated illustrations, not empirical render artifacts. The manuscript caption therefore marks the panel as a schematic roadmap and relies on later real artifact figures for empirical evidence. |
| `fig_acl_method_chain_imagegen_v2.png` | PASS for schematic use | The follow-up generated schematic keeps the four-stage chain, improves spacing and local panel balance, and preserves the footer claim boundary. | It is a superseded AI-generated schematic candidate. It must not be treated as measured render, material, VLM, or navigation evidence. |
| `fig_acl_method_chain_imagegen_v3.png` | PASS for schematic use | The superseded generated schematic has clear stage labels, VLM-grounding and InternNav subpanels, and the required footer claim boundary. | It is still an AI-generated schematic. It must not be treated as measured render, material, VLM, or navigation evidence. |
| `candidates/fig_acl_method_chain_imagegen_v4_candidate.png` | PASS/WARN as a backup candidate | The regenerated imagegen/image2 candidate preserves the same four-stage structure and most labels. | It is not used in the ACL PDF because the footer punctuation spacing and target icon are slightly weaker than v3. |
| `candidates/fig_acl_method_chain_imagegen_v5_candidate.png` | PASS/WARN as a backup candidate | The explicit rerun through the imagegen/image2 route preserves the four-stage chain, readable major labels, node mapping, VLM grounding block, navigation map, and footer claim boundary. | It is retained as a backup rather than promoted because v3 remains at least as clean in the integrated PDF and has already passed page-level visual review. |
| `fig_acl_method_chain_imagegen_v6.png` | PASS for schematic use, superseded | The accepted imagegen/image2 rerun keeps the four-stage method chain, improves the source/conversion panel balance, preserves the footer claim boundary, and keeps red restricted to target boxes and the navigation failure path. | It is still AI-generated roadmap art. It must not be treated as measured render, material, VLM, or navigation evidence. It is superseded in the ACL PDF by v8 for PDF-scale readability. |
| `candidates/fig_acl_method_chain_imagegen_v7_candidate.png` | WARN as a backup candidate | The candidate is visually cleaner than v6 and reduces small internal labels. | It is not used because Stage 3 changes the target label to `cabinet`, which drifts from the paper story. |
| `fig_acl_method_chain_imagegen_v8.png` | PASS for schematic use, superseded | The promoted imagegen/image2 rerun keeps the four-stage method chain, preserves the claim-boundary footer, uses less dense internal text at PDF scale, and restores the exact `Target: box` Stage 3 wording. | It is still AI-generated roadmap art. It must not be treated as measured render, material, VLM, or navigation evidence. It is superseded in the ACL PDF by v9 for larger visual blocks. |
| `fig_acl_method_chain_imagegen_v9.png` | PASS for schematic use, superseded | The imagegen/image2 rerun preserves the exact four-stage labels, exact `Target: box`, and exact claim-boundary footer while making the roadmap visually larger and less dense at PDF scale. | It is still AI-generated roadmap art. It must not be treated as measured render, material, VLM, or navigation evidence. It is superseded in the ACL PDF by v12 for lower text density and less red-trajectory confusion. |
| `candidates/fig_acl_method_chain_imagegen_v10_candidate.png` | WARN as a backup candidate | The candidate removes the red failure trajectory and is visually clean. | It is not used because the NE metric card uses a green-up cue, which can mislead because NE is an error metric. |
| `candidates/fig_acl_method_chain_imagegen_v11_candidate.png` | FAIL/WARN as a backup candidate | The candidate fixes the NE arrow issue and keeps neutral metric cards. | It is not used because a small generated text typo appears in the conversion panel. |
| `fig_acl_method_chain_imagegen_v12.png` | PASS for schematic use, superseded | The promoted low-text candidate keeps the four-stage roadmap readable at PDF scale, preserves `Target: box`, uses purple/green navigation paths, and removes misleading metric-direction arrows. | It is still AI-generated roadmap art. It has been superseded by v13, which further reduces microtext density. |
| `fig_acl_method_chain_imagegen_v13.png` | PASS for schematic use, superseded | The promoted v13 candidate keeps the same four-stage method-chain story while making the blocks larger, reducing generated microtext, keeping `Target: box`, using purple/green navigation paths, and leaving SR/SPL/NE as neutral metric tiles. | It is still AI-generated roadmap art. It has been superseded by v14, which removes more generated microtext. |
| `fig_acl_method_chain_imagegen_v14.png` | PASS for schematic use, superseded | The promoted v14 candidate keeps the same four-stage method-chain story, preserves `Target: box`, uses purple/green navigation paths, removes the small VLM sentence, removes the Stage 4 legend text, and leaves SR/SPL/NE as neutral metric tiles. | It is still AI-generated roadmap art. It must not be treated as measured render, material, VLM, or navigation evidence; the caption and ethics disclosure preserve that boundary. |
| `fig_acl_method_chain_imagegen_v15.png` | PASS for schematic use, superseded | The promoted v15 candidate keeps the same four-stage story and exact key labels while improving page-scale balance for the VLM and InternNav blocks. | It is still AI-generated roadmap art and must remain captioned as schematic, not empirical evidence. It is superseded by v16, which removes the footer microtext. |
| `fig_acl_method_chain_imagegen_v16.png` | PASS for schematic use, superseded | The promoted v16 candidate keeps the same low-text four-stage story, preserves `Target: box`, uses purple/green navigation paths, and leaves SR/SPL/NE as neutral metric tiles while removing the v15 footer. | It is still AI-generated roadmap art and must remain captioned as schematic, not empirical evidence. It is superseded by v18, which uses the clearer `VLM Checks` stage title. |
| `fig_acl_method_chain_imagegen_v18.png` | PASS for schematic use | The promoted v18 candidate keeps the low-text four-stage roadmap, preserves `Target: box`, uses `VLM Checks`, keeps SR/SPL/NE as neutral metric tiles, and avoids the v17 wrong-target text. | It is still AI-generated roadmap art and must remain captioned as schematic, not empirical evidence. It supersedes v16 in the current ACL wrapper. |
| `fig_internnav_rollout_0036_0066_main3.png` | WARN for supplemental/rebuttal use | The selected official KuJiaLe rollout content is visible, but the original contact sheet contains large vertical gaps that make the PDF rendering too small. | A compact derivative removed blank bands while preserving the same start/mid/end stills and labels; a later readable derivative is retained outside the current ACL main PDF. |
| `fig_internnav_rollout_0036_0066_main3_readable.png` | PASS/WARN for retained supplemental/rebuttal use | The selected 0036/0066 official rollout rows remain reproducible from the same script and show multiple official start/end cases. | It is no longer the ACL main-text Fig.3 because the full-width float created a mostly blank standalone page after the latest float-order fix. |
| `fig_internnav_rollout_0036_0066_column.png` | PASS/WARN for ACL main-text qualitative orientation | The representative official KuJiaLe start/end rollout panel fits in one ACL column on the Limitations page while still showing first-person frames and trajectory overlays for original/noMDL. | It remains selected qualitative orientation only, not a replacement for the 99-episode paired run. |

The review was performed locally rather than by a delegated independent
subagent, because the current task did not explicitly authorize multi-agent
delegation. The manuscript now avoids using the schematic as experimental
evidence.

Post-build local visual review of the final PDF pages:

| PDF page | Verdict | Evidence | Risk |
| --- | --- | --- | --- |
| 1 / Abstract | PASS | The refreshed 179-word abstract fits on the first page, keeps the title anonymous, and foregrounds the ACL measurement-reliability story. | The abstract is dense but still inside the ACLPUB guidance and does not overflow. |
| 2 / Figure 1 | PASS for schematic use | The four-stage method chain is visible and the caption clearly labels it as a schematic roadmap. | Small internal labels should not be treated as evidence-bearing text. |
| 2 / Introduction contributions | PASS after column-break polish | A follow-up page-level visual pass found that the contribution list was being split across the column top with a mid-sentence orphan. The four-gate paragraph and the first two contribution bullets were tightened, and a deliberate column break now starts `We make four contributions` at the top of the right column. | This is a layout/narrative polish only; it does not change evidence counts or claim boundaries. |
| 3 / Related Work | PASS | The new gap-framing paragraph and revised related-work paragraphs render normally and do not overflow. | None beyond normal ACL two-column density. |
| 4 / Method opening | PASS after text polish | A later full-page visual pass found the first Method paragraph over-stretched by the long `MDL-to-UsdPreviewSurface` token; the opening sentence was rewritten without changing the method claim, and the re-rendered page now has normal spacing. | Normal ACL two-column hyphenation remains. |
| 5 / VLM stress prose | PASS after text polish | The same pass found the prose token `expanded30` rendered as an opaque dataset identifier in running text; it is now written as `expanded 30-pair stress set` while table/artifact identifiers remain unchanged. | The table identifiers still use `expanded30` where they are artifact names. |
| 6 / Figure 2 | PASS after representative-pair compaction, proxy-cell relayout, and cropped proxy detail | A later visual pass found that the eight-cell Figure 2 still read like thumbnails at PDF scale. The generator now uses the same empirical render sources but compacts the panel to one representative proxy before/after pair and one representative GRScenes before/after pair. The latest 2026-05-28 pass tightens the existing real `#0011` top-front-right proxy crop to expose drawer handles, front lines, and side curvature more clearly at PDF scale; `tests/test_render_scene_evidence_figure.py` now guards a selected-proxy minimum contrast threshold. | The figure is qualitative orientation only; quantitative claims remain table-bound. The crop is disclosed in the sublabel and caption so readers do not treat it as an uncropped full-object statistic. |
| 5-6 / Figure 2 caption and section flow | PASS after text polish and proxy-row sample refresh | After adding the cropped-view disclosure, the caption was shortened and the preceding VLM paragraph was compressed so Section 4.3 no longer leaves an orphaned sentence fragment on page 6. The latest pass keeps the same raw proxy-render pool, uses the `#0011` top-front-right proxy pair in the representative object row, and captions it as a cropped single-object proxy detail pair. | The top proxy objects are still white furniture renders and remain orientation-only; the figure should not be read as proof of preservation. |
| 6 / Material-effect section | PASS after Fig.3 mitigation and 2026-05-28 clean rerender | The material-effect contact sheet is no longer present in the rendered main paper. The selected covered-bin contact sheet now passes clean original-MDL provenance and is retained for supplemental/rebuttal inspection, while the section still uses Table 5 as the main claim-boundary artifact. | The material-effect result is table-bounded; the contact sheet should not be promoted beyond selected qualitative evidence. |
| Main-to-Limitations boundary | PASS/WARN | The Results-to-Discussion `\FloatBarrier` keeps Tables 5/6 before Discussion, while the Limitations-to-Ethics `\FloatBarrier` now drains the single-column Fig.3 before Ethical Considerations and References. | The pre-upload guard rejects both the float-only material-table regression and Fig.3 after References. |
| 8 / Table 6 official-scene performance | PASS after table-density polish | Visual review first found that the wide official-scene performance table was too small, then that a readable three-column version overflowed into the right column. The generated LaTeX table now uses a compact aggregate metric layout with fixed wrapping columns, while the machine-readable CSV keeps per-scene detail. | The table supports load/render stability only; it still omits an NVIDIA official-scene performance row until official-scene NVIDIA conversions exist and pass smoke gates. |
| 8 / Discussion and Conclusion spacing | PASS after ragged-bottom layout fix | A 2026-05-28 pure-visual page review found that the Discussion page had stretched vertical gaps caused by bottom alignment on a short text page. The ACL wrapper now uses `\raggedbottom`, and the final rendered page 8 has normal paragraph spacing. | This is a layout-only change; it does not affect claims, evidence numbers, figures, tables, or page count. |
| 9 / Figure 3 | PASS/WARN after single-column relayout | A follow-up visual pass found that the full-width Fig.3 used a mostly blank standalone page in the 12-page candidate. The ACL main PDF now uses the deterministic single-column representative panel on the Limitations page; the caption remains claim-bounded and the page flows directly into Ethical Considerations. | The selected rollout panel is qualitative orientation only; it should not be read as a population-level InternNav result. |
| 9-11 / Ethical Considerations and References | PASS after single-column Fig.3 relayout, v14 schematic refresh, ragged-bottom pass, and checklist anchor sync | The 2026-05-28 03:51 gate shows an 11-page PDF: Limitations, Fig.3, Ethical Considerations, and the start of References share page 9. The staged and build PDFs are identical with SHA-256 `1331675b11801dca013866facc005390c54e3f8e77234fb62d23b318fa137312`; page-raster hashes are unchanged from the full visual-review pass. | The OpenReview checklist/page anchors now record References starting on page 9; recheck after any further float edits. |

## Claim Boundary

Allowed:

- Use Figure 1 as a schematic overview of the evidence chain.
- Use real render, material-effect, and trajectory panels as selected
  qualitative evidence.
- Use tables and manifests for quantitative claims.

Disallowed:

- Treat generated Figure 1 thumbnails as real render evidence.
- Treat retained selected InternNav rollouts as a replacement for the 99-episode paired
  metric run.
- Promote selected material panels into population-level NVIDIA failure rates
  or all-effect visual fidelity claims.

## Narrative Follow-Up

The follow-up writing pass tightened the ACL-facing story without changing any
experimental numbers:

- `sections/related.tex` now opens with the paper's intersectional gap:
  language grounding, embodied simulation, and synthetic rendering all depend
  on rendered 3D assets, but asset conversion is usually treated as
  infrastructure rather than an experimental intervention.
- `sections/discussion.tex` now frames the contribution as a measurement
  protocol rather than a ConvertAsset-vs-NVIDIA leaderboard.
- `sections/conclusion.tex` now closes on the procedural lesson: material
  conversion should be treated as a controlled perturbation before downstream
  VLM or embodied robustness claims are made.
- `sections/abstract.tex` and `OPENREVIEW_METADATA_PACKET.md` now use a
  179-word abstract that foregrounds the ACL measurement-reliability story and
  keeps the same numeric evidence boundaries.

## Venue-Neutral Main-Paper Polish

The final writing polish removes internal venue-wrapper wording from the
manuscript and metadata abstract while preserving the same claim boundaries and
numbers:

- `sections/abstract.tex` now describes the output as a claim-bounded
  evaluation protocol rather than an ACL protocol.
- `sections/method.tex` and `sections/results.tex` no longer call gates or
  claims "ACL-facing" inside the main paper.
- `sections/ethical-considerations.tex` now gives venue-neutral provenance and
  license guidance for any submission using converted synthetic scenes.
- `OPENREVIEW_METADATA_PACKET.md` mirrors the abstract text and avoids calling
  the current PDF "ACL-facing" in copy-ready metadata.
- `check_claim_boundaries.py` now rejects `ACL-facing`, `main ACL claim`,
  `ACL protocol`, `ACL/ARR claim boundary`, and `Any ACL submission` wording if
  it returns to checked manuscript/metadata text or table captions.
- `tab_acl_evidence_gate_registry.tex` now describes Table 1 as the paper's
  claim boundary rather than an ACL/ARR wrapper artifact.

## Image-Generation Route Note

The method-chain schematic currently used by the ACL draft is
`paper/shared/figures/fig_acl_method_chain_imagegen_v18.png`. It was produced
through the local image-generation assistant workflow using the preserved prompt
at
`paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v18.prompt.txt`
and is used only as a schematic roadmap. The manuscript and provenance notes
therefore claim a project-local imagegen schematic, not empirical render
evidence.

On 2026-05-27, further imagegen/image2 candidates were generated and saved
under:

- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v4_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v5_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v6_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v7_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v8_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v9_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v10_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v11_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v12_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v13_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v14_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v15_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v16_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v17_candidate.png`
- `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v18_candidate.png`

Their prompts are preserved at:

- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v4_candidate.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v5_candidate.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v6.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v8.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v9.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v12.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v13.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v14.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v15.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v16.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v17.prompt.txt`
- `paper/shared/figures/prompts/fig_acl_method_chain_gpt_image2_v18.prompt.txt`

The v4/v5/v7/v8/v10/v11 images are retained as backup candidates only. v12 is
also retained as a superseded acceptable backup. v13/v14/v15 are retained as
previous accepted low-text backups. v16 is retained as the previous accepted
low-text schematic, v17 is rejected because the target label reads
`Target: boy`, and the ACL draft now uses v18 because it keeps the conservative
schematic role, preserves `Target: box`, uses the clearer `VLM Checks` title,
keeps neutral metric cards, and preserves VLM/InternNav block balance at PDF
scale.

A follow-up reviewer-risk pass strengthened the Discussion by making the paper's
main transferable contribution explicit: the evidence gates form a reporting
pattern for benchmark builders, not merely a project-local audit.

The main manuscript now also contains an explicit AI-assistance disclosure in
`sections/ethical-considerations.tex`: AI coding, writing, and image-generation
assistants were used for implementation/manuscript support and the schematic
roadmap, while quantitative claims, citations, reported artifacts, and empirical
visual panels remain checked against repository evidence and cited sources.

## Four-Gate Narrative Alignment

A follow-up ARS-style devil's-advocate pass found a story-consistency weakness:
the Introduction described the evidence base as two layers even though the
current paper, Figure 1, Method, Results, and claim registry are organized as
four separate evidence gates. This made the material-effect/NVIDIA audit and
InternNav sanity evidence read like add-ons rather than planned parts of the ACL
argument.

`paper/venues/acl27/sections/intro.tex` now introduces the same four gates that
the rest of the paper uses:

1. single-object proxy similarity,
2. GRScenes VLM grounding,
3. selected material-effect / NVIDIA-baseline risk audit,
4. scoped KuJiaLe InternNav embodied-stack sanity.

The rewritten paragraph also repeats the claim-boundary rule in plain text: no
proxy score, selected visual panel, or navigation sanity run should stand in for
broad downstream robustness. Local PDF review of pages 1--2 confirmed that the
new paragraph did not break the Figure 1 layout or increase the 11-page profile.

## Verification

After the Fig.3 red-material mitigation and final text integration pass:

- `python paper/venues/acl27/scripts/run_preupload_gate.py` passed the full
  repository-side rehearsal: claim, policy, metadata, checklist, citation,
  evidence-number, 53-source fingerprint, final-blocker, goal-completion,
  69-test focused pytest, clean PDF build, LaTeX log scan, packet staging,
  private-token scan, acknowledgment scan, PDF profile, and `pdftotext` marker
  checks. The latest staged candidate remains 11 A4 pages, PDF 1.5, and
  3,364,751 bytes.
- A later layout-polish pass added a pre-upload guard against a float-only
  material-table page before Limitations and replaced the broad pre-Limitations
  `\clearpage` with targeted `\newpage` breaks. A subsequent Figure 2 proxy-row
  readability pass replaced the nearly blank `#0004` display example with the
  more legible `#0023` pair from the same raw proxy-render pool, added a
  focused pytest contrast guard, and rebuilt the staged ACL candidate as 11 A4
  pages, PDF 1.5, and 3,330,780 bytes. A later v8 method-chain imagegen pass
  rebuilt and staged the ACL candidate as 11 A4 pages, PDF 1.5, and 3,361,922
  bytes. After the follow-up reviewer-risk Discussion paragraph, the full gate
  was rerun again and staged the candidate as 11 A4 pages, PDF 1.5, and
  3,362,820 bytes. After the four-gate Introduction alignment, the full gate
  passed again and staged the then-current candidate as 11 A4 pages, PDF 1.5,
  and 3,364,751 bytes. It kept the accepted imagegen/image2 v8 method-chain
  schematic on page 2, the real render/scene evidence panel on page 6, and the
  selected qualitative InternNav rollout panel as Figure 3 on page 9.
- After the Table 6 density polish, the full gate passed again with the compact
  aggregate official-scene performance table: claim/policy/metadata/checklist,
  citation, evidence-number, 53-source fingerprint, final-blocker,
  goal-completion, 69 focused pytest tests, clean build, LaTeX log scan,
  staging, private-token and acknowledgment scans, PDF profile, and ordered
  `pdftotext` checks. The staged candidate remains 11 A4 pages, PDF 1.5, and
  3,364,227 bytes. Local page-8 visual review confirmed that Table 6 no longer
  spills into the Limitations column.
- After the reference-layout pull-up, the full gate passed again with the same
  claim/policy/metadata/checklist, citation, evidence-number, 53-source
  fingerprint, final-blocker, goal-completion, clean build, LaTeX log scan,
  staging, private-token and acknowledgment scans, PDF profile, and ordered
  `pdftotext` checks, now with 70 focused pytest tests. The staged candidate is
  10 A4 pages, PDF 1.5, and 3,363,874 bytes. Local page-9 visual review
  confirmed that Ethical Considerations and References share the page without
  overlap after the forced post-ethics page break was removed.
- A later Introduction visual-polish pass tightened the four-gate paragraph and
  first two contribution bullets and inserted a deliberate column break before
  the contribution list. The full pre-upload gate passed again with 70 focused
  pytest tests, the 53-source fingerprint, clean build, staging, scans, PDF
  profile, and `pdftotext` checks. The staged candidate remains 10 A4 pages, PDF
  1.5, and 3,363,532 bytes; page-2 visual review confirmed that the
  contribution list no longer starts the right column with a mid-sentence
  orphan, and page 3 still starts Related Work cleanly.
- The stale `fig_material_effect_baseline_qualitative.png` contact sheet is no
  longer in the ACL main text and is no longer part of the final-integrity
  source set. The material-effect claim is table-bounded until clean
  original-MDL rerenders or replacement cases exist.
- A follow-up Fig.3 visual-polish pass keeps the same selected official
  InternNav stills but recolors the source-red agent trajectory/action overlay
  to purple during panel composition. The source stills remain unchanged; the
  generated report records `23118` recolored source-red overlay pixels in the
  main panel and `8116` in the column panel. The ACL caption now says the
  purple executed paths/action arrows are orientation overlays with color
  changed for readability, which reduces confusion with the historical
  red-material fallback issue. The subsequent full pre-upload gate passed again
  with 70 focused pytest tests, the 53-source fingerprint, clean build, staging,
  scans, PDF profile, and `pdftotext` checks. The staged candidate remains 10
  A4 pages, PDF 1.5, and 3,363,508 bytes.
- A follow-up page-8 layout pass changed the compact official-scene performance
  Table 6 from a single-column float to a two-column `table*` in both the
  generated table and the official-scene closure generator, and compressed
  Conclusion to a single claim-boundary paragraph. The full pre-upload gate
  passed again with 70 focused pytest tests, the 53-source fingerprint, clean
  build, staging, scans, PDF profile, and `pdftotext` checks. The staged
  candidate remains 10 A4 pages, PDF 1.5, and 3,363,281 bytes. Local rendered
  page-8/page-9 review confirmed that Table 6, Limitations, and the selected
  InternNav Figure 3 remain readable without overlap.
- A follow-up imagegen/image2 pass generated
  `fig_acl_method_chain_imagegen_v9.png` from the preserved v9 prompt and moved
  the ACL Figure 1 include from v8 to v9. Visual review accepted v9 because it
  keeps the exact `Target: box` and claim-boundary footer while making the
  four-stage roadmap larger and less dense at PDF scale. The schematic remains
  non-evidence roadmap art; empirical claims still come from the recorded
  render, VLM, material, and InternNav artifacts.
- The subsequent full pre-upload gate passed again with 70 focused pytest
  tests, the 53-source fingerprint, clean build, staging, scans, PDF profile,
  and `pdftotext` checks. The staged candidate remains 10 A4 pages, PDF 1.5,
  and 3,313,612 bytes. Local rendered page-2 review from the staged PDF
  confirmed that Figure 1 v9 is readable and does not disturb the contribution
  layout.
- The claim-boundary checker rejects reintroducing the stale material-effect
  panel, and the integrity-fingerprint test asserts that the stale PNG remains
  outside the source set.
- Local rendered-PDF visual checks of pages 5, 6, and 10 confirmed the
  mitigation visually: page 5 is VLM/material text only, page 6 contains the
  render/scene evidence panel plus table-bounded material-effect prose, and
  page 9 contains the selected InternNav Figure 3.
- A final staged-PDF visual spot check after the reviewer-risk Discussion pass
  rendered pages 2, 6, 7, and 9 from
  `paper/submissions/acl27_arr_candidate_20260526/main.pdf`. Page 2 keeps the
  accepted imagegen/image2 method-chain schematic readable, page 6 keeps the
  actual render/scene panel above the tables without overlap, page 7 keeps the
  new reporting-pattern paragraph readable before Conclusion, and page 9 keeps
  the selected InternNav Figure 3 as trajectory-overlay evidence rather than
  red-material fallback.
- A follow-up local visual pass on the current ACL build found that Figure 2
  still looked like a thumbnail contact sheet even though it was evidence-safe.
  The empirical figure was therefore regenerated deterministically, not with
  image generation: it now shows one representative proxy original/noMDL pair
  and one representative GRScenes original/noMDL pair using the same recorded
  render sources. A first oversized version improved readability but grew the
  PDF to 11 pages and was rejected. The accepted compact version rebuilds to a
  10-page A4 PDF. A subsequent pure-visual review still found the white proxy
  row too strip-like at PDF scale, so the generator now uses a narrower proxy
  cell with the same raw `#0023` proxy pair and keeps the GRScenes row full
  width. The current local build is a 10-page A4 PDF
  (`paper/venues/acl27/build/main.pdf`, 3,471,360 bytes), and rendered page 6
  shows the representative render pairs without overlap.
- The subsequent full pre-upload gate passed with the compact Figure 2 and the
  refined PDF-text section check: focused pytest reports 71 tests passing, the
  clean ACL build/staging step produces a 10-page A4 PDF 1.5, and staged
  `main.pdf` is 3,519,802 bytes. The section-order validator was refined after
  it falsely classified a page containing Tables 5/6 plus Discussion body text
  as a float-only pre-Limitations page.
- After the proxy-cell relayout, the full pre-upload gate passed again:
  focused pytest reports 72 tests passing, the clean ACL build/staging step
  produces a 10-page A4 PDF 1.5, and staged `main.pdf` is 3,471,360 bytes.
  Rendered page 6 shows the updated empirical Figure 2 without overlap; the
  change uses deterministic recorded render sources, not image generation.
- A subsequent local render review still found the top proxy row visually weak
  because the selected white front-view crop looked like a low-detail strip at
  PDF scale. A TDD pass raised the selected-proxy contrast gate from `10.0` to
  `13.0`, confirmed the old selected display failed (`12.32` minimum grayscale
  standard deviation), then switched the representative proxy display to the
  same `#0023` asset's recorded full-object back view
  (`A_back.png`/`B_back.png`). This is still deterministic empirical render
  evidence, not image generation or a new experiment. The rebuilt local ACL PDF
  remains 10 A4 pages, PDF 1.5, and 3,487,597 bytes; rendered page 6 shows the
  proxy pair, GRScenes pair, caption, and Table 2 without overlap.
- The subsequent full pre-upload gate passed again after this Figure 2 sample
  refresh: focused pytest reports 72 tests passing, final-integrity fingerprint
  remains `ok=true` with 53 protected sources, clean build/staging completed,
  and the staged candidate at
  `paper/submissions/acl27_arr_candidate_20260526/main.pdf` is a 10-page A4 PDF
  1.5 file of 3,487,597 bytes. A rendered staged page-6 spot check shows the
  refreshed Figure 2 and following table without overlap.
- A subsequent local rendered-PDF review found that the #0023 back-view proxy
  still looked like a low-detail gray slab when integrated into page 6. A TDD
  pass replaced the selected-proxy contrast check with a front-detail
  edge-density guard that rejects back-only representative views, then switched
  the representative proxy row to the recorded `#0011` front-view original/noMDL
  pair (`A_front.png`/`B_front.png`) from the same empirical render pool. This
  is still deterministic render evidence, not image generation or a new
  experiment. The full pre-upload gate passed again with 72 focused pytest
  tests, the 53-source fingerprint, clean build/staging, scans, PDF profile
  checks, and ordered text-section checks. The current build and staged
  candidate are identical 10-page A4 PDF 1.5 files of 3,493,873 bytes, and
  rendered page 6 shows the front drawer/handle details without overlap.
- A follow-up pure visual review still found the flat front-view row usable but
  weaker than an angled object render. The Figure 2 proxy row now uses the
  recorded `#0011` top-front-right original/noMDL pair
  (`A_top_front_right.png`/`B_top_front_right.png`) from the same empirical
  render pool. The guard was updated to require a front/front-angled selected
  path plus minimum edge density and contrast, because the earlier single edge
  threshold produced a false negative on smooth white angled geometry. The full
  pre-upload gate passed again with 72 focused pytest tests, the 53-source
  fingerprint, clean build/staging, scans, PDF profile checks, and ordered
  text-section checks. The current build and staged candidate are identical
  10-page A4 PDF 1.5 files of 3,514,678 bytes, and rendered page 6 shows the
  angled proxy object, Figure 2 caption, and Table 2 without overlap.
- A subsequent local pure-visual review rendered the same 10-page candidate at
  160 DPI and inspected the full-page contact sheet plus pages 6, 8, and 9. No
  new figure or layout blocker was found: Figure 2's angled proxy row remains
  more legible than the prior flat/front row, Tables 5/6 and the Limitations
  transition remain readable, and Figure 3 still shows the selected InternNav
  rollout panel with purple/green orientation overlays rather than the retired
  red material-effect contact sheet. No imagegen rerun was promoted in this
  pass because the accepted v9 method-chain schematic remains adequate and the
  remaining inspected figures are empirical render/navigation evidence, not
  generated art.
- A final label-precision pass made the Figure 2 proxy-cell sublabel match the
  selected camera direction: `#0011 full object view` became
  `#0011 top-front-right object view`. This is a deterministic
  figure-generator/test update over the same empirical render files, not image
  generation and not a new experiment. The refreshed full pre-upload gate passed
  with 73 focused pytest tests, the 53-source fingerprint, clean build/staging,
  packet scans, PDF profile checks, and ordered text-section checks. The build
  and staged candidate are identical 10-page A4 PDF 1.5 files of 3,515,110 bytes
  with SHA-256
  `2800402b662904faf83862cd1f5fd1374e9d81fa6bdd8768f72e0a59458fa794`. A rendered
  staged page-6 spot check shows the angled proxy object, Figure 2 caption, and
  Table 2 without overlap.
- A later local visual review found a typography issue in the page-4 Claim
  Registry paragraph: an inline monospace evidence path produced visibly
  stretched spacing in the narrow ACL column. The method text now says
  "project evidence registry" instead of printing the path inline, and
  `tests/test_paper_layout.py` guards against reintroducing the narrow-column
  `\texttt{paper/shared/evidence}` path. The same pass rechecked the Fig.3
  red-material concern: current Figure 3 is still the selected InternNav panel,
  while the retired material-effect contact sheet remains blocked by clean
  provenance. No imagegen rerun was promoted because the accepted v9 schematic
  remains adequate and Fig.2/Fig.3 are empirical render/navigation evidence.
  The refreshed full pre-upload gate passed with 74 focused pytest tests, the
  53-source fingerprint, clean build/staging, packet scans, PDF profile checks,
  and ordered text-section checks. The build and staged candidate are identical
  10-page A4 PDF 1.5 files of 3,513,952 bytes with SHA-256
  `81acd09574094b915097cc23fa8687f7822ed5dcd976f9d0ea9587faca2a8177`.
- A subsequent page-6 visual pass found that the same white `#0011`
  top-front-right proxy object was still a little faint at PDF scale. The
  generator now applies crop `(140, 40, 780, 720)` to the existing real
  Original MDL/noMDL render pair, exposing the drawer handles, front lines, and
  side curvature while preserving the empirical render source. The sublabel is
  now `#0011 cropped top-front-right object view`, and
  `tests/test_render_scene_evidence_figure.py` checks that the crop improves
  minimum pair contrast over the uncropped view. The refreshed full pre-upload
  gate passed with 75 focused pytest tests, the 53-source fingerprint, clean
  build/staging, packet scans, PDF profile checks, and ordered text-section
  checks. The build and staged candidate are identical 10-page A4 PDF 1.5 files
  of 3,553,091 bytes with SHA-256
  `7fed84db45e19f2e2ed56a67452d27ea04d0e4ffcf9a582e6a591a9e254163fe`.
- A later imagegen plus visual-review iteration replaced the accepted Figure 1
  schematic with the lower-text v12 candidate. v10 was rejected because the NE
  metric card visually implied "up is good"; v11 was rejected because of a
  generated-text typo. v12 was promoted because the rendered page-2 PDF keeps
  the four-stage story readable, removes red trajectory cues, and uses neutral
  SR/SPL/NE metric cards while remaining clearly captioned as schematic
  roadmap art. The refreshed full pre-upload gate passed with 76 focused pytest
  tests, the 53-source fingerprint, clean build/staging, packet scans, PDF
  profile checks, and ordered text-section checks. The build and staged
  candidate are identical 10-page A4 PDF 1.5 files of 3,480,649 bytes with
  SHA-256 `dae622146a5e85805db6284dd8f868f44386eee8f37b567bcb96d17ff9bbfbde`.
- A 2026-05-28 local pure-visual review of the current 11-page PDF found no
  blank pages, overlap, or Fig.1/Fig.3 blocker, but Figure 2's white proxy
  object still read faintly at page scale. A TDD pass added a selected-proxy
  minimum-contrast guard, observed it fail on the existing crop, then tightened
  the same real `#0011` top-front-right crop to `(250, 80, 730, 650)`. The
  generator and caption now disclose the panel as a cropped single-object proxy
  detail pair. This is deterministic display cropping over existing real render
  evidence, not image generation and not a new experiment. The refreshed full
  pre-upload gate passed with 81 focused pytest tests, the 53-source
  fingerprint, clean build/staging, packet scans, PDF profile checks, and
  ordered text-section checks. The build and staged candidate are identical
  11-page A4 PDF 1.5 files of 3,124,396 bytes with SHA-256
  `eaf9fcdeb78f0998ed19cb6090e03b412a078064ed3fb46e20d47799d5fa5464`.
- A follow-up 2026-05-28 local pure-visual review rendered the same 11-page
  staged PDF as a page contact sheet. It found no new imagegen, empirical
  render, navigation-panel, overlap, blank-page, or red-material blocker:
  Figure 1 remained readable as schematic roadmap art, Figure 2 reflected the
  tighter real-render crop, Figure 3 remained the selected InternNav panel, and
  the remaining table-dense page was accepted as a result-float page rather
  than a claim or layout failure. No new imagegen candidate was promoted in this
  pass.
- A later 2026-05-28 evidence-cleanup pass rerendered the four selected
  material-effect covered-bin original/noMDL pairs from the repaired MDL asset
  tree, regenerated `qualitative_render_manifest.json` and
  `fig_material_effect_baseline_qualitative.png`, and cleared the
  clean-provenance gate: 4 selected cases, 4 checked Original MDL logs, and 0
  original-MDL error signals. Local pure-visual review of the regenerated
  contact sheet found no red fallback in the Original MDL cells, while NVIDIA
  rows remain visibly lower-fidelity in places such as clock/backpack. The ACL
  main-paper claim remains table-bounded.
- A subsequent 2026-05-28 imagegen plus pure-visual iteration generated
  `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v13_candidate.png`
  and promoted it to
  `paper/shared/figures/fig_acl_method_chain_imagegen_v13.png`. Compared with
  v12, v13 keeps the same four-stage story but uses larger blocks and fewer
  generated micro-labels. Page-2 PDF visual review accepted it for schematic
  use only; the durable review record is
  `paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v13_visual_review_20260528.json`.
- A subsequent 2026-05-28 imagegen plus pure-visual iteration generated
  `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v14_candidate.png`
  and promoted it to
  `paper/shared/figures/fig_acl_method_chain_imagegen_v14.png`. Compared with
  v13, v14 keeps the same four-stage story but removes the small VLM sentence
  and the Stage 4 legend text. Page-2 PDF visual review accepted it for
  schematic use only; the durable review record is
  `paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v14_visual_review_20260528.json`.
  A follow-up full-PDF pure-visual review found stretched vertical spacing on
  page 8; adding `\raggedbottom` to the ACL preamble fixed the Discussion page
  without changing page count, claims, figures, or evidence numbers.
- A subsequent 2026-05-28 imagegen plus pure-visual iteration generated
  `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v15_candidate.png`
  and promoted it to
  `paper/shared/figures/fig_acl_method_chain_imagegen_v15.png`. Compared with
  v14, v15 keeps the same low-text four-stage story and exact key labels while
  improving page-scale balance for the VLM and InternNav blocks. Page-2 PDF
  visual review accepted it for schematic use only; the durable review record
  is
  `paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v15_visual_review_20260528.json`.
  The final full-review record is
  `paper/shared/evidence/raw/acl27_visual_review/full_pdf_visual_review_20260528.json`.
- A follow-up 2026-05-28 imagegen plus pure-visual iteration generated
  `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v16_candidate.png`
  and promoted it to
  `paper/shared/figures/fig_acl_method_chain_imagegen_v16.png`. Compared with
  v15, v16 keeps the same low-text four-stage story while removing the footer
  and relying on the caption for the schematic/empirical boundary. Page-2 PDF
  visual review accepted it for schematic use only; the durable review record
  is
  `paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v16_visual_review_20260528.json`.
- A later 2026-05-28 imagegen plus local visual-review iteration rejected v17
  for wrong target text, then promoted v18:
  `paper/shared/figures/candidates/fig_acl_method_chain_imagegen_v18_candidate.png`
  to `paper/shared/figures/fig_acl_method_chain_imagegen_v18.png`. Compared
  with v16, v18 keeps the same low-text roadmap while using the clearer
  `VLM Checks` title and preserving `Target: box`. The durable review record
  is
  `paper/shared/evidence/raw/acl27_visual_review/figure1_imagegen_v18_visual_review_20260528.json`.
  The main text therefore continues to use Table 5 as the claim-boundary artifact,
  but the panel is now safe for selected supplemental/rebuttal inspection if
  author/legal media gates allow it. `check_claim_boundaries.py` now permits
  this material-effect panel only when the clean-provenance gate is true.

## Author-Gate Handoff

After the latest complete pre-upload gate, the ignored private author worksheet
was refreshed with:

```bash
python paper/venues/acl27/scripts/prefill_author_gate.py --apply --overwrite
```

The command filled only the repo-verifiable final-evidence rows: clean build
command/timestamp, PDF profile, citation/reference scan, staged packet path,
staged file list, private-token scan, acknowledgment scan, and ordered section
text scan. The latest 2026-05-28 refresh changed the same repo-verifiable
fields for the `bafb5b...` staged packet. It did not fill author identities,
route choice, OpenReview profile readiness, OpenReview form-copy approval,
runtime/AI/license approval, optional-media decision, or final upload decision.
`check_author_gate.py` still reports 19 TODO fields, all human-only, while
confirming that the local worksheet is ignored and untracked.
