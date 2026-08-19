from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_centrifuge_device_profile_balanced_sockets import (
    APERTURE_LOCALS,
    APERTURE_ROTATION_WXYZ,
    INSERTED_BOTTOM_Z_M,
    REVISION,
    SOCKET_1_WORLD_XY_M,
    SOCKET_2_WORLD_XY_M,
    SPIN_CENTER_WORLD_M,
    balanced_socket_frames,
    build_balanced_profile,
    main,
)


PROFILE = Path(
    "outputs/centrifuge_identity_root_r9_mount_contract_v2/package/articulation/device_profile.json"
)


def _predecessor() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


@pytest.mark.skipif(not PROFILE.is_file(), reason="r9 device profile is not on this host")
def test_balanced_frames_cover_both_sockets_with_expected_parents() -> None:
    frames = balanced_socket_frames()
    assert set(frames) == {
        "tube_socket_1_aperture",
        "tube_socket_1_inserted_bottom_parked_root",
        "tube_socket_2_aperture",
        "tube_socket_2_inserted_bottom_parked_root",
    }
    for name in ("tube_socket_1", "tube_socket_2"):
        aperture = frames[f"{name}_aperture"]
        inserted = frames[f"{name}_inserted_bottom_parked_root"]
        assert aperture["parent_prim"] == "/World/Centrifuge/group_6"
        assert inserted["parent_prim"] == "/World/Centrifuge"
        assert aperture["authoritative"] is True
        assert inserted["authoritative"] is True
        assert aperture["rotation_parent_local_wxyz"] == pytest.approx(APERTURE_ROTATION_WXYZ)
        assert inserted["rotation_parent_local_wxyz"] == [1.0, 0.0, 0.0, 0.0]


@pytest.mark.skipif(not PROFILE.is_file(), reason="r9 device profile is not on this host")
def test_socket_pair_is_symmetric_about_the_measured_spin_center() -> None:
    cx, cy = SPIN_CENTER_WORLD_M
    x1, y1 = SOCKET_1_WORLD_XY_M
    x2, y2 = SOCKET_2_WORLD_XY_M
    assert (x1 + x2) / 2 == pytest.approx(cx, abs=1e-4)
    assert (y1 + y2) / 2 == pytest.approx(cy, abs=1e-4)
    r1 = ((x1 - cx) ** 2 + (y1 - cy) ** 2) ** 0.5
    r2 = ((x2 - cx) ** 2 + (y2 - cy) ** 2) ** 0.5
    assert r1 == pytest.approx(r2, abs=1e-4)


@pytest.mark.skipif(not PROFILE.is_file(), reason="r9 device profile is not on this host")
def test_build_balanced_profile_keeps_socket_0_and_bumps_revision() -> None:
    predecessor = _predecessor()
    profile = build_balanced_profile(predecessor)
    assert profile["revision"] == REVISION
    assert profile["source_sha256"] == predecessor["source_sha256"]
    for name, frame in predecessor["named_frames"].items():
        assert profile["named_frames"][name] == frame
    assert "tube_socket_1_aperture" in profile["named_frames"]
    inserted = profile["named_frames"]["tube_socket_1_inserted_bottom_parked_root"]
    assert inserted["translation_parent_local_m"] == pytest.approx(
        [SOCKET_1_WORLD_XY_M[0], SOCKET_1_WORLD_XY_M[1], INSERTED_BOTTOM_Z_M]
    )
    # The predecessor mapping itself is not mutated.
    assert "tube_socket_1_aperture" not in predecessor["named_frames"]


@pytest.mark.skipif(not PROFILE.is_file(), reason="r9 device profile is not on this host")
def test_main_writes_profile_without_touching_predecessor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = PROFILE.read_bytes()
    out = tmp_path / "device_profile_r11.json"
    monkeypatch.setattr(
        "sys.argv", ["prog", "--profile", str(PROFILE), "--out", str(out)]
    )
    assert main() == 0
    assert PROFILE.read_bytes() == before
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["revision"] == REVISION
    assert set(APERTURE_LOCALS) == {"tube_socket_1", "tube_socket_2"}
