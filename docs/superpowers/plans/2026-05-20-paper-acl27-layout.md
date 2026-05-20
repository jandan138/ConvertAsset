# Paper ACL-27 Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an ACL 2027 candidate venue wrapper for the user's intended Japan route.

**Architecture:** Register `acl27` as a third venue in the existing Genesis-LLM-style paper workspace. Reuse `paper/shared` for scientific sections, add ACL-specific compliance sections locally, and keep official style files as missing template dependencies until a verified ACL kit is available.

**Tech Stack:** LaTeX, BibTeX, Make, Python/pytest, Markdown records.

---

### Task 1: Extend The Paper Layout Contract

**Files:**
- Modify: `tests/test_paper_layout.py`

- [x] **Step 1: Add `acl27` to the venue tuple**

Change `VENUES` to `("aaai27", "acl27", "cvpr26")`.

- [x] **Step 2: Add Makefile snippets for `acl27`**

Require `VENUES := aaai27 acl27 cvpr26` and `check-template-acl27:`.

- [x] **Step 3: Verify RED**

Run: `python -m pytest tests/test_paper_layout.py -q`

Expected: fail because `paper/venues/acl27/main.tex` and Makefile registration do not exist yet.

### Task 2: Add The ACL Venue Wrapper

**Files:**
- Create: `paper/venues/acl27/main.tex`
- Create: `paper/venues/acl27/preamble.tex`
- Create: `paper/venues/acl27/.latexmkrc`
- Create: `paper/venues/acl27/STATUS.md`
- Create: `paper/venues/acl27/sections/README.md`
- Create: `paper/venues/acl27/sections/limitations.tex`
- Create: `paper/venues/acl27/sections/ethical-considerations.tex`
- Create: `paper/venues/acl27/rebuttal/README.md`

- [x] **Step 1: Add `main.tex`**

Use `\documentclass[11pt]{article}`, load official `acl.sty` in review mode when present, input the shared manuscript sections, add local limitations and ethical-considerations sections, and use `\bibliographystyle{acl_natbib}` with `\bibliography{references}`.

- [x] **Step 2: Add shared-path preamble and latexmk config**

Mirror the existing venue wrappers with shared `input@path`, `graphicspath`, `math_commands`, `venue_macros`, and `BIBINPUTS`.

- [x] **Step 3: Add ACL status and local-section documentation**

Record that the public CFP/city/date remain unverified in public sources, that Japan is the user-requested route, and that the scientific narrative must pivot to multimodal language grounding for ACL fit.

### Task 3: Register The Venue In Build Docs

**Files:**
- Modify: `paper/Makefile`
- Modify: `paper/README.md`
- Modify: `docs/records/README.md`
- Create: `docs/records/2026-05-20-paper-acl27-candidate.md`

- [x] **Step 1: Add Make target and template check**

Register `acl27` in `VENUES`, list it as an ACL-family candidate, and add checks for `acl.sty` and `acl_natbib.bst`.

- [x] **Step 2: Update paper README and records**

Document `acl27` as a candidate target, not the primary route.

### Task 4: Verify And Commit

**Files:**
- All files above

- [x] **Step 1: Run structure tests**

Run: `python -m pytest tests/test_paper_layout.py -q`

Expected: pass.

- [x] **Step 2: Run Makefile listing**

Run: `make -C paper list`

Expected: shows `aaai27 acl27 cvpr26`.

- [x] **Step 3: Run template check**

Run: `make -C paper template-check`

Result: `make -C paper template-check` fails at `check-template-aaai27` because `venues/aaai27/aaai27.sty` is not committed. `make -C paper check-template-acl27` separately fails because `venues/acl27/acl.sty` is not committed. `make -C paper check-template-cvpr26` passes.

- [x] **Step 4: Run whitespace check**

Run: `git diff --check`

Expected: no output and exit code 0.

- [x] **Step 5: Commit and push**

Commit message: `docs(paper): add acl27 candidate venue`
