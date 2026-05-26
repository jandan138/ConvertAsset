# ACL/ARR Target Call Policy Audit

Checked: 2026-05-26.

This audit records the current external venue state for the ACL-facing
manuscript wrapper. It separates the user's preferred Annual ACL 2027 target
from the currently public ARR/EACL 2027 route so that the paper is not labeled
final-ready for a venue whose official call is not yet public.

Refresh note on 2026-05-26: official ARR, EACL, and ACLPUB pages were reopened
after the consolidated pre-upload gate was added. The route state did not
change: EACL 2027 is still the concrete public 2027 ACL-family ARR route, and
Annual ACL 2027 still lacks an official public CFP/author kit in checked
sources.

Current-gate policy refresh on 2026-05-26: official ARR Dates, ARR Authors,
ARR Common Submission Problems, ACLPUB formatting/review-version pages, EACL
2027 home, and the EACL 2027 main-paper page were reopened again after the
latest pushed pre-upload gate pass. The policy state is still unchanged:
EACL 2027 is the only concrete public 2027 ACL-family ARR route found; Annual
ACL 2027 still has no official CFP/author kit in checked official search
results; the current repository packet remains a generic ACL/ARR candidate
packet until authors choose a route and the final target policy is locked.

Final-blocker handoff policy refresh on 2026-05-26: official ARR Dates,
ARR Authors, ARR Common Submission Problems, ACLPUB formatting/review-version
pages, EACL 2027 home, and the EACL 2027 main-paper page were reopened after
the final blocker report began listing the author-gate initializer command.
The route state is unchanged. ARR Dates still lists EACL 2027 with final ARR
submission date August 3, 2026 and commitment date October 11, 2026; the EACL
site still lists Athens, Greece, March 9-14, 2027 and August 3, 2026 AoE as
the long/short paper ARR submission deadline; the EACL main-paper page still
says the comprehensive CFP and detailed timetable are forthcoming. Official
search still did not find an Annual ACL 2027 CFP, author kit, city/date page,
commitment deadline, or conference-specific supplement policy.

Private-author-gate status policy refresh on 2026-05-26: official ARR Dates,
ARR Authors, ARR author checklist, ACLPUB formatting/review-version pages,
EACL 2027 home, EACL 2027 main-paper page, and ACL Resolutions were reopened
after the private author-gate status report was added. The route state is still
unchanged. ARR Dates still lists EACL 2027 with final ARR submission date
August 3, 2026 and commitment date October 11, 2026; EACL still lists Athens,
Greece, March 9-14, 2027 and the August 3, 2026 ARR deadline; the EACL
main-paper page still says the comprehensive CFP and detailed timetable are
being finalized. The ACL Resolutions page records "2027 ACL Conference
Branding" and says the 2027 ACL conference will be branded as ACL 2027 with no
co-branding with IJCLP/AFNLP, but it is not a CFP, author kit, deadline page,
OpenReview form, or supplement policy. No public official Annual ACL 2027 CFP
was found in the checked official sources.

## Current Target Status

| Candidate route | Official status checked | What this means for this repo |
| --- | --- | --- |
| Annual ACL 2027 | Public search of official ACL/ARR/ACLPUB sources did not find an Annual ACL 2027 CFP, author kit, city/date page, commitment deadline, or conference-specific supplement policy. | Keep `paper/venues/acl27/` as an ACL/ARR candidate wrapper, not an Annual-ACL-final packet. Do not claim Japan/date/deadline unless an official source appears. |
| EACL 2027 | The official EACL 2027 site is live, lists Athens, Greece, March 9-14, 2027, and lists an ARR submission deadline of August 3, 2026. Its main-paper call page says the comprehensive CFP and detailed timetable are still being finalized. | This is the currently public 2027 ACL-family route with an ARR paper deadline. If the authors choose an active 2027 target now, retargeting from Annual ACL 2027 to EACL 2027 is the cleanest policy-backed option. |
| Generic ARR / ACLPUB | ARR authors guidelines, ARR dates/venues, ARR Responsible NLP checklist, ARR common submission problems, and ACLPUB formatting guidance are public. ARR dates list EACL 2027 with final ARR submission date August 3, 2026 and commitment date October 11, 2026. | The current PDF/staging packet can be checked against generic ARR/ACLPUB review rules. Final upload still needs the selected venue's full call and OpenReview form. |

## Latest Official-Source Refresh

The latest refresh checked the same policy-critical public pages:

- ARR Dates and Venues still lists EACL 2027 with final ARR submission date
  August 3, 2026 and commitment date October 11, 2026.
- ARR Dates still lists the August 2026 review cycle as August 3, 2026
  submission with later review-cycle dates marked TBA, so the route is public
  but not yet a complete cycle-level timetable.
- The EACL 2027 main-paper page still says the comprehensive Call for Papers
  and detailed timetable are being finalized, while listing August 3, 2026 AoE
  as the long/short paper ARR submission deadline.
- ACLPUB formatting guidance still points authors to the official ACL style
  files and the generic review-version long-paper budget: 8 content pages plus
  unlimited references, with appendices/supplementary material optional and the
  paper required to be self-contained.
- ARR common-submission guidance still makes author order, OpenReview profiles,
  and reviewer-registration duties human gates that cannot be closed by the
  repository.
- ARR author/common-problem guidance still requires the paper to be in ARR
  scope, all authors to complete OpenReview/reviewer-registration duties, the
  paper not to be under archival review elsewhere, the author list/order to be
  final, and the preprint-status/checklist fields to be completed in the
  official form.
- Public search found ACL 2026 and older Annual ACL pages, but did not expose
  an official Annual ACL 2027 CFP, author kit, city/date page, commitment
  deadline, or conference-specific supplement policy.
- The refresh after the final-blocker command handoff found the same state:
  EACL 2027 remains the concrete public route; Annual ACL 2027 remains
  unavailable as a final public target in checked official sources.
- The refresh after the private author-gate status report added ACL
  Resolutions as a checked source. That page confirms the `2027 ACL Conference Branding`
  resolution, not an Annual ACL 2027 CFP or author kit.

## Policy Facts To Carry Forward

- ARR uses OpenReview submission and points authors to the ARR checklist,
  common-problems page, and ACL-style submission templates.
- ARR dates currently list 10-week review cycles and require all submitting
  authors to register as reviewers shortly after submission.
- Generic ACLPUB review guidance supports long papers up to 8 content pages
  plus unlimited references; Limitations is required and Ethical
  Considerations is encouraged/allowed before references.
- EACL 2027's official site currently provides the primary ARR deadline but not
  the full topic list, supplement policy, AI-use wording, or complete
  conference-specific CFP.

## Decision

The current repository state is best described as:

> ACL/ARR candidate-ready, with EACL 2027 now available as a concrete public
> ARR-family route; not yet Annual-ACL-2027-final ready.

Do not create new experiments merely because the Annual ACL call is missing.
The next required action is policy lock: the authors must choose whether to
submit through the currently public EACL 2027 ARR route or wait for Annual ACL
2027's official call.

## Sources Checked

- `https://aclrollingreview.org/authors`
- `https://aclrollingreview.org/cfp`
- `https://aclrollingreview.org/dates`
- `https://aclrollingreview.org/authorchecklist`
- `https://aclrollingreview.org/responsibleNLPresearch/`
- `https://aclrollingreview.org/responsible-nlp-checklist-appendices`
- `https://acl-org.github.io/ACLPUB/formatting.html`
- `https://acl-org.github.io/ACLPUB/review-version.html`
- `https://www.aclweb.org/adminwiki/index.php/ACL_Resolutions`
- `https://2027.eacl.org/`
- `https://2027.eacl.org/calls/papers/`
