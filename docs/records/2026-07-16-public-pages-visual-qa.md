# 2026-07-16 Public Pages Visual QA: Graduated Cylinder r3 Target-Grasp Summary

## Why this record exists

This record retains the release QA for the public summary page of the
source-bound graduated-cylinder r3 action evidence. It records reader-facing
delivery checks only; the underlying asset-admission and action evidence remain
in the linked ConvertAsset record.

Public report:

- <https://jandan138.github.io/GenManip/reports/aan-graduated-cylinder-r3-target-grasp-qualification-2026-07-16.html>

## Released revision and scope

| Item | Retained value |
|---|---|
| GitHub Pages revision | `d6f80d0bcf3714bf935a9e47c63d32b32f718af9` |
| ConvertAsset r3 evidence-doc revision | `baa4ee3806b34bd009109e8616ef6b01a6ac3719` |
| Page purpose | Public, compact summary of fixed right-arm target close/lift/hold evidence |
| Full evidence record | [2026-07-16 AAN Graduated Cylinder r3 EOS/GenManip Target-Grasp Qualification](2026-07-16-aan-graduated-cylinder-r3-eos-genmanip-target-grasp-qualification.md) |

The page is a reader-facing summary, not a replacement for the retained
source/package locks, action traces, or scoped-warning evidence in the full
record.

## Browser QA result

The released root page and report both returned HTTP 200 and passed Chromium
inspection at these viewport sizes:

| Viewport | Root page | Report page |
|---|---|---|
| Desktop: 1440 x 1024 | pass | pass |
| Tablet: 768 x 1024 | pass | pass |
| Mobile: 390 x 844 | pass | pass |

The final inspection found no console, page, or request errors; no horizontal
page overflow; no broken media (the report intentionally has no images); and
no raw LaTeX or markup. It also found no reader-visible internal paths or
credentials. The report's evidence-record link returned HTTP 200 and identified
the intended r3 qualification record.

## Fixed issues before release

An initial mobile review found a 712 px-wide overflow and a favicon 404. Both
were corrected before deployment. The released mobile page measures 390/390 px
wide and presents the fixed-layout evidence table without horizontal scrolling.

The final pre-deployment preview was served from a `git archive` of the
committed GitHub Pages content rather than from a working tree. Requests for
`/.git` and `/.git/HEAD` returned 404 in that preview, confirming that repository
metadata was not accidentally exposed by the preview server.

## Claim boundary

The public page supports only this narrow statement:

> The source-bound r3 package has recorded fixed right-arm target
> close/lift/hold evidence under its declared action protocol.

It does **not** establish bimanual pouring, source pick, a benchmark result,
global PhysX-warning freedom, or calibrated real-world physics. See the linked
qualification record for the exact action, source/package-integrity, and
target-scoped warning boundaries.

## Validation

The release QA retained these checks:

```bash
git diff --check -- docs/records/2026-07-16-public-pages-visual-qa.md \
  docs/records/README.md

curl --fail --silent --show-error --location --output /dev/null \
  https://jandan138.github.io/GenManip/
curl --fail --silent --show-error --location --output /dev/null \
  https://jandan138.github.io/GenManip/reports/aan-graduated-cylinder-r3-target-grasp-qualification-2026-07-16.html
curl --fail --silent --show-error --location --output /dev/null \
  https://github.com/jandan138/ConvertAsset/blob/main/docs/records/2026-07-16-aan-graduated-cylinder-r3-eos-genmanip-target-grasp-qualification.md

rg -n --pcre2 '(?<!https:)(?<!http:)(?<!file:)(?:/[^[:space:]`<>()]+){3,}' \
  docs/records/2026-07-16-public-pages-visual-qa.md
```

- PASS: Markdown formatting review and `git diff --check` found no whitespace
  or patch-format issue.
- PASS: the public root, report, and linked evidence record each returned HTTP
  200.
- PASS: the path/credential-leak scan found no reader-visible internal path or
  credential in this record or the released page review.
- PASS: Chromium visual review covered all six page/viewport combinations and
  found no reader-facing layout, error, overflow, media, or raw-markup defect.

## Residual risk

This is a static public-page release check. It does not independently rerun
Isaac Sim, recreate the robot action, or broaden the r3 qualification claim.
Any future page change requires a new public-page review at the affected
viewports and must preserve the action-evidence boundary above.
