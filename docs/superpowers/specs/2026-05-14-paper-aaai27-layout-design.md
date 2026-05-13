# Paper AAAI-27 Layout Design

## Goal

Normalize the existing CVPR workshop-only paper into the Genesis-LLM paper workspace pattern so the manuscript can be revised toward an AAAI 2027 submission without losing the current paper, experiment evidence, figures, or review history.

## Context

The current `paper/` tree is a single-venue CVPR/SynData4CV manuscript:

- `paper/writing/main.tex` owns the venue wrapper, abstract, section inputs, bibliography style, and generated PDF.
- `paper/writing/sections/` owns all manuscript body sections.
- `paper/writing/figures/` owns narrative figures and generation scripts.
- `paper/results/figures/` and `paper/results/raw/` own quantitative figures and raw evidence.
- `paper/references/` owns the bibliography and venue/research notes.
- `paper/reviews/` owns paper review artifacts.
- `paper/experiments/` owns scripts that generated the current evidence.

Genesis-LLM separates reusable paper content from venue wrappers:

- `paper/shared/` owns shared sections, figures, references, tables, and evidence.
- `paper/venues/<venue>/` owns venue-specific `main.tex`, `preamble.tex`, `.latexmkrc`, `STATUS.md`, local override folders, and template files.
- `paper/Makefile` owns build and template checks.
- `paper/.gitignore` owns LaTeX build-output ignores.

AAAI 2027 official author-kit details are not yet committed in this repository. The AAAI-27 venue wrapper should therefore be scaffolded as the active target while `venues/aaai27/STATUS.md` records that the official template and policy review remain required before paper-content rewriting or submission.

## Architecture

Use a two-venue paper workspace:

```text
paper/
  README.md
  Makefile
  .gitignore
  shared/
    evidence/
      claims.yaml
      results_manifest.yaml
      raw/
      experiments/
    figures/
      sources.yaml
    references.bib
    sections/
    supplemental/
    tables/
    video/
    math_commands.tex
    venue_macros.tex
  venues/
    aaai27/
      main.tex
      preamble.tex
      STATUS.md
      .latexmkrc
      sections/
      rebuttal/
    cvpr26/
      main.tex
      preamble.tex
      STATUS.md
      .latexmkrc
      cvpr.sty
      ieeenat_fullname.bst
      ieee_fullname.bst
      sections/
      rebuttal/
```

`aaai27` is the active target. `cvpr26` preserves the previous workshop wrapper as a historical baseline and sanity-check venue. Both wrappers input the same shared sections unless a local override is explicitly documented in that venue's `STATUS.md`.

## File Mapping

- `paper/writing/sections/introduction.tex` -> `paper/shared/sections/intro.tex`
- `paper/writing/sections/related_work.tex` -> `paper/shared/sections/related.tex`
- `paper/writing/sections/methodology.tex` -> `paper/shared/sections/method.tex`
- `paper/writing/sections/results.tex` -> `paper/shared/sections/experiments.tex`
- `paper/writing/sections/discussion.tex` -> `paper/shared/sections/discussion.tex`
- `paper/writing/sections/conclusion.tex` -> `paper/shared/sections/conclusion.tex`
- abstract block from `paper/writing/main.tex` -> `paper/shared/sections/abstract.tex`
- empty future appendix scaffold -> `paper/shared/sections/appendix.tex`
- `paper/references/references.bib` -> `paper/shared/references.bib`
- `paper/references/*.md` -> `paper/shared/evidence/references/`
- `paper/reviews/` -> `paper/shared/evidence/reviews/`
- `paper/results/raw/` -> `paper/shared/evidence/raw/`
- `paper/results/figures/` -> `paper/shared/figures/`
- `paper/results/gen_figures.py` -> `paper/shared/figures/gen_figures.py`
- `paper/writing/figures/*` -> `paper/shared/figures/`
- `paper/experiments/` -> `paper/shared/evidence/experiments/`
- `paper/writing/cvpr.sty` and bibliography styles -> `paper/venues/cvpr26/`
- `paper/writing/main.pdf` and `paper/writing/main.brf` -> `archive/paper/cvpr26-workshop/`

## LaTeX Conventions

- Venue wrappers use `\input{preamble}`.
- Venue preambles define:
  - `\def\input@path{{../../shared/}{./}}`
  - `\graphicspath{{../../shared/}{./}}`
  - `\input{../../shared/math_commands}`
  - `\input{../../shared/venue_macros}`
- Venue wrappers use shared section inputs such as `\input{../../shared/sections/method}`.
- Venue wrappers use `\bibliography{references}`. `.latexmkrc` and the Makefile set `BIBINPUTS` to `paper/shared/`, matching Genesis-LLM and avoiding brittle `../../shared/references` paths from build directories.
- Shared figure references use stable shared paths such as `figures/fig_render_pairs.pdf`, not `../results/figures/...`.
- Moved experiment scripts must recompute `PROJECT_ROOT` from their new depth under `paper/shared/evidence/experiments/` and write to `paper/shared/evidence/raw/`.

## Build System

`paper/Makefile` supports:

- `make list`
- `make template-check`
- `make aaai27`
- `make cvpr26`
- `make all`
- `make clean`
- `make check`

`aaai27` template-check fails clearly until an official AAAI-27 style and bibliography style are added under `paper/venues/aaai27/` or are discoverable through TeX. `cvpr26` should remain buildable with the existing committed CVPR style files when local LaTeX tools are installed.

## Evidence Registry

`paper/shared/evidence/claims.yaml` records current numerical claims and their source files. `results_manifest.yaml` records raw outputs, generated figures, and historical review artifacts. `paper/shared/figures/sources.yaml` records figure-generation provenance. These registries are intentionally lightweight YAML so future AAAI revisions can update claims and provenance in the same commit as manuscript changes.

## Documentation Updates

Update active docs that mention old paper paths:

- `paper/README.md` becomes the canonical paper workspace guide.
- `paper/EXPERIMENT_CHECKLIST.md` is updated to the shared evidence paths.
- `docs/operations/codex-agent-playbook.md` and `.codex/file-ownership.md` are updated for the new paper ownership paths.
- Historical archive records can keep old paths because they document past work; do not rewrite them unless a current active index depends on them.

## Verification

Add `tests/test_paper_layout.py` to assert:

- legacy single-venue paths no longer exist (`paper/writing`, `paper/results`, `paper/references`, `paper/reviews`, `paper/experiments`);
- required shared and venue paths exist;
- venue wrappers use shared section inputs and `\bibliography{references}`;
- preambles and `.latexmkrc` contain shared `input@path`, `graphicspath`, and `BIBINPUTS` setup;
- active shared sections no longer reference old figure/result paths;
- evidence registries exist and contain expected top-level keys.
- figure provenance registry exists and contains expected top-level keys.

Run:

- `pytest tests/test_paper_layout.py -q`
- `make -C paper list`
- `make -C paper template-check` and record whether it fails only because the official AAAI-27 kit is missing;
- local Markdown link check for active docs and `paper/*.md`;
- `git diff --check`.

## Non-Goals

- Do not rewrite the scientific narrative for AAAI 2027 in this pass.
- Do not fabricate AAAI 2027 author-kit files.
- Do not change experiment results or numerical claims.
- Do not delete historical CVPR submission artifacts; move them to the new historical location.
