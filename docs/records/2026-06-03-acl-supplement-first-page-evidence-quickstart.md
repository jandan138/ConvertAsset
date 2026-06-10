# 2026-06-03 ACL Supplement First-Page Evidence Quickstart

## Scope

Improved the ACL supplement opening page by adding
`fig_supplement_first_page_evidence_quickstart.png` in the right column before
the detailed visual evidence roadmap.

The quickstart is a compact reader-facing index over already registered visual
materials:

- proxy render evidence: matched original/noMDL render rows
- VLM target evidence: clean GRScenes target-view crops with boxes
- material-effect evidence: covered-bin and scoped failure/limitation examples
- navigation media evidence: selected InternNav rollout and route stills
- reader compass: an imagegen-created schematic slot that explains reading
  order and claim boundary

## Claim Boundary

The `reading_compass` slot is AI-generated and exposition only. It is not a
render result, metric, VLM prediction, navigation run, benchmark row, or
evidence source.

The evidence-bearing rows are copied from registered render/media figures. The
quickstart does not introduce a new evidence source; it only makes the first
page less sparse and helps readers find the detailed appendix sections.

## Layout Outcome

The quickstart lands on supplement page 1 in the right column. The visual
evidence roadmap remains on page 2, and the evidence-gate registry companion
remains readable on page 3.

Measured rendered-page active fractions:

- page 1: `0.134949`, from prior sparse reference `0.052022`
- page 2: `0.280783`
- page 3: `0.132858`
- page 4: `0.074102`

Page 4 is still relatively sparse in the right column; it remains a possible
future density target, but the first-page opening is no longer a text-only
impression.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png`
- `paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_first_page_evidence_quickstart.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_first_page_evidence_quickstart_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "first_page_evidence_quickstart"`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- Rendered PDF pages 1-4 with `pdftoppm`.
- PDF text positive scan for the quickstart caption and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, local paths,
  and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence
JSON records `independent_subagent: false`.
