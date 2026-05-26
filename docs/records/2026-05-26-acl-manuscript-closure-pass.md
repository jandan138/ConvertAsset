# 2026-05-26 ACL Manuscript Closure Pass

## Purpose

This record documents the first ACL/ARR manuscript-closure pass after the paper
story snapshot. The goal is to turn the completed ConvertAsset evidence package
into an ACL-facing draft around VLM grounding reliability and embodied-data
reliability under 3D material perturbations.

## Manuscript Changes

The ACL wrapper now uses local ACL-facing sections for the main narrative:

- `paper/venues/acl27/sections/related.tex`
- `paper/venues/acl27/sections/method.tex`
- `paper/venues/acl27/sections/results.tex`
- `paper/venues/acl27/sections/discussion.tex`

`paper/venues/acl27/main.tex` no longer inputs the shared
`related/method/experiments/discussion` sections directly. It still uses the
shared tables, figures, bibliography, evidence manifests, and appendix.

The local sections make the ACL story explicit:

- material conversion is the controlled perturbation;
- VLM grounding evidence is the primary ACL-facing result;
- official InternNav / KuJiaLe evidence is scoped embodied-data sanity;
- NVIDIA is included for selected material-effect bins, not official-scene
  performance;
- selected videos are qualitative evidence only.

## Related Work Expansion

The ACL related work now includes:

- vision-language navigation and referring-object grounding;
- embodied simulation and synthetic scene benchmarks;
- synthetic rendering shifts;
- proxy visual metrics versus task evidence.

Added bibliography entries:

- R2R / Vision-and-Language Navigation;
- REVERIE;
- Shikra;
- Ferret.

## Claim Audit

Added:

```text
paper/venues/acl27/CLAIM_AUDIT.md
```

The audit maps each ACL-facing claim to existing evidence and records forbidden
claim promotions, including broad embodied benchmark completion,
official-scene speedup, NVIDIA official-scene performance comparison,
population-level NVIDIA failure rates, and procedural-texture preservation.

## Venue Status

Updated:

```text
paper/venues/acl27/STATUS.md
```

Current public source check found generic official ACL style files and the
ACLPUB style guide. Public search surfaced EACL 2027, not a public Annual ACL
2027 CFP/site. The wrapper should therefore remain an ACL/ARR candidate until
the official Annual ACL 2027 call and policy details are public.

## Verification

Expected verification:

```bash
rg -n "sections/related|sections/method|sections/results|sections/discussion" paper/venues/acl27/main.tex
rg -n "broad embodied|official-scene speedup|NVIDIA official-scene" paper/venues/acl27
git diff --check
make -C paper acl27
```
