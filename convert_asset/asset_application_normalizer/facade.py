"""Producer-owned consolidated consumer facade for multi-root stages.

Some sources split content across top-level namespaces (for example
``/world`` for materials, ``/Root`` for room geometry, ``/Render`` for
render settings) with cross-namespace material bindings.  Consuming any
single namespace loses the room; this builder mounts every namespace under
one consumer scope and retargets cross-namespace bindings with a stronger
overlay, leaving the raw tree immutable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NamespaceMount:
    raw_namespace: str  # e.g. "/world"
    mount_path: str  # e.g. "/World/world"


@dataclass(frozen=True)
class FacadeResult:
    status: str
    facade_path: Path
    overlay_path: Path
    provenance_path: Path
    binding_retarget_count: int
    dome_latlong_override_count: int
    namespace_mapping: dict[str, str]


def _retarget_prefixes(mounts: list[NamespaceMount]) -> dict[str, str]:
    return {mount.raw_namespace: mount.mount_path for mount in mounts}


def _collect_binding_retargets(stage: Any, prefixes: dict[str, str]) -> list[dict[str, Any]]:
    retargets: list[dict[str, Any]] = []
    for prim in stage.Traverse():
        rel = prim.GetRelationship("material:binding")
        if not rel:
            continue
        targets = rel.GetTargets()
        new_targets = []
        changed = False
        for target in targets:
            path = target.pathString
            replaced = path
            for raw_prefix, mount_prefix in prefixes.items():
                if path == raw_prefix or path.startswith(raw_prefix + "/"):
                    replaced = mount_prefix + path[len(raw_prefix):]
                    break
            new_targets.append(replaced)
            changed = changed or replaced != path
        if changed:
            source_prim = prim.GetPath().pathString
            retargets.append(
                {
                    "prim": source_prim,
                    "targets": new_targets,
                    "source_targets": [t.pathString for t in targets],
                }
            )
    return retargets


def _consumer_path(source_path: str, prefixes: dict[str, str]) -> str:
    for raw_prefix, mount_prefix in prefixes.items():
        if source_path == raw_prefix or source_path.startswith(raw_prefix + "/"):
            return mount_prefix + source_path[len(raw_prefix):]
    return source_path


def _collect_dome_latlong_overrides(
    stage: Any,
    source_prims: list[str],
    prefixes: dict[str, str],
) -> list[dict[str, str]]:
    overrides: list[dict[str, str]] = []
    for source_path in source_prims:
        prim = stage.GetPrimAtPath(source_path)
        if not prim or prim.GetTypeName() != "DomeLight":
            raise ValueError(
                f"dome latlong override must identify a DomeLight prim: {source_path}"
            )
        source_format = prim.GetAttribute("inputs:texture:format").Get()
        overrides.append(
            {
                "source_prim": source_path,
                "consumer_prim": _consumer_path(source_path, prefixes),
                "source_texture_format": str(source_format or ""),
                "consumer_texture_format": "latlong",
            }
        )
    return overrides


def _overlay_text(
    retargets: list[dict[str, Any]],
    prefixes: dict[str, str],
    dome_latlong_overrides: list[dict[str, str]],
) -> str:
    lines = [
        "#usda 1.0",
        "(",
        '    doc = "Producer-owned binding retarget overlay for the consumer facade."',
        ")",
        "",
    ]
    tree: dict[str, Any] = {}
    for item in retargets:
        source_prim = item["prim"]
        mount_prim = _consumer_path(source_prim, prefixes)
        node = tree
        for part in [p for p in mount_prim.split("/") if p]:
            node = node.setdefault(part, {})
        node["__targets__"] = item["targets"]
    for item in dome_latlong_overrides:
        node = tree
        for part in [p for p in item["consumer_prim"].split("/") if p]:
            node = node.setdefault(part, {})
        node.setdefault("__tokens__", {})["inputs:texture:format"] = "latlong"

    def emit(node: dict[str, Any], indent: str) -> None:
        for name, child in node.items():
            if name in {"__targets__", "__tokens__"}:
                continue
            lines.append(f'{indent}over "{name}"')
            lines.append(f"{indent}{{")
            targets = child.get("__targets__")
            if targets:
                targets_str = ", ".join(f"<{t}>" for t in targets)
                lines.append(f"{indent}    rel material:binding = [{targets_str}]")
            for attribute, value in child.get("__tokens__", {}).items():
                lines.append(f'{indent}    token {attribute} = "{value}"')
            emit(child, indent + "    ")
            lines.append(f"{indent}}}")

    emit(tree, "")
    return "\n".join(lines) + "\n"


def _facade_text(
    source_usd: Path,
    facade_dir: Path,
    mounts: list[NamespaceMount],
    consumer_scope: str,
    overlay_name: str,
    *,
    meters_per_unit: float,
    up_axis: str,
) -> str:
    try:
        rel_source = source_usd.resolve().relative_to(facade_dir.resolve())
        rel_ref = rel_source.as_posix()
    except ValueError:
        rel_ref = source_usd.as_posix()
    scope_name = consumer_scope.rstrip("/").split("/")[-1] or "World"
    root_mounts = [
        mount for mount in mounts
        if mount.mount_path.rstrip("/") == consumer_scope.rstrip("/")
    ]
    if len(root_mounts) > 1 or (root_mounts and len(mounts) != 1):
        raise ValueError(
            "a direct consumer-scope mount must be the only namespace mount"
        )
    lines = [
        "#usda 1.0",
        "(",
        f'    defaultPrim = "{scope_name}"',
        '    doc = "Producer-owned consolidated consumer facade; raw tree immutable."',
        f"    metersPerUnit = {meters_per_unit:g}",
        f'    upAxis = "{up_axis}"',
        "    subLayers = [",
        f"        @{overlay_name}@",
        "    ]",
        ")",
        "",
        (
            f'def Xform "{scope_name}" ('
            if root_mounts
            else f'def Xform "{scope_name}"'
        ),
    ]
    if root_mounts:
        lines.extend(
            [
                f"    references = @{rel_ref}@<{root_mounts[0].raw_namespace}>",
                ")",
            ]
        )
    lines.extend(
        [
        "{",
        ]
    )
    if not root_mounts:
        for mount in mounts:
            child = mount.mount_path.rstrip("/").split("/")[-1]
            lines.extend(
                [
                    f'    def "{child}" (',
                    f"        references = @{rel_ref}@<{mount.raw_namespace}>",
                    "    )",
                    "    {",
                    "    }",
                ]
            )
    lines.append("}")
    return "\n".join(lines) + "\n"


def build_consumer_facade(
    source_usd: Path,
    out_dir: Path,
    *,
    mounts: list[NamespaceMount],
    consumer_scope: str = "/World",
    source_sha256: str | None = None,
    dome_latlong_prims: list[str] | None = None,
) -> FacadeResult:
    """Build facade.usda + binding overlay + provenance for a multi-root stage."""
    from pxr import Usd, UsdGeom  # type: ignore

    out_dir.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.Open(str(source_usd))
    if stage is None:
        raise RuntimeError(f"cannot open source stage: {source_usd}")

    prefixes = _retarget_prefixes(mounts)
    retargets = _collect_binding_retargets(stage, prefixes)
    dome_overrides = _collect_dome_latlong_overrides(
        stage,
        list(dome_latlong_prims or []),
        prefixes,
    )
    overlay_path = out_dir / "binding_fix.usda"
    overlay_path.write_text(
        _overlay_text(retargets, prefixes, dome_overrides),
        encoding="utf-8",
    )
    facade_path = out_dir / "facade.usda"
    facade_path.write_text(
        _facade_text(
            source_usd,
            out_dir,
            mounts,
            consumer_scope,
            overlay_path.name,
            meters_per_unit=float(UsdGeom.GetStageMetersPerUnit(stage)),
            up_axis=str(UsdGeom.GetStageUpAxis(stage)),
        ),
        encoding="utf-8",
    )
    provenance = {
        "raw_source_default_prim": (
            stage.GetDefaultPrim().GetPath().pathString if stage.GetDefaultPrim() else None
        ),
        "raw_source_namespaces": [mount.raw_namespace for mount in mounts],
        "facade_default_prim": consumer_scope.rstrip("/").split("/")[-1] or "World",
        "facade_scope": consumer_scope,
        "namespace_mapping": {mount.raw_namespace: mount.mount_path for mount in mounts},
        "binding_retarget_count": len(retargets),
        "binding_retarget_rule": "prefix raw namespace -> consumer mount on material:binding targets",
        "dome_latlong_overrides": dome_overrides,
        "raw_source_usd": str(source_usd),
        "raw_source_usd_sha256": source_sha256,
    }
    provenance_path = out_dir / "facade_provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return FacadeResult(
        status="pass",
        facade_path=facade_path,
        overlay_path=overlay_path,
        provenance_path=provenance_path,
        binding_retarget_count=len(retargets),
        dome_latlong_override_count=len(dome_overrides),
        namespace_mapping=provenance["namespace_mapping"],
    )
