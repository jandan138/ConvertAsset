# ConvertAsset Paper Workspace

The active target is **ICLR 2027**. The paper studies material changes as a model-input intervention, from visual grounding to episode-level embodied navigation. Its main text is organized around findings, mechanisms, and downstream behavior.

Start with [ICLR status](venues/iclr27/STATUS.md), [experiment runbook](shared/evidence/experiments/11_iclr_model_behavior/README.md), and [submission preparation](../docs/operations/iclr27-submission-preparation.md).

## Layout

```text
paper/
  shared/                 # Venue-neutral manuscript content, evidence, figures, references
  venues/iclr27/          # Active ICLR manuscript, generated assets, appendix and checks
  venues/aaai27/          # Earlier AAAI wrapper
  venues/acl27/           # Earlier ACL wrapper
  venues/cvpr26/          # Preserved CVPR/SynData4CV workshop wrapper
```

## Build

```bash
make list
make iclr27
make iclr27-check
make iclr27-stage
make template-check
make aaai27
make acl27
make cvpr26
make all
make clean
```

`make` defaults to `iclr27`. It recomputes the fixed-denominator analysis and generates the current figures/tables before building the PDF. `iclr27-check` checks sources, PDF structure, citations, anonymity and the 9-page main-text limit. `iclr27-stage` creates a local candidate packet under `submissions/iclr27_candidate/`.

Earlier `aaai27`, `acl27` and `cvpr26` targets remain available for historical reproduction. The ICLR version has its own scientific narrative and artifact checks.

The ICLR wrapper uses the shared bibliography plus `iclr_references.bib` for verified model-behavior literature. Its `.latexmkrc` resolves absolute bibliography search paths so BibTeX also works from the build directory.

## Override Rule

Venue `main.tex` files explicitly choose shared or local sections. Shared inputs look like `\input{../../shared/sections/method}`. A local override uses `\input{sections/method}` and must be recorded in that venue's `STATUS.md`.

## Template Status

| Venue | Template source | Expected files | Readiness intent |
| --- | --- | --- | --- |
| iclr27 | [official ICLR 2027 author kit](https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip), vendored with SHA-256 provenance | `iclr2027_conference.sty`, `iclr2027_conference.bst` | active-target |
| aaai27 | official AAAI 2027 author kit, not yet vendored | `aaai27.sty`, `aaai27.bst` | primary-target |
| acl27 | official ACL style files / ACL 2027 author kit, not yet vendored | `acl.sty`, `acl_natbib.bst` | candidate-target |
| cvpr26 | migrated local SynData4CV/CVPR workshop wrapper | `cvpr.sty`, `ieeenat_fullname.bst` | historical-baseline |

## Evidence Rules

Claims and result provenance live under `shared/evidence/`. Figure provenance lives under `shared/figures/sources.yaml`; `venues/iclr27/ASSET_PROVENANCE.json` additionally fingerprints every generated ICLR table and figure. Quantitative edits must regenerate these artifacts.

## Current evidence organization

- **Model readout archive:** six VLM configurations; 30 close-view and 80 mixed-view pairs. Corrected analysis separates output coverage, end-to-end success, and coordinate interpretations.
- **Clean visual interventions:** four repaired source pairs; two-view query/position swaps and target/context-window crossovers; three models, 384 new predictions.
- **Navigation:** 99 paired episodes over three KuJiaLe scenes, retained in the main paper with SR/SPL, 30 success-state transitions and recorded trajectories.
- **Next experiments:** fresh off-axis RTX views and matched-state navigation repeats. Their actual execution state is in the experiment roadmap; a local package build does not imply these follow-ups have run.
