from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
VENUES = ("aaai27", "acl27", "cvpr26")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(read_text(path))


def active_text_files() -> list[Path]:
    roots = [
        PAPER,
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "docs",
        ROOT / ".codex",
        ROOT / ".claude",
    ]
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
        "VENUES := aaai27 acl27 cvpr26",
        "template-check:",
        "check-template-aaai27:",
        "check-template-acl27:",
        "check-template-cvpr26:",
        "BIBINPUTS=",
        "bibtex build/main",
    ):
        assert snippet in makefile, snippet

    gitignore = read_text(PAPER / ".gitignore")
    for pattern in ("venues/*/build/", "submissions/", "camera-ready/", "*.aux", "*.bbl", "*.blg", "*.log", "*.out"):
        assert pattern in gitignore, pattern

    claims = read_yaml(PAPER / "shared/evidence/claims.yaml")
    manifest = read_yaml(PAPER / "shared/evidence/results_manifest.yaml")
    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    assert claims["schema_version"] == 1
    assert claims["claims"]
    assert manifest["schema_version"] == 1
    assert manifest["results"]
    assert sources["schema_version"] == 1
    assert sources["figures"]


def _relative_exists(relative_path: str) -> bool:
    return (ROOT / relative_path).exists()


def _script_declares_output(script_text: str, output_path: str) -> bool:
    output = Path(output_path)
    suffix = output.suffix.lstrip(".")
    quoted_suffixes = (f'"{suffix}"', f"'{suffix}'", f'"{output.suffix}"', f"'{output.suffix}'")
    return output.name in script_text or (output.stem in script_text and any(token in script_text for token in quoted_suffixes))


def test_figure_sources_outputs_and_generators_are_consistent() -> None:
    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    for figure in sources["figures"]:
        generator = ROOT / figure["generated_by"]
        assert generator.exists(), figure["generated_by"]
        script_text = read_text(generator)

        for output in figure["outputs"]:
            assert _relative_exists(output), output
            assert _script_declares_output(script_text, output), f"{figure['generated_by']} does not declare {output}"

        for source in figure["sources"]:
            assert _relative_exists(source), source


def test_evidence_manifest_covers_claim_sources_and_registered_paths_exist() -> None:
    claims = read_yaml(PAPER / "shared/evidence/claims.yaml")
    manifest = read_yaml(PAPER / "shared/evidence/results_manifest.yaml")
    raw_entries = manifest["results"]["raw"]
    registered_raw_paths = {entry["path"] for entry in raw_entries}

    for entry in raw_entries:
        assert _relative_exists(entry["path"]), entry["path"]
    for figure_path in manifest["results"]["figures"]:
        assert _relative_exists(figure_path), figure_path

    claim_raw_sources = {
        source
        for claim in claims["claims"]
        for source in claim["sources"]
        if source.startswith("paper/shared/evidence/raw/")
    }
    assert sorted(claim_raw_sources - registered_raw_paths) == []


def test_paper_agent_playbooks_reference_shared_layout() -> None:
    claude_figure = read_text(ROOT / ".claude/agents/paper-figure-generator.md")
    codex_figure = read_text(ROOT / ".codex/agents/paper-figure-generator.md")

    assert "paper/shared/evidence/experiments/figures" not in claude_figure
    assert "paper/shared/evidence/experiments/figures" not in codex_figure
    assert "paper/shared/figures/gen_<name>.py" in claude_figure
    assert "paper/shared/figures/" in codex_figure


def test_cvpr_archive_declares_pdf_only_snapshot() -> None:
    readme = read_text(ROOT / "archive/paper/cvpr26-workshop/README.md")
    assert "PDF-only" in readme
    assert "paper/venues/cvpr26" in readme


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
