# ConvertAsset Paper Workspace

This paper workspace follows the Genesis-LLM multi-venue layout. The active target is AAAI 2027; the previous CVPR/SynData4CV workshop draft is retained as a historical venue wrapper and archived PDF.

## Layout

```text
paper/
  shared/                 # Venue-neutral manuscript content, evidence, figures, references
  venues/aaai27/          # AAAI 2027 target wrapper
  venues/cvpr26/          # Preserved CVPR/SynData4CV workshop wrapper
```

## Build

```bash
make list
make template-check
make aaai27
make cvpr26
make all
make clean
```

`make aaai27` is the primary target. It intentionally requires the official AAAI-27 author kit files to be added under `paper/venues/aaai27/` before a submission build can succeed.

Venue wrappers use `\bibliography{references}`. The shared bibliography is resolved by each venue's `.latexmkrc` and the Makefile fallback, which set `BIBINPUTS` to `paper/shared/`.

## Override Rule

Venue `main.tex` files explicitly choose shared or local sections. Shared inputs look like `\input{../../shared/sections/method}`. A local override uses `\input{sections/method}` and must be recorded in that venue's `STATUS.md`.

## Template Status

| Venue | Template source | Expected files | Readiness intent |
| --- | --- | --- | --- |
| aaai27 | official AAAI 2027 author kit, not yet vendored | `aaai27.sty`, `aaai27.bst` | primary-target |
| cvpr26 | migrated local SynData4CV/CVPR workshop wrapper | `cvpr.sty`, `ieeenat_fullname.bst` | historical-baseline |

## Evidence Rules

Claims and result provenance live under `shared/evidence/`. Figure provenance lives under `shared/figures/sources.yaml`. Any future change to quantitative results, figure values, table values, seed reporting, or venue-specific scientific claims must update the relevant registry in the same change.
