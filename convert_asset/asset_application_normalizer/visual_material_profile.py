"""Explicit, source-bound visual material overrides for admitted asset packages.

The normalizer normally preserves a source material verbatim.  A profile is an
exception that is both narrow and auditable: it may replace only the material
binding of explicitly named meshes, never their geometry or physics semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from typing import Any

from .package_layout import TargetPackageLayout


SCHEMA_VERSION_V1 = "aan.visual_material_profile.v1"
SCHEMA_VERSION_V2 = "aan.visual_material_profile.v2"
SCHEMA_VERSIONS = {SCHEMA_VERSION_V1, SCHEMA_VERSION_V2}
SCHEMA_VERSION = SCHEMA_VERSION_V1
_MDL_INPUT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class VisualMaterialProfileResolution:
    status: str
    reason: str | None = None
    schema_version: str | None = None
    profile_id: str | None = None
    revision: str | None = None
    profile_sha256: str | None = None
    profile_bytes: bytes | None = None
    override_kind: str | None = None
    source_mdl: Path | None = None
    source_mdl_dependencies: tuple[Path, ...] = ()
    source_sub_identifier: str | None = None
    material_name: str | None = None
    binding_targets: tuple[str, ...] = ()
    claim_boundary: str | None = None
    diffuse_color: tuple[float, float, float] | None = None
    opacity: float | None = None
    roughness: float | None = None
    metallic: float | None = None
    mdl_inputs: dict[str, dict[str, Any]] | None = None


@dataclass(frozen=True)
class VisualMaterialAuthoringResult:
    overall_status: str
    return_code: int
    profile_record: dict[str, Any]
    normalization_actions: list[dict[str, Any]]
    blocked_reasons: list[dict[str, Any]]


def load_visual_material_profile(
    profile_path: Path,
    source_usd: Path,
) -> VisualMaterialProfileResolution:
    try:
        profile_bytes = profile_path.read_bytes()
        payload = json.loads(profile_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _blocked(f"could not read visual material profile: {exc}")
    if not isinstance(payload, dict):
        return _blocked("visual material profile must be a JSON object")
    schema_version = payload.get("schema_version")
    if schema_version not in SCHEMA_VERSIONS:
        return _blocked(
            "visual material profile schema_version must be one of "
            + ", ".join(sorted(SCHEMA_VERSIONS))
        )
    profile_id = payload.get("profile_id")
    revision = payload.get("revision")
    source_binding = payload.get("source_binding")
    override = payload.get("override")
    if not isinstance(profile_id, str) or not profile_id:
        return _blocked("visual material profile requires non-empty profile_id")
    if not isinstance(revision, str) or not revision:
        return _blocked("visual material profile requires non-empty revision")
    if not isinstance(source_binding, dict) or not isinstance(source_binding.get("sha256"), str):
        return _blocked("visual material profile requires source_binding.sha256")
    source_sha = _sha256(source_usd)
    if source_binding["sha256"] != source_sha:
        return _blocked(
            "visual material profile source sha256 does not match the requested source USD"
        )
    if not isinstance(override, dict):
        return _blocked("visual material profile requires an override object")
    kind = override.get("kind")
    if kind not in {"mdl_glass", "usd_preview_surface"}:
        return _blocked(
            "visual material profile override.kind must be mdl_glass or usd_preview_surface"
        )
    source_mdl = None
    source_mdl_dependencies: tuple[Path, ...] = ()
    sub_identifier = None
    diffuse_color = None
    opacity = None
    roughness = None
    metallic = None
    mdl_inputs = None
    if kind == "mdl_glass":
        source_mdl_raw = override.get("source_mdl")
        if not isinstance(source_mdl_raw, str) or not source_mdl_raw:
            return _blocked("visual material profile requires override.source_mdl")
        source_mdl = Path(source_mdl_raw)
        if not source_mdl.is_absolute():
            source_mdl = profile_path.parent / source_mdl
        source_mdl = source_mdl.resolve()
        if not source_mdl.is_file() or source_mdl.suffix.lower() != ".mdl":
            return _blocked(f"visual material profile MDL is unavailable: {source_mdl}")
        sub_identifier = override.get("source_sub_identifier")
        if not isinstance(sub_identifier, str) or not sub_identifier:
            return _blocked("visual material profile requires override.source_sub_identifier")
        if schema_version == SCHEMA_VERSION_V2:
            mdl_inputs, reason = _load_mdl_inputs(override.get("mdl_inputs"))
            if reason is not None:
                return _blocked(reason)
            dependencies, reason = _load_mdl_dependencies(
                override.get("source_mdl_dependencies", []), profile_path
            )
            if reason is not None:
                return _blocked(reason)
            source_mdl_dependencies = dependencies or ()
    else:
        raw_color = override.get("diffuse_color")
        if (
            not isinstance(raw_color, list)
            or len(raw_color) != 3
            or any(not _unit_number(value) for value in raw_color)
        ):
            return _blocked(
                "usd_preview_surface requires a three-number override.diffuse_color in [0, 1]"
            )
        diffuse_color = tuple(float(value) for value in raw_color)
        for field_name in ("opacity", "roughness", "metallic"):
            if not _unit_number(override.get(field_name)):
                return _blocked(
                    f"usd_preview_surface requires override.{field_name} in [0, 1]"
                )
        opacity = float(override["opacity"])
        roughness = float(override["roughness"])
        metallic = float(override["metallic"])
    material_name = override.get("material_name")
    targets = override.get("binding_targets")
    claim_boundary = override.get("claim_boundary")
    if not isinstance(material_name, str) or not material_name:
        return _blocked("visual material profile requires override.material_name")
    if (
        not isinstance(targets, list)
        or not targets
        or not all(isinstance(path, str) and path.startswith("/") for path in targets)
        or len(set(targets)) != len(targets)
    ):
        return _blocked("visual material profile requires unique absolute override.binding_targets")
    if not isinstance(claim_boundary, str) or not claim_boundary:
        return _blocked("visual material profile requires override.claim_boundary")
    return VisualMaterialProfileResolution(
        status="pass",
        schema_version=schema_version,
        profile_id=profile_id,
        revision=revision,
        profile_sha256=_sha256_bytes(profile_bytes),
        profile_bytes=profile_bytes,
        override_kind=kind,
        source_mdl=source_mdl,
        source_mdl_dependencies=source_mdl_dependencies,
        source_sub_identifier=sub_identifier,
        material_name=material_name,
        binding_targets=tuple(targets),
        claim_boundary=claim_boundary,
        diffuse_color=diffuse_color,
        opacity=opacity,
        roughness=roughness,
        metallic=metallic,
        mdl_inputs=mdl_inputs,
    )


def apply_visual_material_profile(
    layout: TargetPackageLayout,
    profile_path: Path | None,
    source_usd: Path,
    scope_prims: list[str],
) -> VisualMaterialAuthoringResult:
    if profile_path is None:
        return VisualMaterialAuthoringResult(
            overall_status="not_requested",
            return_code=0,
            profile_record={"status": "not_requested"},
            normalization_actions=[],
            blocked_reasons=[],
        )
    resolution = load_visual_material_profile(profile_path, source_usd)
    if resolution.status != "pass":
        return _authoring_blocked(resolution.reason or "visual material profile blocked")
    assert resolution.profile_bytes is not None
    assert resolution.override_kind is not None
    assert resolution.profile_id is not None
    assert resolution.revision is not None
    assert resolution.profile_sha256 is not None
    assert resolution.material_name is not None
    assert resolution.claim_boundary is not None
    assert resolution.schema_version is not None
    if not scope_prims:
        return _authoring_blocked("visual material profile requires an asset scope")
    scope = scope_prims[0]
    if any(not _is_under_scope(target, scope) for target in resolution.binding_targets):
        return _authoring_blocked(
            "visual material profile binding targets must remain inside the declared asset scope"
        )
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        stage = Usd.Stage.Open(str(layout.root_usd))
        if stage is None:
            raise RuntimeError(f"could not open package USD: {layout.root_usd}")
        missing = []
        wrong_type = []
        for target in resolution.binding_targets:
            prim = stage.GetPrimAtPath(target)
            if not prim or not prim.IsValid():
                missing.append(target)
            elif not (prim.IsA(UsdGeom.Mesh) or prim.IsA(UsdGeom.Subset)):
                wrong_type.append(target)
        if missing or wrong_type:
            detail = []
            if missing:
                detail.append("missing targets: " + ", ".join(missing))
            if wrong_type:
                detail.append("non-mesh-or-geometry-subset targets: " + ", ".join(wrong_type))
            return _authoring_blocked("visual material profile target validation failed: " + "; ".join(detail))
    except Exception as exc:
        return _authoring_blocked(f"visual material profile could not inspect package stage: {exc}")

    destination_mdl = None
    dependency_records: list[dict[str, str]] = []
    try:
        if resolution.override_kind == "mdl_glass":
            assert resolution.source_mdl is not None
            assert resolution.source_sub_identifier is not None
            destination_mdl = layout.visual_material_mdl(resolution.source_mdl.name)
            destination_mdl.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolution.source_mdl, destination_mdl)
            for source_dependency in resolution.source_mdl_dependencies:
                destination_dependency = layout.visual_material_mdl(source_dependency.name)
                shutil.copy2(source_dependency, destination_dependency)
                dependency_records.append(
                    {
                        "source_mdl": str(source_dependency),
                        "source_sha256": _sha256(source_dependency),
                        "package_path": destination_dependency.relative_to(layout.root).as_posix(),
                        "package_sha256": _sha256(destination_dependency),
                    }
                )
        layout.visual_material_profile_json.parent.mkdir(parents=True, exist_ok=True)
        layout.visual_material_profile_json.write_bytes(resolution.profile_bytes)
        layout.visual_material_overlay_usd.parent.mkdir(parents=True, exist_ok=True)
        overlay_text = (
            _mdl_overlay_text(
                scope=scope,
                material_name=resolution.material_name,
                mdl_relpath="../deps/mdl/" + destination_mdl.name,
                source_sub_identifier=resolution.source_sub_identifier,
                profile_id=resolution.profile_id,
                profile_sha256=resolution.profile_sha256,
                binding_targets=resolution.binding_targets,
                mdl_inputs=resolution.mdl_inputs or {},
            )
            if destination_mdl is not None
            else _preview_surface_overlay_text(
                scope=scope,
                material_name=resolution.material_name,
                profile_id=resolution.profile_id,
                profile_sha256=resolution.profile_sha256,
                binding_targets=resolution.binding_targets,
                diffuse_color=resolution.diffuse_color,
                opacity=resolution.opacity,
                roughness=resolution.roughness,
                metallic=resolution.metallic,
            )
        )
        layout.visual_material_overlay_usd.write_text(overlay_text, encoding="utf-8")
    except OSError as exc:
        return _authoring_blocked(f"could not write visual material profile package files: {exc}")

    record = {
        "status": "pass",
        "schema_version": resolution.schema_version,
        "profile_id": resolution.profile_id,
        "revision": resolution.revision,
        "profile_sha256": resolution.profile_sha256,
        "profile_package_path": "visual/profile.json",
        "overlay_package_path": "overlays/visual_material.usda",
        "override_kind": resolution.override_kind,
        "material_name": resolution.material_name,
        "binding_targets": list(resolution.binding_targets),
        "claim_boundary": resolution.claim_boundary,
        "source_material_preserved": True,
        "visual_override": "intentional",
    }
    if destination_mdl is not None:
        assert resolution.source_mdl is not None
        record.update(
            {
                "source_mdl": str(resolution.source_mdl),
                "package_mdl_path": destination_mdl.relative_to(layout.root).as_posix(),
                "source_mdl_sha256": _sha256(resolution.source_mdl),
                "package_mdl_sha256": _sha256(destination_mdl),
                "source_sub_identifier": resolution.source_sub_identifier,
                "mdl_inputs": resolution.mdl_inputs or {},
                "package_mdl_dependencies": dependency_records,
            }
        )
    else:
        record["preview_surface"] = {
            "diffuse_color": list(resolution.diffuse_color or ()),
            "opacity": resolution.opacity,
            "roughness": resolution.roughness,
            "metallic": resolution.metallic,
        }
    return VisualMaterialAuthoringResult(
        overall_status="pass",
        return_code=0,
        profile_record=record,
        normalization_actions=[
            {
                "action": "author_visual_material_override",
                "profile_id": resolution.profile_id,
                "binding_targets": list(resolution.binding_targets),
                "overlay_path": "overlays/visual_material.usda",
            }
        ],
        blocked_reasons=[],
    )


def _mdl_overlay_text(
    *,
    scope: str,
    material_name: str,
    mdl_relpath: str,
    source_sub_identifier: str,
    profile_id: str,
    profile_sha256: str,
    binding_targets: tuple[str, ...],
    mdl_inputs: dict[str, dict[str, Any]],
) -> str:
    scope_parts = [part for part in scope.split("/") if part]
    lines = ["#usda 1.0", ""]
    indent = ""
    for part in scope_parts:
        lines.extend([f'{indent}over "{part}"', f"{indent}{{"])
        indent += "    "
    material_path = scope + "/__aan_visual_materials/" + material_name
    lines.extend(
        [
            f'{indent}def Scope "__aan_visual_materials"',
            f"{indent}{{",
            f'{indent}    def Material "{material_name}" (',
            f"{indent}        customData = {{",
            f"{indent}            dictionary aan = {{",
            f'                    string visualMaterialProfileId = "{profile_id}"',
            f'                    string visualMaterialProfileSha256 = "{profile_sha256}"',
            f"{indent}            }}",
            f"{indent}        }}",
            f"{indent}    )",
            f"{indent}    {{",
            f"{indent}        token outputs:mdl:displacement.connect = <{material_path}/Shader.outputs:out>",
            f"{indent}        token outputs:mdl:surface.connect = <{material_path}/Shader.outputs:out>",
            f"{indent}        token outputs:mdl:volume.connect = <{material_path}/Shader.outputs:out>",
            f"{indent}        def Shader \"Shader\"",
            f"{indent}        {{",
            f'{indent}            uniform token info:implementationSource = "sourceAsset"',
            f"{indent}            uniform asset info:mdl:sourceAsset = @{mdl_relpath}@",
            f'                    uniform token info:mdl:sourceAsset:subIdentifier = "{source_sub_identifier}"',
        ]
    )
    for input_name, input_spec in mdl_inputs.items():
        lines.append(f"{indent}            {_mdl_input_usda(input_name, input_spec)}")
    lines.extend(
        [
            f"{indent}            token outputs:out (",
            '                    renderType = "material"',
            f"{indent}            )",
            f"{indent}        }}",
            f"{indent}    }}",
            f"{indent}}}",
        ]
    )
    target_tree: dict[str, Any] = {}
    for path in binding_targets:
        node = target_tree
        for part in [item for item in path.split("/") if item][len(scope_parts):]:
            node = node.setdefault(part, {})
        node["__binding__"] = True

    def emit(children: dict[str, Any], current_indent: str) -> None:
        for name, child in children.items():
            if name == "__binding__":
                continue
            lines.extend([f'{current_indent}over "{name}"', f"{current_indent}{{"])
            if child.get("__binding__"):
                lines.append(f"{current_indent}    rel material:binding = <{material_path}>")
            emit(child, current_indent + "    ")
            lines.append(f"{current_indent}}}")

    emit(target_tree, indent)
    for _ in reversed(scope_parts):
        indent = indent[:-4]
        lines.append(f"{indent}}}")
    return "\n".join(lines) + "\n"


def _preview_surface_overlay_text(
    *,
    scope: str,
    material_name: str,
    profile_id: str,
    profile_sha256: str,
    binding_targets: tuple[str, ...],
    diffuse_color: tuple[float, float, float] | None,
    opacity: float | None,
    roughness: float | None,
    metallic: float | None,
) -> str:
    assert diffuse_color is not None
    assert opacity is not None
    assert roughness is not None
    assert metallic is not None
    scope_parts = [part for part in scope.split("/") if part]
    lines = ["#usda 1.0", ""]
    indent = ""
    for part in scope_parts:
        lines.extend([f'{indent}over "{part}"', f"{indent}{{"])
        indent += "    "
    material_path = scope + "/__aan_visual_materials/" + material_name
    color = ", ".join(str(value) for value in diffuse_color)
    lines.extend(
        [
            f'{indent}def Scope "__aan_visual_materials"',
            f"{indent}{{",
            f'{indent}    def Material "{material_name}" (',
            f"{indent}        customData = {{",
            f"{indent}            dictionary aan = {{",
            f'                    string visualMaterialProfileId = "{profile_id}"',
            f'                    string visualMaterialProfileSha256 = "{profile_sha256}"',
            f"{indent}            }}",
            f"{indent}        }}",
            f"{indent}    )",
            f"{indent}    {{",
            f"{indent}        token outputs:surface.connect = <{material_path}/Shader.outputs:surface>",
            f'{indent}        def Shader "Shader"',
            f"{indent}        {{",
            f'{indent}            uniform token info:id = "UsdPreviewSurface"',
            f"{indent}            color3f inputs:diffuseColor = ({color})",
            f"{indent}            float inputs:metallic = {metallic}",
            f"{indent}            float inputs:opacity = {opacity}",
            f"{indent}            float inputs:roughness = {roughness}",
            f"{indent}            token outputs:surface",
            f"{indent}        }}",
            f"{indent}    }}",
            f"{indent}}}",
        ]
    )
    target_tree: dict[str, Any] = {}
    for path in binding_targets:
        node = target_tree
        for part in [item for item in path.split("/") if item][len(scope_parts):]:
            node = node.setdefault(part, {})
        node["__binding__"] = True

    def emit(children: dict[str, Any], current_indent: str) -> None:
        for name, child in children.items():
            if name == "__binding__":
                continue
            lines.extend([f'{current_indent}over "{name}"', f"{current_indent}{{"])
            if child.get("__binding__"):
                lines.append(f"{current_indent}    rel material:binding = <{material_path}>")
            emit(child, current_indent + "    ")
            lines.append(f"{current_indent}}}")

    emit(target_tree, indent)
    for _ in reversed(scope_parts):
        indent = indent[:-4]
        lines.append(f"{indent}}}")
    return "\n".join(lines) + "\n"


def _load_mdl_inputs(raw_inputs: Any) -> tuple[dict[str, dict[str, Any]] | None, str | None]:
    if not isinstance(raw_inputs, dict) or not raw_inputs:
        return None, "mdl_glass v2 requires non-empty override.mdl_inputs"
    parsed: dict[str, dict[str, Any]] = {}
    for name in sorted(raw_inputs):
        spec = raw_inputs[name]
        prefix = f"visual material profile override.mdl_inputs.{name}"
        if not isinstance(name, str) or not _MDL_INPUT_NAME.fullmatch(name):
            return None, f"{prefix} must use a valid USD input identifier"
        if not isinstance(spec, dict):
            return None, f"{prefix} must be an object"
        input_type = spec.get("type")
        value = spec.get("value")
        if input_type not in {"bool", "float", "color3f"}:
            return None, f"{prefix}.type must be bool, float, or color3f"
        if input_type == "bool":
            if not isinstance(value, bool):
                return None, f"{prefix}.value must be a boolean"
            normalized: Any = value
        elif input_type == "float":
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                return None, f"{prefix}.value must be a finite number"
            normalized = float(value)
        else:
            if (
                not isinstance(value, list)
                or len(value) != 3
                or any(
                    isinstance(component, bool)
                    or not isinstance(component, (int, float))
                    or not math.isfinite(float(component))
                    for component in value
                )
            ):
                return None, f"{prefix}.value must be three finite numbers"
            normalized = [float(component) for component in value]
        parsed[name] = {"type": input_type, "value": normalized}
    return parsed, None


def _load_mdl_dependencies(
    raw_dependencies: Any, profile_path: Path
) -> tuple[tuple[Path, ...] | None, str | None]:
    if not isinstance(raw_dependencies, list) or not all(
        isinstance(value, str) and value for value in raw_dependencies
    ):
        return None, "override.source_mdl_dependencies must be a list of MDL paths"
    dependencies: list[Path] = []
    destination_names: set[str] = set()
    for raw_path in raw_dependencies:
        dependency = Path(raw_path)
        if not dependency.is_absolute():
            dependency = profile_path.parent / dependency
        dependency = dependency.resolve()
        if not dependency.is_file() or dependency.suffix.lower() != ".mdl":
            return None, f"visual material profile MDL dependency is unavailable: {dependency}"
        if dependency.name in destination_names:
            return None, f"duplicate visual material profile MDL dependency name: {dependency.name}"
        destination_names.add(dependency.name)
        dependencies.append(dependency)
    return tuple(dependencies), None


def _mdl_input_usda(name: str, spec: dict[str, Any]) -> str:
    input_type = spec["type"]
    value = spec["value"]
    if input_type == "bool":
        rendered = "true" if value else "false"
    elif input_type == "color3f":
        rendered = "(" + ", ".join(repr(component) for component in value) + ")"
    else:
        rendered = repr(value)
    return f"{input_type} inputs:{name} = {rendered}"


def _authoring_blocked(reason: str) -> VisualMaterialAuthoringResult:
    return VisualMaterialAuthoringResult(
        overall_status="blocked",
        return_code=5,
        profile_record={"status": "blocked", "reason": reason},
        normalization_actions=[],
        blocked_reasons=[
            {
                "blocker_id": "aan_visual_material_profile_blocked",
                "severity": "blocking",
                "summary": reason,
                "required_resolution": "Correct the source-bound visual material profile or omit it.",
            }
        ],
    )


def _blocked(reason: str) -> VisualMaterialProfileResolution:
    return VisualMaterialProfileResolution(status="blocked", reason=reason)


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_under_scope(path: str, scope: str) -> bool:
    return path == scope or path.startswith(scope.rstrip("/") + "/")


def _unit_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and 0.0 <= float(value) <= 1.0
    )
