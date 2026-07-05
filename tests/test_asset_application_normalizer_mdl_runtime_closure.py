from pathlib import Path

from convert_asset.asset_application_normalizer.mdl_runtime_closure import (
    build_binding_scope_report,
    build_material_view_evidence,
    build_material_runtime_closure,
    build_not_run_material_runtime_closure,
    classify_mdl_module,
    discover_mdl_roots,
    merge_runtime_compiler_report,
    parse_material_runtime_log,
    parse_mdl_runtime_dependencies,
)


def test_not_run_material_runtime_closure_keeps_missing_texture_schema() -> None:
    result = build_not_run_material_runtime_closure("static gate blocked")

    assert result.material_runtime_closure["missing_textures"] == []
    assert result.static_material_runtime_report["missing_texture_count"] == 0


def test_parse_mdl_runtime_dependencies_extracts_imports_using_and_textures(
    tmp_path: Path,
) -> None:
    mdl = tmp_path / "material_06.mdl"
    mdl.write_text(
        "mdl 1.0;\n"
        "import ad_3dsmax_maps::*;\n"
        "import ::OmniPBR::OmniPBR;\n"
        "using ::vray_materials import VRayMtl;\n"
        "// import ignored_comment::*;\n"
        "export material m(\n"
        '    texture_2d tex = texture_2d("../textures/image3.jpg"),\n'
        "    texture_2d empty_tex = texture_2d()\n"
        ") = material();\n",
        encoding="utf-8",
    )

    deps = parse_mdl_runtime_dependencies(mdl)

    assert deps.imported_modules == [
        "ad_3dsmax_maps",
        "OmniPBR",
        "vray_materials",
    ]
    assert deps.texture_literals == ["../textures/image3.jpg"]


def test_parse_mdl_runtime_dependencies_accepts_relative_module_imports(
    tmp_path: Path,
) -> None:
    mdl = tmp_path / "koo_material.mdl"
    mdl.write_text(
        "mdl 1.0;\n"
        "import .::KooPbr::KooPbr;\n"
        "using .::KooHelpers import Helper;\n",
        encoding="utf-8",
    )

    deps = parse_mdl_runtime_dependencies(mdl)

    assert deps.imported_modules == ["KooPbr", "KooHelpers"]


def test_classify_mdl_module_treats_stdlib_as_native_and_custom_as_required() -> None:
    assert classify_mdl_module("df") == "native_runtime_module"
    assert classify_mdl_module("::base::file_texture") == "native_runtime_module"
    assert classify_mdl_module("ad_3dsmax_materials") == "required_helper_module"
    assert classify_mdl_module("OmniPBR_ClearCoat") == "required_helper_module"


def test_discover_mdl_roots_uses_material_closure_and_package_mdl_directory(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "mdl" / "from_dir.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (package / "deps" / "mdl" / "from_record.mdl").write_text(
        "mdl 1.0;\n",
        encoding="utf-8",
    )
    material_closure = [
        {
            "source_mdl_assets": [
                {"package_path": "deps/mdl/from_record.mdl"},
                {"package_path": "deps/mdl/missing_from_record.mdl"},
            ]
        }
    ]

    roots = discover_mdl_roots(package, material_closure)

    assert roots == [
        package / "deps" / "mdl" / "from_dir.mdl",
        package / "deps" / "mdl" / "from_record.mdl",
    ]


def test_build_material_runtime_closure_blocks_unresolved_required_helper_and_records_texture(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "textures").mkdir(parents=True)
    (package / "deps" / "textures" / "image3.jpg").write_bytes(b"jpg")
    (package / "deps" / "mdl" / "material_06.mdl").write_text(
        "mdl 1.0;\n"
        "import ad_3dsmax_materials::*;\n"
        'export material m(texture_2d tex = texture_2d("../textures/image3.jpg")) = material();\n',
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 5
    assert result.stage_gate["check_id"] == "AAN-11-material-runtime-closure"
    assert result.stage_gate["status"] == "blocked"
    report = result.material_runtime_closure
    assert report["status"] == "blocked"
    assert report["root_mdl_assets"] == ["deps/mdl/material_06.mdl"]
    assert report["imported_mdl_modules"][0]["module"] == "ad_3dsmax_materials"
    assert report["imported_mdl_modules"][0]["resolution"] == "blocked"
    assert report["mdl_texture_assets"][0]["raw_asset_path"] == "../textures/image3.jpg"
    assert report["mdl_texture_assets"][0]["resolution"] == "mirrored"
    assert result.blocked_reasons[0]["blocker_id"] == (
        "aan11_block_required_mdl_runtime_dependency"
    )


def test_material_runtime_closure_reports_exact_missing_soap_to_dish_textures(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "mdl" / "MI_655dcc9a9237ad0001ba8197.mdl").write_text(
        "mdl 1.0;\n"
        'export material m(texture_2d tex = texture_2d("../textures/c00e97e58585d8ddb0f8b16a724d05a13eae31.jpg")) = material();\n',
        encoding="utf-8",
    )
    (package / "deps" / "mdl" / "MI_655dcc9ad6b50e000157727c.mdl").write_text(
        "mdl 1.0;\n"
        'export material m(texture_2d base = texture_2d("../textures/bf77ddc86c270d02747e7d0517103514ab51d0f.jpg"),\n'
        '                  texture_2d rough = texture_2d("../textures/c9c274d4ea1de7d059cec0a795b3b27e3941935.jpg")) = material();\n',
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 5
    report = result.material_runtime_closure
    assert report["status"] == "blocked"
    assert report["missing_textures"] == [
        "../textures/c00e97e58585d8ddb0f8b16a724d05a13eae31.jpg",
        "../textures/bf77ddc86c270d02747e7d0517103514ab51d0f.jpg",
        "../textures/c9c274d4ea1de7d059cec0a795b3b27e3941935.jpg",
    ]
    assert [
        (record["raw_asset_path"], record["package_path"], record["failure_mode"])
        for record in report["mdl_texture_assets"]
    ] == [
        (
            "../textures/c00e97e58585d8ddb0f8b16a724d05a13eae31.jpg",
            "deps/textures/c00e97e58585d8ddb0f8b16a724d05a13eae31.jpg",
            "missing_texture",
        ),
        (
            "../textures/bf77ddc86c270d02747e7d0517103514ab51d0f.jpg",
            "deps/textures/bf77ddc86c270d02747e7d0517103514ab51d0f.jpg",
            "missing_texture",
        ),
        (
            "../textures/c9c274d4ea1de7d059cec0a795b3b27e3941935.jpg",
            "deps/textures/c9c274d4ea1de7d059cec0a795b3b27e3941935.jpg",
            "missing_texture",
        ),
    ]
    assert result.static_material_runtime_report["missing_texture_count"] == 3


def test_build_material_runtime_closure_includes_binding_scope_static_hints(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "mdl" / "paint.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    material_closure = [
        {
            "material_prim": "/Looks/Paint",
            "binding_scope": "/World/DryingBox",
            "source_mdl_assets": [{"package_path": "deps/mdl/paint.mdl"}],
        }
    ]

    result = build_material_runtime_closure(
        package,
        material_closure=material_closure,
        required_prims=["/World/DryingBox"],
    )

    assert result.return_code == 0
    assert result.material_runtime_closure["binding_scope"]["status"] == "static_hint"
    assert result.material_runtime_closure["binding_scope"]["required_materials"][0] == {
        "required_prim": "/World/DryingBox",
        "material_prim": "/Looks/Paint",
        "binding_source": "material_closure.binding_scope",
    }


def test_material_runtime_closure_blocks_absolute_texture_escape(tmp_path: Path) -> None:
    package = tmp_path / "package"
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"png")
    (package / "deps" / "mdl").mkdir(parents=True)
    (package / "deps" / "mdl" / "paint.mdl").write_text(
        "mdl 1.0;\n"
        f'export material m(texture_2d tex = texture_2d("{outside}")) = material();\n',
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 5
    texture = result.material_runtime_closure["mdl_texture_assets"][0]
    assert texture["resolution"] == "blocked"
    assert texture["failure_mode"] == "package_escape"


def test_material_runtime_closure_resolves_nested_relative_mdl_modules(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl" / "templates").mkdir(parents=True)
    (package / "deps" / "mdl" / "root.mdl").write_text(
        "mdl 1.0;\nimport .::templates::mdl_0001::*;\n",
        encoding="utf-8",
    )
    (package / "deps" / "mdl" / "templates" / "mdl_0001.mdl").write_text(
        "mdl 1.0;\n",
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 0
    module = result.material_runtime_closure["imported_mdl_modules"][0]
    assert module["module"] == "templates::mdl_0001"
    assert module["resolution"] == "mirrored"
    assert module["package_path"] == "deps/mdl/templates/mdl_0001.mdl"


def test_material_runtime_closure_blocks_second_order_mdl_dependencies(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    (package / "deps" / "mdl" / "templates").mkdir(parents=True)
    (package / "deps" / "mdl" / "root.mdl").write_text(
        "mdl 1.0;\nimport .::templates::mdl_0001::*;\n",
        encoding="utf-8",
    )
    (package / "deps" / "mdl" / "templates" / "mdl_0001.mdl").write_text(
        "mdl 1.0;\nimport .::second_order::*;\n",
        encoding="utf-8",
    )

    result = build_material_runtime_closure(package, material_closure=[])

    assert result.return_code == 5
    blocked_modules = [
        record["module"]
        for record in result.material_runtime_closure["imported_mdl_modules"]
        if record["resolution"] == "blocked"
    ]
    assert blocked_modules == ["second_order"]


def test_material_runtime_closure_mirrors_source_context_helper_and_texture(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    package = tmp_path / "package"
    (source / "materials" / "helpers").mkdir(parents=True)
    (source / "textures").mkdir(parents=True)
    (package / "deps" / "mdl").mkdir(parents=True)
    (source / "textures" / "albedo.png").write_bytes(b"png")
    (source / "materials" / "helpers" / "paint.mdl").write_text(
        "mdl 1.0;\n",
        encoding="utf-8",
    )
    root_text = (
        "mdl 1.0;\n"
        "import .::helpers::paint::*;\n"
        'export material m(texture_2d tex = texture_2d("../textures/albedo.png")) = material();\n'
    )
    (source / "materials" / "root.mdl").write_text(root_text, encoding="utf-8")
    (package / "deps" / "mdl" / "root.mdl").write_text(root_text, encoding="utf-8")
    material_closure = [
        {
            "source_mdl_assets": [
                {
                    "package_path": "deps/mdl/root.mdl",
                    "resolved_path": str(source / "materials" / "root.mdl"),
                }
            ]
        }
    ]

    result = build_material_runtime_closure(package, material_closure=material_closure)

    assert result.return_code == 0
    assert (package / "deps" / "mdl" / "helpers" / "paint.mdl").exists()
    assert (package / "deps" / "textures" / "albedo.png").exists()
    assert result.material_runtime_closure["root_mdl_assets"] == [
        "deps/mdl/helpers/paint.mdl",
        "deps/mdl/root.mdl",
    ]
    action_ids = [
        action["action_id"] for action in result.material_runtime_closure["mirror_actions"]
    ]
    assert action_ids == [
        "aan11_mirror_helper_mdl",
        "aan11_mirror_mdl_texture",
    ]


def test_material_runtime_closure_resolves_approved_runtime_mdl_modules(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    runtime_root = tmp_path / "isaac_runtime" / "mdl"
    (package / "deps" / "mdl").mkdir(parents=True)
    (runtime_root / "OmniSurface").mkdir(parents=True)
    (runtime_root / "nvidia").mkdir(parents=True)
    (runtime_root / "OmniSurface" / "OmniImage.mdl").write_text(
        "mdl 1.0;\n",
        encoding="utf-8",
    )
    (runtime_root / "nvidia" / "core_definitions.mdl").write_text(
        "mdl 1.0;\n",
        encoding="utf-8",
    )
    (runtime_root / "debug.mdl").write_text("mdl 1.0;\n", encoding="utf-8")
    (package / "deps" / "mdl" / "root.mdl").write_text(
        "mdl 1.0;\n"
        "import .::OmniSurface::OmniImage::*;\n"
        "import debug::*;\n"
        "using nvidia::core_definitions::file_texture import file_texture;\n",
        encoding="utf-8",
    )

    result = build_material_runtime_closure(
        package,
        material_closure=[],
        runtime_mdl_roots=[runtime_root],
    )

    assert result.return_code == 0
    records = {
        record["module"]: record
        for record in result.material_runtime_closure["imported_mdl_modules"]
    }
    assert records["OmniSurface::OmniImage"]["resolution"] == "native_runtime_module"
    assert records["OmniSurface::OmniImage"]["classification"] == "approved_runtime_module"
    assert records["OmniSurface::OmniImage"]["runtime_path"].endswith(
        "OmniSurface/OmniImage.mdl"
    )
    assert records["nvidia::core_definitions::file_texture"]["resolution"] == (
        "native_runtime_module"
    )
    assert records["nvidia::core_definitions::file_texture"]["runtime_module"] == (
        "nvidia::core_definitions"
    )
    assert len(records["debug"]["runtime_sha256"]) == 64


def test_parse_material_runtime_log_counts_mdlc_and_shader_failures() -> None:
    text = (
        "[Error] [rtx.mdltranslator] MDLC: could not find module .::ad_3dsmax_materials\n"
        "[Error] Failed to create MDL shade node for /Looks/Paint/Shader\n"
        "[Warning] [omni.hydra] unrelated warning\n"
    )

    report = parse_material_runtime_log(text)

    assert report["status"] == "blocked"
    assert report["counters"]["error_count"] == 2
    assert report["counters"]["warning_count"] == 1
    assert report["counters"]["mdlc_count"] == 1
    assert report["counters"]["failed_shader_node_count"] == 1
    assert report["missing_modules"] == ["ad_3dsmax_materials"]
    assert report["exemplars"][0]["line_hash"]


def test_merge_runtime_compiler_report_blocks_required_material_errors() -> None:
    closure = {
        "status": "pass",
        "claim_level": "required_surface_runtime_dependency_closure",
        "full_material_parity_claimed": False,
        "root_mdl_assets": ["deps/mdl/paint.mdl"],
        "imported_mdl_modules": [],
        "mdl_texture_assets": [],
        "native_runtime_modules": [],
        "rewrite_actions": [],
        "runtime_compiler": {"status": "not_run"},
        "view_evidence": [],
    }
    compiler = {
        "status": "blocked",
        "counters": {"mdlc_count": 1, "failed_shader_node_count": 1},
        "missing_modules": ["ad_3dsmax_materials"],
        "exemplars": [{"line_hash": "abc", "message": "MDLC could not find module"}],
    }

    merged = merge_runtime_compiler_report(closure, compiler)

    assert merged["status"] == "blocked"
    assert merged["claim_level"] == "not_claimed"
    assert merged["runtime_compiler"] == compiler


def test_build_binding_scope_report_uses_static_material_hints_for_required_prims() -> None:
    material_closure = [
        {
            "material_prim": "/Looks/Paint",
            "binding_scope": "/World/DryingBox",
            "source_mdl_assets": [{"package_path": "deps/mdl/paint.mdl"}],
        }
    ]

    report = build_binding_scope_report(
        material_closure,
        required_prims=["/World/DryingBox"],
    )

    assert report["status"] == "static_hint"
    assert report["required_materials"] == [
        {
            "required_prim": "/World/DryingBox",
            "material_prim": "/Looks/Paint",
            "binding_source": "material_closure.binding_scope",
        }
    ]
    assert report["unknown_required_prims"] == []


def test_build_binding_scope_report_traces_effective_usdshade_binding(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    root_usd = package / "asset.usda"
    root_usd.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" (\n"
        "        prepend apiSchemas = [\"MaterialBindingAPI\"]\n"
        "    ) {\n"
        "        rel material:binding = </Looks/Paint>\n"
        "        def Mesh \"Body\" {\n"
        "            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]\n"
        "            int[] faceVertexCounts = [3]\n"
        "            int[] faceVertexIndices = [0, 1, 2]\n"
        "        }\n"
        "    }\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {}\n"
        "}\n",
        encoding="utf-8",
    )

    report = build_binding_scope_report(
        material_closure=[],
        required_prims=["/World/DryingBox/Body"],
        package_root=package,
        root_usd=root_usd,
    )

    assert report["status"] == "effective_binding"
    assert report["required_materials"] == [
        {
            "required_prim": "/World/DryingBox/Body",
            "material_prim": "/Looks/Paint",
            "binding_source": "UsdShade.MaterialBindingAPI.ComputeBoundMaterial",
            "binding_strength": "inherited_or_weaker",
            "bound_at_prim": "/World/DryingBox",
        }
    ]
    assert report["unknown_required_prims"] == []


def test_build_binding_scope_report_traces_required_root_render_mesh_binding(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    root_usd = package / "asset.usda"
    root_usd.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"DryingBox\" {\n"
        "        def Mesh \"Body\" (\n"
        "            prepend apiSchemas = [\"MaterialBindingAPI\"]\n"
        "        ) {\n"
        "            rel material:binding = </Looks/Paint>\n"
        "            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]\n"
        "            int[] faceVertexCounts = [3]\n"
        "            int[] faceVertexIndices = [0, 1, 2]\n"
        "        }\n"
        "    }\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {}\n"
        "}\n",
        encoding="utf-8",
    )

    report = build_binding_scope_report(
        material_closure=[],
        required_prims=["/World/DryingBox"],
        package_root=package,
        root_usd=root_usd,
    )

    assert report["status"] == "effective_binding"
    assert report["required_materials"] == [
        {
            "required_prim": "/World/DryingBox",
            "render_prim": "/World/DryingBox/Body",
            "material_prim": "/Looks/Paint",
            "binding_source": "UsdShade.MaterialBindingAPI.ComputeBoundMaterial",
            "binding_strength": "direct",
            "bound_at_prim": "/World/DryingBox/Body",
        }
    ]
    assert report["unknown_required_prims"] == []


def test_build_binding_scope_report_separates_non_render_required_prims(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    root_usd = package / "asset.usda"
    root_usd.write_text(
        "#usda 1.0\n"
        "(\n"
        "    defaultPrim = \"World\"\n"
        ")\n"
        "def Xform \"World\" {\n"
        "    def Xform \"Door\" {\n"
        "        def Mesh \"Body\" (\n"
        "            prepend apiSchemas = [\"MaterialBindingAPI\"]\n"
        "        ) {\n"
        "            rel material:binding = </Looks/Paint>\n"
        "            point3f[] points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]\n"
        "            int[] faceVertexCounts = [3]\n"
        "            int[] faceVertexIndices = [0, 1, 2]\n"
        "        }\n"
        "        def PhysicsRevoluteJoint \"DoorJoint\" {}\n"
        "    }\n"
        "}\n"
        "def Scope \"Looks\" {\n"
        "    def Material \"Paint\" {}\n"
        "}\n",
        encoding="utf-8",
    )

    report = build_binding_scope_report(
        material_closure=[],
        required_prims=["/World/Door", "/World/Door/DoorJoint"],
        package_root=package,
        root_usd=root_usd,
    )

    assert report["status"] == "effective_binding"
    assert report["unknown_required_prims"] == []
    assert report["non_render_required_prims"] == ["/World/Door/DoorJoint"]


def test_build_material_view_evidence_preserves_required_render_metrics() -> None:
    evidence = build_material_view_evidence(
        [
            {
                "view_id": "front",
                "camera_pose": {"position": [1, 0, 1], "look_at": [0, 0, 0]},
                "target_prim": "/World/DryingBox",
                "render_hash": "a" * 64,
                "mean_rgb": [0.2, 0.3, 0.4],
                "foreground_rgb": [0.25, 0.35, 0.45],
                "non_background_ratio": 0.42,
                "bbox_ratio": 0.3,
                "render_path": "evidence/runtime_smoke/material_views/front.png",
                "bbox_source": "authored",
            }
        ]
    )

    assert evidence == [
        {
            "view_id": "front",
            "camera_pose": {"position": [1, 0, 1], "look_at": [0, 0, 0]},
            "target_prim": "/World/DryingBox",
            "render_hash": "a" * 64,
            "mean_rgb": [0.2, 0.3, 0.4],
            "foreground_rgb": [0.25, 0.35, 0.45],
            "non_background_ratio": 0.42,
            "bbox_ratio": 0.3,
            "render_path": "evidence/runtime_smoke/material_views/front.png",
            "bbox_source": "authored",
        }
    ]
