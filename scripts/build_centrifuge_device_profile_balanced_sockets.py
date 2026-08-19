#!/usr/bin/env python3
"""Author the balanced-socket-pair revision of the HCI r9 device profile.

Adds tube_socket_1 (arm-plate hole at world (+0.0208, +0.0142)) and
tube_socket_2 (its 180-degree balance partner at (-0.1016, -0.1107) about the
measured rotor spin center (-0.0404, -0.0482)) to the r9 device profile.
Both holes are large visual arm-plate holes whose vertical channels clear the
HCI-fit closed 15 mL tube (nearest material >= 6 mm from the axis below the
rim). The socket_0 frames stay untouched; the source binding is unchanged.

The parent-local aperture values were computed against package
outputs/centrifuge_identity_root_r9_mount_contract_v2/package/asset.usd and
verified to resolve to the intended world poses through the same transform
math used by scripts/qualify_centrifuge_task_interactions.py.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


DEFAULT_PROFILE = Path(
    "outputs/centrifuge_identity_root_r9_mount_contract_v2/package/articulation/device_profile.json"
)
DEFAULT_OUT = Path(
    "outputs/centrifuge_identity_root_r9_mount_contract_v2/articulation/"
    "device_profile_r11_visual_cup_sockets.json"
)
REVISION = "r11-balanced-visual-cup-pair"
ROTOR_BODY = "/World/Centrifuge/group_6"
CENTRIFUGE_ROOT = "/World/Centrifuge"
SPIN_CENTER_WORLD_M = (-0.0404004111, -0.0482212505)
ROTOR_TOP_PLANE_Z_M = 0.15289813
# Measured floor of the 17 mm visual arm-plate cups (the tube seats on it).
INSERTED_BOTTOM_Z_M = 0.1281

# World XY of the balanced hole pair, measured from the rotor visual mesh.
SOCKET_1_WORLD_XY_M = (0.0208, 0.0142)
SOCKET_2_WORLD_XY_M = (-0.1016, -0.1107)

# Rotor-parent-local aperture poses (resolve to world +Z axis and the world XY
# above through the parked rotor transform; verified by runtime resolution).
APERTURE_ROTATION_WXYZ = (0.707106781, -0.707106781, 0.0, 0.0)
APERTURE_LOCALS = {
    "tube_socket_1": (0.081142859, 0.281515033, 0.118857145),
    "tube_socket_2": (-0.632571439, 0.281515033, -0.580571438),
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _frame(parent: str, translation: tuple[float, ...], rotation: tuple[float, ...]) -> dict[str, Any]:
    return {
        "authoritative": True,
        "parent_prim": parent,
        "rotation_parent_local_wxyz": [float(v) for v in rotation],
        "translation_parent_local_m": [float(v) for v in translation],
    }


def balanced_socket_frames() -> dict[str, dict[str, Any]]:
    frames: dict[str, dict[str, Any]] = {}
    for name, xy in (
        ("tube_socket_1", SOCKET_1_WORLD_XY_M),
        ("tube_socket_2", SOCKET_2_WORLD_XY_M),
    ):
        frames[f"{name}_aperture"] = _frame(
            ROTOR_BODY, APERTURE_LOCALS[name], APERTURE_ROTATION_WXYZ
        )
        frames[f"{name}_inserted_bottom_parked_root"] = _frame(
            CENTRIFUGE_ROOT,
            (xy[0], xy[1], INSERTED_BOTTOM_Z_M),
            (1.0, 0.0, 0.0, 0.0),
        )
    return frames


def build_balanced_profile(
    predecessor: dict[str, Any], *, source_sha256: str | None = None
) -> dict[str, Any]:
    profile = deepcopy(predecessor)
    frames = profile.get("named_frames")
    if not isinstance(frames, dict):
        raise ValueError("predecessor profile named_frames are missing")
    for required in ("tube_socket_0_aperture", "tube_socket_0_inserted_bottom_parked_root"):
        if required not in frames:
            raise ValueError(f"predecessor profile is missing {required}")
    frames.update(balanced_socket_frames())
    profile["revision"] = REVISION
    if source_sha256 is not None:
        profile["source_sha256"] = source_sha256
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--source-sha256",
        default=None,
        help=(
            "Rebind the profile to a different facade/package source hash "
            "(e.g. the r10 cup-collider facade)."
        ),
    )
    args = parser.parse_args()
    predecessor = json.loads(args.profile.read_text(encoding="utf-8"))
    source_before = _sha(args.profile)
    profile = build_balanced_profile(predecessor, source_sha256=args.source_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if _sha(args.profile) != source_before:
        raise RuntimeError("predecessor device profile was modified")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "out_sha256": _sha(args.out),
                "revision": REVISION,
                "sockets": ["tube_socket_1", "tube_socket_2"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
