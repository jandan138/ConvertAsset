# ICLR 2027 submission copy source

Paste these values into https://openreview.net/group?id=ICLR.cc/2027/Conference.
Do **not** copy the broken LaTeX-macro fragment from older drafts
(`52.5\ status:`). Use the PDF-expanded abstract below.

## Title
Same Scene, Different Decisions: Material Sensitivity in Embodied Models

## Abstract
Embodied models must connect visual appearance to task-relevant decisions. We study their material sensitivity: how those decisions change when scene geometry is retained but materials are converted to a different representation. In 99 paired navigation episodes, success falls from 52.5% to 48.5%, yet 30 episodes change success status: gains and losses largely cancel in the average. We investigate this hidden turnover through paired visual grounding and navigation experiments. A readout study across six vision-language model configurations separates localization from response-format and coordinate-scale effects. Controlled two-view tests then require models to follow a queried object across positions, and target-window crossovers reveal that changes to the target and its surroundings can shift grounding in opposite directions. In navigation, 17 previously successful episodes fail while 13 previously failed episodes succeed under converted materials. These results put the identity of successful decisions alongside mean accuracy as a central object of evaluation. Material representation is therefore more than an asset-format choice: it is an input variable through which we can study the visual dependence of embodied models.

## TL;DR
Material sensitivity in embodied models emerges in which grounding queries and navigation episodes succeed, beyond changes in average scores.

## Keywords
vision-language models, visual grounding, embodied navigation, material sensitivity, material conversion, controlled visual interventions

## Primary area
applications to robotics, autonomy, planning

If the form allows only one area, use the robotics item above. The earlier
"representation learning for computer vision" suggestion is **not** an official
2027 enum value. Closest extra-area alternatives, if you later want a different
primary match: `applications to computer vision, audio, language, and other modalities`
or `interpretability and explainable AI`.

## PDF
`paper/submissions/iclr27_candidate/main.pdf` (42.4 MB; OpenReview limit 50 MB).
Optional at the abstract deadline; required by the full-paper deadline.

## Supplementary material
Optional zip/pdf, max 100 MB, must stay anonymous. Code can wait until
2026-09-25 AOE. Do not upload this repository as-is: it contains author paths
and non-anonymous records.

## AI assistance (form checkboxes)
Select all that apply; each selected item must be covered by the paper's
AI Use Statement:

- Yes, to aid or polish writing. Details are described in the paper.
- Yes, for research ideation or execution. Details are described in the paper.
- Yes, to draft sections of the paper. Details are described in the paper.

Do **not** check synthetic-dataset generation or mathematical-proof assistance
unless the authors later expand the paper statement to cover those uses.

## Official dates
- Abstract: 2026-09-18 23:59 AoE (Beijing 2026-09-19 19:59).
- Full paper and supplementary: 2026-09-25 23:59 AoE (Beijing 2026-09-26 19:59).
- Source: https://iclr.cc/Conferences/2027/AuthorGuidelines

## Author-only fields
Author list, OpenReview profile IDs, reciprocal-reviewer author, exemption
reason, Code of Ethics / visibility / submission-requirement checkboxes, and
the optional PAT box are completed in OpenReview by the authors. After the
abstract deadline, authors cannot be added or removed, and the reciprocal-
reviewer fields cannot be changed.

## Local preparation status
Copy source for author review. No OpenReview submission has been created by
this workflow.
