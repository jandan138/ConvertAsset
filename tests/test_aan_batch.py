"""Tests for convert_asset.asset_application_normalizer.batch."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import yaml

from convert_asset.asset_application_normalizer.batch import run_batch_admission


def _request_yaml(tmp_path, items):
    path = tmp_path / "request.yaml"
    path.write_text(yaml.safe_dump({"request_id": "r1", "items": items}), encoding="utf-8")
    return path


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_batch_marks_sha_mismatch_without_running(tmp_path) -> None:
    source = tmp_path / "a.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    request = _request_yaml(
        tmp_path,
        [
            {
                "candidate_id": "cand_a",
                "source_usd": str(source),
                "source_sha256": "0" * 64,
                "source_scope": "/World",
            }
        ],
    )
    calls = []

    def fake_runner(item, out_dir):
        calls.append(item["candidate_id"])
        return SimpleNamespace(return_code=0, manifest_path=None, overall_status="pass")

    summary = run_batch_admission(request, tmp_path / "out", runner=fake_runner)

    assert calls == []
    record = summary["results"][0]
    assert record["status"] == "sha256_mismatch"
    assert record["sha256_match"] is False


def test_batch_runs_matching_candidates_and_collects_status(tmp_path) -> None:
    source = tmp_path / "a.usda"
    source.write_text("#usda 1.0\n", encoding="utf-8")
    request = _request_yaml(
        tmp_path,
        [
            {
                "candidate_id": "cand_a",
                "source_usd": str(source),
                "source_sha256": _sha256(source),
                "source_scope": "/World",
            }
        ],
    )

    def fake_runner(item, out_dir):
        return SimpleNamespace(
            return_code=0,
            manifest_path=None,
            overall_status="pass",
        )

    summary = run_batch_admission(request, tmp_path / "out", runner=fake_runner)

    record = summary["results"][0]
    assert record["status"] == "done"
    assert record["sha256_match"] is True
    assert record["overall_status"] == "pass"
    assert record["return_code"] == 0
