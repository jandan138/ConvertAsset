#!/usr/bin/env python3
"""Build source-bound facade candidates for one role-inventory phase."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.audit_scientific_workbench_asset_library import CATALOG
from scripts.build_source_bound_usd_facade import build as build_facade


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _smoke_scene(packages: list[dict[str, object]]) -> str:
    instances: list[str] = []
    for index, package in enumerate(packages):
        asset_id = str(package["asset_id"])
        entry = f"/World/Asset_{asset_id}"
        x = (index % 4) * 0.6
        y = (index // 4) * 0.6
        instances.append(
            f'''        def Xform "{asset_id}" (
            prepend references = @packages/{asset_id}/asset.usd@<{entry}>
        )
        {{
            double3 xformOp:translate = ({x}, {y}, 0)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }}'''
        )
    joined = "\n".join(instances)
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "Candidates"
    {{
{joined}
    }}
}}
"""


def build(
    *, source_root: Path, audit_report: Path, out: Path, phase: int = 2
) -> dict[str, object]:
    source_root = source_root.resolve()
    out = out.resolve()
    audit = json.loads(audit_report.read_text(encoding="utf-8"))
    by_id = {asset["asset_id"]: asset for asset in audit["assets"]}
    selected = [spec for spec in CATALOG if spec.phase == phase]
    expected = {1: 13, 2: 16}.get(phase)
    if expected is None or len(selected) != expected:
        raise ValueError("phase must be 1 or 2 with the locked catalog count")
    if out.exists():
        raise FileExistsError(f"refusing to overwrite candidate batch: {out}")
    out.mkdir(parents=True)
    packages: list[dict[str, object]] = []
    for spec in selected:
        package = build_facade(
            source=source_root / spec.source,
            out=out / "packages" / spec.asset_id,
            entry_name=f"Asset_{spec.asset_id}",
        )
        manifest_path = package / "evidence/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(
            {
                "asset_id": spec.asset_id,
                "role": spec.role,
                "phase": spec.phase,
                "overall_status": "candidate_runtime_pending",
                "required_runtime_gates": {
                    "liquid_container": [
                        "gpu_collision_cooking",
                        "static_retention",
                        "zero_below_support",
                    ],
                    "liquid_conduit": ["gpu_collision_cooking", "conduit_transfer"],
                    "rigid_tool": [
                        "dynamic_reset",
                        "stable_support",
                        "gripper_collision",
                    ],
                    "receptacle_support": ["static_reset", "support_or_insertion"],
                    "instrument_static": ["load", "render", "step", "reset"],
                }[spec.role],
                "topology_audit": by_id[spec.asset_id],
            }
        )
        _write(manifest_path, manifest)
        packages.append(
            {
                "asset_id": spec.asset_id,
                "role": spec.role,
                "package": package.relative_to(out).as_posix(),
                "entrypoint": (package / "asset.usd").relative_to(out).as_posix(),
                "manifest": manifest_path.relative_to(out).as_posix(),
                "manifest_sha256": _sha(manifest_path),
                "status": "candidate_runtime_pending",
            }
        )
    result = {
        "schema_version": "aan.scientific_workbench_role_candidate_batch.v1",
        "phase": phase,
        "overall_status": "candidate_runtime_pending",
        "asset_count": len(packages),
        "packages": packages,
        "claim_boundary": (
            "Source-bound facades and role declarations only. No Phase-2 asset is "
            "promoted until its role-specific runtime gates pass."
        ),
    }
    (out / "batch_smoke.usda").write_text(_smoke_scene(packages), encoding="utf-8")
    result["batch_smoke_scene"] = "batch_smoke.usda"
    _write(out / "manifest.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--audit-report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--phase", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    result = build(
        source_root=args.source_root,
        audit_report=args.audit_report,
        out=args.out,
        phase=args.phase,
    )
    print(json.dumps({"asset_count": result["asset_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
