import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper/venues/acl27/scripts/run_preupload_gate.py"


def load_module():
    assert SCRIPT.exists(), "ACL pre-upload gate runner is missing"
    spec = importlib.util.spec_from_file_location("acl_preupload_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preupload_plan_orders_checks_before_staging() -> None:
    module = load_module()

    plan = module.build_preupload_plan(ROOT)
    step_ids = [step["id"] for step in plan]

    assert step_ids == [
        "claim_boundaries",
        "metadata_consistency",
        "focused_pytest",
        "clean_acl_build",
        "latex_log_scan",
        "stage_packet",
        "packet_inventory",
        "packet_private_scan",
        "packet_acknowledgment_scan",
        "pdfinfo",
        "pdftotext_sections",
    ]
    assert step_ids.index("claim_boundaries") < step_ids.index("stage_packet")
    assert step_ids.index("metadata_consistency") < step_ids.index("stage_packet")


def test_packet_inventory_rejects_extra_files(tmp_path: Path) -> None:
    module = load_module()
    packet_root = tmp_path / "packet"
    for relative in module.EXPECTED_PACKET_FILES:
        path = packet_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")
    extra = packet_root / "extra.txt"
    extra.write_text("not allowed", encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected"):
        module.check_packet_inventory(packet_root)


def test_text_scan_detects_private_tokens(tmp_path: Path) -> None:
    module = load_module()
    packet_root = tmp_path / "packet"
    packet_root.mkdir()
    leaked = packet_root / "leak.md"
    leaked.write_text("local path /cpfs/user/example leaked", encoding="utf-8")

    with pytest.raises(ValueError, match="/cpfs"):
        module.scan_text_forbidden_tokens(
            packet_root,
            tokens=module.PRIVATE_TOKENS,
            label="private token",
        )
