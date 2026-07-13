"""AAN-10 MJCF semantic inventory scout.

This module intentionally does not convert MJCF to USD.  It extracts a compact
source inventory and records target-application semantic gaps so future adapters
can be planned without claiming lossless MuJoCo/AutoBio reproduction.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "aan10.mjcf_scout.v1"
OVERALL_STATUS = "semantic_gap_report_only"


def build_mjcf_scout_manifest(source: Path) -> dict[str, Any]:
    tree = ET.parse(source)
    root = tree.getroot()
    if _local_name(root.tag) != "mujoco":
        raise ValueError(f"expected MJCF <mujoco> root, got <{root.tag}>")

    inventory = _build_inventory(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "milestone": "AAN-10-mjcf-scout",
        "overall_status": OVERALL_STATUS,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": {
            "path": str(source),
            "source_format": "mjcf",
            "source_runtime_lineage": "mujoco",
            "model": root.attrib.get("model"),
        },
        "inventory": inventory,
        "semantic_gaps": _semantic_gaps(inventory),
        "target_mapping": {
            "usd_candidate": [
                "mesh and primitive geometry inventory",
                "body tree transforms",
                "material and texture asset references",
                "limited joint type, axis, and range records",
            ],
            "requires_surrogate_or_manual_contract": [
                "actuator model and control semantics",
                "sensor readout semantics",
                "contact pair policy",
                "equality constraints",
                "tendon routing and force semantics",
                "task success predicates and reset semantics",
            ],
            "blocked_without_policy": [
                "custom MuJoCo plugins",
                "fluid/process-specific simulator behavior",
                "official benchmark comparability claims",
            ],
        },
        "claims_allowed": [
            "AAN-10 extracted MJCF source inventory and semantic gap evidence.",
            "A future adapter can use this manifest to decide convert, surrogate, waiver, or block policy.",
        ],
        "claims_forbidden": [
            "MJCF has been converted to USD.",
            "MJCF runtime semantics are preserved in Isaac Sim.",
            "AutoBio official reproduction is supported.",
            "MuJoCo actuator, sensor, contact, tendon, equality, plugin, or task semantics are losslessly supported.",
        ],
    }


def write_mjcf_scout_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_inventory(root: ET.Element) -> dict[str, Any]:
    meshes = [_asset_record(element) for element in root.findall("./asset/mesh")]
    textures = [_asset_record(element) for element in root.findall("./asset/texture")]
    materials = [_asset_record(element) for element in root.findall("./asset/material")]
    bodies = _body_records(root)
    geoms = [_named_record(element) for element in root.findall("./worldbody//geom")]
    joints = [_named_record(element) for element in root.findall("./worldbody//joint")]
    sites = [_named_record(element) for element in root.findall("./worldbody//site")]
    actuators = [_named_record(element) for element in root.findall("./actuator/*")]
    sensors = [_named_record(element) for element in root.findall("./sensor/*")]
    contacts = [_named_record(element) for element in root.findall("./contact/*")]
    equality = [_named_record(element) for element in root.findall("./equality/*")]
    tendons = [_named_record(element) for element in root.findall("./tendon/*")]
    plugins = [_named_record(element) for element in root.findall("./extension/plugin")]
    task_semantics = _task_semantic_records(root)

    return {
        "counts": {
            "bodies": len(bodies),
            "geoms": len(geoms),
            "joints": len(joints),
            "sites": len(sites),
            "meshes": len(meshes),
            "textures": len(textures),
            "materials": len(materials),
            "actuators": len(actuators),
            "sensors": len(sensors),
            "contacts": len(contacts),
            "equality": len(equality),
            "tendons": len(tendons),
            "plugins": len(plugins),
        },
        "assets": {
            "meshes": meshes,
            "textures": textures,
            "materials": materials,
        },
        "bodies": bodies,
        "geoms": geoms,
        "joints": joints,
        "sites": sites,
        "actuators": actuators,
        "sensors": sensors,
        "contacts": contacts,
        "equality": equality,
        "tendons": tendons,
        "plugins": plugins,
        "task_semantics": task_semantics,
    }


def _body_records(root: ET.Element) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    worldbody = root.find("./worldbody")
    if worldbody is None:
        return records

    def visit(body: ET.Element, parent_path: str) -> None:
        name = body.attrib.get("name") or f"body_{len(records)}"
        path = f"{parent_path}/{name}" if parent_path else f"/{name}"
        records.append(
            {
                "tag": _local_name(body.tag),
                "name": body.attrib.get("name"),
                "path": path,
                "pos": body.attrib.get("pos"),
                "quat": body.attrib.get("quat"),
                "euler": body.attrib.get("euler"),
                "mocap": body.attrib.get("mocap"),
                "child_body_count": len(body.findall("./body")),
                "geom_count": len(body.findall("./geom")),
                "joint_count": len(body.findall("./joint")),
                "site_count": len(body.findall("./site")),
            }
        )
        for child in body.findall("./body"):
            visit(child, path)

    for body in worldbody.findall("./body"):
        visit(body, "")
    return records


def _asset_record(element: ET.Element) -> dict[str, Any]:
    record = _named_record(element)
    if "file" in element.attrib:
        record["file"] = element.attrib["file"]
    return record


def _named_record(element: ET.Element) -> dict[str, Any]:
    return {
        "tag": _local_name(element.tag),
        "name": element.attrib.get("name"),
        "attributes": dict(element.attrib),
    }


def _task_semantic_records(root: ET.Element) -> list[dict[str, Any]]:
    records = []
    for element in root.iter():
        tag = _local_name(element.tag).lower()
        if tag in {"task", "goal", "reward", "metric", "success"}:
            records.append(_named_record(element))
    return records


def _semantic_gaps(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    gap_specs = [
        (
            "actuator",
            "actuators",
            "MuJoCo actuator/control model must be mapped to a target controller or blocked.",
        ),
        (
            "sensor",
            "sensors",
            "MuJoCo sensors require target runtime readout and evaluator contract.",
        ),
        (
            "contact",
            "contacts",
            "Contact pair policy affects physics behavior and cannot be inferred from geometry alone.",
        ),
        (
            "equality",
            "equality",
            "Equality constraints require explicit target simulator support or surrogate authoring.",
        ),
        (
            "tendon",
            "tendons",
            "Tendon routing/force semantics need a target-specific representation.",
        ),
        (
            "plugin",
            "plugins",
            "Custom MuJoCo plugins are blocked until a policy or surrogate implementation exists.",
        ),
        (
            "task_semantic",
            "task_semantics",
            "Task, reward, metric, success, and reset semantics need a benchmark adapter contract.",
        ),
    ]
    gaps = []
    counts = inventory["counts"]
    for category, count_key, summary in gap_specs:
        count = len(inventory.get(count_key, [])) if count_key == "task_semantics" else counts.get(count_key, 0)
        if count:
            gaps.append(
                {
                    "category": category,
                    "count": count,
                    "status": (
                        "blocked_without_policy"
                        if category == "plugin"
                        else "requires_target_adapter_or_surrogate"
                    ),
                    "summary": summary,
                }
            )
    if not inventory.get("task_semantics"):
        gaps.append(
            {
                "category": "task_semantic",
                "count": 0,
                "status": "requires_external_benchmark_contract",
                "summary": "No explicit task semantic element was found; success/reset semantics must come from an external contract.",
            }
        )
    return gaps


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an AAN-10 MJCF semantic gap manifest")
    parser.add_argument("source", help="MJCF XML path")
    parser.add_argument("--out", required=True, help="Scout manifest JSON output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    manifest = build_mjcf_scout_manifest(Path(args.source))
    write_mjcf_scout_manifest(Path(args.out), manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
