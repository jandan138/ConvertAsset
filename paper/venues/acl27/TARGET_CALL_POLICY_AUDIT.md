# ACL/ARR Target Call Policy Audit

Checked: 2026-05-26.

This audit records the current external venue state for the ACL-facing
manuscript wrapper. It separates the user's preferred Annual ACL 2027 target
from the currently public ARR/EACL 2027 route so that the paper is not labeled
final-ready for a venue whose official call is not yet public.

## Current Target Status

| Candidate route | Official status checked | What this means for this repo |
| --- | --- | --- |
| Annual ACL 2027 | Public search of official ACL/ARR/ACLPUB sources did not find an Annual ACL 2027 CFP, author kit, city/date page, commitment deadline, or conference-specific supplement policy. | Keep `paper/venues/acl27/` as an ACL/ARR candidate wrapper, not an Annual-ACL-final packet. Do not claim Japan/date/deadline unless an official source appears. |
| EACL 2027 | The official EACL 2027 site is live, lists Athens, Greece, March 9-14, 2027, and lists an ARR submission deadline of August 3, 2026. Its main-paper call page says the comprehensive CFP and detailed timetable are still being finalized. | This is the currently public 2027 ACL-family route with an ARR paper deadline. If the authors choose an active 2027 target now, retargeting from Annual ACL 2027 to EACL 2027 is the cleanest policy-backed option. |
| Generic ARR / ACLPUB | ARR authors guidelines, ARR dates/venues, ARR Responsible NLP checklist, ARR common submission problems, and ACLPUB formatting guidance are public. ARR dates list EACL 2027 with final ARR submission date August 3, 2026 and commitment date October 11, 2026. | The current PDF/staging packet can be checked against generic ARR/ACLPUB review rules. Final upload still needs the selected venue's full call and OpenReview form. |

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
- `https://2027.eacl.org/`
- `https://2027.eacl.org/calls/papers/`
