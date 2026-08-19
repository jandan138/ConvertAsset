#!/usr/bin/env python3
"""Mark the legacy housing/rotor/button/lid collision proxies invisible.

The r8-era facade chain authored the __aan_collision_proxy cubes without a
visibility attribute, so they show as stray gray plates in GUI viewports.
This display-only overlay sets ``token visibility = "invisible"`` on every
legacy proxy prim (the r9 benchtop pad and the r10 cup colliders are already
invisible). Collision content, transforms, joints, drives, and the mass
bundle are inherited from the r10 facade by sublayering; only display hints
change. The physics profile is rebound to the new facade hash without
parameter changes.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_R10_FACADE = (
    REPO_ROOT / "outputs/centrifuge_identity_root_r10_cup_colliders/facade/facade.usda"
)
DEFAULT_R10_PHYSICS = (
    REPO_ROOT / "outputs/centrifuge_identity_root_r10_cup_colliders/centrifuge.physics.json"
)
DEFAULT_OUT_ROOT = REPO_ROOT / "outputs/centrifuge_identity_root_r10v2_proxy_invisible"
PROFILE_REVISION = "r4-proxy-visibility"
ROOT = "/World/Centrifuge"

# Legacy visible proxies enumerated from the composed r10 facade
# (scripts/build_centrifuge_cup_collider_facade_r10.py prims stay invisible).
LEGACY_PROXY_PRIMS: dict[str, tuple[str, ...]] = {
    "group_0": ("housing", "housing_top_left", "housing_top_right", "housing_notch_back"),
    "group_2": ("button_face",),
    "group_6": (
        "hub",
        "quad_0",
        "quad_1",
        "quad_2",
        "quad_3",
        "ring_0",
        "ring_1",
        "ring_2",
        "ring_3",
    ),
    "group_23": ("lid_shell",),
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _rebind_physics_profile(value: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    rebound = deepcopy(value)
    binding = rebound.get("source_binding")
    if not isinstance(binding, dict):
        raise ValueError("physics profile source_binding must be an object")
    profile_id = rebound.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("physics profile profile_id must be a non-empty string")
    binding["sha256"] = source_sha256
    rebound["profile_id"] = f"{profile_id}.proxy-invisible"
    rebound["revision"] = PROFILE_REVISION
    return rebound


def visibility_overlay_text() -> str:
    groups = []
    for group, names in LEGACY_PROXY_PRIMS.items():
        overs = "\n".join(
            f'''                over "{name}"
                {{
                    token visibility = "invisible"
                }}'''
            for name in names
        )
        groups.append(
            f'''        over "{group}"
        {{
            over "__aan_collision_proxy"
            {{
{overs}
            }}
        }}'''
        )
    joined = "\n".join(groups)
    return f'''over "World"
{{
    over "Centrifuge"
    {{
{joined}
    }}
}}
'''


def build(*, r10_facade: Path, r10_physics: Path, out_root: Path) -> dict[str, Path]:
    r10_facade = r10_facade.resolve()
    r10_physics = r10_physics.resolve()
    if not r10_facade.is_file():
        raise FileNotFoundError(r10_facade)
    if not r10_physics.is_file():
        raise FileNotFoundError(r10_physics)
    facade_dir = out_root / "facade"
    facade_dir.mkdir(parents=True, exist_ok=True)
    relative_r10 = Path(os.path.relpath(r10_facade, facade_dir))
    facade_text = f'''#usda 1.0
(
    defaultPrim = "World"
    framesPerSecond = 24
    metersPerUnit = 1
    subLayers = [
        @{relative_r10.as_posix()}@
    ]
    timeCodesPerSecond = 60
    upAxis = "Z"
)

{visibility_overlay_text()}'''
    facade_path = facade_dir / "facade.usda"
    if facade_path.exists():
        raise FileExistsError(f"refusing to replace generated artifact: {facade_path}")
    facade_path.write_text(facade_text, encoding="utf-8")
    facade_sha = _sha(facade_path)

    physics = json.loads(r10_physics.read_text(encoding="utf-8"))
    rebound = _rebind_physics_profile(physics, source_sha256=facade_sha)
    rebound["revision"] = PROFILE_REVISION
    physics_path = out_root / "centrifuge.physics.json"
    if physics_path.exists():
        raise FileExistsError(f"refusing to replace generated artifact: {physics_path}")
    physics_path.write_text(
        json.dumps(rebound, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    provenance = {
        "schema_version": "aan.centrifuge_proxy_visibility_facade.v1",
        "base_facade": str(r10_facade),
        "base_facade_sha256": _sha(r10_facade),
        "facade_sha256": facade_sha,
        "physics_profile_sha256": _sha(physics_path),
        "revision": PROFILE_REVISION,
        "visibility_overrides": {
            group: list(names) for group, names in LEGACY_PROXY_PRIMS.items()
        },
        "claim_boundary": (
            "Display-only overlay: legacy collision proxies become invisible. "
            "Collision shapes, transforms, joints, drives, and the mass bundle "
            "are inherited from the r10 facade unchanged."
        ),
    }
    provenance_path = facade_dir / "facade_provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "facade": facade_path,
        "physics": physics_path,
        "provenance": provenance_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r10-facade", type=Path, default=DEFAULT_R10_FACADE)
    parser.add_argument("--r10-physics", type=Path, default=DEFAULT_R10_PHYSICS)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    args = parser.parse_args()
    result = build(
        r10_facade=args.r10_facade,
        r10_physics=args.r10_physics,
        out_root=args.out_root,
    )
    print(json.dumps({k: str(v) for k, v in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
