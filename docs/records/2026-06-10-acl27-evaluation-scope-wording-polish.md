# 2026-06-10 ACL27 Evaluation Scope Wording Polish

## Summary

Revised the ACL27 manuscript and related submission checks to remove reviewer-facing "claim", "gate", "registry", "boundary", "bounded", and "promotion" framing where it read like authorial scaffolding rather than normal paper prose.

The main-paper narrative now describes the four checks as evaluation scope: what each check tests, what data it uses, and what remains outside the experiment. Table 1 was updated from the previous reader-gate framing to an evaluation-scope table, and its companion image was replaced with an AI-generated academic visual guide that avoids internal production wording.

## Updated Areas

- Main text: abstract, introduction, method, results, discussion, limitations, conclusion, ethics, and related work.
- Table text: Table 1 and shared table captions/headers that previously used gate, boundary, or claim phrasing.
- Visuals: replaced the Table 1 companion with `fig_supplement_evidence_scope_reader_v6_ai_slot.png` and regenerated `fig_supplement_evidence_gate_registry_companion.png`.
- Supplement visuals: regenerated the raster figure labels emitted by `gen_supplement_task_media_atlases.py` and `gen_supplement_vlm_clean_rerender_panel.py` so reviewer-facing panels no longer show claim/gate/boundary or AI-slot production wording.
- Submission files: synchronized the OpenReview metadata/checklist text, evidence-number guards, integrity fingerprint, and pre-upload route checks.
- Layout: inserted a page break before Limitations so the final main PDF avoids a float-only page and keeps the appendix/references transition stable.

## Verification

- `python paper/venues/acl27/scripts/run_preupload_gate.py --repo-root .`
- `python -m pytest tests/test_acl_openreview_checklist.py tests/test_acl_integrity_fingerprint.py tests/test_acl_preupload_gate.py tests/test_acl_claim_boundaries.py tests/test_acl_metadata_consistency.py tests/test_paper_layout.py -q`
- `python -m py_compile paper/shared/figures/gen_supplement_task_media_atlases.py paper/venues/acl27/scripts/run_preupload_gate.py paper/venues/acl27/scripts/check_claim_boundaries.py paper/venues/acl27/scripts/check_metadata_consistency.py`
- Final PDF text scans were run for the old reviewer-facing scaffolding terms after rebuilding the PDFs.
- Visual checks covered the main Table 1 page and high-risk supplement pages with regenerated raster labels, including pages 1, 3, 4, 5, 10, 15, 22, 24, 27, 28, 37, 38, 40, 41, and 45.

The pre-upload gate completes successfully, but the final blocker report still keeps `upload_ready: false` for human-only items: private author checks, target-route confirmation, and copying the OpenReview form fields.
