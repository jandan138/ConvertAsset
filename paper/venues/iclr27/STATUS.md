# ICLR 2027 preparation status

## Active story
**Same Scene, Different Decisions: Material Sensitivity in Embodied Models.**

The main text follows material input changes, query-conditioned visual localization,
image-region dependence and episode-level navigation turnover. Navigation is a main
experiment, with all 99 paired records and a retained trajectory figure.

## Current integration — appendix render repair

Figures 14 and 15 (pages 24–25) now use five newly rendered Original/Converted
pairs after the existing MDL dependency repair. All ten captures have zero
material compiler/loading error counts and passed visual inspection. The
versioned source is `appendix_rerender_v1/manifest.json`; figure generation and
submission checks reject old red captures, incomplete diagnostics and unreviewed
replacements. Appendix E explains that these are qualitative rerenders and that
historical scores remain attached to their recorded inputs.

- `make -C paper iclr27-stage`: passed, zero failures; 9 main-text pages,
  33 total pages, 44,438,198-byte staged PDF.
- Focused source/layout regression: 101 tests passed.
- Historical images/prediction sources (354 files), runtime sources (1,694 files),
  numerical tables/CSV and Figure 1 sources (15 files) remain unchanged.
- Figure 1 PNG is byte-identical; the other 13 appendix plates are unchanged.
- Final page review: `visual_iterations/appendix_repair_20260922/pdf_review.json`.
- No model inference, OpenReview upload or git commit was performed.

## Figure 1 integration — 2026-09-22

Figure 1 is now the three-panel real-evidence hero from the fig1-0922 pipeline
(`paper/shared/figures/fig1-0922/rebuild/`): Material Intervention / Paired
Visual Grounding / Closed-loop Navigation, with all 15 photo slots filled from
library evidence (paired zoom_018 renders, recorded Qwen3-VL-2B inputs and the
recorded point [304, 180], recorded episode 898_898 navigation maps) and a
rewritten caption. `figure_hero.py` rebuilds it through `build_assets.py`;
`iclr27-check` passes with zero failures and the staged bundle is at
`paper/submissions/iclr27_candidate/`. The previous glass hero remains
reproducible via `iclr_system_hero/build_hero.py`. Figure 2 (overview) is
unchanged.

## Previous integration — 2026-09-16

The current paper has **8 main-text pages and 33 total pages**. The approved
glass system overview is Figure 1 (page 2); the unchanged empirical overview
is Figure 2 (page 3). Seven appendix sections incorporate 15 rebuilt evidence
plates and six additional generated tables. The migration inventory resolves
49 active ACL figure references while retaining all distinct empirical cases.

- Main and appendix build/source checks pass; 97 analysis/layout tests pass.
- Figure geometry uses at least 7 pt at manuscript width. Final visual review
  and exact hashes are recorded in `VISUAL_REVIEW.json`.
- Citation coverage is 18 sources and 21 contexts. The effective strict audit
  remains `REVIEW_REQUIRED` for the documented resolver/human checks; raw
  resolver output and the evidenced SSIM name normalization remain available.
- Source analysis and the original overview PNG are unchanged. No new
  experiment, model inference, scene capture, or navigation rollout was run.
- `FIGURE_MIGRATION.md` links the old figure inventory to rebuilt plates.
  `visual_iterations/integration_20260916/` contains comparisons and review rounds.

## Available artifacts
- Official ICLR 2027 review template and `TEMPLATE_PROVENANCE.json`.
- Local main paper, same-PDF appendix, generated figures and tables.
- Corrected all-query paired analysis, actual-pixel displacements and target-cluster intervals.
- Three completed clean-image model campaigns, 128 queries each.
- OpenReview title, abstract, TL;DR and keyword copy source.
- `make -C paper iclr27-check` and `iclr27-stage`.

## Research state
This is a **local submission-preparation candidate**, not a claim that the full
research agenda is finished. The 30/80-pair raster archive includes older render
issues; it is used for readout analysis with provenance details in the appendix.
The clean image-region experiment is built from four repaired source pairs.

Fresh off-axis rendering was attempted under the detected Isaac 4.5 runtime: the
original capture timed out after camera binding. The attempted pair was not used
in material-effect tables. A navigation follow-up manifest specifies 12 paired
episodes and 72 rollout jobs; those repeat/matched-state jobs have not run.

## Writing conventions
Lead with findings, then explain the mechanism and experimental definition.
Keep numerical denominators and units clear. Detailed implementation/source scope
belongs in the appendix. The ICLR checker verifies artifact correctness; it does
not demand `only`, `bounded`, `sanity` or other defensive vocabulary.

## Quality refresh — 2026-09-15

The existing-evidence revision is complete: five main figures redesigned, a
standalone grounding companion refreshed, and the prose reorganized around
paired decision turnover. No additional inference, rendering experiment, or
navigation rollout was run. Figure export is SVG/PDF/360-dpi PNG with registered
raw-image inputs, typed fonts, and label/data containment checks.

- Final paper: 8 main-text pages, 13 total pages.
- Figure/page review: independent image-only review PASS; all 13 PDF pages
  reviewed by the lead. Exact hashes are in `VISUAL_REVIEW.json`.
- Analysis/layout regression: 97 tests passed; artifact checks passed.
- Active bibliography: venue-specific `references.bib`, 14 sources and 17
  citation contexts inspected. `REFERENCES_VERIFIED.md` records corrections,
  resolver limitations, and the unconfirmed human ledger. The strict citation
  gate remains `REVIEW_REQUIRED`; machine/advisory inspection is complete.
- Local candidate package refreshed; no OpenReview upload or git commit.

## Reference-led visual refinement

Three overview candidates and four phases of visual refinement are retained in
`visual_iterations/`. VIMA, RoboPoint and Molmo figure designs informed image
hierarchy, aligned evidence panels and concise labels. The final five main
figures passed independent before/after and manuscript-scale review. Main text
and all main figures end on page 8; the full PDF has 13 pages. All labels are at
least 7 pt at 5.5-inch figure width. The source analysis is byte-identical to the
preceding revision. See `VISUAL_REVIEW.json` for final output hashes and
`visual_iterations/comparison/all_figures.pdf` for the visual comparison.

## Official submission settings
- Abstract deadline: **2026-09-18 23:59 AoE**.
- Full-paper deadline: **2026-09-25 23:59 AoE**.
- Initial main-text limit: **9 pages**; references and appendix additional.
- AI-use section: required, outside the main-text page budget.
- Sources: https://iclr.cc/Conferences/2027/AuthorGuidelines and https://iclr.cc/Conferences/2027/AIPolicyForAuthors
- Local staging does not create or upload an OpenReview submission.
