from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.build_tube_rack_r4_facade import (
    TubeRackR4BuildError,
    build_tube_rack_r4_facade,
)
from scripts.qualify_tube_rack_insertion import (
    PackageIdentityError,
    evaluate_insertion_observations,
    load_package_identity,
)


PROXY_SPECS = {
    "base": ((0.0803, 0.02684, 0.003), (0.0, 0.0, 0.0015)),
    "wall_left": ((0.003, 0.02684, 0.026), (-0.03815, 0.0, 0.013)),
    "wall_right": ((0.003, 0.02684, 0.026), (0.03815, 0.0, 0.013)),
    "wall_back": ((0.0803, 0.003, 0.026), (0.0, -0.01192, 0.013)),
    "wall_front": ((0.0803, 0.003, 0.026), (0.0, 0.01192, 0.013)),
    "socket_0_bottom": ((0.0132, 0.0132, 0.002), (-0.0100375, -0.006424, 0.0025)),
    "socket_0_wall_pos_x": ((0.002, 0.0132, 0.032), (-0.0034375, -0.006424, 0.0185)),
    "socket_0_wall_neg_x": ((0.002, 0.0132, 0.032), (-0.0166375, -0.006424, 0.0185)),
    "socket_0_wall_pos_y": ((0.0092, 0.002, 0.032), (-0.0100375, 0.000176, 0.0185)),
    "socket_0_wall_neg_y": ((0.0092, 0.002, 0.032), (-0.0100375, -0.013024, 0.0185)),
}


def _vec(values: tuple[float, float, float]) -> str:
    return ", ".join(str(value) for value in values)


def _r3_facade_text() -> str:
    blocks = []
    for name, (scale, translate) in PROXY_SPECS.items():
        blocks.append(
            f'''
            def Cube "{name}" (
                prepend apiSchemas = ["PhysicsCollisionAPI"]
            )
            {{
                float3 xformOp:scale = ({_vec(scale)})
                float3 xformOp:translate = ({_vec(translate)})
                uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            }}
'''
        )
    return (
        '#usda 1.0\n'
        '(\n'
        '    defaultPrim = "World"\n'
        '    framesPerSecond = 24\n'
        '    metersPerUnit = 1\n'
        '    timeCodesPerSecond = 60\n'
        '    upAxis = "Z"\n'
        ')\n'
        'over "World"\n{\n    over "TubeRack"\n    {\n'
        '        def Xform "__aan_collision_proxy"\n        {\n'
        + "".join(blocks)
        + "        }\n    }\n}\n"
    )


def _write_r3_inputs(tmp_path: Path) -> tuple[Path, Path]:
    facade = tmp_path / "r3" / "facade.usda"
    facade.parent.mkdir()
    facade.write_text(_r3_facade_text(), encoding="utf-8")
    provenance = {
        "schema_version": "tube_task_uniform_scale_provenance.v1",
        "raw_source_usd": "/producer/source.usd",
        "raw_sha256": "b" * 64,
        "asset_entry_prim": "/World/TubeRack",
        "facade_revision": "r3-compound-proxy",
        "facade_sha256": sha256(facade.read_bytes()).hexdigest(),
        "compound_proxy": {
            "status": "declared",
            "proxy_count": 11,
            "proxies": list(PROXY_SPECS),
            "scale_lineage": "k0.365_authoritative",
        },
    }
    provenance_path = tmp_path / "r3" / "facade_provenance.json"
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    return facade, provenance_path


def _write_r3_profiles(
    tmp_path: Path,
    *,
    facade_sha256: str,
) -> tuple[Path, Path]:
    interaction = {
        "schema_version": "aan.object_interaction_profile.v1",
        "profile_id": "blenderkit.tube_rack.uniform_scale_k0365.interaction.r3",
        "revision": "r3",
        "source_binding": {
            "sha256": facade_sha256,
            "stage_metrics": {
                "meters_per_unit": 1.0,
                "kilograms_per_unit": 1.0,
                "up_axis": "Z",
            },
            "raw_sha256_provenance_only": "b" * 64,
        },
        "asset_entry_prim": "/World/TubeRack",
        "colliders": [
            {
                "relative_path": "__aan_collision_proxy/socket_0_bottom",
                "mode": "preserve",
                "purpose": ["containment", "gripper"],
            }
        ],
        "named_frames": {
            "support": {
                "translation_body_local_usd": [0.0, 0.0, 0.0],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
            "socket_0_inserted_bottom": {
                "translation_body_local_usd": [-0.0100375, -0.006424, 0.0098215],
                "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
        },
        "runtime_gates": {
            "stable_support": {"required": True},
            "root_motion": {"required": True, "min_translation_m": 0.01},
        },
    }
    physics = {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": (
            "blenderkit.tube_rack.uniform_scale_k0365."
            "provisional.r3-compound-proxy"
        ),
        "revision": "r3-compound-proxy",
        "source_binding": {
            "sha256": facade_sha256,
            "stage_metrics": {
                "meters_per_unit": 1.0,
                "kilograms_per_unit": 1.0,
                "up_axis": "Z",
            },
            "raw_sha256_provenance_only": "b" * 64,
        },
        "evidence": {
            "parameter_status": "provisional_geometry",
            "replacement_contract": "replace the complete bundle",
        },
        "scope_rules": [
            {
                "scope_path": "/World/TubeRack",
                "body_rules": [
                    {
                        "relative_path": ".",
                        "motion_role": "dynamic",
                        "mass_properties": {
                            "mass_kg": 0.01701949375,
                            "diagonal_inertia_kg_m2": [
                                3.307082304949084e-06,
                                1.143158619317057e-05,
                                1.0166034020851426e-05,
                            ],
                            "center_of_mass_body_local": [0.0, 0.0, 0.020075],
                        },
                    }
                ],
            }
        ],
    }
    interaction_path = tmp_path / "r3" / "interaction.json"
    physics_path = tmp_path / "r3" / "physics.json"
    interaction_path.write_text(json.dumps(interaction), encoding="utf-8")
    physics_path.write_text(json.dumps(physics), encoding="utf-8")
    return interaction_path, physics_path


def test_r4_builder_corrects_cube_semantics_and_visual_leakage(
    tmp_path: Path,
) -> None:
    facade, provenance = _write_r3_inputs(tmp_path)
    out_facade = tmp_path / "r4" / "facade.usda"
    out_provenance = tmp_path / "r4" / "facade_provenance.json"

    result = build_tube_rack_r4_facade(
        predecessor_facade_path=facade,
        predecessor_provenance_path=provenance,
        output_facade_path=out_facade,
        output_provenance_path=out_provenance,
    )

    text = out_facade.read_text(encoding="utf-8")
    metadata = json.loads(out_provenance.read_text(encoding="utf-8"))
    assert "framesPerSecond = 24" in text
    assert "timeCodesPerSecond = 60" in text
    assert text.count("double size = 1") == len(PROXY_SPECS)
    assert text.count('token visibility = "invisible"') == len(PROXY_SPECS)
    for name, (size, _translation) in PROXY_SPECS.items():
        assert f'over "{name}"' in text
        assert f"float3 xformOp:scale = ({_vec(size)})" in text
    assert metadata["compound_proxy"]["proxy_count"] == len(PROXY_SPECS)
    assert metadata["compound_proxy"]["proxies"] == list(PROXY_SPECS)
    assert metadata["compound_proxy"]["cube_size"] == 1.0
    assert metadata["compound_proxy"]["render_visibility"] == "invisible"
    assert metadata["compound_proxy"]["support_min_z_m"] == pytest.approx(0.0)
    assert metadata["predecessor_facade"]["sha256"] == sha256(
        facade.read_bytes()
    ).hexdigest()
    assert metadata["facade_sha256"] == sha256(out_facade.read_bytes()).hexdigest()
    assert result["proxy_count"] == 10


def test_r4_builder_rebinds_profiles_without_changing_semantics(
    tmp_path: Path,
) -> None:
    facade, provenance = _write_r3_inputs(tmp_path)
    predecessor_sha256 = sha256(facade.read_bytes()).hexdigest()
    interaction, physics = _write_r3_profiles(
        tmp_path,
        facade_sha256=predecessor_sha256,
    )
    old_interaction = json.loads(interaction.read_text(encoding="utf-8"))
    old_physics = json.loads(physics.read_text(encoding="utf-8"))
    out_facade = tmp_path / "r4" / "facade.usda"
    out_provenance = tmp_path / "r4" / "facade_provenance.json"
    out_interaction = tmp_path / "r4" / "interaction.json"
    out_physics = tmp_path / "r4" / "physics.json"

    result = build_tube_rack_r4_facade(
        predecessor_facade_path=facade,
        predecessor_provenance_path=provenance,
        output_facade_path=out_facade,
        output_provenance_path=out_provenance,
        predecessor_interaction_path=interaction,
        predecessor_physics_path=physics,
        output_interaction_path=out_interaction,
        output_physics_path=out_physics,
    )

    r4_sha256 = sha256(out_facade.read_bytes()).hexdigest()
    new_interaction = json.loads(out_interaction.read_text(encoding="utf-8"))
    new_physics = json.loads(out_physics.read_text(encoding="utf-8"))
    expected_interaction = json.loads(json.dumps(old_interaction))
    expected_interaction["profile_id"] = (
        "blenderkit.tube_rack.uniform_scale_k0365.interaction.r4"
    )
    expected_interaction["revision"] = "r4"
    expected_interaction["source_binding"]["sha256"] = r4_sha256
    expected_physics = json.loads(json.dumps(old_physics))
    expected_physics["profile_id"] = (
        "blenderkit.tube_rack.uniform_scale_k0365."
        "provisional.r4-compound-proxy-cube-size-correction"
    )
    expected_physics["revision"] = "r4-compound-proxy-cube-size-correction"
    expected_physics["source_binding"]["sha256"] = r4_sha256

    assert new_interaction == expected_interaction
    assert new_physics == expected_physics
    assert out_interaction.read_text(encoding="utf-8") == (
        json.dumps(
            expected_interaction,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    assert out_physics.read_text(encoding="utf-8") == (
        json.dumps(
            expected_physics,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    assert result["interaction_profile_sha256"] == sha256(
        out_interaction.read_bytes()
    ).hexdigest()
    assert result["physics_profile_sha256"] == sha256(
        out_physics.read_bytes()
    ).hexdigest()


def test_r4_builder_rejects_profile_not_bound_to_predecessor_facade(
    tmp_path: Path,
) -> None:
    facade, provenance = _write_r3_inputs(tmp_path)
    interaction, physics = _write_r3_profiles(
        tmp_path,
        facade_sha256=sha256(facade.read_bytes()).hexdigest(),
    )
    value = json.loads(physics.read_text(encoding="utf-8"))
    value["source_binding"]["sha256"] = "f" * 64
    physics.write_text(json.dumps(value), encoding="utf-8")
    outputs = [
        tmp_path / "r4" / "facade.usda",
        tmp_path / "r4" / "facade_provenance.json",
        tmp_path / "r4" / "interaction.json",
        tmp_path / "r4" / "physics.json",
    ]

    with pytest.raises(TubeRackR4BuildError, match="source_binding"):
        build_tube_rack_r4_facade(
            predecessor_facade_path=facade,
            predecessor_provenance_path=provenance,
            output_facade_path=outputs[0],
            output_provenance_path=outputs[1],
            predecessor_interaction_path=interaction,
            predecessor_physics_path=physics,
            output_interaction_path=outputs[2],
            output_physics_path=outputs[3],
        )

    assert not any(path.exists() for path in outputs)


def test_r4_builder_refuses_to_replace_a_profile_output(
    tmp_path: Path,
) -> None:
    facade, provenance = _write_r3_inputs(tmp_path)
    interaction, physics = _write_r3_profiles(
        tmp_path,
        facade_sha256=sha256(facade.read_bytes()).hexdigest(),
    )
    out_interaction = tmp_path / "r4" / "interaction.json"
    out_interaction.parent.mkdir()
    out_interaction.write_text("do not replace\n", encoding="utf-8")

    with pytest.raises(TubeRackR4BuildError, match="refusing to replace"):
        build_tube_rack_r4_facade(
            predecessor_facade_path=facade,
            predecessor_provenance_path=provenance,
            output_facade_path=tmp_path / "r4" / "facade.usda",
            output_provenance_path=tmp_path / "r4" / "facade_provenance.json",
            predecessor_interaction_path=interaction,
            predecessor_physics_path=physics,
            output_interaction_path=out_interaction,
            output_physics_path=tmp_path / "r4" / "physics.json",
        )

    assert out_interaction.read_text(encoding="utf-8") == "do not replace\n"
    assert not (tmp_path / "r4" / "facade.usda").exists()


def test_r4_builder_rejects_a_proxy_below_the_support_frame(
    tmp_path: Path,
) -> None:
    facade, provenance = _write_r3_inputs(tmp_path)
    facade.write_text(
        facade.read_text(encoding="utf-8").replace(
            "float3 xformOp:translate = (0.0, 0.0, 0.0015)",
            "float3 xformOp:translate = (0.0, 0.0, 0.0)",
            1,
        ),
        encoding="utf-8",
    )
    value = json.loads(provenance.read_text(encoding="utf-8"))
    value["facade_sha256"] = sha256(facade.read_bytes()).hexdigest()
    provenance.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(TubeRackR4BuildError, match="support frame"):
        build_tube_rack_r4_facade(
            predecessor_facade_path=facade,
            predecessor_provenance_path=provenance,
            output_facade_path=tmp_path / "r4" / "facade.usda",
            output_provenance_path=tmp_path / "r4" / "facade_provenance.json",
        )


def _write_package(
    root: Path,
    *,
    entry_prim: str,
    include_socket_frames: bool,
) -> tuple[Path, Path]:
    package = root / "package"
    package.mkdir(parents=True)
    (package / "asset.usd").write_text("#usda 1.0\n", encoding="utf-8")
    asset_sha256 = sha256((package / "asset.usd").read_bytes()).hexdigest()
    frames = {
        "support": {
            "prim_path": f"{entry_prim}/__aan_frame_support",
            "parent_prim": entry_prim,
            "translation_body_local_usd": [0.0, 0.0, 0.0],
            "authoritative": True,
        }
    }
    if include_socket_frames:
        frames.update(
            {
                "socket_0_aperture": {
                    "prim_path": f"{entry_prim}/__aan_frame_socket_0_aperture",
                    "parent_prim": entry_prim,
                    "translation_body_local_usd": [0.0, 0.0, 0.04],
                    "authoritative": True,
                },
                "socket_0_inserted_bottom": {
                    "prim_path": f"{entry_prim}/__aan_frame_socket_0_inserted_bottom",
                    "parent_prim": entry_prim,
                    "translation_body_local_usd": [0.0, 0.0, 0.004],
                    "authoritative": True,
                },
            }
        )
    manifest = {
        "schema_version": "asset_application_normalizer.v1",
        "overall_status": "pass",
        "entrypoints": {"asset_entry_prim": entry_prim},
        "interaction_contract": {
            "status": "pass",
            "asset_entry_prim": entry_prim,
            "runtime_identity": {
                "rigid_root_prim": entry_prim,
                "active_rigid_body_prims": [entry_prim],
                "exactly_one_active_rigid_body": True,
            },
            "closure": {
                "status": "pass",
                "artifacts": [
                    {"path": "asset.usd", "sha256": asset_sha256}
                ],
            },
            "named_frames": frames,
            "collider_prims": (
                [
                    {
                        "prim_path": f"{entry_prim}/__aan_collision_proxy/socket_0_bottom",
                        "purpose": ["containment"],
                    },
                    {
                        "prim_path": f"{entry_prim}/__aan_collision_proxy/socket_0_wall_pos_x",
                        "purpose": ["gripper"],
                    },
                ]
                if include_socket_frames
                else []
            ),
        },
    }
    manifest_path = root / "package.manifest.json"
    embedded = package / "evidence" / "manifest.json"
    embedded.parent.mkdir(parents=True)
    serialized = json.dumps(manifest, indent=2) + "\n"
    manifest_path.write_text(serialized, encoding="utf-8")
    embedded.write_text(serialized, encoding="utf-8")
    return package, manifest_path


def test_package_identity_hash_binds_manifest_asset_and_entry_prim(
    tmp_path: Path,
) -> None:
    package, manifest = _write_package(
        tmp_path / "rack",
        entry_prim="/World/TubeRack",
        include_socket_frames=True,
    )

    identity = load_package_identity(package, manifest, role="rack")

    assert identity["package_manifest_sha256"] == sha256(
        manifest.read_bytes()
    ).hexdigest()
    assert identity["asset_usd_sha256"] == sha256(
        (package / "asset.usd").read_bytes()
    ).hexdigest()
    assert identity["asset_entry_prim"] == "/World/TubeRack"
    assert identity["active_rigid_body_prims"] == ["/World/TubeRack"]


def test_package_identity_rejects_non_authoritative_support_frame(
    tmp_path: Path,
) -> None:
    package, manifest = _write_package(
        tmp_path / "rack",
        entry_prim="/World/TubeRack",
        include_socket_frames=True,
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["interaction_contract"]["named_frames"]["support"][
        "authoritative"
    ] = False
    serialized = json.dumps(value, indent=2) + "\n"
    manifest.write_text(serialized, encoding="utf-8")
    (package / "evidence" / "manifest.json").write_text(
        serialized,
        encoding="utf-8",
    )

    with pytest.raises(PackageIdentityError, match="authoritative"):
        load_package_identity(package, manifest, role="rack")


def test_package_identity_rejects_contract_entry_prim_mismatch(
    tmp_path: Path,
) -> None:
    package, manifest = _write_package(
        tmp_path / "rack",
        entry_prim="/World/TubeRack",
        include_socket_frames=True,
    )
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["interaction_contract"]["asset_entry_prim"] = "/World/Wrong"
    serialized = json.dumps(value, indent=2) + "\n"
    manifest.write_text(serialized, encoding="utf-8")
    (package / "evidence" / "manifest.json").write_text(
        serialized,
        encoding="utf-8",
    )

    with pytest.raises(PackageIdentityError, match="asset_entry_prim"):
        load_package_identity(package, manifest, role="rack")


def _passing_observations() -> dict[str, object]:
    return {
        "finite": True,
        "composition": {
            "rack_active_rigid_body_prims": ["/World/TubeRack"],
            "tube_active_rigid_body_prims": ["/World/TestTube"],
            "rack_expected_rigid_root": "/World/TubeRack",
            "tube_expected_rigid_root": "/World/TestTube",
            "tube_kinematic": False,
            "authored_translation_updates": 0,
        },
        "trajectory": {
            "sample_count": 180,
            "expected_insertion_depth_m": 0.036,
            "observed_insertion_depth_m": 0.035,
            "final_bottom_distance_m": 0.001,
            "axis_alignment_error_deg": 2.0,
        },
        "contacts": {
            "contact_probe_available": True,
            "bottom_pair_contact_samples": 4,
            "side_pair_contact_samples": 2,
            "max_penetration_m": 0.0004,
        },
    }


def test_insertion_evaluator_requires_dynamic_pair_contact_and_clearance() -> None:
    result = evaluate_insertion_observations(_passing_observations())

    assert result["status"] == "pass"
    assert all(gate["status"] == "pass" for gate in result["gates"].values())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("composition", "tube_kinematic", True), "kinematic"),
        (("composition", "authored_translation_updates", 1), "translate"),
        (("contacts", "bottom_pair_contact_samples", 0), "bottom"),
        (("contacts", "max_penetration_m", 0.00101), "penetration"),
        (("trajectory", "final_bottom_distance_m", 0.00201), "bottom"),
    ],
)
def test_insertion_evaluator_fails_closed(
    mutation: tuple[str, str, object],
    message: str,
) -> None:
    observations = _passing_observations()
    group, key, value = mutation
    observations[group][key] = value  # type: ignore[index]

    result = evaluate_insertion_observations(observations)

    assert result["status"] == "blocked"
    assert message in json.dumps(result["gates"]).lower()
