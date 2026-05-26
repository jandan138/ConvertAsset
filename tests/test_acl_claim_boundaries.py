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
        "The official-scene noMDL speedup is significant. "
        "The NVIDIA official-scene performance comparison shows our method wins. "
        "Procedural texture preservation is successful after conversion."
    )

    violations = module.find_claim_boundary_violations(
        {"unsafe.tex": unsafe_text}
    )

    assert {violation["rule_id"] for violation in violations} >= {
        "broad_embodied_robustness",
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

