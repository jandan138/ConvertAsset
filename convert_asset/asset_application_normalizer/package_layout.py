"""Target package path helpers for AAN."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TargetPackageLayout:
    root: Path

    @property
    def root_usd(self) -> Path:
        return self.root / "asset.usd"

    @property
    def evidence_manifest(self) -> Path:
        return self.root / "evidence" / "manifest.json"

    @property
    def task_config(self) -> Path:
        return self.root / "task" / "task_config.yaml"

    @property
    def required_prims(self) -> Path:
        return self.root / "task" / "required_prims.yaml"

    @property
    def evaluator(self) -> Path:
        return self.root / "task" / "evaluator.yaml"


def default_evidence_out(out_dir: Path) -> Path:
    """Use a sidecar manifest during the skeleton phase to avoid package writes."""
    if out_dir.suffix:
        return out_dir.with_suffix(out_dir.suffix + ".manifest.json")
    return out_dir.parent / f"{out_dir.name}.manifest.json"
