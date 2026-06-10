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
        "shared/figures/fig_render_scene_evidence_wide.png",
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


def test_aaai27_uses_official_2027_style_and_local_acl_story_sections() -> None:
    main = read_text(PAPER / "venues/aaai27/main.tex")
    makefile = read_text(PAPER / "Makefile")
    status = read_text(PAPER / "venues/aaai27/STATUS.md")

    assert r"\usepackage[submission]{aaai2027}" in main
    assert r"\bibliographystyle{aaai27}" not in main
    assert "Material Conversion as a Controlled Perturbation" in main
    assert "Evaluating MDL-to-UsdPreviewSurface Material Simplification" not in main
    assert "../../shared/sections/abstract" not in main
    for section in (
        "abstract",
        "intro",
        "related",
        "method",
        "results",
        "discussion",
        "conclusion",
        "limitations",
        "ethical-considerations",
    ):
        assert rf"\input{{./sections/{section}}}" in main
        assert (PAPER / f"venues/aaai27/sections/{section}.tex").exists()

    assert "venues/aaai27/aaai2027.sty" in makefile
    assert "venues/aaai27/aaai2027.bst" in makefile
    assert "AuthorKit27.zip" in status
    assert "e28c6ac9bc6eb3b4e2d849547d2cefb5162610ee39d0a12e0dc62d1126b44a7d" in status


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


def test_acl_clean_pool_table_is_not_downscaled_as_an_image() -> None:
    table = read_text(PAPER / "shared/tables/tab_grscenes_vlm_clean_pool_pass15.tex")
    assert r"\label{tab:grscenes_vlm_clean_pool_pass15}" in table
    assert r"\resizebox" not in table
    assert r"\footnotesize" in table
    assert r"\textbf{Scope}" in table
    assert "structured\\_text" not in table


def test_acl_method_avoids_narrow_column_monospace_evidence_path() -> None:
    method = read_text(PAPER / "venues/acl27/sections/method.tex")
    assert r"\texttt{paper/shared/evidence}" not in method


def test_acl_intro_uses_latest_low_text_method_chain_schematic() -> None:
    intro = read_text(PAPER / "venues/acl27/sections/intro.tex")
    assert "fig_acl_method_chain_imagegen_v18.png" in intro
    assert "fig_acl_method_chain_imagegen_v17.png" not in intro
    assert "fig_acl_method_chain_imagegen_v16.png" not in intro
    assert "fig_acl_method_chain_imagegen_v15.png" not in intro
    assert "fig_acl_method_chain_imagegen_v14.png" not in intro
    assert "fig_acl_method_chain_imagegen_v9.png" not in intro


def test_acl_main_forces_results_floats_before_discussion() -> None:
    main = read_text(PAPER / "venues/acl27/main.tex")
    assert "\\usepackage{placeins}" in read_text(PAPER / "venues/acl27/preamble.tex")
    assert (
        "\\input{./sections/results}\n"
        "\\FloatBarrier\n"
        "\\input{./sections/discussion}"
    ) in main
    assert (
        "\\input{./sections/limitations}\n"
        "\\FloatBarrier\n"
        "\\input{./sections/ethical-considerations}"
    ) in main
    assert "\\input{./sections/limitations}\n\\clearpage\n" not in main


def test_acl_uses_raggedbottom_to_avoid_stretched_discussion_page() -> None:
    preamble = read_text(PAPER / "venues/acl27/preamble.tex")
    assert "\\raggedbottom" in preamble


def test_acl_results_avoids_page_break_prone_original_nomdl_phrase() -> None:
    results = read_text(PAPER / "venues/acl27/sections/results.tex")

    assert "18 required paired runs" in results
    assert "original/noMDL fresh-process runs" not in results
    assert "fresh-process official-scene" not in results
    assert "paired official-scene runs" not in results


def test_acl_late_results_tables_are_two_column_floats() -> None:
    material_table = read_text(PAPER / "shared/tables/tab_material_effect_risk_matrix.tex")
    official_table = read_text(PAPER / "shared/tables/tab_official_scene_performance_summary.tex")
    material_generator = read_text(
        PAPER / "shared/evidence/experiments/08_material_effect_baseline/build_material_effect_risk_matrix.py"
    )
    official_generator = read_text(
        PAPER
        / "shared/evidence/experiments/10_official_scene_submission_closure/build_submission_closure_package.py"
    )

    for text in [material_table, official_table]:
        assert "\\begin{table*}[t]" in text
        assert "\\end{table*}" in text
        assert "\\columnwidth" not in text

    assert "p{0.24\\textwidth}" in material_table
    assert "p{0.30\\textwidth}" in official_table
    assert '"\\\\begin{table*}[t]"' in material_generator
    assert '"\\\\end{table*}"' in material_generator
    assert "p{0.24\\\\textwidth}" in material_generator
    assert '"\\\\begin{table*}[t]"' in official_generator
    assert '"\\\\end{table*}"' in official_generator
    assert "p{0.30\\\\textwidth}" in official_generator


def test_acl_material_figure_enters_float_queue_before_claim_boundary_table() -> None:
    results = read_text(PAPER / "venues/acl27/sections/results.tex")
    figure_pos = results.index(r"\label{fig:material_effect_baseline_qualitative_acl}")
    table_pos = results.index(r"\input{tables/tab_material_effect_risk_matrix}")
    embodied_pos = results.index(r"\label{sec:embodied_sanity}")
    between = results[figure_pos:embodied_pos]

    assert figure_pos < table_pos < embodied_pos
    assert r"\FloatBarrier" not in between


def test_acl_material_figure_can_use_bottom_double_column_placement() -> None:
    preamble = read_text(PAPER / "venues/acl27/preamble.tex")
    results = read_text(PAPER / "venues/acl27/sections/results.tex")
    figure_start = results.index(r"\begin{figure*}[")
    material_figure_start = results.index(
        r"\label{fig:material_effect_baseline_qualitative_acl}"
    )
    material_figure_block = results[figure_start:material_figure_start]

    assert r"\usepackage{stfloats}" in preamble
    assert r"\begin{figure*}[b]" in material_figure_block


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


def test_acl_supplement_has_appendix_sections() -> None:
    root = PAPER / "venues/acl27/sections/supplement"
    expected = {
        "00_overview.tex": "Evaluation Scope",
        "01a_render_atlas.tex": "Render Evidence Atlas",
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


def test_acl_supplement_has_render_evidence_atlas() -> None:
    supplement = read_text(PAPER / "venues/acl27/supplement.tex")
    section_path = PAPER / "venues/acl27/sections/supplement/01a_render_atlas.tex"

    assert r"\input{./sections/supplement/01a_render_atlas}" in supplement
    assert section_path.exists()

    section = read_text(section_path)
    for required in (
        "fig_supplement_render_atlas.png",
        "fig_supplement_render_scene_evidence_extended.png",
        "fig_grscene_qualitative.png",
        "fig_supplement_vlm_clean_rerender_panel.png",
        "fig_material_effect_baseline_qualitative.png",
    ):
        assert required in section

    assert "Extended render-scene evidence view" in section
    assert (
        r"\includegraphics[width=\textwidth,height=0.88\textheight,keepaspectratio]{figures/fig_supplement_render_scene_evidence_extended.png}"
        in section
    )


def test_supplement_render_scene_evidence_extended_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_render_scene_evidence_extended"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_render_scene_evidence_extended.png"]
    assert {
        "paper/shared/evidence/raw/renders/chestofdrawers_0011/A_top_front_right.png",
        "paper/shared/evidence/raw/renders/chestofdrawers_0011/B_top_front_right.png",
        "paper/shared/evidence/raw/renders/chestofdrawers_0023/A_top_front_right.png",
        "paper/shared/evidence/raw/renders/chestofdrawers_0023/B_top_front_right.png",
        "paper/shared/figures/out_tmp/mdl_images/orbit_mdl_01.png",
        "paper/shared/figures/out_tmp/nomdl_images/orbit_01.png",
        "paper/shared/figures/out_tmp/mdl_images/orbit_mdl_03.png",
        "paper/shared/figures/out_tmp/nomdl_images/orbit_03.png",
    }.issubset(set(figure["sources"]))

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1800
    assert height >= 1400
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.55


def test_supplement_render_evidence_preserves_proxy_object_context() -> None:
    render_atlas = read_text(PAPER / "shared/figures/gen_supplement_render_atlas.py")
    extended = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")

    for object_id in ("0004", "0011", "0023", "0029"):
        assert f"chestofdrawers_{object_id}/A_front.png" in render_atlas
        assert f"chestofdrawers_{object_id}/B_front.png" in render_atlas

    assert "_draw_proxy_context_row" in render_atlas
    assert "cover=True" not in render_atlas
    assert "Proxy object full-context + material-detail pair" in extended
    assert "_proxy_context_detail_pair(" in extended
    assert "_crop_fit(PROXY_OBJECT_0011_A" not in extended
    assert "_crop_fit(PROXY_OBJECT_0023_A" not in extended


def test_acl_supplement_excludes_unsafe_vlm_red_material_panel() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/01a_render_atlas.tex")

    assert "fig_vlm_grounding_cases.png" not in section
    assert "Red material in these diagnostic cases" not in section
    assert "registered diagnostic figure" not in section


def test_shared_experiments_excludes_unsafe_vlm_red_material_panel() -> None:
    section = read_text(PAPER / "shared/sections/experiments.tex")

    assert "fig_vlm_grounding_cases" not in section
    assert "Red material in these diagnostic cases" not in section
    assert "registered diagnostic figure" not in section


def test_acl_supplement_vlm_protocol_has_coordinate_visual_atlas() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/02_vlm_protocol.tex")

    assert "fig_supplement_vlm_coordinate_protocol_atlas.png" in section
    assert "VLM coordinate protocol" in section
    assert "The panels use real" in section
    assert "route diagram summarizes the path" in section
    assert r"\captionof{figure}" in section
    assert r"\onecolumn" in section
    assert (
        r"\includegraphics[width=\textwidth,height=0.76\textheight,keepaspectratio]{figures/fig_supplement_vlm_coordinate_protocol_atlas.png}"
        in section
    )


def test_acl_supplement_vlm_protocol_has_coordinate_table_companion() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/02_vlm_protocol.tex")
    compact_section = " ".join(section.split())

    table_pos = section.index("tab_grscenes_vlm_coordinate_ablation")
    figure_pos = section.index("fig_supplement_vlm_coordinate_table_companion.png")
    assert table_pos < figure_pos
    assert "VLM coordinate table companion" in section
    assert "explains the frame transformation" in section
    assert "Original/noMDL render pairs show why" in compact_section


def test_acl_supplement_vlm_protocol_has_coordinate_baseline_sanity_companion() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/02_vlm_protocol.tex")

    table_pos = section.index("tab_vlm_coordinate_baselines")
    figure_pos = section.index("fig_supplement_vlm_coordinate_baseline_sanity_companion.png")
    assert table_pos < figure_pos
    assert "Coordinate-baseline sanity companion" in section
    assert "summarizes the reading rule" in section
    assert "baseline audit strip adds" in section
    assert "scorer sanity checks rather than model" in section
    assert (
        r"\includegraphics[width=\textwidth,height=0.50\textheight,keepaspectratio]{figures/fig_supplement_vlm_coordinate_baseline_sanity_companion.png}"
        in section
    )


def test_acl_supplement_derivations_have_render_companions() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/01_derivations.tex")
    compact_section = " ".join(section.split())

    proxy_pos = section.index("Paired Render Notation")
    proxy_figure_pos = section.index("fig_supplement_proxy_metric_derivation_companion.png")
    feature_pos = section.index("Feature Similarity")
    point_grounding_pos = section.index("Point-in-Box Grounding")
    grounding_pos = section.index("Normalized-1000 Coordinate Contract")
    grounding_figure_pos = section.index("fig_supplement_grounding_derivation_companion.png")
    bootstrap_pos = section.index("Bootstrap Paired Intervals")
    navigation_pos = section.index("Navigation Metrics")
    navigation_figure_pos = section.index("fig_supplement_navigation_derivation_companion.png")

    assert proxy_pos < proxy_figure_pos < grounding_pos
    assert feature_pos < grounding_figure_pos < point_grounding_pos < grounding_pos
    assert bootstrap_pos < navigation_figure_pos < navigation_pos
    assert "Proxy metric derivation companion" in section
    assert "proxy render ladder anchor" in compact_section
    assert "Grounding derivation render companion" in section
    assert "formula-to-render audit strip" in section
    assert "coordinate-conversion render wall adds" in compact_section
    assert "target close-up scorer wall" in compact_section
    assert "Navigation derivation media companion" in section
    assert "formula-to-route panel" in compact_section
    assert "summarizes how the proxy quantities relate" in compact_section
    assert "connect point-in-box and normalized-coordinate formulas" in compact_section
    assert "different objects" in compact_section
    assert "matched original/converted evidence" in compact_section
    assert (
        r"\includegraphics[width=\textwidth,height=0.40\textheight,keepaspectratio]{figures/fig_supplement_proxy_metric_derivation_companion.png}"
        in section
    )
    assert (
        r"\includegraphics[width=\textwidth,height=0.40\textheight,keepaspectratio]{figures/fig_supplement_grounding_derivation_companion.png}"
        in section
    )
    assert (
        r"\includegraphics[width=\textwidth,height=0.30\textheight,keepaspectratio]{figures/fig_supplement_navigation_derivation_companion.png}"
        in section
    )


def test_supplement_proxy_metric_derivation_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_proxy_metric_derivation_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_proxy_metric_derivation_companion.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_render_scene_evidence_wide.png",
        "paper/shared/figures/fig_supplement_render_atlas.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_019/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_019/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_019/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_019/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_proxy_metric_axis_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_proxy_metric_derivation_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_proxy_metric_derivation_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_proxy_metric_derivation_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "proxy_metric_axis" in manifest["slots"]
    assert (
        manifest["slots"]["proxy_metric_axis"]
        == "paper/shared/figures/ai_slots/fig_supplement_proxy_metric_axis_v2_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["proxy_metric_axis"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert 1200 <= height <= 1320
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.37
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_derivation_companions_are_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    expected = {
        "fig_supplement_grounding_derivation_companion": {
            "output": "paper/shared/figures/fig_supplement_grounding_derivation_companion.png",
            "sources": {
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_019/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_019/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_019/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_019/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
                "paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_v3_ai_slot.png",
                "paper/shared/figures/ai_slot_manifests/fig_supplement_grounding_derivation_companion.yaml",
            },
            "height_range": (1180, 1360),
            "active_min": 0.40,
            "slot_path": "paper/shared/figures/ai_slots/fig_supplement_metric_contract_gate_v3_ai_slot.png",
        },
        "fig_supplement_navigation_derivation_companion": {
            "output": "paper/shared/figures/fig_supplement_navigation_derivation_companion.png",
            "sources": {
                "paper/shared/figures/fig_internnav_downstream_panel.png",
                "paper/shared/figures/fig_internnav_rollout_stills.png",
                "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
                "paper/shared/figures/fig_internnav_rollout_selected6_supp.png",
                "paper/shared/figures/fig_internnav_rollout_0036_0066_selected6_supp.png",
                "paper/shared/figures/supplement/internnav_selected6_case01.png",
                "paper/shared/figures/supplement/internnav_selected6_case02.png",
                "paper/shared/figures/supplement/internnav_selected6_case03.png",
                "paper/shared/figures/supplement/internnav_selected6_case04.png",
                "paper/shared/figures/supplement/internnav_selected6_case05.png",
                "paper/shared/figures/supplement/internnav_selected6_case06.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case01.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case02.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case03.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case04.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case05.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case06.png",
                "paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v4_ai_slot.png",
                "paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_derivation_companion.yaml",
            },
            "slot_name": "navigation_metric_gate",
            "slot_path": "paper/shared/figures/ai_slots/fig_supplement_navigation_metric_gate_v4_ai_slot.png",
            "height_range": (680, 760),
            "active_min": 0.43,
        },
    }

    for figure_id, spec in expected.items():
        figure = by_id[figure_id]
        assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
        assert figure["outputs"] == [spec["output"]]
        assert spec["sources"].issubset(set(figure["sources"]))

        manifest = read_yaml(PAPER / f"shared/figures/ai_slot_manifests/{figure_id}.yaml")
        assert manifest["mode"] == "ai_slot_composition"
        assert manifest["figure_id"] == figure_id
        assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
        slot_name = spec.get("slot_name", "metric_contract_gate")
        assert slot_name in manifest["slots"]
        if "slot_path" in spec:
            assert manifest["slots"][slot_name] == spec["slot_path"]
        assert manifest["replaceable_by_real_render"] == [slot_name]

        output = ROOT / spec["output"]
        assert output.exists()
        with Image.open(output) as image:
            width, height = image.size
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

        assert width >= 1700
        low, high = spec.get("height_range", (560, 840))
        assert low <= height <= high
        active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
        assert active.mean() >= spec.get("active_min", 0.25)
        red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
        assert red_fallback.mean() < 0.015


def test_supplement_navigation_derivation_companion_keeps_footer_inside_canvas() -> None:
    from PIL import Image
    import numpy as np

    output = PAPER / "shared/figures/fig_supplement_navigation_derivation_companion.png"

    with Image.open(output) as image:
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    bottom_safety_band = pixels[-20:]
    active = (
        (bottom_safety_band.max(axis=2) - bottom_safety_band.min(axis=2) > 15)
        | (bottom_safety_band.mean(axis=2) < 220)
    )
    assert active.mean() < 0.01


def test_supplement_vlm_coordinate_table_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_vlm_coordinate_table_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_vlm_coordinate_table_companion.png"]
    assert {
        "paper/shared/tables/tab_grscenes_vlm_coordinate_ablation.tex",
        "paper/shared/tables/tab_vlm_coordinate_baselines.tex",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_table_companion.yaml",
    }.issubset(set(figure["sources"]))
    section = read_text(PAPER / "venues/acl27/sections/supplement/02_vlm_protocol.tex")
    assert (
        r"\includegraphics[width=\textwidth,height=0.50\textheight,keepaspectratio]{figures/fig_supplement_vlm_coordinate_table_companion.png}"
        in section
    )
    assert "explains the frame transformation" in section

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_table_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_vlm_coordinate_table_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert (
        manifest["slots"]["coordinate_contract_gate"]
        == "paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["coordinate_contract_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert 1180 <= height <= 1300
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.45
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015

    ai_slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_contract_gate_v3_ai_slot.png"
    assert ai_slot.exists()
    with Image.open(ai_slot) as image:
        ai_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    ai_active = ((ai_pixels.max(axis=2) - ai_pixels.min(axis=2) > 15) | (ai_pixels.mean(axis=2) < 238))
    assert ai_active.mean() >= 0.20


def test_supplement_vlm_coordinate_baseline_sanity_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_vlm_coordinate_baseline_sanity_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_vlm_coordinate_baseline_sanity_companion.png"]
    assert {
        "paper/shared/tables/tab_vlm_coordinate_baselines.tex",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_baseline_gate_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_baseline_sanity_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_baseline_sanity_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_vlm_coordinate_baseline_sanity_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "baseline_gate" in manifest["slots"]
    assert manifest["slots"]["baseline_gate"] == "paper/shared/figures/ai_slots/fig_supplement_vlm_coordinate_baseline_gate_v2_ai_slot.png"
    assert manifest["replaceable_by_real_render"] == ["baseline_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert 1040 <= height <= 1260
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.30
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_grscenes_has_vlm_stress_render_strip() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/03_grscenes_visuals.tex")

    assert "fig_supplement_grscenes_vlm_stress_render_strip.png" in section
    assert "GRScenes VLM stress render strip" in section
    assert "prompt/point/score panel summarizes" in section
    assert "scoring setup" in section
    assert r"\captionof{figure}" in section


def test_acl_supplement_grscenes_tables_have_render_companions() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/03_grscenes_visuals.tex")
    compact_section = " ".join(section.split())

    for table_name, figure_name, caption in (
        (
            "tab_grscenes_vlm_failure_taxonomy",
            "fig_supplement_grscenes_failure_taxonomy_table_companion.png",
            "GRScenes failure-taxonomy table companion",
        ),
        (
            "tab_grscenes_vlm_pass_only_pilot",
            "fig_supplement_grscenes_pass_only_table_companion.png",
            "GRScenes PASS-only table companion",
        ),
        (
            "tab_grscenes_vlm_zoom_stress",
            "fig_supplement_grscenes_zoom_stress_table_companion.png",
            "GRScenes zoom-stress table companion",
        ),
    ):
        assert table_name in section
        table_pos = section.index(table_name)
        figure_pos = section.index(figure_name)
        assert table_pos < figure_pos, f"{figure_name} should follow {table_name}"
        assert caption in section

    assert "diagram explains the row inspection flow" in compact_section
    assert "zoom-level audit strip" in section
    assert "make selected table rows visually inspectable" in section
    assert (
        r"\includegraphics[width=\textwidth,height=0.56\textheight,keepaspectratio]{figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png}"
        in section
    )
    assert (
        r"\includegraphics[width=\textwidth,height=0.50\textheight,keepaspectratio]{figures/fig_supplement_grscenes_pass_only_table_companion.png}"
        in section
    )
    assert (
        r"\includegraphics[width=\textwidth,height=0.56\textheight,keepaspectratio]{figures/fig_supplement_grscenes_zoom_stress_table_companion.png}"
        in section
    )


def test_supplement_grscenes_table_companions_are_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    default_render_sources = {
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
    }
    expected = {
        "fig_supplement_grscenes_failure_taxonomy_table_companion": {
            "output": "paper/shared/figures/fig_supplement_grscenes_failure_taxonomy_table_companion.png",
            "table": "paper/shared/tables/tab_grscenes_vlm_failure_taxonomy.tex",
            "ai_slot": "paper/shared/figures/ai_slots/fig_supplement_grscenes_failure_taxonomy_gate_v4_ai_slot.png",
            "height_range": (1500, 1720),
            "active_min": 0.42,
            "render_sources": default_render_sources
            | {
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
            },
        },
        "fig_supplement_grscenes_pass_only_table_companion": {
            "output": "paper/shared/figures/fig_supplement_grscenes_pass_only_table_companion.png",
            "table": "paper/shared/tables/tab_grscenes_vlm_pass_only_pilot.tex",
            "ai_slot": "paper/shared/figures/ai_slots/fig_supplement_grscenes_pass_only_gate_v3_ai_slot.png",
            "slot_name": "pass_only_gate",
            "height_range": (1120, 1280),
            "active_min": 0.32,
            "red_max": 0.025,
            "render_sources": {
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
            },
        },
        "fig_supplement_grscenes_zoom_stress_table_companion": {
            "output": "paper/shared/figures/fig_supplement_grscenes_zoom_stress_table_companion.png",
            "table": "paper/shared/tables/tab_grscenes_vlm_zoom_stress.tex",
            "ai_slot": "paper/shared/figures/ai_slots/fig_supplement_grscenes_zoom_stress_gate_v3_ai_slot.png",
            "slot_name": "zoom_stress_gate",
            "height_range": (1220, 1460),
            "active_min": 0.34,
            "render_sources": default_render_sources
            | {
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
                "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
            },
        },
    }

    for figure_id, spec in expected.items():
        figure = by_id[figure_id]
        assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
        assert figure["outputs"] == [spec["output"]]
        expected_sources = {
            spec["table"],
            "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
            f"paper/shared/figures/ai_slot_manifests/{figure_id}.yaml",
        } | set(spec.get("render_sources", default_render_sources))
        assert expected_sources.issubset(set(figure["sources"]))
        assert spec.get("ai_slot", "paper/shared/figures/ai_slots/fig_supplement_grscenes_table_reading_gate_ai_slot.png") in figure["sources"]

        manifest = read_yaml(PAPER / f"shared/figures/ai_slot_manifests/{figure_id}.yaml")
        assert manifest["mode"] == "ai_slot_composition"
        assert manifest["figure_id"] == figure_id
        assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
        slot_name = spec.get("slot_name", "table_reading_gate")
        assert slot_name in manifest["slots"]
        assert manifest["slots"][slot_name] == spec.get(
            "ai_slot", "paper/shared/figures/ai_slots/fig_supplement_grscenes_table_reading_gate_ai_slot.png"
        )
        assert manifest["replaceable_by_real_render"] == [slot_name]

        output = ROOT / spec["output"]
        assert output.exists()
        with Image.open(output) as image:
            width, height = image.size
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

        assert width >= 1700
        low, high = spec.get("height_range", (520, 780))
        assert low <= height <= high
        active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
        assert active.mean() >= spec.get("active_min", 0.24)
        red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
        assert red_fallback.mean() < spec.get("red_max", 0.015)


def test_supplement_grscenes_vlm_stress_render_strip_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_grscenes_vlm_stress_render_strip"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_grscenes_vlm_stress_render_strip.png"]
    assert {
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_scoring_gate_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_vlm_stress_render_strip.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_grscenes_vlm_stress_render_strip.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_grscenes_vlm_stress_render_strip"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "scoring_gate" in manifest["slots"]
    assert manifest["replaceable_by_real_render"] == ["scoring_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert 1450 <= width <= 1650
    assert 1600 <= height <= 1780
    assert 0.82 <= width / height <= 0.98
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.35
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_vlm_coordinate_protocol_atlas_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_vlm_coordinate_protocol_atlas"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_vlm_coordinate_protocol_atlas.png"]
    assert {
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_vlm_protocol_route_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_protocol_atlas.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_vlm_coordinate_protocol_atlas.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_vlm_coordinate_protocol_atlas"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["protocol_route"] == (
        "paper/shared/figures/ai_slots/fig_supplement_vlm_protocol_route_v2_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["protocol_route"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert height >= 1800
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.36

    slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_vlm_protocol_route_v2_ai_slot.png"
    assert slot.exists()
    with Image.open(slot) as image:
        slot_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    slot_active = ((slot_pixels.max(axis=2) - slot_pixels.min(axis=2) > 15) | (slot_pixels.mean(axis=2) < 238))
    assert slot_active.mean() >= 0.20


def test_supplement_vlm_clean_rerender_panel_is_registered_and_not_red() -> None:
    from PIL import Image
    import json
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_vlm_clean_rerender_panel"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_vlm_clean_rerender_panel.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png"]
    assert {
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/47aa36277a54f6ca90cc.zoom_018.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/f35ef3d86c42446b7ddf.zoom_018.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/c27086f557d316584264.zoom_018.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/e2ec085d524d5df4455d.zoom_020.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
    }.issubset(set(figure["sources"]))

    for report in figure["sources"]:
        if not report.endswith(".clean_rerender_20260528.json"):
            continue
        data = json.loads((ROOT / report).read_text(encoding="utf-8"))
        assert data["summary"]["both_commands_exit_zero"] is True
        assert data["summary"]["both_images_exist"] is True
        assert data["summary"]["original_mdl_error_signal"] == 0
        assert data["summary"]["converted_mdl_error_signal"] == 0

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert 1650 <= height <= 1900
    assert 0.82 <= width / height <= 1.02
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.47
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015

    section = read_text(PAPER / "venues/acl27/sections/supplement/01a_render_atlas.tex")
    assert "target close-up strip" in section


def test_supplement_render_atlas_figure_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    atlas_entries = [figure for figure in sources["figures"] if figure["id"] == "fig_supplement_render_atlas"]
    assert len(atlas_entries) == 1

    atlas = atlas_entries[0]
    assert atlas["generated_by"] == "paper/shared/figures/gen_supplement_render_atlas.py"
    assert atlas["outputs"] == ["paper/shared/figures/fig_supplement_render_atlas.png"]
    assert "paper/shared/evidence/raw/renders/" in atlas["sources"]
    assert "paper/shared/figures/out_tmp/" in atlas["sources"]

    output = ROOT / atlas["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1800
    assert height >= 1300
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.30


def test_acl_supplement_render_atlas_has_wide_opener() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/01a_render_atlas.tex")
    opener_block = section.split(r"\twocolumn", 1)[0]

    assert "fig_supplement_render_atlas_opener.png" in section
    assert "Render evidence section opener" in section
    assert r"\onecolumn" in opener_block
    assert r"\twocolumn" in section
    assert r"\includegraphics[width=\textwidth" in opener_block
    assert r"\captionof{figure}" in opener_block
    assert r"\begin{figure*}[p]" not in opener_block


def test_supplement_render_atlas_opener_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_render_atlas_opener"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_render_atlas_opener.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_supplement_render_atlas.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
    }.issubset(set(figure["sources"]))

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 1000
    assert 1.35 <= width / height <= 1.85
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.28
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_derivations_has_metric_boundary_bridge() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/01_derivations.tex")
    bridge_block = section.split("fig_supplement_metric_boundary_bridge.png", 1)[0]

    assert "fig_supplement_metric_boundary_bridge.png" in section
    assert "Metric summary panel" in section
    assert "metric-scope lens strip" in section
    assert r"\captionof{figure}" in section
    assert r"\twocolumn" not in bridge_block.rsplit(r"\clearpage", 1)[-1]
    assert (
        r"\includegraphics[width=\textwidth,height=0.52\textheight,keepaspectratio]{figures/fig_supplement_metric_boundary_bridge.png}"
        in section
    )


def test_supplement_metric_boundary_bridge_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_metric_boundary_bridge"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_metric_boundary_bridge.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_metric_boundary_lens_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_metric_boundary_bridge.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_metric_boundary_bridge.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_metric_boundary_bridge"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["metric_boundary_lens"] == (
        "paper/shared/figures/ai_slots/fig_supplement_metric_boundary_lens_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["metric_boundary_lens"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 1200
    assert 1.10 <= width / height <= 1.55
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.35
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_overview_has_visual_evidence_roadmap() -> None:
    overview = read_text(PAPER / "venues/acl27/sections/supplement/00_overview.tex")

    assert "fig_supplement_visual_evidence_roadmap.png" in overview
    assert "Evidence roadmap" in overview
    assert "sequence of disconnected tables" in overview
    assert "not a new evidence source" not in overview


def test_acl_supplement_overview_has_first_page_evidence_quickstart() -> None:
    overview = read_text(PAPER / "venues/acl27/sections/supplement/00_overview.tex")
    compact_overview = " ".join(overview.split())

    assert "fig_supplement_first_page_evidence_quickstart.png" in overview
    quickstart_pos = overview.index("fig_supplement_first_page_evidence_quickstart.png")
    roadmap_pos = overview.index("fig_supplement_visual_evidence_roadmap.png")
    assert quickstart_pos < roadmap_pos
    assert "First-page evidence quickstart" in overview
    assert "compass panel summarizes the reading order" in compact_overview
    assert "opening-render examples" in compact_overview
    assert "adds no new metric, VLM run, or navigation run" not in overview
    assert r"\begin{figure}[t]" in overview
    assert (
        r"\includegraphics[width=\columnwidth,height=0.60\textheight,keepaspectratio]{figures/fig_supplement_first_page_evidence_quickstart.png}"
        in overview
    )


def test_supplement_first_page_evidence_quickstart_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_first_page_evidence_quickstart"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_first_page_evidence_quickstart.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_supplement_render_scene_evidence_extended.png",
        "paper/shared/figures/fig_supplement_vlm_coordinate_protocol_atlas.png",
        "paper/shared/figures/fig_supplement_grscenes_vlm_visual_guide.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v4_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_first_page_evidence_quickstart.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_first_page_evidence_quickstart.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_first_page_evidence_quickstart"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "reading_compass" in manifest["slots"]
    assert manifest["slots"]["reading_compass"] == "paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v4_ai_slot.png"
    assert manifest["replaceable_by_real_render"] == ["reading_compass"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 850
    assert height >= 1760
    assert 1.90 <= height / width <= 2.05
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.47
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015

    slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_first_page_reading_compass_v4_ai_slot.png"
    assert slot.exists()
    with Image.open(slot) as image:
        slot_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    slot_active = ((slot_pixels.max(axis=2) - slot_pixels.min(axis=2) > 15) | (slot_pixels.mean(axis=2) < 238))
    assert slot_active.mean() >= 0.42


def test_acl_supplement_overview_has_page4_claim_boundary_companion() -> None:
    overview = read_text(PAPER / "venues/acl27/sections/supplement/00_overview.tex")

    assert "fig_supplement_page4_claim_boundary_companion.png" not in overview
    assert r"\subsection{What This Supplement Does Not Prove}" not in overview
    assert "methodological rather than rhetorical" not in overview
    assert "not a new metric, VLM run, or navigation run" not in overview


def test_supplement_page4_claim_boundary_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_page4_claim_boundary_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_page4_claim_boundary_companion.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/supplement/internnav_selected6_case01.png",
        "paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_v3_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_page4_claim_boundary_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_page4_claim_boundary_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_page4_claim_boundary_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "boundary_marker" in manifest["slots"]
    assert (
        manifest["slots"]["boundary_marker"]
        == "paper/shared/figures/ai_slots/fig_supplement_page4_boundary_marker_v3_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["boundary_marker"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 850
    assert height >= 1400
    assert 1.45 <= height / width <= 1.75
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.43
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_ai_slots_are_not_cover_cropped() -> None:
    script = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    offending = [
        line.strip()
        for line in script.splitlines()
        if "AI_SLOT" in line and "cover=True" in line
    ]

    assert offending == []


def test_supplement_visual_evidence_roadmap_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_visual_evidence_roadmap"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_visual_evidence_roadmap.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
    }.issubset(set(figure["sources"]))

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 1900
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.18
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_overview_has_evidence_gate_registry_companion() -> None:
    overview = read_text(PAPER / "venues/acl27/sections/supplement/00_overview.tex")
    table = read_text(PAPER / "shared/tables/tab_acl_evidence_gate_registry.tex")

    assert r"\input{tables/tab_acl_evidence_gate_registry}" in overview
    assert "fig_supplement_evidence_gate_registry_companion.png" in table
    assert r"height=0.50\textheight" in table
    assert "Evaluation scope for the four checks" in table
    assert "thumbnails link the table entries" in table
    assert "AI-generated" not in table
    assert "not an additional experiment, metric, VLM run, or navigation run" not in table


def test_supplement_evidence_gate_registry_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_evidence_gate_registry_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_evidence_gate_registry_companion.png"]
    assert {
        "paper/shared/tables/tab_acl_evidence_gate_registry.tex",
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_render_scene_evidence_wide.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
        "paper/shared/figures/ai_slots/fig_supplement_evidence_scope_reader_v6_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_evidence_gate_registry_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_evidence_gate_registry_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_evidence_gate_registry_companion"
    assert manifest["evaluation_scope"] == "Visual guide only; not experimental evidence."
    assert manifest["slots"]["reader_gate"] == "paper/shared/figures/ai_slots/fig_supplement_evidence_scope_reader_v6_ai_slot.png"
    assert manifest["replaceable_by_real_render"] == ["reader_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 1200
    assert 1.40 <= width / height <= 1.55
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.30

    ai_slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_evidence_scope_reader_v6_ai_slot.png"
    with Image.open(ai_slot) as image:
        ai_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    ai_active = ((ai_pixels.max(axis=2) - ai_pixels.min(axis=2) > 15) | (ai_pixels.mean(axis=2) < 238))
    assert ai_active.mean() >= 0.10
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_overview_has_claim_boundary_examples() -> None:
    overview = read_text(PAPER / "venues/acl27/sections/supplement/00_overview.tex")

    assert "fig_supplement_claim_boundary_examples.png" not in overview
    assert "Evaluation-scope examples" not in overview
    assert "not a new metric" not in overview
    assert "AI-generated" not in overview
    assert r"\captionof{figure}" not in overview
    assert r"\onecolumn" not in overview
    assert r"\twocolumn" not in overview


def test_supplement_claim_boundary_examples_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    script = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    assert '("covered", _crop_fit(MATERIAL_BASELINE, (12, 55, 742, 337)' not in script

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_claim_boundary_examples"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_claim_boundary_examples.png"]
    assert {
        "paper/shared/figures/fig_render_scene_evidence_wide.png",
        "paper/shared/figures/fig_supplement_render_scene_evidence_extended.png",
        "paper/shared/figures/fig_supplement_vlm_coordinate_protocol_atlas.png",
        "paper/shared/figures/fig_supplement_grscenes_vlm_visual_guide.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
        "paper/shared/figures/supplement/internnav_selected6_case04.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case04.png",
        "paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_claim_boundary_examples.yaml",
    }.issubset(set(figure["sources"]))
    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_claim_boundary_examples.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_claim_boundary_examples"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["claim_boundary_gate"] == (
        "paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["claim_boundary_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 2250
    assert 0.74 <= width / height <= 0.86
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.30
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015

    slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_claim_boundary_examples_gate_v2_ai_slot.png"
    assert slot.exists()
    with Image.open(slot) as image:
        slot_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    slot_active = ((slot_pixels.max(axis=2) - slot_pixels.min(axis=2) > 15) | (slot_pixels.mean(axis=2) < 238))
    assert slot_active.mean() >= 0.38


def test_acl_supplement_has_task_media_atlases() -> None:
    material = read_text(PAPER / "venues/acl27/sections/supplement/04_material_effects.tex")
    internnav = read_text(PAPER / "venues/acl27/sections/supplement/05_internnav_visuals.tex")

    assert "fig_supplement_material_diagnostic_atlas.png" in material
    assert "fig_supplement_material_claim_boundary_atlas.png" in material
    assert "fig_supplement_material_decision_map.png" in material
    assert "Material-risk atlas" in material
    assert "Material safe-conversion decision map" in material
    assert r"\input{tables/tab_material_effect_risk_matrix}" not in material
    assert r"\input{tables/tab_material_safe_conversion_recommender}" not in material
    assert (
        "\\input{tables/tab_material_effect_risk_matrix}\n\n"
        "\\clearpage\n\n"
        "\\input{tables/tab_material_safe_conversion_recommender}"
    ) not in material
    assert r"\includegraphics[width=0.95\textwidth]{figures/fig_material_effect_supplemental_qualitative.png}" not in material

    assert "fig_supplement_navigation_media_atlas.png" in internnav
    assert "fig_supplement_navigation_media_boundary_strip.png" in internnav
    assert "fig_supplement_internnav_selected6_neutral_companion.png" in internnav
    assert "fig_supplement_internnav_0036_neutral_companion.png" in internnav
    assert "Navigation media scope strip" in internnav
    assert "Selected official neutral navigation companion" in internnav
    assert "Selected 0036/0066 neutral navigation companion" in internnav
    assert "media-package panel" in internnav
    assert "right panel summarizes that review scope" in " ".join(internnav.split())
    assert (
        r"\includegraphics[width=\textwidth,height=0.74\textheight,keepaspectratio]{figures/fig_supplement_navigation_media_boundary_strip.png}"
        in internnav
    )
    assert (
        r"\includegraphics[width=\textwidth,height=0.78\textheight,keepaspectratio]{figures/fig_supplement_internnav_selected6_neutral_companion.png}"
        in internnav
    )
    assert (
        r"\includegraphics[width=\textwidth,height=0.78\textheight,keepaspectratio]{figures/fig_supplement_internnav_0036_neutral_companion.png}"
        in internnav
    )
    assert "fig:supp-internnav-selected6-neutral-companion" in internnav
    assert "fig:supp-internnav-0036-neutral-companion" in internnav
    assert "fig:supp-internnav-selected6-pair03" not in internnav
    assert "fig:supp-internnav-0036-pair03" not in internnav
    assert r"\captionof{figure}" in internnav
    assert "fig_internnav_rollout_selected6_supp.png" not in internnav
    assert "fig_internnav_rollout_0036_0066_selected6_supp.png" not in internnav


def test_supplement_internnav_0036_neutral_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_internnav_0036_neutral_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_internnav_0036_neutral_companion.png"]
    assert {
        "paper/shared/figures/supplement/internnav_0036_0066_case05.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case06.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
    }.issubset(set(figure["sources"]))

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert 1450 <= width <= 1650
    assert 1600 <= height <= 1780
    assert 0.82 <= width / height <= 0.98
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.46
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_internnav_selected6_neutral_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_internnav_selected6_neutral_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_internnav_selected6_neutral_companion.png"]
    assert {
        "paper/shared/figures/supplement/internnav_selected6_case05.png",
        "paper/shared/figures/supplement/internnav_selected6_case06.png",
        "paper/shared/figures/fig_internnav_rollout_selected6_supp.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/ai_slots/fig_supplement_internnav_selected6_neutral_gate_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_internnav_selected6_neutral_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_internnav_selected6_neutral_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_internnav_selected6_neutral_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert (
        manifest["slots"]["selected6_neutral_gate"]
        == "paper/shared/figures/ai_slots/fig_supplement_internnav_selected6_neutral_gate_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["selected6_neutral_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert 1450 <= width <= 1700
    assert 1750 <= height <= 2050
    assert 0.72 <= width / height <= 0.92
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.44
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.02

    slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_internnav_selected6_neutral_gate_ai_slot.png"
    assert slot.exists()
    with Image.open(slot) as image:
        slot_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    slot_active = ((slot_pixels.max(axis=2) - slot_pixels.min(axis=2) > 15) | (slot_pixels.mean(axis=2) < 238))
    assert slot_active.mean() >= 0.32


def test_supplement_navigation_media_boundary_strip_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_navigation_media_boundary_strip"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png"]
    assert {
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
        "paper/shared/figures/supplement/internnav_selected6_case01.png",
        "paper/shared/figures/supplement/internnav_selected6_case02.png",
        "paper/shared/figures/supplement/internnav_selected6_case03.png",
        "paper/shared/figures/supplement/internnav_selected6_case04.png",
        "paper/shared/figures/supplement/internnav_selected6_case05.png",
        "paper/shared/figures/supplement/internnav_selected6_case06.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case01.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case02.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case03.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case04.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case05.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case06.png",
        "paper/shared/figures/ai_slots/fig_supplement_navigation_media_package_v3_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_media_boundary_strip.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_navigation_media_boundary_strip.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_navigation_media_boundary_strip"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "media_package_gate" in manifest["slots"]
    assert (
        manifest["slots"]["media_package_gate"]
        == "paper/shared/figures/ai_slots/fig_supplement_navigation_media_package_v3_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["media_package_gate"]

    composer = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    assert "_fit(NAV_MEDIA_PACKAGE_V3_AI_SLOT, (left_w - 44, gate_h - 106), cover=False)" in composer
    assert "_fit(NAVIGATION_MEDIA_BOUNDARY_OUT, (bottom_w - 20, bottom_h - 52), cover=False)" in composer

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 2000
    assert height >= 2200
    assert 0.86 <= width / height <= 0.98
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.36
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_internnav_has_upload_gate_closure_card() -> None:
    internnav = read_text(PAPER / "venues/acl27/sections/supplement/05_internnav_visuals.tex")

    assert "fig_supplement_internnav_upload_gate_closure_card.png" in internnav
    assert "Official-scene upload package closure card" in internnav
    assert "final review records" in internnav
    assert "machine-readable closure artifacts" in internnav
    assert "not a new navigation metric" not in internnav
    assert r"\input{tables/tab_official_scene_submission_closure_status}" not in internnav


def test_supplement_internnav_upload_gate_closure_card_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_internnav_upload_gate_closure_card"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_internnav_upload_gate_closure_card.png"]
    assert {
        "paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
        "paper/shared/figures/supplement/internnav_selected6_case01.png",
        "paper/shared/figures/supplement/internnav_selected6_case02.png",
        "paper/shared/figures/supplement/internnav_selected6_case03.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case01.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case02.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case03.png",
        "paper/shared/figures/ai_slots/fig_supplement_internnav_upload_gate_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_internnav_upload_gate_closure_card.yaml",
        "paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_plan.json",
        "paper/shared/evidence/raw/official_scene_submission_closure/official_scene_performance_runs.csv",
        "paper/shared/evidence/raw/internnav_vln_downstream/official_selected_qualitative_videos/package_index.json",
        "paper/shared/evidence/raw/official_scene_submission_closure/official_scene_claim_audit_checklist.json",
        "paper/shared/evidence/raw/official_scene_submission_closure/official_scene_claim_audit_decision.json",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_internnav_upload_gate_closure_card.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_internnav_upload_gate_closure_card"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["upload_gate"] == "paper/shared/figures/ai_slots/fig_supplement_internnav_upload_gate_v2_ai_slot.png"
    assert manifest["replaceable_by_real_render"] == ["upload_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 2100
    assert 0.70 <= width / height <= 0.90
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.28
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_material_claim_boundary_atlas_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_material_claim_boundary_atlas"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_material_claim_boundary_atlas.png"]
    assert {
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/ai_slots/fig_supplement_material_claim_boundary_gate_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_material_claim_boundary_atlas.yaml",
        "paper/shared/evidence/raw/material_effect_baseline/material_effect_risk_profile.json",
        "paper/shared/tables/tab_material_effect_risk_matrix.tex",
        "paper/shared/tables/tab_material_safe_conversion_recommender.tex",
    }.issubset(set(figure["sources"]))
    section = read_text(PAPER / "venues/acl27/sections/supplement/04_material_effects.tex")
    assert "selected NVIDIA failure diagnostic" in " ".join(section.split())

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_material_claim_boundary_atlas.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_material_claim_boundary_atlas"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["material_claim_boundary_gate"] == (
        "paper/shared/figures/ai_slots/fig_supplement_material_claim_boundary_gate_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["material_claim_boundary_gate"]
    generator = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    footer_block = generator.split("def _draw_material_claim_boundary_gate_footer", 1)[1].split(
        "\ndef build_material_claim_boundary_atlas", 1
    )[0]
    assert "MATERIAL_CLAIM_BOUNDARY_GATE_AI_SLOT, (slot_w, slot_h), cover=True" not in footer_block

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert height >= 1850
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.26
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_material_decision_map_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_material_decision_map"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_material_decision_map.png"]
    assert {
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/ai_slots/fig_supplement_material_decision_gate_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_material_decision_map.yaml",
        "paper/shared/evidence/raw/material_effect_baseline/material_effect_risk_profile.json",
        "paper/shared/evidence/raw/reviewer_closure_package/material_safe_conversion_recommender.json",
        "paper/shared/tables/material_effect_risk_matrix.csv",
        "paper/shared/tables/material_safe_conversion_recommender.csv",
    }.issubset(set(figure["sources"]))
    section = read_text(PAPER / "venues/acl27/sections/supplement/04_material_effects.tex")
    assert "risk matrix and lightweight recommender" in " ".join(section.split())
    composer = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    assert "_fit(MATERIAL_DECISION_GATE_AI_SLOT, (slot_w, slot_h), cover=False)" in composer

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_material_decision_map.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_material_decision_map"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["material_decision_gate"] == (
        "paper/shared/figures/ai_slots/fig_supplement_material_decision_gate_v2_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["material_decision_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert 2380 <= height <= 2580
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.25
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_task_media_atlases_are_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    expected = {
        "fig_supplement_material_diagnostic_atlas": {
            "output": "paper/shared/figures/fig_supplement_material_diagnostic_atlas.png",
            "sources": {
                "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
                "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
            },
        },
        "fig_supplement_navigation_media_atlas": {
            "output": "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
            "sources": {
                "paper/shared/figures/fig_internnav_downstream_panel.png",
                "paper/shared/figures/fig_internnav_rollout_stills.png",
                "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
            },
        },
    }

    by_id = {figure["id"]: figure for figure in sources["figures"]}
    for figure_id, spec in expected.items():
        assert figure_id in by_id
        figure = by_id[figure_id]
        assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
        assert figure["outputs"] == [spec["output"]]
        assert spec["sources"].issubset(set(figure["sources"]))

        output = ROOT / spec["output"]
        assert output.exists()
        with Image.open(output) as image:
            width, height = image.size
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
        assert width >= 1600
        assert height >= 2000
        active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
        assert active.mean() >= 0.30


def test_supplement_navigation_media_atlas_uses_non_cover_index_row_summaries() -> None:
    script = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    build_block = script.split("def build_navigation_atlas() -> None:", 1)[1].split("\ndef _case_frame_tile", 1)[0]
    internnav = read_text(PAPER / "venues/acl27/sections/supplement/05_internnav_visuals.tex")

    assert "Selected6 index rows 05-06" in build_block
    assert "0036/0066 official still rows" in build_block
    assert "_navigation_pair_row_cards(" in build_block
    assert "_navigation_0036_row_detail_cards(" in build_block
    assert "crop=(0, 420, 1706" not in build_block
    assert "cover=True" not in build_block
    assert "compact index-row context" in internnav
    assert "compact index-sheet context" not in internnav


def test_acl_supplement_intro_pages_have_real_visual_strips() -> None:
    material = read_text(PAPER / "venues/acl27/sections/supplement/04_material_effects.tex")
    internnav = read_text(PAPER / "venues/acl27/sections/supplement/05_internnav_visuals.tex")

    assert "fig_supplement_material_intro_column.png" in material
    assert (
        r"\includegraphics[width=0.96\textwidth,height=0.78\textheight,keepaspectratio]{figures/fig_supplement_material_intro_column.png}"
        in material
    )
    assert "fig_supplement_navigation_intro_column.png" in internnav
    assert "Navigation evidence opener" in internnav
    assert "opener summarizes the review packet" in internnav
    assert "not a new" not in internnav
    assert "navigation metric or benchmark run" not in " ".join(internnav.split())
    assert (
        r"\includegraphics[width=0.96\textwidth,height=0.76\textheight,keepaspectratio]{figures/fig_supplement_navigation_intro_column.png}"
        in internnav
    )
    assert r"\captionof{figure}" in internnav
    assert "fig_supplement_material_intro_strip.png" not in material
    assert "fig_supplement_navigation_intro_strip.png" not in internnav


def test_supplement_intro_strips_are_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    expected = {
        "fig_supplement_material_intro_column": {
            "output": "paper/shared/figures/fig_supplement_material_intro_column.png",
            "sources": {
                "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
                "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
            },
        },
        "fig_supplement_navigation_intro_column": {
            "output": "paper/shared/figures/fig_supplement_navigation_intro_column.png",
            "sources": {
                "paper/shared/figures/fig_internnav_downstream_panel.png",
                "paper/shared/figures/fig_internnav_rollout_stills.png",
                "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
                "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
                "paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png",
                "paper/shared/figures/supplement/internnav_selected6_case01.png",
                "paper/shared/figures/supplement/internnav_selected6_case02.png",
                "paper/shared/figures/supplement/internnav_selected6_case03.png",
                "paper/shared/figures/supplement/internnav_selected6_case04.png",
                "paper/shared/figures/supplement/internnav_selected6_case05.png",
                "paper/shared/figures/supplement/internnav_selected6_case06.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case01.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case02.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case03.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case04.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case05.png",
                "paper/shared/figures/supplement/internnav_0036_0066_case06.png",
                "paper/shared/figures/ai_slots/fig_supplement_navigation_review_gate_ai_slot.png",
                "paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_intro_column.yaml",
            },
            "ai_slot": "paper/shared/figures/ai_slots/fig_supplement_navigation_review_gate_ai_slot.png",
            "manifest": "paper/shared/figures/ai_slot_manifests/fig_supplement_navigation_intro_column.yaml",
        },
    }

    by_id = {figure["id"]: figure for figure in sources["figures"]}
    for figure_id, spec in expected.items():
        assert figure_id in by_id
        figure = by_id[figure_id]
        assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
        assert figure["outputs"] == [spec["output"]]
        assert spec["sources"].issubset(set(figure["sources"]))
        if "manifest" in spec:
            manifest = read_yaml(ROOT / spec["manifest"])
            assert manifest["mode"] == "ai_slot_composition"
            assert manifest["figure_id"] == figure_id
            assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
            assert manifest["slots"]["navigation_review_gate"] == spec["ai_slot"]
            assert manifest["replaceable_by_real_render"] == ["navigation_review_gate"]

        output = ROOT / spec["output"]
        assert output.exists()
        with Image.open(output) as image:
            width, height = image.size
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
        if figure_id == "fig_supplement_navigation_intro_column":
            assert width >= 1600
            assert height >= 1250
            assert 0.95 <= width / height <= 1.45
        else:
            assert width >= 1500
            assert height >= 1650
            assert 0.82 <= width / height <= 1.05
        active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
        assert active.mean() >= 0.38


def test_acl_supplement_theory_has_visual_evidence_bridge() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/06_theory.tex")

    assert "fig_supplement_theory_evidence_bridge.png" in section
    assert "Theory bridge" in section
    assert "selected-failure render wall" in section
    assert r"\captionof{figure}" in section
    assert (
        r"\includegraphics[width=\textwidth,height=0.74\textheight,keepaspectratio]{figures/fig_supplement_theory_evidence_bridge.png}"
        in section
    )
    assert r"\begin{figure}[p]" not in section
    assert "\\clearpage\n\n\\subsection{Why Selected Failures Still Matter}" not in section


def test_supplement_theory_bridge_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_theory_evidence_bridge"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_theory_evidence_bridge.png"]
    assert {
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
        "paper/shared/figures/supplement/internnav_selected6_case01.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case01.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_theory_evidence_lens_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_theory_evidence_bridge.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_theory_evidence_bridge.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_theory_evidence_bridge"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["theory_evidence_lens"] == (
        "paper/shared/figures/ai_slots/fig_supplement_theory_evidence_lens_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["theory_evidence_lens"]

    generator = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    bridge_block = generator.split("def build_theory_bridge", 1)[1].split("\ndef _draw_failure_mode_lane", 1)[0]
    material_bridge_block = generator.split("def _compose_material_bridge", 1)[1].split(
        "\ndef _draw_material_claim_row", 1
    )[0]
    assert "_compose_grounding_contract_bridge((image_w, band_image_h))" in bridge_block
    assert "_fit(VLM_CLEAN_RERENDER, (image_w, band_image_h), cover=True)" not in bridge_block
    assert "_crop_contain(MATERIAL_SUPPLEMENTAL, (24, 62, 832, 258)" in material_bridge_block
    assert "_crop_contain(MATERIAL_SUPPLEMENTAL, (24, 340, 832, 535)" in material_bridge_block
    assert "_crop_fit(MATERIAL_SUPPLEMENTAL, (24, 62, 832, 258)" not in material_bridge_block
    assert "_crop_fit(MATERIAL_SUPPLEMENTAL, (24, 340, 832, 535)" not in material_bridge_block

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert height >= 1650
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.37


def test_acl_supplement_theory_has_failure_mode_map() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/06_theory.tex")

    assert "fig_supplement_theory_failure_mode_map.png" in section
    assert (
        r"\includegraphics[width=0.98\textwidth,height=0.74\textheight,keepaspectratio]{figures/fig_supplement_theory_failure_mode_map.png}"
        in section
    )
    assert "Failure-mode interpretation map" in section
    assert r"\captionof{figure}" in section
    assert "fig_vlm_grounding_cases" not in section
    assert "Red material in these diagnostic cases" not in section


def test_supplement_theory_failure_mode_map_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_theory_failure_mode_map"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_theory_failure_mode_map.png"]
    assert {
        "paper/shared/figures/fig_material_effect_baseline_qualitative.png",
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/fig_internnav_rollout_stills.png",
        "paper/shared/figures/fig_internnav_rollout_0036_0066_main3_readable.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_theory_failure_mode_gate_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_theory_failure_mode_map.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_theory_failure_mode_map.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_theory_failure_mode_map"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["failure_mode_gate"] == (
        "paper/shared/figures/ai_slots/fig_supplement_theory_failure_mode_gate_v2_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["failure_mode_gate"]

    composer = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    assert "_fit(THEORY_FAILURE_MODE_GATE_V2_AI_SLOT, (gate_w, gate_h), cover=False)" in composer

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1700
    assert height >= 1680
    assert 0.95 <= width / height <= 1.20
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.40
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_theory_has_hypothesis_boundary_companion() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/06_theory.tex")

    assert "fig_supplement_theory_hypothesis_boundary_companion.png" in section
    figure_pos = section.index("fig_supplement_theory_hypothesis_boundary_companion.png")
    failure_map_pos = section.index("fig_supplement_theory_failure_mode_map.png")
    twocolumn_pos = section.index(r"\twocolumn")
    material_pos = section.index("Material Salience Hypothesis")
    negative_pos = section.index("Negative-Result Discipline")
    assert failure_map_pos < figure_pos < twocolumn_pos < material_pos < negative_pos
    assert "Hypothesis-scope companion" in section
    assert "render-backed lens summarizes" in section
    assert "new experiment, causal proof, or population rate" not in " ".join(section.split())
    assert "selected failure render wall" in section
    assert "render-backed lens" in section
    assert r"\captionsetup{hypcap=false}" in section
    assert (
        r"\includegraphics[width=0.86\textwidth,height=0.72\textheight,keepaspectratio]{figures/fig_supplement_theory_hypothesis_boundary_companion.png}"
        in section
    )


def test_supplement_theory_hypothesis_boundary_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_theory_hypothesis_boundary_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_theory_hypothesis_boundary_companion.png"]
    assert {
        "paper/shared/figures/fig_material_effect_supplemental_qualitative.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/bb985fd4504a1afe8516/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADY8_usd/c8ee4b66274b05d242c2/zoom_017/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADI8_usd/ef6a4fe9448f672c2ecc/zoom_017/converted/converted_0000.png",
        "paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_theory_hypothesis_boundary_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_theory_hypothesis_boundary_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert "hypothesis_boundary" in manifest["slots"]
    assert manifest["slots"]["hypothesis_boundary"] == (
        "paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png"
    )
    composer = read_text(PAPER / "shared/figures/gen_supplement_task_media_atlases.py")
    assert "slot_w = min(width - 2 * margin - 36, max(260, int(slot_h * 1.5)))" in composer
    assert "_fit(THEORY_HYPOTHESIS_BOUNDARY_V6_AI_SLOT, (slot_w, slot_h), cover=False)" in composer
    assert manifest["replaceable_by_real_render"] == ["hypothesis_boundary"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 850
    assert height >= 1520
    assert height / width >= 1.65
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.43
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015

    slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_theory_hypothesis_boundary_v6_ai_slot.png"
    assert slot.exists()
    with Image.open(slot) as image:
        slot_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    slot_active = ((slot_pixels.max(axis=2) - slot_pixels.min(axis=2) > 15) | (slot_pixels.mean(axis=2) < 238))
    assert slot_active.mean() >= 0.29


def test_acl_supplement_reproducibility_has_visual_media_manifest() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/07_reproducibility.tex")

    assert "fig_supplement_review_packet_contact_sheet.png" in section
    assert "Review-packet media manifest" in section
    assert (
        r"\includegraphics[width=0.98\textwidth,height=0.78\textheight,keepaspectratio]{figures/fig_supplement_review_packet_contact_sheet.png}"
        in section
    )
    assert "fig_supplement_source_boundary_companion.png" in section
    assert "Source-scope review companion" in section
    assert "right panel marks excluded raw/private artifacts" in section
    assert "not a new evidence source, experiment, metric, VLM run, or navigation run" not in " ".join(section.split())
    assert "visual index of tracked render figures" in " ".join(section.split())
    assert (
        r"\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{figures/fig_supplement_source_boundary_companion.png}"
        in section
    )
    assert r"\begin{figure*}[p]" in section
    assert r"\caption{" in section
    assert section.index(r"\subsection{Final Upload Decision}") < section.index("fig_supplement_source_boundary_companion.png")
    assert "\\end{figure*}\n\\clearpage" in section
    assert r"\onecolumn" in section
    assert r"\twocolumn" in section


def test_supplement_review_packet_contact_sheet_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_review_packet_contact_sheet"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_review_packet_contact_sheet.png"]
    assert {
        "paper/shared/figures/fig_render_pairs.png",
        "paper/shared/figures/fig_render_scene_evidence_wide.png",
        "paper/shared/figures/fig_grscene_qualitative.png",
        "paper/shared/figures/fig_supplement_render_atlas.png",
        "paper/shared/figures/fig_supplement_render_scene_evidence_extended.png",
        "paper/shared/figures/fig_supplement_material_diagnostic_atlas.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png",
        "paper/shared/figures/fig_supplement_navigation_media_atlas.png",
        "paper/shared/figures/supplement/internnav_selected6_case01.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case01.png",
    }.issubset(set(figure["sources"]))

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1800
    assert height >= 2100
    assert 0.78 <= width / height <= 0.90
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.25
    near_black = pixels.mean(axis=2) < 8
    assert near_black.mean() < 0.025

    generator = (PAPER / "shared/figures/gen_supplement_task_media_atlases.py").read_text(encoding="utf-8")
    contact_row_block = generator.split("def _draw_contact_row", 1)[1].split("\ndef _draw_vlm_guide_row", 1)[0]
    assert "label_w = 280" in contact_row_block
    assert "_crop_contain(path, crop" in contact_row_block
    assert "_crop_fit(path, crop" not in contact_row_block
    contact_sheet_block = generator.split("def build_review_packet_contact_sheet", 1)[1].split(
        "\ndef _draw_source_boundary_tile", 1
    )[0]
    assert "(810, 108, 1582, 490)" in contact_sheet_block
    assert "1782" not in contact_sheet_block


def test_supplement_source_boundary_companion_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_source_boundary_companion"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_source_boundary_companion.png"]
    assert {
        "paper/shared/figures/fig_supplement_review_packet_contact_sheet.png",
        "paper/shared/figures/fig_supplement_render_atlas_opener.png",
        "paper/shared/figures/fig_supplement_material_diagnostic_atlas.png",
        "paper/shared/figures/fig_supplement_vlm_clean_rerender_panel.png",
        "paper/shared/figures/fig_supplement_navigation_media_boundary_strip.png",
        "paper/shared/figures/supplement/internnav_selected6_case04.png",
        "paper/shared/figures/supplement/internnav_0036_0066_case04.png",
        "paper/shared/figures/ai_slots/fig_supplement_source_boundary_gate_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_source_boundary_companion.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_source_boundary_companion.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_source_boundary_companion"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert manifest["slots"]["source_boundary_gate"] == "paper/shared/figures/ai_slots/fig_supplement_source_boundary_gate_ai_slot.png"
    assert manifest["replaceable_by_real_render"] == ["source_boundary_gate"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1200
    assert 1300 <= height <= 1450
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.43
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_acl_supplement_grscenes_vlm_has_visual_guide() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/03_grscenes_visuals.tex")

    assert "fig_supplement_grscenes_vlm_visual_guide.png" in section
    assert "GRScenes VLM diagnostic overview" in section
    assert r"\captionof{figure}" in section
    assert (
        r"\includegraphics[width=\textwidth,height=0.84\textheight,keepaspectratio]{figures/fig_supplement_grscenes_vlm_visual_guide.png}"
        in section
    )
    assert "route diagram summarizes how the page is organized" in section
    assert r"\onecolumn" in section
    assert r"\twocolumn" not in section
    assert "fig_vlm_grounding_cases.png" not in section


def test_acl_supplement_grscenes_has_diagnostic_case_atlas() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/03_grscenes_visuals.tex")

    assert "fig_supplement_grscenes_diagnostic_case_atlas.png" in section
    assert "GRScenes diagnostic case atlas" in section
    assert r"\captionof{figure}" in section
    assert "fig_vlm_grounding_cases.png" not in section


def test_supplement_grscenes_diagnostic_case_atlas_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_grscenes_diagnostic_case_atlas"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_grscenes_diagnostic_case_atlas.png"]
    assert {
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/47aa36277a54f6ca90cc.zoom_018.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/f35ef3d86c42446b7ddf.zoom_018.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/c27086f557d316584264.zoom_018.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_paired_render_reports/e2ec085d524d5df4455d.zoom_020.clean_rerender_20260528.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
    }.issubset(set(figure["sources"]))

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert height >= 1500
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.36
    red_fallback = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 90) & (pixels[:, :, 2] < 90)
    assert red_fallback.mean() < 0.015


def test_supplement_grscenes_vlm_visual_guide_is_registered_and_dense() -> None:
    from PIL import Image
    import numpy as np

    sources = read_yaml(PAPER / "shared/figures/sources.yaml")
    by_id = {figure["id"]: figure for figure in sources["figures"]}
    figure = by_id["fig_supplement_grscenes_vlm_visual_guide"]

    assert figure["generated_by"] == "paper/shared/figures/gen_supplement_task_media_atlases.py"
    assert figure["outputs"] == ["paper/shared/figures/fig_supplement_grscenes_vlm_visual_guide.png"]
    assert {
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_expanded30_target_projection_qa_report.json",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/47aa36277a54f6ca90cc/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/f35ef3d86c42446b7ddf/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADA8_usd/c27086f557d316584264/zoom_018/converted/converted_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/original/original_0000.png",
        "paper/shared/evidence/raw/grscene_vlm_grounding/retake_zoom_renders/MV7J6NIKTKJZ2AABAAAAADQ8_usd/e2ec085d524d5df4455d/zoom_020/converted/converted_0000.png",
        "paper/shared/figures/fig_grscene_qualitative.png",
        "paper/shared/figures/fig_render_scene_evidence_wide.png",
        "paper/shared/figures/fig_supplement_render_atlas.png",
        "paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png",
        "paper/shared/figures/ai_slot_manifests/fig_supplement_grscenes_vlm_visual_guide.yaml",
    }.issubset(set(figure["sources"]))

    manifest = read_yaml(PAPER / "shared/figures/ai_slot_manifests/fig_supplement_grscenes_vlm_visual_guide.yaml")
    assert manifest["mode"] == "ai_slot_composition"
    assert manifest["figure_id"] == "fig_supplement_grscenes_vlm_visual_guide"
    assert manifest["claim_boundary"] == "Exposition only; not experimental evidence."
    assert (
        manifest["slots"]["reading_route"]
        == "paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png"
    )
    assert manifest["replaceable_by_real_render"] == ["reading_route"]

    output = ROOT / figure["outputs"][0]
    assert output.exists()
    with Image.open(output) as image:
        width, height = image.size
        pixels = np.asarray(image.convert("RGB"), dtype=np.int16)

    assert width >= 1600
    assert height >= 1680
    assert height / width >= 0.92
    active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 238))
    assert active.mean() >= 0.37

    ai_slot = ROOT / "paper/shared/figures/ai_slots/fig_supplement_grscenes_vlm_reading_route_v2_ai_slot.png"
    assert ai_slot.exists()
    with Image.open(ai_slot) as image:
        ai_pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
    ai_active = ((ai_pixels.max(axis=2) - ai_pixels.min(axis=2) > 15) | (ai_pixels.mean(axis=2) < 238))
    assert ai_active.mean() >= 0.18


def test_acl_supplement_sources_stay_anonymous() -> None:
    root = PAPER / "venues/acl27"
    paths = [root / "supplement.tex"]
    paths.extend(sorted((root / "sections/supplement").glob("*.tex")))
    forbidden = (
        "/cpfs",
        "/home/",
        "/root/",
        "zhuzihou",
        "jandan138",
        "github.com/jandan138",
        "ConvertAsset.git",
    )
    offenders: list[str] = []
    for path in paths:
        text = read_text(path)
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}: {token}")
    assert offenders == []


def test_acl_supplement_navigation_0036_crops_are_readable_panels() -> None:
    from PIL import Image
    import numpy as np

    generator = read_text(PAPER / "shared/figures/gen_acl_supplement_navigation_crops.py")
    assert "crop_0036_rows" in generator

    crops = sorted((PAPER / "shared/figures/supplement").glob("internnav_0036_0066_case*.png"))
    assert len(crops) == 6
    for crop in crops:
        with Image.open(crop) as image:
            width, height = image.size
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
        assert height / width >= 0.4, crop.name
        active = ((pixels.max(axis=2) - pixels.min(axis=2) > 15) | (pixels.mean(axis=2) < 220))
        assert active.mean() >= 0.20, crop.name


def test_acl_supplement_navigation_selected6_crops_keep_titles_visible() -> None:
    from PIL import Image
    import numpy as np

    crops = sorted((PAPER / "shared/figures/supplement").glob("internnav_selected6_case*.png"))
    assert len(crops) == 6
    for crop in crops:
        with Image.open(crop) as image:
            pixels = np.asarray(image.convert("RGB"), dtype=np.int16)
        top_band = pixels[:40]
        dark_rows = np.where(top_band.mean(axis=2) < 80)[0]
        assert dark_rows.size > 0, crop.name
        assert int(dark_rows.min()) >= 5, f"{crop.name} title is clipped at the top edge"


def test_acl_supplement_groups_internnav_case_figures() -> None:
    section = read_text(PAPER / "venues/acl27/sections/supplement/05_internnav_visuals.tex")
    supplement = read_text(PAPER / "venues/acl27/supplement.tex")

    assert r"\newcommand{\suppcasepair}" in supplement
    assert r"\suppfig{figures/supplement/internnav_" not in section
    assert section.count(r"\suppcasepair{") == 4
    assert section.count("figures/supplement/internnav_selected6_case") == 4
    assert section.count("figures/supplement/internnav_0036_0066_case") == 4
    assert "fig_supplement_internnav_selected6_neutral_companion.png" in section
    assert "figures/supplement/internnav_selected6_case05" not in section
    assert "figures/supplement/internnav_selected6_case06" not in section
    assert "fig_supplement_internnav_0036_neutral_companion.png" in section
    assert "figures/supplement/internnav_0036_0066_case05" not in section
    assert "figures/supplement/internnav_0036_0066_case06" not in section
