#!/usr/bin/env python3
"""Inventory and compose review grids for the workbench rigid-object intake."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


CATEGORIES = {
    "beaker": ("beaker",),
    "device": ("funnel", "magnetic stirrer", "magnetic stirrer with hot plate"),
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _bounds(stage: Any, prim: Any) -> dict[str, list[float]]:
    from pxr import Usd, UsdGeom  # type: ignore

    value = (
        UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
        )
        .ComputeWorldBound(prim)
        .ComputeAlignedRange()
    )
    lower = [float(item) for item in value.GetMin()]
    upper = [float(item) for item in value.GetMax()]
    return {
        "min": lower,
        "max": upper,
        "size": [upper[index] - lower[index] for index in range(3)],
    }


def _candidate_record(source: Path, archive_root: Path) -> dict[str, object]:
    from pxr import Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(source))
    if stage is None:
        raise RuntimeError(f"cannot open candidate: {source}")
    default = stage.GetDefaultPrim()
    if not default:
        raise RuntimeError(f"candidate has no default prim: {source}")
    meshes = [prim for prim in stage.Traverse() if prim.GetTypeName() == "Mesh"]
    return {
        "source": source.relative_to(archive_root).as_posix(),
        "sha256": _sha256(source),
        "default_prim": default.GetPath().pathString,
        "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
        "meters_per_unit": float(UsdGeom.GetStageMetersPerUnit(stage)),
        "mesh_count": len(meshes),
        "bounds": _bounds(stage, default),
    }


def _compose_grid(
    records: list[dict[str, object]],
    archive_root: Path,
    stage_path: Path,
) -> None:
    from pxr import Gf, Usd, UsdGeom  # type: ignore

    if stage_path.exists():
        stage_path.unlink()
    stage = Usd.Stage.CreateNew(str(stage_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    UsdGeom.Xform.Define(stage, "/World/Candidates")
    columns = 6
    spacing = 2.8
    for index, record in enumerate(records):
        prim = UsdGeom.Xform.Define(stage, f"/World/Candidates/C{index:03d}")
        source = archive_root / str(record["source"])
        visual = UsdGeom.Xform.Define(stage, f"/World/Candidates/C{index:03d}/Visual")
        source_prim = UsdGeom.Xform.Define(
            stage, f"/World/Candidates/C{index:03d}/Visual/Source"
        )
        source_prim.GetPrim().GetReferences().AddReference(
            str(source), str(record["default_prim"])
        )
        row, column = divmod(index, columns)
        size = list(record["bounds"]["size"])  # type: ignore[index]
        longest = max(float(item) for item in size)
        scale = 1.5 / longest if longest > 0 else 1.0
        UsdGeom.Xformable(prim).AddTranslateOp().Set(
            Gf.Vec3d(column * spacing, -row * spacing, 0.0)
        )
        xform = UsdGeom.Xformable(visual)
        xform.AddRotateXYZOp().Set(Gf.Vec3f(90.0, 0.0, 0.0))
        xform.AddScaleOp().Set(Gf.Vec3f(scale, scale, scale))
        prim.GetPrim().SetCustomDataByKey("candidateIndex", index)
        prim.GetPrim().SetCustomDataByKey("candidateSource", str(record["source"]))
    stage.GetRootLayer().Save()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_root", type=Path)
    parser.add_argument("--archive-zip", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    archive_root = args.archive_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "schema_version": "aan.scientific_workbench_asset_screening.v1",
        "archive_root": str(archive_root),
        "archive_sha256": (
            _sha256(args.archive_zip.resolve())
            if args.archive_zip is not None and args.archive_zip.is_file()
            else None
        ),
        "categories": {},
    }
    for group, categories in CATEGORIES.items():
        records = [
            _candidate_record(source, archive_root)
            for category in categories
            for source in sorted((archive_root / category).glob("*.usd"))
        ]
        for index, record in enumerate(records):
            record["review_index"] = index
        _compose_grid(records, archive_root, out / f"{group}_candidates.usda")
        manifest["categories"][group] = records  # type: ignore[index]
    (out / "screening_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(out / "screening_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
