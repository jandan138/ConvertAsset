import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SCRIPT = PAPER / "venues/acl27/scripts/check_evidence_numbers.py"


def load_module():
    assert SCRIPT.exists(), "ACL evidence-number checker is missing"
    spec = importlib.util.spec_from_file_location("acl_evidence_numbers", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_acl_evidence_numbers_match_sources_and_manuscript() -> None:
    module = load_module()

    report = module.check_acl_evidence_numbers(PAPER)

    assert report["ok"] is True
    assert report["violations"] == []

    snapshot = report["snapshot"]
    assert snapshot["proxy"]["asset_count"] == 4
    assert snapshot["proxy"]["render_pair_count"] == 24
    assert snapshot["proxy"]["psnr"] == "35.52"
    assert snapshot["proxy"]["ssim"] == "0.990"
    assert snapshot["proxy"]["lpips"] == "0.020"
    assert snapshot["proxy"]["clip"] == "0.925"
    assert snapshot["proxy"]["dinov2"] == "0.872"

    assert snapshot["stress"]["gemma_answer_original"] == "30/30"
    assert snapshot["stress"]["gemma_answer_converted"] == "30/30"
    assert snapshot["stress"]["gemma_norm_original"] == "27/30"
    assert snapshot["stress"]["gemma_norm_converted"] == "29/30"
    assert snapshot["stress"]["gemma_pair_agreement"] == "28/30"
    assert snapshot["stress"]["qwen_raw_original"] == "22/29"
    assert snapshot["stress"]["qwen_raw_converted"] == "19/29"
    assert snapshot["stress"]["qwen_norm_original"] == "3/29"
    assert snapshot["stress"]["qwen_norm_converted"] == "3/29"

    assert snapshot["internnav"]["episode_count"] == 99
    assert snapshot["internnav"]["official_scene_count"] == 3
    assert snapshot["internnav"]["SR"] == "0.5253/0.4848"
    assert snapshot["internnav"]["SPL"] == "0.4739/0.4298"
    assert snapshot["internnav"]["NE"] == "3.6798/3.6306"
    assert snapshot["internnav"]["TL"] == "6.9754/7.0598"

    assert snapshot["official_scene_stability"]["success_total"] == 18
    assert snapshot["official_scene_stability"]["failure_total"] == 0


def test_text_marker_validation_rejects_missing_or_stale_numbers() -> None:
    module = load_module()
    snapshot = module.build_evidence_snapshot(PAPER)
    bad_text = {
        "bad.tex": (
            "Mean PSNR is 35.53 dB, mean SSIM is 0.990, and the official "
            "KuJiaLe route covers 99 paired episodes."
        )
    }

    violations = module.find_text_marker_violations(
        bad_text,
        module.build_required_text_markers(snapshot),
    )

    assert any(violation["claim_id"] == "proxy_psnr" for violation in violations)
    assert any(violation["claim_id"] == "internnav_sr_spl_ne_tl" for violation in violations)
