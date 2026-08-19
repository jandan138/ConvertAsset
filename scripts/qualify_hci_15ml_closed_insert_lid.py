#!/usr/bin/env python3
"""Qualify the HCI-fit closed 15 mL tube against the r9 HCI centrifuge.

This wrapper binds the new closed-tube package, refuses the k=0.365 glass
test-tube hash, and records only producer-owned kinematic contact evidence.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

from scripts.build_hci_15ml_closed_insert_lid_assets import (
    ENTRY_PRIM,
    FORBIDDEN_K0365_TUBE_SHA256,
    K_D,
    K_H_SHORT,
    K_H_SHORT_BAND,
    scaled_geometry,
)
from scripts.qualify_centrifuge_task_interactions import (
    build_parser,
    main as qualify_main,
)


CLOSED_TUBE_ENTRY_PRIM = ENTRY_PRIM
DEFAULT_CENTRIFUGE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "centrifuge_identity_root_r9_mount_contract_v2/package"
)
DEFAULT_DEVICE_PROFILE = DEFAULT_CENTRIFUGE / "articulation" / "device_profile.json"
DEFAULT_TUBE_PACKAGE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "hci_15ml_closed_insert_lid_20260818/package"
)
SHORT_TUBE_PACKAGE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "hci_15ml_closed_insert_lid_r2_20260818/package"
)


def reject_forbidden_tube_hash(sha: str) -> None:
    if sha == FORBIDDEN_K0365_TUBE_SHA256:
        raise ValueError(
            "k=0.365 glass test-tube evidence is forbidden for this HCI-fit closed 15 mL request"
        )


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    import sys as _sys

    raw = list(_sys.argv[1:]) if argv is None else list(argv)
    short = "--short-cup-variant" in raw
    raw = [item for item in raw if item != "--short-cup-variant"]
    geometry = (
        scaled_geometry(K_D, K_H_SHORT, k_h_band=K_H_SHORT_BAND)
        if short
        else scaled_geometry()
    )
    parser = build_parser()
    parser.set_defaults(
        centrifuge_package=DEFAULT_CENTRIFUGE,
        tube_package=SHORT_TUBE_PACKAGE if short else DEFAULT_TUBE_PACKAGE,
        device_profile=DEFAULT_DEVICE_PROFILE,
        tube_entry_prim=CLOSED_TUBE_ENTRY_PRIM,
        tube_radius_m=geometry["tube_radius_m"],
        tube_height_m=geometry["tube_height_m"],
    )
    args = parser.parse_args(raw)
    tube_asset = args.tube_package.resolve() / "asset.usd"
    if tube_asset.is_file():
        reject_forbidden_tube_hash(_sha(tube_asset))
    sys.argv = [sys.argv[0], *[
        "--centrifuge-package", str(args.centrifuge_package),
        "--tube-package", str(args.tube_package),
        "--device-profile", str(args.device_profile),
        "--tube-entry-prim", str(args.tube_entry_prim),
        "--tube-radius-m", str(args.tube_radius_m),
        "--tube-height-m", str(args.tube_height_m),
    ]]
    if args.centrifuge_manifest is not None:
        sys.argv.extend(["--centrifuge-manifest", str(args.centrifuge_manifest)])
    if args.tube_manifest is not None:
        sys.argv.extend(["--tube-manifest", str(args.tube_manifest)])
    if args.out_dir is not None:
        sys.argv.extend(["--out-dir", str(args.out_dir)])
    sys.argv.extend(["--socket-name", str(args.socket_name)])
    if args.additional_parked_socket is not None:
        sys.argv.extend(["--additional-parked-socket", str(args.additional_parked_socket)])
    sys.argv.extend(["--physics-dt", str(args.physics_dt), "--lid-sweep-rad", str(args.lid_sweep_rad)])
    return qualify_main()


if __name__ == "__main__":
    raise SystemExit(main())
