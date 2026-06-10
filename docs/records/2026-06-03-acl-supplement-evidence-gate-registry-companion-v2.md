# 2026-06-03 ACL Supplement Evidence-Gate Registry Companion V2

## Scope

Reworked the ACL supplement Table S1 evidence-gate registry companion after the
page-density audit identified page 3 as one of the sparsest non-reference pages.

The v2 companion keeps the registry as a hybrid figure:

- registered proxy, GRScenes, material, and InternNav thumbnails remain the
  evidence-bearing content;
- a new `reader_gate` imagegen slot explains the registry-reading flow;
- an enlarged cross-evidence render strip adds more real render material to the
  lower half of the page;
- deterministic code owns the figure layout, labels, captions, and claim
  boundary text.

## Claim Boundary

The `reader_gate` slot is AI-generated and exposition only. It is not a metric,
VLM run, navigation run, benchmark row, render result, or material-preservation
claim.

The evidence-bearing content remains the registered render thumbnails and the
Table S1 evidence-gate rows. The caption continues to state that the companion
is not a new experiment, metric, VLM run, or navigation run.

## Layout Outcome

The companion was expanded from a 720px-era compact card to a 1800 x 1160
deterministic composite. The final layout uses:

- four gate cards for proxy similarity, VLM grounding, material cases, and
  embodied sanity;
- one separated AI reader-gate card;
- six bottom-strip real render tiles spanning proxy scene, original/noMDL VLM
  views, material bins, material limits, and InternNav media.

Page 3 active fraction improved from the prior density-audit reference
`0.087227` to `0.149676` under the same `pdftoppm -r 110` audit resolution.
The final `pdftoppm -r 140` visual-review render recorded page 3 at `0.141003`.
The supplement remains 44 pages.

Local visual review result:

- standalone figure: PASS after replacing text-heavy material crops with
  image-only material render crops;
- rendered PDF page 3: Table S1, enlarged companion, and caption remain on one
  page with visibly reduced lower-page blank area;
- rendered PDF page 4: the following claim-boundary page remains normal.

## Files

- `paper/shared/figures/gen_supplement_task_media_atlases.py`
- `paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png`
- `paper/shared/figures/ai_slots/fig_supplement_evidence_gate_reader_v2_ai_slot.png`
- `paper/shared/figures/ai_slot_manifests/fig_supplement_evidence_gate_registry_companion.yaml`
- `paper/shared/figures/sources.yaml`
- `paper/shared/tables/tab_acl_evidence_gate_registry.tex`
- `tests/test_paper_layout.py`
- `paper/shared/evidence/raw/acl27_visual_review/supplement_evidence_gate_registry_companion_v2_20260603.json`

## Verification

- `python paper/shared/figures/gen_supplement_task_media_atlases.py`
- `python -m pytest -q tests/test_paper_layout.py -k "evidence_gate_registry_companion"`
- `python -m pytest -q tests/test_paper_layout.py` (`73 passed`)
- `make -C paper acl27-supplement`
- `python -m json.tool paper/shared/evidence/raw/acl27_visual_review/supplement_evidence_gate_registry_companion_v2_20260603.json >/dev/null`
- `pdftotext paper/venues/acl27/build/supplement.pdf -` positive/negative claim-boundary scan
- Rendered PDF pages 3-4 with `pdftoppm -f 3 -l 4 -r 140 -png`.
- Rendered PDF page 3 with `pdftoppm -f 3 -l 3 -r 110 -png` for density
  comparison.
- Visual review was local rather than an independent subagent review; the
  evidence JSON records `independent_subagent: false`.
