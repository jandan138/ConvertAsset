# Paper ACL-27 Layout Design

## Goal

Add a third paper venue wrapper for the user's intended Annual ACL 2027 Japan route while preserving the existing shared manuscript, AAAI 2027 primary target, and CVPR workshop baseline.

## Context

The paper workspace already follows a Genesis-LLM-style layout:

- `paper/shared/` owns venue-neutral sections, figures, evidence, references, supplemental notes, and macros.
- `paper/venues/aaai27/` owns the active AAAI 2027 wrapper.
- `paper/venues/cvpr26/` preserves the CVPR/SynData4CV workshop wrapper.
- `paper/Makefile` registers known venue targets and template checks.
- `tests/test_paper_layout.py` locks this structure.

The user clarified that the desired ACL target is the Japan meeting, not EACL 2027 in Athens. Public checks on 2026-05-20 found an ACL Executive Committee resolution that the 2027 conference is branded as `ACL 2027`, but no public ACL 2027 CFP or official city/date page was found. Therefore this pass should record Japan as the user-intended route and avoid fabricating deadline or city details.

## Architecture

Add `paper/venues/acl27/` as a candidate target wrapper:

```text
paper/venues/acl27/
  main.tex
  preamble.tex
  .latexmkrc
  STATUS.md
  sections/
    README.md
    limitations.tex
    ethical-considerations.tex
  rebuttal/
    README.md
```

The wrapper inputs shared scientific sections directly and adds ACL-specific compliance sections locally. The target uses official ACL style-file names, `acl.sty` and `acl_natbib.bst`, but does not vendor template files in this pass.

## Fit Decision

The ACL version is a candidate route, not the main route. The current paper is stronger for AAAI unless the scientific narrative shifts from material conversion and synthetic-data engineering toward multimodal language grounding. The ACL version should be developed around questions such as:

- whether USD/MDL conversion changes visual evidence used by VLMs;
- whether synthetic scene conversion affects captioning, VQA, grounding, embodied instruction following, or agent perception;
- whether the pipeline can produce controlled evaluation data for multimodal language models;
- whether failure modes can be explained in language-grounded terms.

## Build Rules

`paper/Makefile` should add `acl27` to `VENUES`, show it in `make list`, and add `check-template-acl27` for `acl.sty` and `acl_natbib.bst`. `make template-check` is expected to fail until official AAAI and ACL templates are supplied.

## Verification

Update `tests/test_paper_layout.py` so the ACL wrapper becomes part of the structural contract. Run:

- `python -m pytest tests/test_paper_layout.py -q`
- `make -C paper list`
- `make -C paper template-check`
- `git diff --check`

Record template-check failures as expected if they are only missing official style files.
