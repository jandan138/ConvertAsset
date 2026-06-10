# 2026-06-03 ACL Supplement Evidence-Gate Registry Companion

## Scope

Improved the sparse evidence-gate registry area in the ACL supplement by adding `fig_supplement_evidence_gate_registry_companion.png` under Table S1.

The companion binds the four registry rows to registered visual thumbnails:

- proxy similarity: render pair evidence
- VLM grounding: target-box render evidence
- material mechanisms: material-effect render evidence
- embodied-data sanity: InternNav still evidence

It also includes an imagegen-created `reader_gate` schematic slot.

During the same page-level visual review, the following `Claim-boundary examples`
figure was also tightened: its material-mechanism `covered` tile now crops only
the render area, rather than the wider source panel that exposed a `ConvertAsset`
column heading.

## Claim Boundary

The AI-generated `reader_gate` slot is exposition only. It is not an experiment, metric, VLM run, navigation run, baseline result, or evidence-bearing panel.

The evidence-bearing content remains the registered render, grounding, material, and navigation thumbnails.

## Layout Outcome

The first implementation inserted the strip as a normal two-column object and overlapped the right column. The final implementation places the companion inside the same `table*` float as the evidence-gate registry, then flushes the float before explanatory prose.

The overview prose was also reflowed so `What This Supplement Does Not Prove` remains in two-column text before the one-column claim-boundary example figure. This removes the previous right-column blank page pattern.

Measured rendered-page active fractions:

- page 3: `0.075959`, from prior sparse reference `0.0327`
- page 4: `0.069015`
- page 5: `0.104054`

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_evidence_gate_registry_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/shared/tables/tab_acl_evidence_gate_registry.tex`
- `paper/venues/acl27/sections/supplement/00_overview.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_evidence_gate_registry_companion_20260603.json`

## Verification

- `python -m pytest -q tests/test_paper_layout.py -k "evidence_gate_registry_companion"`
- `python -m pytest -q tests/test_paper_layout.py -k "claim_boundary_examples"`
- `python -m pytest -q tests/test_paper_layout.py`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_evidence_gate_registry_companion_20260603.json >/dev/null`
- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `make -C paper acl27-supplement`
- Rendered PDF pages 3-6 with `pdftoppm`.
- PDF text positive scan for the registry companion and AI-exposition boundary.
- PDF text negative scan for stale red-material diagnostic wording, absolute local paths, and author-profile leakage.

Visual review was local rather than an independent subagent review; the evidence JSON records `independent_subagent: false`.
