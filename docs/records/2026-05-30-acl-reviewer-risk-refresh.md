# 2026-05-30 ACL Reviewer-Risk Refresh

## Scope

This record updates the ACL reviewer-risk audit after the current ACL/ARR
candidate reached an 11-page figure-forward PDF with current route-policy and
visual-review evidence.

## Findings

The stale `ACL_REVIEWER_RISK_AUDIT.md` date was still 2026-05-26. Since then,
the paper gained:

- the accepted Figure 1 imagegen v18 method-chain schematic;
- real render Figure 2 and selected material-effect Figure 3 in the main paper;
- a wide selected InternNav Figure 4 panel;
- a 2026-05-30 target-policy refresh;
- a full-PDF visual recheck; and
- a fresh Figure 3 red-material diagnosis showing no recurrence in the current
  build artifact.

Official route sources were rechecked on 2026-05-30. ARR Dates still lists the
August 2026 ARR cycle with submission deadline August 3, 2026, and lists EACL
2027 with final ARR submission date August 3, 2026 and commitment deadline
October 11, 2026. The EACL 2027 home and call pages still list the August 3,
2026 AoE ARR deadline, while the comprehensive CFP and detailed timetable remain
forthcoming. Public official search still did not expose an Annual ACL 2027 CFP
or author kit.

## Changes

Updated `paper/venues/acl27/ACL_REVIEWER_RISK_AUDIT.md` to:

- set `Checked: 2026-05-30`;
- include the EACL 2027 home page as a route source;
- add a 2026-05-30 status refresh section;
- add current figure and visual-review status;
- add Figure 3 red-material confusion as a reviewer-facing risk with mitigation;
- clarify that the remaining risk is now ACL contribution fit and bounded scope,
  not absence of a paper draft.

## Verification

Commands:

```bash
python paper/shared/evidence/experiments/08_material_effect_baseline/check_qualitative_clean_provenance.py
python paper/venues/acl27/scripts/check_claim_boundaries.py
git diff --check -- paper/venues/acl27/ACL_REVIEWER_RISK_AUDIT.md docs/records/2026-05-30-acl-reviewer-risk-refresh.md docs/records/README.md
```

Results:

- material-effect clean provenance: pass, `clean_material_effect_panel_ready`;
- claim-boundary check: pass;
- whitespace diff check: pass.

## Remaining Risk

The manuscript is still not final-upload complete. Human-only blockers remain:
final route lock, private OpenReview author form fields, runtime/AI/media
approval wording, and final upload decision.
