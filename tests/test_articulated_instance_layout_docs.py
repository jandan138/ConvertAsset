from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_articulated_appliance_docs_distinguish_candidate_from_v2_final() -> None:
    design = (ROOT / "docs/design/articulated-appliance-relocation.md").read_text(
        encoding="utf-8"
    )
    operation = (ROOT / "docs/operations/normalize-articulated-appliance.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "identity `Xform`",
        "Instance/Joints/BaseFixed",
        "non-kinematic",
        "legacy candidate",
    ):
        assert required in design
    assert "must not add an articulation root" in operation
    assert "must not toggle kinematic state" in operation
