from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/attach_role_candidate_baseline.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("attach_role_baseline", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_passing_baseline_does_not_promote_role_candidates(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    report = batch / "evidence/stage/report.json"
    report.parent.mkdir(parents=True)
    (batch / "manifest.json").write_text(json.dumps({"packages": []}))
    report.write_text(json.dumps({"overall_status": "pass", "required_cold_runs": 3}))

    result = _module().attach(batch=batch, report=report)

    assert result["baseline_stage_update"]["status"] == "pass"
    assert result["promotion"]["allowed"] is False
    assert result["overall_status"] == "candidate_role_gates_pending"
