# ACL27 Supplement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone ACL-style supplement PDF for the ACL/ARR candidate with at least 20 pages and a v0 target of 32+ pages.

**Architecture:** Add a separate `supplement.tex` entry point under `paper/venues/acl27/`, split supplement content into ACL-local section files, and add a Makefile target that builds `build/supplement.pdf` without changing the current main-paper target. Use current shared figures/tables and keep media as still panels plus manifest text until final media upload is approved.

**Tech Stack:** ACL LaTeX style files, `latexmk`, existing `paper/Makefile`, Python/pytest layout tests, `pdfinfo`, `pdftotext`, `rg`.

---

### Task 1: Add Build Entry Point

**Files:**
- Create: `paper/venues/acl27/supplement.tex`
- Modify: `paper/Makefile`
- Test: `tests/test_paper_layout.py`

- [ ] **Step 1: Add a failing layout test**

Add a test that asserts the ACL supplement entry point and Makefile target exist:

```python
def test_acl_supplement_entrypoint_and_build_target() -> None:
    supplement = PAPER / "venues/acl27/supplement.tex"
    assert supplement.exists()

    supplement_text = read_text(supplement)
    assert r"\input{preamble}" in supplement_text
    assert r"\bibliography{references}" in supplement_text
    assert "sections/supplement/" in supplement_text

    makefile = read_text(PAPER / "Makefile")
    assert "acl27-supplement:" in makefile
    assert "supplement.tex" in makefile
    assert "build/supplement.pdf" in makefile
```

- [ ] **Step 2: Run the new test and confirm it fails**

Run:

```bash
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_entrypoint_and_build_target
```

Expected: failure because `supplement.tex` and the new Makefile target are not present yet.

- [ ] **Step 3: Add the supplement entry point**

Create `paper/venues/acl27/supplement.tex` with the ACL review style, shared preamble, appendix-style numbering, eight section inputs, and bibliography.

- [ ] **Step 4: Add Makefile supplement targets**

Add explicit `acl27-supplement` and `clean-acl27-supplement` targets that build and clean `venues/acl27/build/supplement.pdf`.

- [ ] **Step 5: Run the target test again**

Run:

```bash
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_entrypoint_and_build_target
```

Expected: pass.

### Task 2: Add Supplement Sections

**Files:**
- Create: `paper/venues/acl27/sections/supplement/00_overview.tex`
- Create: `paper/venues/acl27/sections/supplement/01_derivations.tex`
- Create: `paper/venues/acl27/sections/supplement/02_vlm_protocol.tex`
- Create: `paper/venues/acl27/sections/supplement/03_grscenes_visuals.tex`
- Create: `paper/venues/acl27/sections/supplement/04_material_effects.tex`
- Create: `paper/venues/acl27/sections/supplement/05_internnav_visuals.tex`
- Create: `paper/venues/acl27/sections/supplement/06_theory.tex`
- Create: `paper/venues/acl27/sections/supplement/07_reproducibility.tex`
- Test: `tests/test_paper_layout.py`

- [ ] **Step 1: Add a failing structure test**

Add a test that checks all eight supplement sections exist and contain the expected appendix markers:

```python
def test_acl_supplement_has_eight_appendix_sections() -> None:
    root = PAPER / "venues/acl27/sections/supplement"
    expected = {
        "00_overview.tex": "Claim Boundary",
        "01_derivations.tex": "Mathematical",
        "02_vlm_protocol.tex": "VLM",
        "03_grscenes_visuals.tex": "GRScenes",
        "04_material_effects.tex": "Material-Effect",
        "05_internnav_visuals.tex": "InternNav",
        "06_theory.tex": "Hypotheses",
        "07_reproducibility.tex": "Reproducibility",
    }
    for name, marker in expected.items():
        text = read_text(root / name)
        assert r"\section{" in text
        assert marker in text
```

- [ ] **Step 2: Run the structure test and confirm it fails**

Run:

```bash
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_has_eight_appendix_sections
```

Expected: failure until section files are created.

- [ ] **Step 3: Create section files**

Create the eight files with evidence-bounded text. Use current tables and figures rather than introducing unverified assets.

- [ ] **Step 4: Run the structure test again**

Run:

```bash
python -m pytest -q tests/test_paper_layout.py::test_acl_supplement_has_eight_appendix_sections
```

Expected: pass.

### Task 3: Build and Page-Count Gate

**Files:**
- Modify: `tests/test_paper_layout.py`
- Build output: `paper/venues/acl27/build/supplement.pdf`

- [ ] **Step 1: Add a page-count smoke test**

Add a test that asserts the supplement build target is declared and that page count checks can be run manually with `pdfinfo`.

- [ ] **Step 2: Build the supplement**

Run:

```bash
make -C paper acl27-supplement
```

Expected: exit 0 and output `paper/venues/acl27/build/supplement.pdf`.

- [ ] **Step 3: Check PDF profile**

Run:

```bash
pdfinfo paper/venues/acl27/build/supplement.pdf
```

Expected: A4 page size and at least 20 pages. The v0 target is 32+ pages.

### Task 4: Privacy and Claim-Boundary Checks

**Files:**
- Modify: `tests/test_paper_layout.py`
- Create: `docs/records/2026-06-02-acl-supplement-scaffold.md`

- [ ] **Step 1: Add privacy-token assertions**

Add test coverage that the supplement source does not contain `/cpfs`, `/home/`, `/root/`, `zhuzihou`, `jandan138`, `github.com/jandan138`, or `ConvertAsset.git`.

- [ ] **Step 2: Run layout tests**

Run:

```bash
python -m pytest -q tests/test_paper_layout.py
```

Expected: pass.

- [ ] **Step 3: Scan the built supplement PDF text**

Run:

```bash
pdftotext -layout paper/venues/acl27/build/supplement.pdf /tmp/acl27_supplement.txt
rg -n "/cpfs|/home/|/root/|zhuzihou|jandan138|github.com/jandan138|ConvertAsset.git" /tmp/acl27_supplement.txt
```

Expected: no matches.

- [ ] **Step 4: Document the scaffold**

Create `docs/records/2026-06-02-acl-supplement-scaffold.md` with changed files, build command, page count, privacy scan, and remaining work.

### Task 5: Visual Review

**Files:**
- Build output: `paper/venues/acl27/build/supplement.pdf`
- Optional evidence: `paper/shared/evidence/raw/acl27_visual_review/supplement_v0_visual_review_20260602.json`

- [ ] **Step 1: Render representative pages**

Run:

```bash
rm -rf /tmp/acl27_supplement_review
mkdir -p /tmp/acl27_supplement_review
pdftoppm -png -r 150 paper/venues/acl27/build/supplement.pdf /tmp/acl27_supplement_review/page
```

- [ ] **Step 2: Inspect the first, derivation, material, InternNav, and final pages**

Use `view_image` on representative rendered pages. Check for blank pages, clipped figures, overlapping captions, unreadable tables, and visible private tokens.

- [ ] **Step 3: Record review**

If the layout is acceptable for v0, create a compact visual-review JSON record. If not, fix the relevant section and rerun the build.

## Self-Review

This plan covers the approved supplement design: standalone ACL wrapper, eight appendices, 20+ page requirement with 32+ page v0 target, extensive InternNav stills, math derivations, theory/hypothesis discussion, reproducibility manifest, privacy scanning, build verification, and visual review. It avoids adding media ZIP upload logic in this first scaffold because that needs separate author/legal approval.
