"""Static material closure evidence for AAN-04."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence_manifest import sha256_file
from .model import MILESTONE_AAN04
from .package_layout import TargetPackageLayout


CLOSURE_MODES = (
    "native_resolved",
    "local_mirror",
    "preview_surface_fallback",
    "explicit_waiver",
    "blocked",
)

CHANNEL_ALIASES = {
    "baseColor": ("diffuseColor", "baseColor", "base_color", "albedo", "color", "tint"),
    "roughness": ("roughness", "reflection_roughness", "reflectionroughness", "glossiness"),
    "metallic": ("metallic", "metalness", "metallic_constant"),
    "normal": ("normal", "normalmap", "normal_texture", "normalmap_texture", "bump"),
    "opacity": ("opacity", "alpha", "opacity_texture", "alpha_texture", "transmission"),
}

MATERIAL_NOT_RUN_REPORT = {
    "status": "not_run",
    "material_count": 0,
    "closure_mode_counts": {mode: 0 for mode in CLOSURE_MODES},
    "blocked_material_count": 0,
    "mdl_asset_count": 0,
    "texture_asset_count": 0,
}


@dataclass(frozen=True)
class MaterialClosureResult:
    overall_status: str
    return_code: int
    material_closure: list[dict[str, Any]]
    static_material_report: dict[str, Any]
    stage_gate: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]


def build_not_run_material_closure(reason: str) -> MaterialClosureResult:
    return MaterialClosureResult(
        overall_status="blocked",
        return_code=0,
        material_closure=[],
        static_material_report={**MATERIAL_NOT_RUN_REPORT, "reason": reason},
        stage_gate={
            "check_id": MILESTONE_AAN04,
            "stage": "material_closure",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
    )


def build_material_closure(
    layout: TargetPackageLayout,
    dependency_closure: dict[str, Any],
    material_policy: str,
) -> MaterialClosureResult:
    root_usd = layout.root_usd
    stage = _open_stage(root_usd)
    if stage is None:
        reason = "AAN-04 could not open the package root USD for material inspection."
        return MaterialClosureResult(
            overall_status="blocked",
            return_code=5,
            material_closure=[],
            static_material_report={
                **MATERIAL_NOT_RUN_REPORT,
                "status": "blocked",
                "reason": reason,
                "root_usd": str(root_usd),
            },
            stage_gate={
                "check_id": MILESTONE_AAN04,
                "stage": "material_closure",
                "status": "blocked",
                "summary": reason,
            },
            blocked_reasons=[
                {
                    "blocker_id": "aan04_block_material_stage_open",
                    "severity": "blocking",
                    "summary": reason,
                    "required_resolution": "Fix the package USD so Usd.Stage.Open succeeds.",
                }
            ],
        )

    dependency_records = _material_asset_records(
        layout.root,
        dependency_closure.get("local_files", []),
    )
    dependency_context = {
        "by_material": _dependency_records_by_material(dependency_records),
        "by_package_path": {
            str(record["package_path"]): record
            for record in dependency_records
            if record.get("package_path")
        },
    }
    records = [
        _material_record(material_prim, layout.root, dependency_context, material_policy)
        for material_prim in _iter_material_prims(stage)
    ]
    report = _static_material_report(records, root_usd, material_policy)
    blocked = [record for record in records if record["closure_mode"] == "blocked"]
    if blocked:
        blockers = [
            {
                "blocker_id": "aan04_block_material_dependency",
                "severity": "blocking",
                "summary": "One or more materials lack package-local MDL/texture provenance.",
                "count": len(blocked),
                "required_resolution": (
                    "Mirror the missing material asset, add a PreviewSurface fallback with "
                    "provenance, or attach an explicit material waiver."
                ),
            }
        ]
        status = "blocked"
        return_code = 5
        summary = "AAN-04 material closure found blocking material gaps."
    else:
        blockers = []
        status = "pass"
        return_code = 0
        summary = "AAN-04 material closure recorded source-preserved material evidence."

    return MaterialClosureResult(
        overall_status=status,
        return_code=return_code,
        material_closure=records,
        static_material_report=report,
        stage_gate={
            "check_id": MILESTONE_AAN04,
            "stage": "material_closure",
            "status": status,
            "summary": summary,
        },
        blocked_reasons=blockers,
    )


def _open_stage(root_usd: Path) -> Any | None:
    try:
        from pxr import Usd  # type: ignore
    except Exception:
        return None
    try:
        return Usd.Stage.Open(str(root_usd))
    except Exception:
        return None


def _iter_material_prims(stage: Any) -> list[Any]:
    return [prim for prim in stage.Traverse() if prim.GetTypeName() == "Material"]


def _material_asset_records(
    package_root: Path,
    local_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _material_asset_record(package_root, dep)
        for dep in local_files
        if dep.get("kind") in {"mdl", "texture"}
    ]


def _dependency_records_by_material(
    asset_records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in asset_records:
        prim_path = record.get("source_shader_prim")
        if not prim_path:
            continue
        material_path = _material_path_from_dependency_prim(str(prim_path))
        if material_path is None:
            continue
        grouped.setdefault(material_path, []).append(record)
    return grouped


def _material_path_from_dependency_prim(prim_path: str) -> str | None:
    if "/Looks/" not in prim_path:
        return None
    prefix, rest = prim_path.split("/Looks/", 1)
    if not rest:
        return None
    material_name = rest.split("/", 1)[0]
    if not material_name:
        return None
    return f"{prefix}/Looks/{material_name}" if prefix else f"/Looks/{material_name}"


def _material_asset_record(package_root: Path, dep: dict[str, Any]) -> dict[str, Any]:
    record = {
        "kind": dep.get("kind"),
        "arc_kind": dep.get("arc_kind"),
        "raw_asset_path": dep.get("raw_asset_path"),
        "resolved_path": dep.get("resolved_path"),
        "package_path": dep.get("package_path"),
        "source_shader_prim": dep.get("prim_path"),
        "status": dep.get("status"),
        "resolution": dep.get("resolution"),
    }
    resolved_path = dep.get("resolved_path")
    if resolved_path and Path(str(resolved_path)).exists():
        record["source_sha256"] = sha256_file(Path(str(resolved_path)))
    package_path = dep.get("package_path")
    if package_path:
        package_file = package_root / str(package_path)
        if package_file.exists():
            record["package_sha256"] = sha256_file(package_file)
    if dep.get("kind") == "mdl" and package_path:
        record["effect_tags"] = _mdl_effect_tags(package_root / str(package_path))
    return record


def _material_record(
    material_prim: Any,
    package_root: Path,
    dependency_context: dict[str, Any],
    material_policy: str,
) -> dict[str, Any]:
    material_path = material_prim.GetPath().pathString
    shaders = _shader_records(material_prim)
    asset_records = [
        *dependency_context["by_material"].get(material_path, []),
        *_asset_records_from_shader_references(
            package_root,
            shaders,
            dependency_context["by_package_path"],
        ),
    ]
    asset_records = _unique_asset_records(asset_records)
    source_mdl_assets = [record for record in asset_records if record.get("kind") == "mdl"]
    texture_paths = [record for record in asset_records if record.get("kind") == "texture"]
    missing_package_assets = [
        record
        for record in asset_records
        if not record.get("package_path") or not record.get("package_sha256")
    ]
    channels = _extracted_channels(shaders)
    has_preview_surface = any(shader.get("shader_id") == "UsdPreviewSurface" for shader in shaders)

    if missing_package_assets:
        closure_mode = "blocked"
    elif source_mdl_assets or texture_paths:
        closure_mode = "local_mirror"
    elif has_preview_surface:
        closure_mode = "native_resolved"
    else:
        closure_mode = "native_resolved"

    return {
        "material_prim": material_path,
        "owning_layer": _owning_layer(material_prim),
        "closure_mode": closure_mode,
        "material_policy": material_policy,
        "source_assets_preserved": closure_mode in {"native_resolved", "local_mirror"},
        "shader_prims": shaders,
        "source_mdl_assets": source_mdl_assets,
        "texture_paths": texture_paths,
        "extracted_channels": channels,
        "color_space": {
            "baseColor": "sRGB",
            "roughness": "raw",
            "metallic": "raw",
            "normal": "raw",
            "opacity": "raw",
        },
        "roughness_transform": "direct",
        "transparency_strategy": _transparency_strategy(
            material_path,
            channels,
            source_mdl_assets,
            texture_paths,
        ),
        "preview_surface_fallback": _preview_fallback_record(closure_mode),
        "defaults_used": [
            channel
            for channel, record in channels.items()
            if record.get("source") in {"default", "missing"}
        ],
        "losses": [] if closure_mode in {"native_resolved", "local_mirror"} else ["material_blocked"],
        "evidence_level": (
            "package_hash" if source_mdl_assets or texture_paths else "usd_native_shader"
        ),
        "residual_mdl": {
            "status": "source_mdl_preserved" if source_mdl_assets else "none",
            "local_count": len(source_mdl_assets),
            "external_count": 0,
            "blocked_count": len(missing_package_assets),
        },
        "visibility_evidence": {
            "status": "not_run",
            "required_gate": "AAN-06-runtime-smoke",
        },
    }


def _shader_records(material_prim: Any) -> list[dict[str, Any]]:
    try:
        from pxr import Usd, UsdShade  # type: ignore
    except Exception:
        return []

    records = []
    for prim in Usd.PrimRange(material_prim):
        if prim == material_prim or prim.GetTypeName() != "Shader":
            continue
        shader = UsdShade.Shader(prim)
        records.append(
            {
                "prim_path": prim.GetPath().pathString,
                "owning_layer": _owning_layer(prim),
                "shader_id": _attr_value(shader.GetIdAttr()),
                "implementation_source": _attr_value(shader.GetImplementationSourceAttr()),
                "source_asset": _attr_value(prim.GetAttribute("info:mdl:sourceAsset")),
                "source_sub_identifier": _attr_value(
                    prim.GetAttribute("info:mdl:sourceAsset:subIdentifier")
                ),
                "inputs": _shader_input_records(shader),
            }
        )
    return records


def _asset_records_from_shader_references(
    package_root: Path,
    shaders: list[dict[str, Any]],
    by_package_path: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records = []
    for shader in shaders:
        raw_candidates = []
        if shader.get("source_asset"):
            raw_candidates.append(("mdl", str(shader["source_asset"])))
        for input_record in shader.get("inputs", []):
            value = input_record.get("value")
            if _looks_like_asset_path(value):
                raw_candidates.append((_kind_from_asset_path(str(value)), str(value)))
        for kind, raw in raw_candidates:
            package_path = _package_path_from_asset_reference(
                package_root,
                shader.get("owning_layer"),
                raw,
            )
            if not package_path:
                records.append(
                    {
                        "kind": kind,
                        "raw_asset_path": raw,
                        "package_path": None,
                        "source_shader_prim": shader.get("prim_path"),
                        "status": "blocked",
                    }
                )
                continue
            existing = by_package_path.get(package_path)
            if existing:
                record = {**existing}
                record["source_shader_prim"] = shader.get("prim_path")
                records.append(record)
                continue
            records.append(
                {
                    "kind": kind,
                    "raw_asset_path": raw,
                    "package_path": package_path,
                    "source_shader_prim": shader.get("prim_path"),
                    "status": "blocked",
                }
            )
    return records


def _package_path_from_asset_reference(
    package_root: Path,
    owning_layer: Any,
    raw: str,
) -> str | None:
    if "://" in raw:
        return None
    raw_path = Path(raw)
    root = package_root.resolve()
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path.resolve())
    else:
        if owning_layer:
            candidates.append((Path(str(owning_layer)).parent / raw_path).resolve())
        candidates.append((root / raw_path).resolve())
    for candidate in candidates:
        try:
            return candidate.relative_to(root).as_posix()
        except ValueError:
            continue
    return None


def _kind_from_asset_path(raw: str) -> str:
    suffix = Path(raw).suffix.lower()
    if suffix in {".mdl", ".mdle"}:
        return "mdl"
    return "texture"


def _unique_asset_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = []
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        key = (
            str(record.get("kind", "")),
            str(record.get("package_path", "")),
            str(record.get("source_shader_prim", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def _shader_input_records(shader: Any) -> list[dict[str, Any]]:
    records = []
    for input_obj in shader.GetInputs():
        value = _attr_value(input_obj.GetAttr())
        record = {
            "name": input_obj.GetBaseName(),
            "value": value,
        }
        try:
            record["connected"] = bool(input_obj.HasConnectedSource())
        except Exception:
            record["connected"] = False
        records.append(record)
    return records


def _extracted_channels(shaders: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    channels = {}
    for channel, aliases in CHANNEL_ALIASES.items():
        channels[channel] = _channel_record(shaders, aliases)
    return channels


def _channel_record(shaders: list[dict[str, Any]], aliases: tuple[str, ...]) -> dict[str, Any]:
    alias_set = {alias.lower() for alias in aliases}
    for shader in shaders:
        for input_record in shader.get("inputs", []):
            name = str(input_record.get("name", ""))
            if name.lower() not in alias_set:
                continue
            if input_record.get("connected"):
                return {
                    "source": "connected",
                    "shader_prim": shader.get("prim_path"),
                    "input": name,
                }
            value = input_record.get("value")
            if _looks_like_asset_path(value):
                return {
                    "source": "asset",
                    "shader_prim": shader.get("prim_path"),
                    "input": name,
                    "raw_asset_path": value,
                }
            if value is not None:
                return {
                    "source": "constant",
                    "shader_prim": shader.get("prim_path"),
                    "input": name,
                    "value": value,
                }
    return {"source": "missing"}


def _preview_fallback_record(closure_mode: str) -> dict[str, Any]:
    if closure_mode == "preview_surface_fallback":
        return {"status": "generated"}
    return {
        "status": "not_generated",
        "reason": "Source material assets are preserved under the current material policy.",
    }


def _transparency_strategy(
    material_path: str,
    channels: dict[str, dict[str, Any]],
    source_mdl_assets: list[dict[str, Any]],
    texture_paths: list[dict[str, Any]],
) -> str:
    opacity_source = channels.get("opacity", {}).get("source")
    if opacity_source in {"asset", "constant", "connected"}:
        return "opacity_input"
    haystack = " ".join(
        [
            material_path,
            *[str(asset.get("raw_asset_path", "")) for asset in source_mdl_assets],
            *[str(asset.get("raw_asset_path", "")) for asset in texture_paths],
            *[
                " ".join(str(tag) for tag in asset.get("effect_tags", []))
                for asset in source_mdl_assets
            ],
        ]
    ).lower()
    if any(token in haystack for token in ("opacity", "alpha", "glass", "translucent", "transparent")):
        return "opacity_input"
    return "opaque"


def _static_material_report(
    records: list[dict[str, Any]],
    root_usd: Path,
    material_policy: str,
) -> dict[str, Any]:
    closure_counts = {mode: 0 for mode in CLOSURE_MODES}
    transparency_counts: dict[str, int] = {}
    for record in records:
        closure_counts[record["closure_mode"]] += 1
        transparency = record["transparency_strategy"]
        transparency_counts[transparency] = transparency_counts.get(transparency, 0) + 1
    return {
        "status": "pass" if closure_counts["blocked"] == 0 else "blocked",
        "root_usd": str(root_usd),
        "material_policy": material_policy,
        "material_count": len(records),
        "closure_mode_counts": closure_counts,
        "blocked_material_count": closure_counts["blocked"],
        "mdl_asset_count": sum(len(record["source_mdl_assets"]) for record in records),
        "texture_asset_count": sum(len(record["texture_paths"]) for record in records),
        "transparency_strategy_counts": transparency_counts,
    }


def _owning_layer(prim: Any) -> str | None:
    try:
        stack = prim.GetPrimStack()
    except Exception:
        return None
    if not stack:
        return None
    layer = getattr(stack[0], "layer", None)
    if not layer:
        return None
    return str(getattr(layer, "realPath", None) or getattr(layer, "identifier", ""))


def _attr_value(attr: Any) -> Any:
    if not attr:
        return None
    try:
        return _json_value(attr.Get())
    except Exception:
        return None


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    path = getattr(value, "path", None)
    if path is not None:
        return str(path)
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(float(value), 6)
    if isinstance(value, (list, tuple)) or (
        hasattr(value, "__len__") and hasattr(value, "__getitem__")
    ):
        try:
            return [_json_value(value[idx]) for idx in range(len(value))]
        except Exception:
            return str(value)
    return str(value)


def _looks_like_asset_path(value: Any) -> bool:
    return isinstance(value, str) and bool(Path(value).suffix)


def _mdl_effect_tags(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return []
    tags = []
    checks = {
        "opacity_transparency": ("opacity", "transparent", "translucent", "glass", "transmission"),
        "normal_bump": ("normal", "bump"),
        "emission": ("emission", "emissive"),
        "clearcoat": ("clearcoat", "clear_coat"),
        "procedural": ("noise", "procedural"),
    }
    for tag, needles in checks.items():
        if any(needle in text for needle in needles):
            tags.append(tag)
    return tags
