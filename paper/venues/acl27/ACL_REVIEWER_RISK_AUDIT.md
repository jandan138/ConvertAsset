# ACL Reviewer-Risk Audit

Checked: 2026-05-26.

This is a pre-submission reviewer-risk audit for the current ACL/ARR candidate.
It answers the practical question: if the authors want to submit to an
ACL-family venue, what is the next large goal and what must be hardened before
upload?

It is not a new experiment record, not a final acceptance forecast, and not a
replacement for the final venue-policy check.

## Bottom Line

The next large goal should be:

> Lock the ACL-family route and harden the current packet against likely ACL
> reviewer objections, then run the final integrity/upload gate.

For the current date, the actionable ACL-family route is EACL 2027 via ARR. ARR
Dates lists EACL 2027 with final ARR submission date August 3, 2026 and
commitment date October 11, 2026. The EACL 2027 main-paper page lists the same
August 3, 2026 ARR deadline and says the comprehensive CFP and detailed
timetable are still being finalized. Public search still does not expose an
official Annual ACL 2027 CFP/author kit.

Official route sources checked:

- ARR Dates and Venues: https://aclrollingreview.org/dates
- EACL 2027 main-paper call: https://2027.eacl.org/calls/papers/

Therefore, if the authors mean "submit to ACL" in the broad ACL-family sense,
use EACL 2027 via ARR as the working target. If they specifically require the
Annual ACL 2027 meeting, keep the current packet in ACL/ARR-candidate mode
until the official Annual ACL 2027 call exists.

## Reviewer-Facing Posture

The strongest posture is:

- This is a VLM grounding and embodied-data reliability paper under controlled
  3D material perturbations.
- ConvertAsset is the intervention mechanism, not the paper's only
  contribution.
- The contribution is an evidence-gated protocol: proxy similarity, VLM answer
  stability, point grounding, coordinate-contract compliance, material-effect
  boundaries, and scoped embodied-stack usability.
- The paper should not be sold as a broad embodied-navigation benchmark, a
  universal converter, or an NVIDIA comparison paper.

In plain terms: the paper is strongest when it says, "before using converted 3D
synthetic scenes for language grounding claims, here is the evidence ladder we
require and here is what happens on a bounded GRScenes/InternNav case study."

## Simulated Reviewer Risk Table

| Risk | Likely reviewer concern | Current mitigation | Required action |
| --- | --- | --- | --- |
| ACL fit | "This looks like graphics/simulation tooling, not NLP." | The ACL wrapper now frames the work around VLM grounding, coordinate contracts, and embodied-language data reliability. | Keep title, abstract, introduction, and contributions centered on language grounding. Avoid tool-first wording in the first page. |
| Scope too small | "15 clean pairs, 30 stress pairs, and 99 InternNav episodes may be too narrow." | Claims are bounded to frozen evidence pools; `CLAIM_AUDIT.md` forbids broad benchmark wording. | Present the work as a diagnostic protocol and case study, not as a population benchmark. Do not add larger claims without larger evidence. |
| Evidence feels heterogeneous | "Proxy metrics, VLM probes, NVIDIA cases, InternNav, and load/render timing may feel like separate projects." | `sections/method.tex` now organizes the method as evidence gates and includes Table `tab:acl_evidence_gate_registry`, which maps each stream to supported and forbidden claims. | Preserve the table and keep every result tied back to the same claim registry after any edit. |
| NVIDIA baseline over-read | "The selected NVIDIA baseline could be treated as an unfair or cherry-picked comparison." | Current text limits it to selected material-effect bins and one selected clearcoat failure. | Keep all NVIDIA claims selected and material-effect scoped. Do not claim population failure rate or official-scene NVIDIA performance. |
| Coordinate scoring confusion | "Qwen's raw-vs-normalized behavior may look like a prompt artifact." | Discussion already frames this as a coordinate-contract finding, not a model ranking. | Keep parser coverage, raw coordinate, and normalized-1000 scoring separated. Avoid saying one VLM is generally better. |
| Embodied claim overreach | "InternNav results are too small for a navigation benchmark." | Results say CIs cross zero and use official KuJiaLe only as downstream sanity evidence. | Keep InternNav as scoped sanity evidence. Do not promote it to broad embodied robustness. |
| Media/legal risk | "Scene videos or raw assets may create anonymous-review or redistribution issues." | Safe staged packet excludes videos, raw scenes, scratch USDs, frame dumps, and model artifacts. | Keep optional videos out of the default packet unless authors approve a separate legal/anonymization path. |
| Venue-policy drift | "The paper may not match the final target's rules." | EACL 2027 via ARR is public; Annual ACL 2027 is not yet public. | Refresh official policy immediately before upload and after the full EACL CFP or Annual ACL CFP appears. |

## What Is Already Completed

The current packet already has the pieces needed for an ACL-family candidate:

- ACL-local abstract, introduction, related work, method, results, discussion,
  conclusion, limitations, and ethical considerations.
- Claim audit that forbids unsupported broad embodied, speedup, NVIDIA
  official-scene, population-failure-rate, procedural-texture-success, and
  selected-video-as-quantitative claims.
- Citation/provenance and reference web-trail audits for the current
  ACL-wrapper bibliography.
- OpenReview metadata source and Responsible NLP checklist source.
- Author-gate worksheet for private human-only fields.
- Clean build/staging rehearsal with an anonymous five-file packet.
- Compact evidence-gate table in the ACL method section tying each evidence
  stream to its allowed and forbidden claim boundary.
- Current route evidence for EACL 2027 via ARR and a documented blocker for
  Annual ACL 2027 finalization.

## What Is Still Missing

The remaining work is mostly submission hardening, not more unbounded
experiments:

1. Choose the final route: EACL 2027 via ARR now, or wait for Annual ACL 2027.
2. Fill the private ignored author worksheet with author order, OpenReview
   profiles, reviewer-registration commitment, dual-submission/resubmission
   status, preprint status, runtime wording, AI-assistance wording, and media
   decision.
3. Do one human read for ACL fit: first page must read as VLM grounding /
   language-grounding reliability, not as an asset-conversion manual.
4. Rebuild the PDF from clean state after any edits.
5. Re-stage the exact upload packet and rerun anonymization scans.
6. Copy metadata and Responsible NLP answers into the official OpenReview form.
7. Keep optional scene-derived media excluded unless the authors approve a
   separate legal/anonymization route.

## When To Add More Experiments

More experiments are not the default next goal. Add them only if they directly
resolve a reviewer-facing weakness that the current claim boundary cannot
handle.

Reasonable optional additions:

- selected qualitative videos or panels for rebuttal/appendix explanation,
  kept qualitative and outside the default safe packet;
- a larger official InternNav run only if the authors want to claim broader
  embodied navigation, which the current paper deliberately does not claim.

Not recommended before the next submission gate:

- expanding into GRScenes as a navigation benchmark without a new design;
- making NVIDIA official-scene performance claims without matched conversions
  and smoke gates;
- adding procedural-texture success claims without evidence that conversion
  preserves those textures;
- turning the rule table into a learned classifier claim.

## Definition Of Done For The Next Large Goal

The next goal is done when:

- the target route is locked and recorded;
- official policy has been refreshed for that route;
- the first-page story has passed a reviewer-risk read;
- the private author gate is filled locally and remains uncommitted;
- the final PDF builds cleanly;
- the final staged packet contains only the safe upload boundary;
- local path, username, private repository, acknowledgment, and optional-media
  scans pass over the exact staged directory;
- OpenReview metadata and Responsible NLP answers match the final PDF;
- `STATUS.md`, `SUBMISSION_READINESS_AUDIT.md`, and
  `FINAL_SUBMISSION_PACKET_CHECKLIST.md` record the final outcome.
