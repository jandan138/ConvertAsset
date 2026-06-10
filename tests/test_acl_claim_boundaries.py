import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SCRIPT = PAPER / "venues/acl27/scripts/check_claim_boundaries.py"


def load_module():
    assert SCRIPT.exists(), "ACL claim-boundary checker is missing"
    spec = importlib.util.spec_from_file_location("acl_claim_boundaries", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_acl_manuscript_preserves_claim_boundaries() -> None:
    module = load_module()

    report = module.check_claim_boundaries(PAPER)

    assert report["ok"] is True
    assert report["violations"] == []
    assert report["checked_files"]


def test_positive_forbidden_claims_are_rejected() -> None:
    module = load_module()
    unsafe_text = (
        "Our converted scenes establish broad embodied-navigation robustness. "
        "The official route establishes all InternNav benchmark robustness. "
        "The official-scene noMDL speedup is significant. "
        "The NVIDIA official-scene performance comparison shows our method wins. "
        "Procedural texture preservation is successful after conversion."
    )

    violations = module.find_claim_boundary_violations(
        {"unsafe.tex": unsafe_text}
    )

    assert {violation["rule_id"] for violation in violations} >= {
        "broad_embodied_robustness",
        "all_scene_robustness",
        "official_scene_speedup",
        "nvidia_official_scene_performance",
        "procedural_texture_success",
    }


def test_guardrailed_forbidden_topics_are_allowed() -> None:
    module = load_module()
    guarded_text = (
        "The current evidence does not establish broad embodied-navigation "
        "robustness. The official-scene performance table supports loadability "
        "rather than speedup. We do not report an NVIDIA official-scene "
        "performance row because matching conversions have not been generated. "
        "Procedural texture remains a limitation case for both converters."
    )

    violations = module.find_claim_boundary_violations(
        {"guarded.tex": guarded_text}
    )

    assert violations == []


def test_internal_venue_wrapper_phrasing_is_rejected() -> None:
    module = load_module()

    violations = module.find_venue_wrapper_phrasing_violations(
        {
            "sections/method.tex": "The second gate is the ACL-facing VLM grounding protocol.",
            "sections/results.tex": "This is not the main ACL claim.",
            "sections/abstract.tex": "The result is a claim-bounded ACL protocol.",
            "sections/ethical-considerations.tex": "Any ACL submission should document provenance.",
            "shared/tables/tab.tex": "Evidence-gate registry for the ACL/ARR claim boundary.",
        }
    )

    assert {violation["rule_id"] for violation in violations} == {
        "acl_facing",
        "main_acl_claim",
        "acl_protocol",
        "any_acl_submission",
        "acl_arr_claim_boundary",
    }


def test_unsafe_qualitative_figure_is_rejected_from_acl_main_text() -> None:
    module = load_module()

    violations = module.find_unsafe_figure_violations(
        {"sections/results.tex": r"\includegraphics{figures/fig_vlm_grounding_cases.pdf}"}
    )

    assert violations == [
        {
            "path": "sections/results.tex",
            "rule_id": "unsafe_vlm_grounding_qualitative_panel",
            "description": "The current VLM grounding qualitative panel is not final-upload safe.",
            "figure": "fig_vlm_grounding_cases",
        }
    ]


def test_unsafe_material_effect_figure_is_rejected_from_acl_main_text() -> None:
    module = load_module()

    violations = module.find_unsafe_figure_violations(
        {
            "sections/results.tex": (
                r"\includegraphics[width=\textwidth]"
                r"{figures/fig_material_effect_baseline_qualitative.png}"
            )
        }
    )

    assert violations == [
        {
            "path": "sections/results.tex",
            "rule_id": "unsafe_material_effect_qualitative_panel",
            "description": "The material-effect qualitative panel requires clean original-MDL provenance.",
            "figure": "fig_material_effect_baseline_qualitative",
        }
    ]


def test_clean_material_effect_figure_is_allowed_after_provenance_gate() -> None:
    module = load_module()

    violations = module.find_unsafe_figure_violations(
        {
            "sections/results.tex": (
                r"\includegraphics[width=\textwidth]"
                r"{figures/fig_material_effect_baseline_qualitative.png}"
            )
        },
        material_effect_clean_provenance_ready=True,
    )

    assert violations == []


def test_current_acl_manuscript_excludes_unsafe_qualitative_figure() -> None:
    module = load_module()

    report = module.check_claim_boundaries(PAPER)

    assert report["unsafe_figure_violations"] == []


def test_acl_material_effect_static_gates_do_not_imply_effect_preservation() -> None:
    method = (PAPER / "venues/acl27/sections/method.tex").read_text(encoding="utf-8")
    results = (PAPER / "venues/acl27/sections/results.tex").read_text(encoding="utf-8")
    method_words = " ".join(method.split())
    results_words = " ".join(results.split())

    assert "covers a practical subset of MDL" in method_words
    assert "They mark cues rather than rates or full MDL semantics" in results_words
