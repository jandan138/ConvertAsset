import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SCRIPT = PAPER / "venues/acl27/scripts/check_metadata_consistency.py"


def load_module():
    assert SCRIPT.exists(), "ACL metadata consistency checker is missing"
    spec = importlib.util.spec_from_file_location("acl_metadata_consistency", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_acl_openreview_metadata_matches_title_and_abstract_sources() -> None:
    module = load_module()

    report = module.check_metadata_consistency(PAPER)

    assert report["title"] == (
        "Material Conversion as a Controlled Perturbation for "
        "Vision-Language Grounding in Synthetic 3D Scenes"
    )
    assert report["metadata_title"] == report["title"]
    assert report["metadata_abstract"] == report["source_abstract"]
    assert report["abstract_word_count"] == 171
    assert report["abstract_word_count"] <= 200


def test_acl_abstract_uses_bounded_proxy_fidelity_wording() -> None:
    module = load_module()

    report = module.check_metadata_consistency(PAPER)
    abstract = report["source_abstract"]

    assert "proxy fidelity does not determine grounding behavior" not in abstract
    assert "proxy fidelity does not certify grounding behavior" not in abstract
    assert "proxy fidelity does not certify downstream grounding" not in abstract
    assert "while grounding behavior still requires task-level checks" in abstract
    assert (
        "scores 27/30 original versus 29/30 converted normalized-1000 point hits"
        in abstract
    )
    assert "scores 27/30 versus 29/30 normalized-1000 point hits" not in abstract
    assert "downstream robustness claims" not in abstract
    assert "from merging into one task claim" not in abstract
    assert "collapsed into one task result" in abstract
    assert report["metadata_abstract"] == abstract
