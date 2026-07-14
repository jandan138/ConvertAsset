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
    def source_root_usd(self) -> Path:
        """Package-local source root composed below the owned entry overlay."""
        return self.root / "deps" / "usd" / "source_root.usd"

    @property
    def scoped_source_usd(self) -> Path:
        """Role-scoped USDA composed below the owned entry overlay when required."""
        return self.root / "deps" / "usd" / "scoped_source.usda"

    @property
    def physics_overlay_usd(self) -> Path:
        """Strong, ConvertAsset-owned layer for a dynamic physics profile."""
        return self.root / "overlays" / "physics_profile.usda"

    @property
    def physics_profile_json(self) -> Path:
        """Immutable package copy of the source-bound physics profile."""
        return self.root / "physics" / "profile.json"

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
