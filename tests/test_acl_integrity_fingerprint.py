import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/check_integrity_fingerprint.py"


def load_module():
    assert SCRIPT.exists(), "ACL integrity fingerprint checker is missing"
    spec = importlib.util.spec_from_file_location("acl_integrity_fingerprint", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_acl_integrity_fingerprint_matches_sources() -> None:
    module = load_module()

    report = module.check_fingerprint(ROOT / "paper")

    assert report["ok"] is True
    assert report["source_count"] >= 20


def test_integrity_fingerprint_tracks_expected_current_sources() -> None:
    module = load_module()

    source_paths = {
        path.relative_to(ROOT / "paper").as_posix()
        for path in module.iter_source_paths(ROOT / "paper")
    }

    assert "venues/acl27/main.tex" in source_paths
    assert "venues/acl27/sections/abstract.tex" in source_paths
    assert "shared/sections/appendix.tex" in source_paths
    assert "shared/references.bib" in source_paths
    assert "venues/acl27/OPENREVIEW_METADATA_PACKET.md" in source_paths
    assert "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md" in source_paths
    assert "venues/acl27/TARGET_CALL_POLICY_AUDIT.md" in source_paths
    assert "shared/evidence/references/verification_report.md" in source_paths
    assert "shared/tables/grscenes_vlm_stress_expanded30.csv" in source_paths
    assert (
        "shared/evidence/raw/internnav_vln_downstream/"
        "official_val_unseen_99/paired_99_summary.json"
    ) in source_paths


def test_integrity_fingerprint_detects_source_drift(tmp_path: Path) -> None:
    module = load_module()
    paper_root = tmp_path / "paper"
    (paper_root / "nested").mkdir(parents=True)
    source_a = paper_root / "source-a.md"
    source_b = paper_root / "nested/source-b.csv"
    source_a.write_text("original source\n", encoding="utf-8")
    source_b.write_text("metric,value\nx,1\n", encoding="utf-8")
    source_relpaths = ("source-a.md", "nested/source-b.csv")
    fingerprint_path = paper_root / "fingerprint.json"

    module.write_fingerprint(
        module.build_fingerprint(paper_root, source_relpaths=source_relpaths),
        fingerprint_path,
    )

    module.check_fingerprint(
        paper_root,
        fingerprint_path=fingerprint_path,
        source_relpaths=source_relpaths,
    )

    source_a.write_text("changed source\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        module.check_fingerprint(
            paper_root,
            fingerprint_path=fingerprint_path,
            source_relpaths=source_relpaths,
        )
