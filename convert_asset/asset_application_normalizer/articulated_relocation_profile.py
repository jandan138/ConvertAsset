"""Validated contracts for relocatable complex articulated appliances."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "aan.articulated_relocation_profile.v1"
_TIERS = {"relocatable_full", "relocatable_task_scoped"}


def _absolute_prim_path(value: object, field: str) -> str:
    path = str(value or "")
    if not path.startswith("/") or path == "/" or "//" in path:
        raise ValueError(f"{field} must be an absolute non-root USD prim path")
    return path.rstrip("/")


@dataclass(frozen=True)
class ControllerHook:
    kind: str
    strategy: str
    controller_prim: str
    controller_suffix: str
    source_root: str
    source_script_sha256: str


@dataclass(frozen=True)
class PromotionContract:
    requested_tier: str
    required_functions: tuple[str, ...]


@dataclass(frozen=True)
class ArticulatedRelocationProfile:
    """Fail-closed v1 profile for a one-chassis jointed rigid graph."""

    schema_version: str
    profile_id: str
    source_usd_sha256: str
    entry_prim: str
    chassis_prim: str
    joint_scope_prim: str
    topology: str
    support_frame_prim: str
    local_support_z_m: float
    controller_hooks: tuple[ControllerHook, ...]
    promotion: PromotionContract

    @classmethod
    def from_path(cls, path: Path) -> "ArticulatedRelocationProfile":
        return cls.from_mapping(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any]
    ) -> "ArticulatedRelocationProfile":
        if value.get("schema_version") != _SCHEMA:
            raise ValueError(f"schema_version must be {_SCHEMA!r}")
        profile_id = str(value.get("profile_id") or "").strip()
        if not profile_id:
            raise ValueError("profile_id is required")
        source = value.get("source")
        if not isinstance(source, Mapping):
            raise ValueError("source.usd_sha256 is required")
        source_hash = str(source.get("usd_sha256") or "")
        if not _SHA256_RE.fullmatch(source_hash):
            raise ValueError("source.usd_sha256 must be a lowercase SHA-256")
        entry = _absolute_prim_path(value.get("entry_prim"), "entry_prim")
        chassis = _absolute_prim_path(value.get("chassis_prim"), "chassis_prim")
        joint_scope = _absolute_prim_path(
            value.get("joint_scope_prim"), "joint_scope_prim"
        )
        if not chassis.startswith(entry + "/"):
            raise ValueError("chassis_prim must be below entry_prim")
        if not (joint_scope == entry or joint_scope.startswith(entry + "/")):
            raise ValueError("joint_scope_prim must be entry_prim or a descendant")
        topology = str(value.get("topology") or "")
        if topology != "jointed_rigid_graph":
            raise ValueError("topology must be 'jointed_rigid_graph' in profile v1")
        support = value.get("support_frame")
        if not isinstance(support, Mapping):
            raise ValueError("support_frame is required")
        support_prim = _absolute_prim_path(support.get("prim"), "support_frame.prim")
        if support_prim != entry:
            raise ValueError("profile v1 support_frame.prim must equal entry_prim")
        support_z = float(support.get("local_support_z_m", 0.0))

        hooks: list[ControllerHook] = []
        raw_hooks = value.get("controller_hooks", [])
        if not isinstance(raw_hooks, list):
            raise ValueError("controller_hooks must be a list")
        for index, raw in enumerate(raw_hooks):
            if not isinstance(raw, Mapping):
                raise ValueError(f"controller_hooks[{index}] must be an object")
            kind = str(raw.get("kind") or "")
            strategy = str(raw.get("strategy") or "")
            if (
                kind != "scriptnode_root_from_node_path"
                or strategy != "contextvar_node_path_v1"
            ):
                raise ValueError(f"controller_hooks[{index}] uses an unsupported hook")
            controller_prim = _absolute_prim_path(
                raw.get("controller_prim"), f"controller_hooks[{index}].controller_prim"
            )
            if not controller_prim.startswith(entry + "/"):
                raise ValueError("controller hook must be below entry_prim")
            suffix = str(raw.get("controller_suffix") or "")
            if not suffix.startswith("/") or not controller_prim.endswith(suffix):
                raise ValueError("controller_suffix must match controller_prim")
            source_root = _absolute_prim_path(
                raw.get("source_root"), f"controller_hooks[{index}].source_root"
            )
            if source_root != entry:
                raise ValueError("controller source_root must equal entry_prim")
            script_hash = str(raw.get("source_script_sha256") or "")
            if not _SHA256_RE.fullmatch(script_hash):
                raise ValueError("controller source_script_sha256 must be a SHA-256")
            hooks.append(
                ControllerHook(
                    kind=kind,
                    strategy=strategy,
                    controller_prim=controller_prim,
                    controller_suffix=suffix,
                    source_root=source_root,
                    source_script_sha256=script_hash,
                )
            )

        raw_promotion = value.get("promotion")
        if not isinstance(raw_promotion, Mapping):
            raise ValueError("promotion is required")
        requested_tier = str(raw_promotion.get("requested_tier") or "")
        if requested_tier not in _TIERS:
            raise ValueError(f"promotion.requested_tier must be one of {sorted(_TIERS)}")
        raw_functions = raw_promotion.get("required_functions", [])
        if not isinstance(raw_functions, list) or any(
            not str(item).strip() for item in raw_functions
        ):
            raise ValueError("promotion.required_functions must be a string list")

        return cls(
            schema_version=_SCHEMA,
            profile_id=profile_id,
            source_usd_sha256=source_hash,
            entry_prim=entry,
            chassis_prim=chassis,
            joint_scope_prim=joint_scope,
            topology=topology,
            support_frame_prim=support_prim,
            local_support_z_m=support_z,
            controller_hooks=tuple(hooks),
            promotion=PromotionContract(
                requested_tier=requested_tier,
                required_functions=tuple(str(item) for item in raw_functions),
            ),
        )
