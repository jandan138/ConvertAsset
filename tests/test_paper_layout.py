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
