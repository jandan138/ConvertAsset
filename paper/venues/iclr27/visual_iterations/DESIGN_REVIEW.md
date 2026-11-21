# ICLR reference-led visual review — 2026-09-15

## Design objective

Preserve the existing paper structure and measured evidence while making the five main figures more readable and visually coherent at publication size. Use existing scene images, predictions, counts and recorded endings. No new experiments or generated scene imagery.

## Reference grammar

Reference inspection notes were supplied by the lead from the original PDF pages; the panel author also inspected VIMA Fig. 4 and RoboPoint Fig. 3. Page numbers below are one-based PDF pages.

| Reference | Figures | Adopt | Do not copy |
| --- | --- | --- | --- |
| [VIMA, ICML 2023](https://proceedings.mlr.press/v202/jiang23b/jiang23b.pdf) | Fig. 1, p. 2; Fig. 4, p. 5 | Image-to-text balance, repeated panel rhythm, aligned small multiples and restrained legends | Task-specific colors, unrelated plots or source-specific layout |
| [RoboPoint, CoRL 2024 / proceedings 2025](https://proceedings.mlr.press/v270/yuan25c.html) | Fig. 3, p. 6; Fig. 6, p. 8 | Place queries, predicted points and target outlines directly beside real scenes | Dense multi-label color systems irrelevant to this dataset |
| [Molmo/PixMo, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Deitke_Molmo_and_PixMo_Open_Weights_and_Open_Data_for_State-of-the-Art_CVPR_2025_paper.pdf) | Fig. 1, p. 2 | Spatial grouping, semantic color and image-led examples | Decorative colored cards and production-oriented text |

External figures are references only. No external figure images are bundled into the manuscript assets.

## Iteration ledger

| Round | Saved artifacts | Decision and revision |
| --- | --- | --- |
| 0 | `round0/`: previous PNGs, generator sources, PDF and review snapshot | Preserve the comparison baseline before editing |
| 1 | `round1/`: balanced / detail / compact in SVG, PDF and PNG | Explore hero composition with identical underlying evidence |
| 2 | `panel_work/round2/`: four panels, geometry and crops | Align intervention details, protocol columns, navigation transitions and recorded image/map halves |
| 3 | `round3/`: six PNGs, source snapshot, crop and geometry records | Independent review ranked balanced above compact above detail; increase unit-mark visibility, clarify common branch stem and crop legend, distinguish changed-task count from net success change |
| 4 | `round4/`, `iterations.json`, final manuscript pages and `VISUAL_REVIEW.json` | All five main figures improved against Round 0 and passed actual-page comparison; preserve figure size while allowing conclusion text to fill page 7 |

## Figure decisions

- **Overview:** balanced keeps the scene pair large enough to carry the figure. An explicit `(190,50,455,405)` detail crop enlarges measured pointing coordinates. Original and converted predictions share a labeled original-image reference. The branch lines denote two evaluation settings, not causal mediation. All 99 navigation pairs remain represented.
- **Interventions:** a complete-canvas strip locates the matched `(120,25,480,415)` enlarged region in all four conditions. A separate green target outline avoids confusing the zoom boundary with the ground-truth box. No new sample is introduced by the zoom.
- **Protocol:** both matrices spell out Normalized / Pixels and align Text / JSON subcolumns. Numeric output coverage and hit-rate change retain separate meanings.
- **Navigation:** opposing loss/gain bars expose cancellation; 30/99 changed and -4.0 pp net change remain separately labeled. Per-scene pairs use the same condition colors as all other figures.
- **Recorded endings:** split each existing 1024×512 source still at integer x=512 into observation/map squares, retaining the pixels and scene aspect ratio. Three episodes share column baselines. The source is an independent qualitative rerun, not the main-run score record.

Typography uses explicitly registered Liberation Sans with DejaVu Sans fallback. Original is blue; converted is orange; loss and gain use separate semantic colors. Output formats are SVG, PDF and 360 dpi PNG. Four generator hashes and crop provenance are carried by the asset records.

## Verification

Final validation confirmed by the lead:

- Build/check PASS; 97 tests passed in 18.55 s. Strict overview spec: zero errors and zero warnings.
- All source, output and generator hashes match; six SVGs are self-contained and inert; 17 explicit native-image crops are within bounds; all figure labels are at least 7 pt.
- Independent comparison ranked balanced > compact > detail and found all five final main figures improved against Round 0. The lead inspected all 13 final pages; final review is bound in `../VISUAL_REVIEW.json`, with renders in `../build/visual_polish_final/`.
- Main text and all main figures end on page 8. The last layout pass changed the trajectory `H` placement to `!t`, keeping the float barrier after the conclusion and before the main-end marker/statements. Figure 5 remains counted main content on page 8. Figure and text sizes were retained while conclusion text filled the large page-7 blank.
- Staging PASS; candidate PDF and build PDF are byte-identical. Final PDF SHA-256: `e6580c4d6b86704f9fad2e747a623c7fe628282e6f3058f8d4287145fff4c0f5`.
- Existing analysis SHA-256 is unchanged: `dea5ca75206bdaed906db00876357db0ff8c82558c1818f3e3977d7766e0babc`.

`iterations.json` records the four-phase process. `comparison/all_figures.pdf` provides five pages of before/after comparisons, accompanied by individual PNGs and source hashes. Citation contexts were rebound only (14 keys / 17 contexts); strict `REVIEW_REQUIRED` remains unchanged, with no new source research or attestations. No experiments, commits, pushes or uploads were performed.

See [the implementation record](../../../../docs/records/2026-09-15-iclr-reference-led-figure-polish.md) for build commands, final validation and delivery status.
