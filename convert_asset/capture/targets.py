# -*- coding: utf-8 -*-
"""Logical target discovery for scene-level capture.

The functions in this module deliberately use a small duck-typed USD surface so
unit tests can run without constructing real USD stages. Real `pxr` objects work
through the same methods.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import re
from typing import Iterable


TARGET_LEVELS = {"object", "mesh", "category"}
LIGHT_TYPE_NAMES = {
    "DistantLight",
    "SphereLight",
    "DiskLight",
    "RectLight",
    "CylinderLight",
    "DomeLight",
}


@dataclass(frozen=True)
class TargetConfig:
    target_scope: str = "auto"
    target_level: str = "object"
    include_animation: bool = False
    limit: int | None = None


@dataclass(frozen=True)
class TargetSpec:
    prim_path: str
    target_id: str
    name: str
    category: str
    level: str
    mesh_count: int
    type_name: str

    def to_dict(self) -> dict:
        return asdict(self)


def _path_string(prim_or_path) -> str:
    if isinstance(prim_or_path, str):
        return prim_or_path
    path = prim_or_path.GetPath()
    return getattr(path, "pathString", str(path))


def _is_valid_prim(prim) -> bool:
    if prim is None:
        return False
    is_valid = getattr(prim, "IsValid", None)
    if callable(is_valid):
        try:
            return bool(is_valid())
        except Exception:
            return False
    return True


def _stage_get_prim(stage, path: str):
    try:
        return stage.GetPrimAtPath(path)
    except Exception:
        try:
            from pxr import Sdf  # type: ignore

            return stage.GetPrimAtPath(Sdf.Path(path))
        except Exception:
            return None


def _stage_has_prim(stage, path: str) -> bool:
    return _is_valid_prim(_stage_get_prim(stage, path))


def _default_prim_path(stage) -> str | None:
    getter = getattr(stage, "GetDefaultPrim", None)
    if not callable(getter):
        return None
    try:
        prim = getter()
    except Exception:
        return None
    if not _is_valid_prim(prim):
        return None
    return _path_string(prim)


def _children(prim) -> list:
    try:
        return list(prim.GetChildren())
    except Exception:
        return []


def _name(prim) -> str:
    try:
        return str(prim.GetName())
    except Exception:
        return _path_string(prim).rstrip("/").rsplit("/", 1)[-1]


def _type_name(prim) -> str:
    try:
        return str(prim.GetTypeName())
    except Exception:
        return ""


def _is_active(prim) -> bool:
    fn = getattr(prim, "IsActive", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:
            return False
    return True


def _is_instance_proxy(prim) -> bool:
    fn = getattr(prim, "IsInstanceProxy", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:
            return True
    return False


def _is_light_prim(prim) -> bool:
    type_name = _type_name(prim)
    return type_name in LIGHT_TYPE_NAMES or type_name.endswith("Light")


def _is_proxy_or_guide_purpose(prim) -> bool:
    try:
        from pxr import UsdGeom  # type: ignore

        imageable = UsdGeom.Imageable(prim)
        if not imageable:
            return False
        purpose = imageable.ComputePurpose()
        return purpose in (UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide)
    except Exception:
        return False


def _is_excluded_path(path: str, *, include_animation: bool, allow_structural: bool) -> bool:
    token = path.lower()
    if "__default_setting" in token:
        return True
    if "/lights" in token or token.endswith("/lights"):
        return True
    if "hdr" in token and "sphere" in token:
        return True
    if "skydome" in token or "environment" in token:
        return True
    if allow_structural:
        return False
    if not include_animation and "/meshes/animation" in token:
        return True
    if "/meshes/base/" in token or token.endswith("/meshes/base"):
        return True
    if "/meshes/baseanimation/" in token or token.endswith("/meshes/baseanimation"):
        return True
    return False


def _is_usable_prim(
    prim,
    *,
    include_animation: bool,
    allow_instance_proxy: bool = False,
    allow_structural: bool = False,
) -> bool:
    if not _is_valid_prim(prim):
        return False
    if not _is_active(prim):
        return False
    if _is_instance_proxy(prim) and not allow_instance_proxy:
        return False
    if _is_light_prim(prim):
        return False
    if _is_excluded_path(
        _path_string(prim),
        include_animation=include_animation,
        allow_structural=allow_structural,
    ):
        return False
    return True


def resolve_target_scope(stage, requested_scope: str = "auto") -> str:
    """Resolve a CLI target scope to a concrete prim path.

    `auto` is tuned for GRScenes opened either directly (`/Root`) or referenced
    under `/World/scene`.
    """
    requested_scope = (requested_scope or "auto").strip()
    if requested_scope == "auto":
        candidates = [
            "/World/scene/Meshes/Furnitures",
            "/Root/Meshes/Furnitures",
            "/World/scene/Instances",
            "/Root/Instances",
            "/World/scene",
            "/Root",
        ]
    elif requested_scope.startswith("/"):
        candidates = [requested_scope]
    else:
        cleaned = requested_scope.strip("/")
        candidates = [
            f"/World/{cleaned}",
            f"/{cleaned}",
            f"/World/scene/{cleaned}",
        ]
        default_path = _default_prim_path(stage)
        if default_path:
            candidates.append(f"{default_path.rstrip('/')}/{cleaned}")

    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if _stage_has_prim(stage, candidate):
            return candidate
    raise RuntimeError(f"Target scope not found: {requested_scope}")


def _iter_prims(root) -> Iterable:
    stack = [root]
    while stack:
        prim = stack.pop()
        yield prim
        stack.extend(reversed(_children(prim)))


def _mesh_descendants(root, *, include_animation: bool, allow_structural: bool = False) -> list:
    meshes = []
    for prim in _iter_prims(root):
        if not _is_usable_prim(
            prim,
            include_animation=include_animation,
            allow_instance_proxy=True,
            allow_structural=allow_structural,
        ):
            continue
        if _type_name(prim) == "Mesh" and not _is_proxy_or_guide_purpose(prim):
            meshes.append(prim)
    return meshes


def _mesh_count(root, *, include_animation: bool, allow_structural: bool = False) -> int:
    return len(_mesh_descendants(root, include_animation=include_animation, allow_structural=allow_structural))


def _category_from_path(path: str, fallback: str) -> str:
    parts = [part for part in path.strip("/").split("/") if part]
    for anchor in ("Furnitures", "Furniture", "Objects", "Instances"):
        if anchor in parts:
            idx = parts.index(anchor)
            if idx + 1 < len(parts):
                return parts[idx + 1]
    if len(parts) >= 2:
        parent = parts[-2]
        if not parent.startswith("model_"):
            return parent
    return fallback


def _target_id(path: str) -> str:
    token = path.strip("/")
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", token)
    return token or "root"


def _spec_for_prim(prim, *, level: str, category: str, mesh_count: int) -> TargetSpec:
    path = _path_string(prim)
    return TargetSpec(
        prim_path=path,
        target_id=_target_id(path),
        name=_name(prim),
        category=category,
        level=level,
        mesh_count=int(mesh_count),
        type_name=_type_name(prim),
    )


def _object_targets_from_scope(scope, *, include_animation: bool, allow_structural: bool) -> list[TargetSpec]:
    targets: list[TargetSpec] = []

    for category_prim in _children(scope):
        if not _is_usable_prim(
            category_prim,
            include_animation=include_animation,
            allow_structural=allow_structural,
        ):
            continue
        category_name = _name(category_prim)
        model_children = [
            child
            for child in _children(category_prim)
            if _name(child).startswith("model_")
            and _is_usable_prim(
                child,
                include_animation=include_animation,
                allow_structural=allow_structural,
            )
        ]
        if model_children:
            for model in model_children:
                count = _mesh_count(
                    model,
                    include_animation=include_animation,
                    allow_structural=allow_structural,
                )
                if count <= 0:
                    continue
                targets.append(_spec_for_prim(model, level="object", category=category_name, mesh_count=count))
        else:
            count = _mesh_count(
                category_prim,
                include_animation=include_animation,
                allow_structural=allow_structural,
            )
            if count <= 0:
                continue
            category = _category_from_path(_path_string(category_prim), _name(category_prim))
            targets.append(_spec_for_prim(category_prim, level="object", category=category, mesh_count=count))
    return targets


def _mesh_targets_from_scope(scope, *, include_animation: bool, allow_structural: bool) -> list[TargetSpec]:
    targets: list[TargetSpec] = []
    for mesh in _mesh_descendants(scope, include_animation=include_animation, allow_structural=allow_structural):
        category = _category_from_path(_path_string(mesh), _name(mesh))
        targets.append(_spec_for_prim(mesh, level="mesh", category=category, mesh_count=1))
    return targets


def _category_targets_from_scope(scope, *, include_animation: bool, allow_structural: bool) -> list[TargetSpec]:
    targets: list[TargetSpec] = []
    for child in _children(scope):
        if not _is_usable_prim(
            child,
            include_animation=include_animation,
            allow_structural=allow_structural,
        ):
            continue
        count = _mesh_count(child, include_animation=include_animation, allow_structural=allow_structural)
        if count <= 0:
            continue
        category = _category_from_path(_path_string(child), _name(child))
        targets.append(_spec_for_prim(child, level="category", category=category, mesh_count=count))
    return targets


def _dedupe_target_ids(targets: list[TargetSpec]) -> list[TargetSpec]:
    counts: dict[str, int] = {}
    for target in targets:
        counts[target.target_id] = counts.get(target.target_id, 0) + 1
    if all(count == 1 for count in counts.values()):
        return targets
    deduped = []
    for target in targets:
        if counts[target.target_id] == 1:
            deduped.append(target)
            continue
        digest = hashlib.sha1(target.prim_path.encode("utf-8")).hexdigest()[:8]
        deduped.append(replace(target, target_id=f"{target.target_id}_{digest}"))
    return deduped


def list_scene_targets(stage, config: TargetConfig | None = None) -> list[TargetSpec]:
    config = config or TargetConfig()
    target_level = str(config.target_level).strip().lower()
    if target_level not in TARGET_LEVELS:
        raise ValueError(f"Unsupported target level: {config.target_level}")

    scope_path = resolve_target_scope(stage, config.target_scope)
    scope = _stage_get_prim(stage, scope_path)
    explicit_scope = (config.target_scope or "auto").strip() != "auto"
    if not _is_usable_prim(
        scope,
        include_animation=config.include_animation,
        allow_structural=explicit_scope,
    ):
        raise RuntimeError(f"Target scope is not usable: {scope_path}")

    if target_level == "object":
        targets = _object_targets_from_scope(
            scope,
            include_animation=config.include_animation,
            allow_structural=explicit_scope,
        )
    elif target_level == "mesh":
        targets = _mesh_targets_from_scope(
            scope,
            include_animation=config.include_animation,
            allow_structural=explicit_scope,
        )
    else:
        targets = _category_targets_from_scope(
            scope,
            include_animation=config.include_animation,
            allow_structural=explicit_scope,
        )

    targets = _dedupe_target_ids(targets)
    if config.limit is not None:
        return targets[: max(0, int(config.limit))]
    return targets
