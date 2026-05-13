# Paper AAAI-27 Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the current CVPR workshop-only paper into a Genesis-LLM-style `paper/shared` plus `paper/venues/{aaai27,cvpr26}` workspace.

**Architecture:** Shared manuscript content, figures, references, experiments, results, and evidence registries move under `paper/shared/`. Venue wrappers under `paper/venues/` own only template/preamble/status/build concerns. The previous CVPR workshop PDF is preserved under `archive/paper/cvpr26-workshop/`.

**Tech Stack:** LaTeX, BibTeX, Make, Python/pytest, YAML text registries.

---

## File Structure

- Create `tests/test_paper_layout.py` to lock the Genesis-style paper contract.
- Create `paper/README.md`, `paper/Makefile`, and `paper/.gitignore`.
- Create `paper/shared/sections/`, `paper/shared/figures/`, `paper/shared/evidence/`, `paper/shared/tables/`, `paper/shared/supplemental/`, and `paper/shared/video/`.
- Create `paper/venues/aaai27/` and `paper/venues/cvpr26/` with `main.tex`, `preamble.tex`, `.latexmkrc`, `STATUS.md`, `sections/README.md`, and `rebuttal/README.md`.
- Move old `paper/writing/`, `paper/results/`, `paper/references/`, `paper/reviews/`, and `paper/experiments/` content into the new locations.
- Update active docs and ownership rules that reference current paper paths.

### Task 1: Add Paper Layout Contract Test

**Files:**
- Create: `tests/test_paper_layout.py`

- [ ] **Step 1: Add failing layout test**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
VENUES = ("aaai27", "cvpr26")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def active_text_files() -> list[Path]:
    roots = [PAPER, ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CLAUDE.md", ROOT / "docs", ROOT / ".codex"]
    paths: list[Path] = []
    for root in roots:
        if root.is_file():
            paths.append(root)
        elif root.exists():
            paths.extend(
                path
                for path in root.rglob("*")
                if path.is_file()
                and path.suffix in {".md", ".tex", ".py", ".bib", ".yaml", ".yml"}
                and "build" not in path.parts
                and "superpowers" not in path.parts
            )
    return sorted(paths)


def test_shared_tree_and_legacy_single_venue_paths_removed() -> None:
    for removed in ("writing", "results", "references", "reviews", "experiments"):
        assert not (PAPER / removed).exists(), removed

    required_paths = (
        "README.md",
        "Makefile",
        ".gitignore",
        "shared/sections/abstract.tex",
        "shared/sections/intro.tex",
        "shared/sections/related.tex",
        "shared/sections/method.tex",
        "shared/sections/experiments.tex",
        "shared/sections/discussion.tex",
        "shared/sections/conclusion.tex",
        "shared/sections/appendix.tex",
        "shared/figures/sources.yaml",
        "shared/figures/fig_method_pipeline.pdf",
        "shared/figures/fig_render_pairs.pdf",
        "shared/figures/fig_image_quality.pdf",
        "shared/figures/fig_feature_similarity.pdf",
        "shared/figures/fig_tsne_dino.pdf",
        "shared/references.bib",
        "shared/math_commands.tex",
        "shared/venue_macros.tex",
        "shared/evidence/claims.yaml",
        "shared/evidence/results_manifest.yaml",
        "shared/evidence/raw/image_quality.csv",
        "shared/evidence/raw/feature_similarity.csv",
        "shared/evidence/raw/perf_benchmark.csv",
        "shared/evidence/experiments/01_render_pairs/run.py",
        "shared/supplemental/README.md",
        "shared/tables/README.md",
        "shared/video/README.md",
    )
    for relative_path in required_paths:
        assert (PAPER / relative_path).exists(), relative_path


def test_venue_entrypoints_status_preambles_and_bib_paths() -> None:
    for venue in VENUES:
        venue_dir = PAPER / "venues" / venue
        for name in ("main.tex", "preamble.tex", ".latexmkrc", "STATUS.md", "sections/README.md", "rebuttal/README.md"):
            assert (venue_dir / name).exists(), f"{venue}: {name}"

        status = read_text(venue_dir / "STATUS.md")
        for marker in ("Template provenance:", "Readiness:", "Local section overrides:", "Known missing checks:"):
            assert marker in status, f"{venue}: {marker}"

        preamble = read_text(venue_dir / "preamble.tex")
        for snippet in (
            r"\def\input@path{{../../shared/}{./}}",
            r"\graphicspath{{../../shared/}{./}}",
            r"\input{../../shared/math_commands}",
            r"\input{../../shared/venue_macros}",
        ):
            assert snippet in preamble, f"{venue}: {snippet}"

        main = read_text(venue_dir / "main.tex")
        assert r"\input{preamble}" in main, venue
        assert "../../shared/sections/" in main, venue
        assert r"\bibliography{references}" in main, venue
        assert "../../shared/references" not in main, venue

        latexmkrc = read_text(venue_dir / ".latexmkrc")
        assert "abs_path('../../shared')" in latexmkrc, venue
        assert "BIBINPUTS" in latexmkrc, venue


def test_build_files_and_evidence_registries() -> None:
    makefile = read_text(PAPER / "Makefile")
    for snippet in (
        "VENUES := aaai27 cvpr26",
        "template-check:",
        "check-template-aaai27:",
        "check-template-cvpr26:",
        "BIBINPUTS=",
        "bibtex build/main",
    ):
        assert snippet in makefile, snippet

    gitignore = read_text(PAPER / ".gitignore")
    for pattern in ("venues/*/build/", "submissions/", "camera-ready/", "*.aux", "*.bbl", "*.blg", "*.log", "*.out"):
        assert pattern in gitignore, pattern

    claims = read_text(PAPER / "shared/evidence/claims.yaml")
    manifest = read_text(PAPER / "shared/evidence/results_manifest.yaml")
    sources = read_text(PAPER / "shared/figures/sources.yaml")
    assert "schema_version:" in claims
    assert "claims:" in claims
    assert "schema_version:" in manifest
    assert "results:" in manifest
    assert "schema_version:" in sources
    assert "figures:" in sources


def test_active_sources_do_not_reference_old_paper_paths() -> None:
    forbidden = (
        "paper/writing",
        "paper/results",
        "paper/references",
        "paper/reviews",
        "paper/experiments",
        "../results/figures",
        "../references/references",
    )
    offenders: list[str] = []
    for path in active_text_files():
        if "archive" in path.parts:
            continue
        text = read_text(path)
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}: {token}")
    assert offenders == []
```

- [ ] **Step 2: Run test and verify RED**

Run: `pytest tests/test_paper_layout.py -q`

Expected: FAIL because `paper/writing`, `paper/results`, `paper/references`, `paper/reviews`, and `paper/experiments` still exist and the required shared/venue paths do not exist.

- [ ] **Step 3: Commit test**

```bash
git add tests/test_paper_layout.py
git commit -m "test: add paper layout contract"
```

### Task 2: Move Paper Assets into Shared and Venue Trees

**Files:**
- Move: `paper/writing/sections/*.tex` to `paper/shared/sections/`
- Move: `paper/writing/figures/*` and `paper/results/figures/*` to `paper/shared/figures/`
- Move: `paper/results/raw/` to `paper/shared/evidence/raw/`
- Move: `paper/experiments/` to `paper/shared/evidence/experiments/`
- Move: `paper/references/references.bib` to `paper/shared/references.bib`
- Move: `paper/references/*.md` to `paper/shared/evidence/references/`
- Move: `paper/reviews/` to `paper/shared/evidence/reviews/`
- Move: `paper/writing/cvpr.sty`, `paper/writing/ieee_fullname.bst`, `paper/writing/ieeenat_fullname.bst` to `paper/venues/cvpr26/`
- Move: `paper/writing/main.pdf`, `paper/writing/main.brf` to `archive/paper/cvpr26-workshop/`

- [ ] **Step 1: Create target directories**

```bash
mkdir -p paper/shared/sections paper/shared/figures paper/shared/evidence/raw paper/shared/evidence/experiments paper/shared/evidence/references paper/shared/evidence/reviews paper/shared/tables paper/shared/supplemental paper/shared/video paper/venues/aaai27/sections paper/venues/aaai27/rebuttal paper/venues/cvpr26/sections paper/venues/cvpr26/rebuttal archive/paper/cvpr26-workshop
```

- [ ] **Step 2: Move tracked paper content**

```bash
git mv paper/writing/sections/introduction.tex paper/shared/sections/intro.tex
git mv paper/writing/sections/related_work.tex paper/shared/sections/related.tex
git mv paper/writing/sections/methodology.tex paper/shared/sections/method.tex
git mv paper/writing/sections/results.tex paper/shared/sections/experiments.tex
git mv paper/writing/sections/discussion.tex paper/shared/sections/discussion.tex
git mv paper/writing/sections/conclusion.tex paper/shared/sections/conclusion.tex
git mv paper/results/figures/* paper/shared/figures/
git mv paper/writing/figures/* paper/shared/figures/
git mv paper/results/raw/* paper/shared/evidence/raw/
git mv paper/experiments/* paper/shared/evidence/experiments/
git mv paper/references/references.bib paper/shared/references.bib
git mv paper/references/*.md paper/shared/evidence/references/
git mv paper/reviews/* paper/shared/evidence/reviews/
git mv paper/results/gen_figures.py paper/shared/figures/gen_figures.py
git mv paper/writing/cvpr.sty paper/venues/cvpr26/cvpr.sty
git mv paper/writing/ieee_fullname.bst paper/venues/cvpr26/ieee_fullname.bst
git mv paper/writing/ieeenat_fullname.bst paper/venues/cvpr26/ieeenat_fullname.bst
git mv paper/writing/main.pdf archive/paper/cvpr26-workshop/main.pdf
git mv paper/writing/main.brf archive/paper/cvpr26-workshop/main.brf
```

- [ ] **Step 3: Remove empty legacy directories**

```bash
find paper/writing paper/results paper/references paper/reviews paper/experiments -depth -type d -empty -delete 2>/dev/null || true
```

### Task 3: Add Shared Sections, Venue Wrappers, Build Files, and Evidence Registries

**Files:**
- Create/modify: `paper/shared/sections/abstract.tex`, `paper/shared/sections/appendix.tex`
- Create: `paper/shared/math_commands.tex`, `paper/shared/venue_macros.tex`
- Create: `paper/shared/evidence/claims.yaml`, `paper/shared/evidence/results_manifest.yaml`
- Create: `paper/shared/figures/sources.yaml`
- Create: `paper/README.md`, `paper/Makefile`, `paper/.gitignore`
- Create: `paper/venues/aaai27/*`
- Create: `paper/venues/cvpr26/*`

- [ ] **Step 1: Extract current abstract into shared section**

Create `paper/shared/sections/abstract.tex` with the abstract text from old `paper/writing/main.tex`, wrapped in:

```tex
\begin{abstract}
...
\end{abstract}
```

- [ ] **Step 2: Add empty appendix and shared macro files**

Create:

```tex
% paper/shared/sections/appendix.tex
\appendix
\section{Supplementary Material}
\label{sec:appendix}

This appendix is reserved for AAAI 2027 supplementary material once the official
submission policy and author kit are verified.
```

```tex
% paper/shared/math_commands.tex
% Shared math commands for all venue wrappers.
```

```tex
% paper/shared/venue_macros.tex
% Shared venue-neutral macros for all venue wrappers.
```

- [ ] **Step 3: Add AAAI-27 venue wrapper**

Create `paper/venues/aaai27/main.tex`:

```tex
% AAAI 2027 target wrapper.
% Official AAAI-27 style files are not committed yet; see STATUS.md.
\documentclass[letterpaper]{article}

\IfFileExists{aaai27.sty}{%
  \usepackage[submission]{aaai27}%
}{%
  \PackageError{convertasset-aaai27}{Missing aaai27.sty}{Add the official AAAI-27 author kit to paper/venues/aaai27 before building this venue.}%
}

\input{preamble}

\title{Evaluating MDL-to-UsdPreviewSurface Material Simplification for Synthetic Data Pipelines}
\author{Anonymous AAAI 2027 Submission}

\begin{document}
\maketitle

\input{../../shared/sections/abstract}
\input{../../shared/sections/intro}
\input{../../shared/sections/related}
\input{../../shared/sections/method}
\input{../../shared/sections/experiments}
\input{../../shared/sections/discussion}
\input{../../shared/sections/conclusion}

\bibliographystyle{aaai27}
\bibliography{references}

\end{document}
```

Create `paper/venues/aaai27/preamble.tex`, `.latexmkrc`, `STATUS.md`, `sections/README.md`, and `rebuttal/README.md` following the conventions in the design.

- [ ] **Step 4: Add CVPR-26 preserved venue wrapper**

Create `paper/venues/cvpr26/main.tex` with the old CVPR title/authorship fields, `\usepackage[review]{cvpr}`, shared section inputs, and `\bibliographystyle{ieeenat_fullname}` plus `\bibliography{references}`.

Create matching `preamble.tex`, `.latexmkrc`, `STATUS.md`, `sections/README.md`, and `rebuttal/README.md`.

- [ ] **Step 5: Add Makefile, paper README, paper gitignore, evidence registries, figure sources registry, and README files**

Use the Genesis-LLM conventions: `VENUES := aaai27 cvpr26`, primary is `aaai27`, `template-check` checks `aaai27` style/BST and `cvpr26` local style files, and all venue build rules set `BIBINPUTS` to `paper/shared/`.

- [ ] **Step 6: Commit migration content**

```bash
git add paper archive/paper
git commit -m "docs: reorganize paper workspace for aaai27"
```

### Task 4: Update Paths in Active Paper Sources and Docs

**Files:**
- Modify: `paper/shared/sections/*.tex`
- Modify: `paper/shared/figures/*.py`
- Modify: `paper/shared/evidence/experiments/*/run*.py`
- Modify: `paper/EXPERIMENT_CHECKLIST.md`
- Modify: `.codex/file-ownership.md`
- Modify: `docs/operations/codex-agent-playbook.md`

- [ ] **Step 1: Update LaTeX figure paths**

Replace old figure paths in shared sections:

```text
../results/figures/fig_render_pairs.pdf -> figures/fig_render_pairs.pdf
../results/figures/fig_image_quality.pdf -> figures/fig_image_quality.pdf
../results/figures/fig_feature_similarity.pdf -> figures/fig_feature_similarity.pdf
../results/figures/fig_tsne_dino.pdf -> figures/fig_tsne_dino.pdf
```

Keep narrative figure paths as `figures/fig_method_pipeline.pdf` and `figures/fig_grscene_qualitative.pdf`.

- [ ] **Step 2: Update figure-generation scripts**

Update `paper/shared/figures/gen_figures.py` so:

```python
BASE = os.path.dirname(os.path.abspath(__file__))
PAPER_SHARED = os.path.dirname(BASE)
RAW = os.path.join(PAPER_SHARED, "evidence", "raw")
FIG_DIR = BASE
```

Update `paper/shared/figures/candidates/option_b/build_candidate_b.py` to point at `paper/shared/figures/final_run/final.svg` and `paper/shared/figures/candidates/option_b`.

- [ ] **Step 3: Update moved experiment scripts**

For every script under `paper/shared/evidence/experiments/*/run*.py`, change:

```python
PROJECT_ROOT = Path(__file__).resolve().parents[3]
```

to:

```python
PROJECT_ROOT = Path(__file__).resolve().parents[5]
```

Update output paths:

```python
PROJECT_ROOT / "paper" / "results" / "raw"
PROJECT_ROOT / "paper" / "results" / "raw" / "renders"
```

to:

```python
PROJECT_ROOT / "paper" / "shared" / "evidence" / "raw"
PROJECT_ROOT / "paper" / "shared" / "evidence" / "raw" / "renders"
```

Update usage strings from `paper/experiments/...` to `paper/shared/evidence/experiments/...`.

- [ ] **Step 4: Update active docs and ownership references**

Replace current active path references:

```text
paper/references/references.bib -> paper/shared/references.bib
paper/writing/ -> paper/shared/sections/ or paper/venues/<venue>/ as appropriate
paper/results/raw/ -> paper/shared/evidence/raw/
paper/results/figures/ -> paper/shared/figures/
paper/experiments/ -> paper/shared/evidence/experiments/
```

Do not rewrite archived records under `archive/docs/paper/`.

- [ ] **Step 5: Commit active path updates**

```bash
git add paper docs .codex
git commit -m "docs: update paper paths for shared venue layout"
```

### Task 5: Verify, Review, and Integrate

**Files:**
- Read-only verification across repository.

- [ ] **Step 1: Run contract test**

Run: `pytest tests/test_paper_layout.py -q`

Expected: PASS.

- [ ] **Step 2: Run paper build metadata checks**

Run: `make -C paper list`

Expected: prints `Available venues: aaai27 cvpr26` and `Primary: aaai27`.

Run: `make -C paper template-check`

Expected: it may fail only with a clear missing AAAI-27 author-kit message. If it fails for CVPR-26 missing local files or Makefile syntax, fix before proceeding.

- [ ] **Step 3: Run Markdown link and whitespace checks**

Run local Markdown link checker across `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/`, `paper/`, and `archive/`.

Run: `git diff --check HEAD~3..HEAD`

Expected: no whitespace errors.

- [ ] **Step 4: Request code review**

Dispatch a reviewer with:

- implemented scope: Genesis-style paper workspace normalization for AAAI-27
- base SHA: commit before this branch
- head SHA: current branch head
- requirements: design document and this plan

Fix any Critical or Important findings, re-run verification, and commit fixes.

- [ ] **Step 5: Merge back to main locally**

After verification and review, fast-forward merge `paper/aaai27-layout` back to `main`, remove the worktree, and report the final commit SHAs.
