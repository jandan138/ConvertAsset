"""Explicit, source-bound visual material overrides for admitted asset packages.

The normalizer normally preserves a source material verbatim.  A profile is an
exception that is both narrow and auditable: it may replace only the material
binding of explicitly named meshes, never their geometry or physics semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from .package_layout import TargetPackageLayout


SCHEMA_VERSION = "aan.visual_material_profile.v1"


@dataclass(frozen=True)
class VisualMaterialProfileResolution:
    status: str
    reason: str | None = None
    profile_id: str | None = None
    revision: str | None = None
    profile_sha256: str | None = None
    profile_bytes: bytes | None = None
    source_mdl: Path | None = None
    source_sub_identifier: str | None = None
    material_name: str | None = None
    binding_targets: tuple[str, ...] = ()
    claim_boundary: str | None = None


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
    if payload.get("schema_version") != SCHEMA_VERSION:
        return _blocked(f"visual material profile schema_version must be {SCHEMA_VERSION}")
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
    if override.get("kind") != "mdl_glass":
        return _blocked("visual material profile override.kind must be mdl_glass")
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
    material_name = override.get("material_name")
    targets = override.get("binding_targets")
    claim_boundary = override.get("claim_boundary")
    if not isinstance(sub_identifier, str) or not sub_identifier:
        return _blocked("visual material profile requires override.source_sub_identifier")
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
        profile_id=profile_id,
        revision=revision,
        profile_sha256=_sha256_bytes(profile_bytes),
        profile_bytes=profile_bytes,
        source_mdl=source_mdl,
        source_sub_identifier=sub_identifier,
        material_name=material_name,
        binding_targets=tuple(targets),
        claim_boundary=claim_boundary,
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
    assert resolution.source_mdl is not None
    assert resolution.profile_bytes is not None
    assert resolution.profile_id is not None
    assert resolution.revision is not None
    assert resolution.profile_sha256 is not None
    assert resolution.source_sub_identifier is not None
    assert resolution.material_name is not None
    assert resolution.claim_boundary is not None
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
            elif not prim.IsA(UsdGeom.Mesh):
                wrong_type.append(target)
        if missing or wrong_type:
            detail = []
            if missing:
                detail.append("missing targets: " + ", ".join(missing))
            if wrong_type:
                detail.append("non-mesh targets: " + ", ".join(wrong_type))
            return _authoring_blocked("visual material profile target validation failed: " + "; ".join(detail))
    except Exception as exc:
        return _authoring_blocked(f"visual material profile could not inspect package stage: {exc}")

    destination_mdl = layout.visual_material_mdl(resolution.source_mdl.name)
    try:
        destination_mdl.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolution.source_mdl, destination_mdl)
        layout.visual_material_profile_json.parent.mkdir(parents=True, exist_ok=True)
        layout.visual_material_profile_json.write_bytes(resolution.profile_bytes)
        layout.visual_material_overlay_usd.parent.mkdir(parents=True, exist_ok=True)
        layout.visual_material_overlay_usd.write_text(
            _overlay_text(
                scope=scope,
                material_name=resolution.material_name,
                mdl_relpath="../deps/mdl/" + destination_mdl.name,
                source_sub_identifier=resolution.source_sub_identifier,
                profile_id=resolution.profile_id,
                profile_sha256=resolution.profile_sha256,
                binding_targets=resolution.binding_targets,
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        return _authoring_blocked(f"could not write visual material profile package files: {exc}")

    record = {
        "status": "pass",
        "schema_version": SCHEMA_VERSION,
        "profile_id": resolution.profile_id,
        "revision": resolution.revision,
        "profile_sha256": resolution.profile_sha256,
        "profile_package_path": "visual/profile.json",
        "overlay_package_path": "overlays/visual_material.usda",
        "source_mdl": str(resolution.source_mdl),
        "package_mdl_path": destination_mdl.relative_to(layout.root).as_posix(),
        "source_mdl_sha256": _sha256(resolution.source_mdl),
        "package_mdl_sha256": _sha256(destination_mdl),
        "source_sub_identifier": resolution.source_sub_identifier,
        "material_name": resolution.material_name,
        "binding_targets": list(resolution.binding_targets),
        "claim_boundary": resolution.claim_boundary,
        "source_material_preserved": True,
        "visual_override": "intentional",
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


def _overlay_text(
    *,
    scope: str,
    material_name: str,
    mdl_relpath: str,
    source_sub_identifier: str,
    profile_id: str,
    profile_sha256: str,
    binding_targets: tuple[str, ...],
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
