import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/stage_submission_packet.py"
FORBIDDEN_TOKENS = (
    "/cpfs",
    "/home/",
    "/root/",
    "zhuzihou",
    "jandan138",
    "github.com/jandan138",
    "ConvertAsset.git",
)


def load_module():
    assert SCRIPT.exists(), "ACL submission staging script is missing"
    spec = importlib.util.spec_from_file_location("acl_submission_staging", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_fake_paper_root(tmp_path: Path) -> Path:
    paper_root = tmp_path / "paper"
    pdf_path = paper_root / "venues/acl27/build/main.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF-1.7\n% fake anonymous pdf\n")
    checklist_path = paper_root / "venues/acl27/OPENREVIEW_RESPONSIBLE_NLP_CHECKLIST.md"
    checklist_path.write_text(
        "# OpenReview Responsible NLP Checklist\n\n"
        "Copy these answers into the official ARR/OpenReview form.\n",
        encoding="utf-8",
    )
    return paper_root


def read_packet_texts(packet_root: Path) -> str:
    texts = []
    for path in sorted(packet_root.rglob("*")):
        if path.is_file() and path.suffix in {".json", ".md", ".txt"}:
            texts.append(path.read_text(encoding="utf-8"))
    return "\n".join(texts)


def test_stage_submission_packet_builds_sanitized_minimal_packet(tmp_path: Path) -> None:
    module = load_module()
    paper_root = make_fake_paper_root(tmp_path)
    out_dir = tmp_path / "acl27_arr_candidate"

    manifest = module.stage_submission_packet(
        paper_root=paper_root,
        out_dir=out_dir,
        packet_id="acl27_arr_candidate_test",
        include_media=False,
        force=False,
    )

    assert (out_dir / "main.pdf").read_bytes() == b"%PDF-1.7\n% fake anonymous pdf\n"
    assert (out_dir / "openreview/RESPONSIBLE_NLP_CHECKLIST.md").exists()
    assert (out_dir / "supplemental/README.md").exists()
    assert (out_dir / "supplemental/manifest.json").exists()
    assert manifest["packet_id"] == "acl27_arr_candidate_test"
    assert manifest["include_media"] is False
    assert manifest["claim_boundary"] == "selected_media_excluded_pending_license_and_anonymization_review"
    assert "raw source scenes" in manifest["excluded_materials"]
    assert "local model checkpoints" in manifest["excluded_materials"]
    assert "selected qualitative videos" in manifest["excluded_materials"]
    assert sorted(item["path"] for item in manifest["files"]) == [
        "main.pdf",
        "openreview/RESPONSIBLE_NLP_CHECKLIST.md",
        "supplemental/README.md",
        "supplemental/manifest.json",
    ]
    assert not (out_dir / "raw").exists()
    assert not list(out_dir.rglob("*.mp4"))

    combined_text = read_packet_texts(out_dir)
    for token in FORBIDDEN_TOKENS:
        assert token not in combined_text


def test_stage_submission_packet_refuses_existing_directory_without_force(tmp_path: Path) -> None:
    module = load_module()
    paper_root = make_fake_paper_root(tmp_path)
    out_dir = tmp_path / "acl27_arr_candidate"
    out_dir.mkdir()
    (out_dir / "leftover.txt").write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(FileExistsError):
        module.stage_submission_packet(
            paper_root=paper_root,
            out_dir=out_dir,
            packet_id="acl27_arr_candidate_test",
            include_media=False,
            force=False,
        )


def test_manifest_json_matches_returned_manifest(tmp_path: Path) -> None:
    module = load_module()
    paper_root = make_fake_paper_root(tmp_path)
    out_dir = tmp_path / "acl27_arr_candidate"

    manifest = module.stage_submission_packet(
        paper_root=paper_root,
        out_dir=out_dir,
        packet_id="acl27_arr_candidate_test",
        include_media=False,
        force=False,
    )

    manifest_path = out_dir / "supplemental/manifest.json"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
