#!/usr/bin/env python3
"""Build the source-bound r4 tube-rack facade from the audited r3 facade.

The r3 Cube transforms already contain the intended *full* proxy dimensions,
but ``UsdGeomCube`` defaults to ``size = 2``.  This builder keeps those measured
transforms, explicitly authors ``size = 1``, hides every collision proxy from
rendering, and records the corrected geometry in provenance.  It does not edit
the raw source USD or an existing package.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
from typing import Any
import uuid


EXPECTED_PROXY_NAMES = (
    "base",
    "wall_left",
    "wall_right",
    "wall_back",
    "wall_front",
    "socket_0_bottom",
    "socket_0_wall_pos_x",
    "socket_0_wall_neg_x",
    "socket_0_wall_pos_y",
    "socket_0_wall_neg_y",
)
R3_INTERACTION_PROFILE_ID = (
    "blenderkit.tube_rack.uniform_scale_k0365.interaction.r3"
)
R4_INTERACTION_PROFILE_ID = (
    "blenderkit.tube_rack.uniform_scale_k0365.interaction.r4"
)
R3_PHYSICS_PROFILE_ID = (
    "blenderkit.tube_rack.uniform_scale_k0365."
    "provisional.r3-compound-proxy"
)
R4_PHYSICS_PROFILE_ID = (
    "blenderkit.tube_rack.uniform_scale_k0365."
    "provisional.r4-compound-proxy-cube-size-correction"
)
R3_INTERACTION_REVISION = "r3"
R4_INTERACTION_REVISION = "r4"
R3_PHYSICS_REVISION = "r3-compound-proxy"
R4_PHYSICS_REVISION = "r4-compound-proxy-cube-size-correction"
_CUBE_PATTERN = re.compile(
    r'def\s+Cube\s+"(?P<name>[^"]+)"[^{]*\{(?P<body>.*?)^\s*\}',
    re.MULTILINE | re.DOTALL,
)
_VECTOR_PATTERN = (
    r"{attribute}\s*=\s*\(\s*"
    r"(?P<x>[-+0-9.eE]+)\s*,\s*"
    r"(?P<y>[-+0-9.eE]+)\s*,\s*"
    r"(?P<z>[-+0-9.eE]+)\s*\)"
)


class TubeRackR4BuildError(ValueError):
    """Raised when the predecessor facade cannot be corrected safely."""


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise TubeRackR4BuildError(
            f"predecessor provenance is not valid JSON: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise TubeRackR4BuildError("predecessor provenance must be a JSON object")
    return value


def _load_profile_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise TubeRackR4BuildError(
            f"audited r3 {label} profile is not valid JSON: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise TubeRackR4BuildError(
            f"audited r3 {label} profile must be a JSON object"
        )
    return value


def _standard_json_bytes(value: dict[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise TubeRackR4BuildError(
            "profile contains a value that cannot be represented in standard JSON"
        ) from exc
    return (encoded + "\n").encode("utf-8")


def _rebound_profile_bytes(
    path: Path,
    *,
    label: str,
    expected_schema_version: str,
    expected_profile_id: str,
    expected_revision: str,
    new_profile_id: str,
    new_revision: str,
    predecessor_facade_sha256: str,
    r4_facade_sha256: str,
    inserted_bottom_frame_m: list[float] | None = None,
) -> bytes:
    profile = _load_profile_object(path, label)
    if profile.get("schema_version") != expected_schema_version:
        raise TubeRackR4BuildError(
            f"audited r3 {label} profile schema_version is unsupported"
        )
    if profile.get("profile_id") != expected_profile_id:
        raise TubeRackR4BuildError(
            f"audited r3 {label} profile_id does not match the approved r3 profile"
        )
    if profile.get("revision") != expected_revision:
        raise TubeRackR4BuildError(
            f"audited r3 {label} revision does not match the approved r3 profile"
        )
    source_binding = profile.get("source_binding")
    if not isinstance(source_binding, dict):
        raise TubeRackR4BuildError(
            f"audited r3 {label} source_binding must be an object"
        )
    if source_binding.get("sha256") != predecessor_facade_sha256:
        raise TubeRackR4BuildError(
            f"audited r3 {label} source_binding.sha256 does not match "
            "the predecessor facade"
        )
    rebound = deepcopy(profile)
    rebound["profile_id"] = new_profile_id
    rebound["revision"] = new_revision
    rebound_source_binding = rebound["source_binding"]
    rebound_source_binding["sha256"] = r4_facade_sha256
    if inserted_bottom_frame_m is not None:
        named_frames = rebound.get("named_frames")
        frame = (
            named_frames.get("socket_0_inserted_bottom")
            if isinstance(named_frames, dict)
            else None
        )
        if not isinstance(frame, dict):
            raise TubeRackR4BuildError(
                "audited r3 interaction profile is missing "
                "socket_0_inserted_bottom"
            )
        frame["translation_body_local_usd"] = inserted_bottom_frame_m
    return _standard_json_bytes(rebound)


def _vector(body: str, attribute: str, proxy_name: str) -> tuple[float, float, float]:
    pattern = re.compile(_VECTOR_PATTERN.format(attribute=re.escape(attribute)))
    match = pattern.search(body)
    if match is None:
        raise TubeRackR4BuildError(
            f"{proxy_name} is missing a three-component {attribute}"
        )
    result = tuple(float(match.group(axis)) for axis in ("x", "y", "z"))
    if not all(math.isfinite(value) for value in result):
        raise TubeRackR4BuildError(f"{proxy_name} has non-finite {attribute}")
    return result


def _parse_proxy_specs(
    facade_text: str,
) -> dict[str, dict[str, tuple[float, float, float]]]:
    specs: dict[str, dict[str, tuple[float, float, float]]] = {}
    for match in _CUBE_PATTERN.finditer(facade_text):
        name = match.group("name")
        if name in specs:
            raise TubeRackR4BuildError(f"duplicate Cube proxy: {name}")
        body = match.group("body")
        specs[name] = {
            "scale": _vector(body, "xformOp:scale", name),
            "translate": _vector(body, "xformOp:translate", name),
        }
    if tuple(specs) != EXPECTED_PROXY_NAMES:
        raise TubeRackR4BuildError(
            "r3 facade Cube proxy order/names differ from the audited ten-proxy ABI"
        )
    for name, spec in specs.items():
        scale = spec["scale"]
        if any(value <= 0.0 for value in scale):
            raise TubeRackR4BuildError(f"{name} scale must be finite and positive")
    return specs


def _format_number(value: float) -> str:
    if value == 0.0:
        return "0.0"
    return repr(float(value))


def _format_vector(values: tuple[float, float, float]) -> str:
    return ", ".join(_format_number(value) for value in values)


def _stage_rate(facade_text: str, field: str) -> float:
    match = re.search(
        rf"^\s*{re.escape(field)}\s*=\s*(?P<value>[-+0-9.eE]+)\s*$",
        facade_text,
        re.MULTILINE,
    )
    if match is None:
        raise TubeRackR4BuildError(
            f"predecessor facade is missing authored {field}"
        )
    value = float(match.group("value"))
    if not math.isfinite(value) or value <= 0.0:
        raise TubeRackR4BuildError(
            f"predecessor facade has invalid {field}"
        )
    return value


def _proxy_bounds(
    specs: dict[str, dict[str, tuple[float, float, float]]],
) -> tuple[list[float], list[float]]:
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    for spec in specs.values():
        scale = spec["scale"]
        translate = spec["translate"]
        for axis in range(3):
            minimum[axis] = min(
                minimum[axis],
                translate[axis] - 0.5 * scale[axis],
            )
            maximum[axis] = max(
                maximum[axis],
                translate[axis] + 0.5 * scale[axis],
            )
    return minimum, maximum


def _facade_text(
    predecessor_facade_path: Path,
    output_facade_path: Path,
    specs: dict[str, dict[str, tuple[float, float, float]]],
    *,
    frames_per_second: float,
    time_codes_per_second: float,
) -> str:
    relative_predecessor = Path(
        os.path.relpath(
            predecessor_facade_path,
            start=output_facade_path.parent,
        )
    ).as_posix()
    blocks: list[str] = []
    for name in EXPECTED_PROXY_NAMES:
        scale = specs[name]["scale"]
        translate = specs[name]["translate"]
        blocks.append(
            f'''
            over "{name}"
            {{
                double size = 1
                token visibility = "invisible"
                float3 xformOp:scale = ({_format_vector(scale)})
                float3 xformOp:translate = ({_format_vector(translate)})
                uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            }}
'''
        )
    return f'''#usda 1.0
(
    defaultPrim = "World"
    framesPerSecond = {_format_number(frames_per_second)}
    metersPerUnit = 1
    subLayers = [
        @{relative_predecessor}@
    ]
    timeCodesPerSecond = {_format_number(time_codes_per_second)}
    upAxis = "Z"
)

over "World"
{{
    over "TubeRack"
    {{
        over "__aan_collision_proxy"
        {{{"".join(blocks)}
        }}
    }}
}}
'''


def _atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(value)
    temporary.replace(path)


def build_tube_rack_r4_facade(
    *,
    predecessor_facade_path: Path,
    predecessor_provenance_path: Path,
    output_facade_path: Path,
    output_provenance_path: Path,
    predecessor_interaction_path: Path | None = None,
    predecessor_physics_path: Path | None = None,
    output_interaction_path: Path | None = None,
    output_physics_path: Path | None = None,
) -> dict[str, Any]:
    """Write a new r4 overlay, provenance, and optionally rebound profiles."""
    predecessor_facade_path = predecessor_facade_path.resolve()
    predecessor_provenance_path = predecessor_provenance_path.resolve()
    output_facade_path = output_facade_path.resolve()
    output_provenance_path = output_provenance_path.resolve()
    profile_arguments = (
        predecessor_interaction_path,
        predecessor_physics_path,
        output_interaction_path,
        output_physics_path,
    )
    profiles_requested = any(path is not None for path in profile_arguments)
    if profiles_requested and not all(path is not None for path in profile_arguments):
        raise TubeRackR4BuildError(
            "interaction/physics profile inputs and outputs must be provided together"
        )
    if profiles_requested:
        assert predecessor_interaction_path is not None
        assert predecessor_physics_path is not None
        assert output_interaction_path is not None
        assert output_physics_path is not None
        predecessor_interaction_path = predecessor_interaction_path.resolve()
        predecessor_physics_path = predecessor_physics_path.resolve()
        output_interaction_path = output_interaction_path.resolve()
        output_physics_path = output_physics_path.resolve()
    output_paths = [output_facade_path, output_provenance_path]
    if profiles_requested:
        assert output_interaction_path is not None
        assert output_physics_path is not None
        output_paths.extend([output_interaction_path, output_physics_path])
    if len(set(output_paths)) != len(output_paths):
        raise TubeRackR4BuildError("r4 output paths must be distinct")
    for path in output_paths:
        if path.exists() or path.is_symlink():
            raise TubeRackR4BuildError(f"refusing to replace existing output: {path}")
    try:
        facade_bytes = predecessor_facade_path.read_bytes()
        facade_text = facade_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise TubeRackR4BuildError(
            f"predecessor facade is unreadable: {predecessor_facade_path}"
        ) from exc
    provenance = _load_json_object(predecessor_provenance_path)
    predecessor_sha256 = sha256(facade_bytes).hexdigest()
    if provenance.get("facade_sha256") != predecessor_sha256:
        raise TubeRackR4BuildError(
            "predecessor facade SHA-256 does not match its provenance"
        )
    if provenance.get("asset_entry_prim") != "/World/TubeRack":
        raise TubeRackR4BuildError(
            "predecessor asset_entry_prim must be /World/TubeRack"
        )
    compound = provenance.get("compound_proxy")
    if not isinstance(compound, dict):
        raise TubeRackR4BuildError("predecessor compound_proxy record is missing")
    if compound.get("proxies") != list(EXPECTED_PROXY_NAMES):
        raise TubeRackR4BuildError(
            "predecessor provenance proxy list differs from the audited ABI"
        )
    specs = _parse_proxy_specs(facade_text)
    frames_per_second = _stage_rate(facade_text, "framesPerSecond")
    time_codes_per_second = _stage_rate(facade_text, "timeCodesPerSecond")
    minimum, maximum = _proxy_bounds(specs)
    bottom_spec = specs["socket_0_bottom"]
    inserted_bottom_frame_m = [
        bottom_spec["translate"][0],
        bottom_spec["translate"][1],
        bottom_spec["translate"][2] + 0.5 * bottom_spec["scale"][2],
    ]
    if not math.isclose(minimum[2], 0.0, abs_tol=1.0e-9):
        raise TubeRackR4BuildError(
            "corrected proxy minimum Z must align with the support frame at 0 m"
        )
    output_text = _facade_text(
        predecessor_facade_path,
        output_facade_path,
        specs,
        frames_per_second=frames_per_second,
        time_codes_per_second=time_codes_per_second,
    )
    output_bytes = output_text.encode("utf-8")
    output_sha256 = sha256(output_bytes).hexdigest()
    corrected = dict(provenance)
    corrected["facade_revision"] = "r4-compound-proxy-cube-size-correction"
    corrected["facade_sha256"] = output_sha256
    corrected["predecessor_facade"] = {
        "path": str(predecessor_facade_path),
        "sha256": predecessor_sha256,
        "provenance_path": str(predecessor_provenance_path),
        "provenance_sha256": _sha256_file(predecessor_provenance_path),
    }
    corrected["compound_proxy"] = {
        **compound,
        "status": "declared",
        "proxy_count": len(EXPECTED_PROXY_NAMES),
        "proxies": list(EXPECTED_PROXY_NAMES),
        "cube_size": 1.0,
        "render_visibility": "invisible",
        "support_min_z_m": minimum[2],
        "proxy_bound_m": {"min": minimum, "max": maximum},
        "full_dimensions_m": {
            name: list(specs[name]["scale"]) for name in EXPECTED_PROXY_NAMES
        },
        "r3_correction": {
            "previous_declared_proxy_count": compound.get("proxy_count"),
            "reason": (
                "UsdGeomCube defaults to size=2; r3 authored intended full "
                "dimensions directly as scale and leaked proxies into rendering."
            ),
        },
    }
    corrected["interaction_semantic_corrections"] = {
        "socket_0_inserted_bottom": {
            "translation_body_local_usd": inserted_bottom_frame_m,
            "basis": (
                "top face of the corrected socket_0_bottom Cube; the r3 "
                "frame was above the physical contact plane"
            ),
        }
    }
    provenance_bytes = (
        _standard_json_bytes(corrected)
    )
    interaction_bytes: bytes | None = None
    physics_bytes: bytes | None = None
    if profiles_requested:
        assert predecessor_interaction_path is not None
        assert predecessor_physics_path is not None
        interaction_bytes = _rebound_profile_bytes(
            predecessor_interaction_path,
            label="interaction",
            expected_schema_version="aan.object_interaction_profile.v1",
            expected_profile_id=R3_INTERACTION_PROFILE_ID,
            expected_revision=R3_INTERACTION_REVISION,
            new_profile_id=R4_INTERACTION_PROFILE_ID,
            new_revision=R4_INTERACTION_REVISION,
            predecessor_facade_sha256=predecessor_sha256,
            r4_facade_sha256=output_sha256,
            inserted_bottom_frame_m=inserted_bottom_frame_m,
        )
        physics_bytes = _rebound_profile_bytes(
            predecessor_physics_path,
            label="physics",
            expected_schema_version="aan.physics_profile.v1",
            expected_profile_id=R3_PHYSICS_PROFILE_ID,
            expected_revision=R3_PHYSICS_REVISION,
            new_profile_id=R4_PHYSICS_PROFILE_ID,
            new_revision=R4_PHYSICS_REVISION,
            predecessor_facade_sha256=predecessor_sha256,
            r4_facade_sha256=output_sha256,
        )
    _atomic_write(output_facade_path, output_bytes)
    _atomic_write(output_provenance_path, provenance_bytes)
    result = {
        "status": "pass",
        "facade_path": str(output_facade_path),
        "facade_sha256": output_sha256,
        "provenance_path": str(output_provenance_path),
        "proxy_count": len(EXPECTED_PROXY_NAMES),
        "support_min_z_m": minimum[2],
        "inserted_bottom_frame_m": inserted_bottom_frame_m,
    }
    if profiles_requested:
        assert interaction_bytes is not None
        assert physics_bytes is not None
        assert output_interaction_path is not None
        assert output_physics_path is not None
        _atomic_write(output_interaction_path, interaction_bytes)
        _atomic_write(output_physics_path, physics_bytes)
        result.update(
            {
                "interaction_profile_path": str(output_interaction_path),
                "interaction_profile_sha256": sha256(
                    interaction_bytes
                ).hexdigest(),
                "physics_profile_path": str(output_physics_path),
                "physics_profile_sha256": sha256(physics_bytes).hexdigest(),
            }
        )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the source-bound corrected tube-rack r4 facade."
    )
    parser.add_argument("--predecessor-facade", type=Path, required=True)
    parser.add_argument("--predecessor-provenance", type=Path, required=True)
    parser.add_argument("--predecessor-interaction", type=Path, required=True)
    parser.add_argument("--predecessor-physics", type=Path, required=True)
    parser.add_argument("--out-facade", type=Path, required=True)
    parser.add_argument("--out-provenance", type=Path, required=True)
    parser.add_argument("--out-interaction", type=Path, required=True)
    parser.add_argument("--out-physics", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = build_tube_rack_r4_facade(
            predecessor_facade_path=args.predecessor_facade,
            predecessor_provenance_path=args.predecessor_provenance,
            output_facade_path=args.out_facade,
            output_provenance_path=args.out_provenance,
            predecessor_interaction_path=args.predecessor_interaction,
            predecessor_physics_path=args.predecessor_physics,
            output_interaction_path=args.out_interaction,
            output_physics_path=args.out_physics,
        )
    except TubeRackR4BuildError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
