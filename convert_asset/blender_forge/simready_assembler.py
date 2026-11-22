"""SimReady OpenUSD & v0.2 Deformable Assembler for Blender 4.4+ Forge outputs.

Combines Blender's high-detail Boolean/SubSurf/UV geometry with strict SimReady OpenUSD
contracts (ART-001 single-root Links/* + Joints/* + Visual/Collision separation +
named_frame("grasp")) and 4-engine deformable bundle/v0.2 compilation.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from convert_asset.deformable_parity.contracts import DeformableSourceSpec
from convert_asset.deformable_v05.contracts_v05 import FractureBudgetV02
from convert_asset.deformable_v05.morph_compiler import compile_deformable_bundle_v02

from .contracts import AssetForgeSpec, ForgeHygieneReport


def _compose_2x2_contact_sheet(
    view_paths: Mapping[str, str],
    out_sheet: Path,
    title: str,
    *,
    family: str = "articulated_cad",
    template: str = "",
) -> Path:
    if template == "amber_latex_cooling_hose":
        order = [
            ("preview_iso", "1. Hero 3/4 Iso S-Catenary Drape (AgX)"),
            ("preview_front", "2. Side Gravity Sag & Bench Clearance"),
            ("preview_detail", "3. Ribbed Nozzle Cuff & Matte Latex Sheen"),
            ("preview_ui", "4. Opposite 3/4 Smooth 96-Ring Curvature"),
        ]
    elif template == "magnetic_heating_water_bath":
        order = [
            ("preview_iso", "1. Hero 3/4 Iso Glass Bath & Stirrer (AgX)"),
            ("preview_front", "2. Front-Right 3/4 Dials & Hollow Dish"),
            ("preview_detail", "3. Double-Walled Borosilicate Bath & Stir Bar"),
            ("preview_ui", "4. Recessed 82.5°C LED & Knurled Rotary Dials"),
        ]
    elif family == "deformable_sculpted":
        order = [
            ("preview_iso", "1. Hero 3/4 Iso (Cycles AgX)"),
            ("preview_front", "2. Side Profile & Flat Baked Base"),
            ("preview_detail", "3. Laminated Flaky Crust Macro"),
            ("preview_ui", "4. Opposite 3/4 & Crescent Horn Curl"),
        ]
    else:
        order = [
            ("preview_iso", "1. Hero 3/4 Iso (Closed Rest Pose)"),
            ("preview_front", "2. Front-Right 3/4 (Hinges, Handle & UI)"),
            ("preview_detail", "3. Articulated Open-Door (-58°) & Tray Out"),
            ("preview_ui", "4. OLED 37.0°C, Tactile Keys & Knurled Dial"),
        ]
    tiles: list[tuple[str, Image.Image]] = []
    for key, label in order:
        p = Path(view_paths[key])
        im = Image.open(p).convert("RGB")
        tiles.append((label, im))

    tw, th = tiles[0][1].size
    header_h = 46
    sheet = Image.new("RGB", (tw * 2, th * 2 + header_h), (15, 23, 42))
    draw = ImageDraw.Draw(sheet)
    try:
        font_hdr = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 20)
        font_lbl = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 15)
    except Exception:
        font_hdr = ImageFont.load_default()
        font_lbl = ImageFont.load_default()

    draw.text((16, 10), title, fill=(248, 250, 252), font=font_hdr)
    for idx, (label, im) in enumerate(tiles):
        r, c = idx // 2, idx % 2
        x0, y0 = c * tw, header_h + r * th
        sheet.paste(im, (x0, y0))
        draw.rectangle((x0 + 8, y0 + 8, x0 + 340, y0 + 34), fill=(15, 23, 42))
        draw.text((x0 + 14, y0 + 11), label, fill=(125, 211, 252), font=font_lbl)
        draw.rectangle((x0, y0, x0 + tw - 1, y0 + th - 1), outline=(51, 65, 85), width=2)

    out_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_sheet, format="PNG")
    return out_sheet


def _format_usd_mesh_prim(prim_name: str, npz_path: Path, *, is_collision: bool) -> str:
    with np.load(npz_path, allow_pickle=False) as z:
        verts = np.asarray(z["vertices"], dtype=np.float64)
        faces = np.asarray(z["faces"], dtype=np.int32)
    pts_str = ", ".join(f"({v[0]:.6f}, {v[1]:.6f}, {v[2]:.6f})" for v in verts)
    cnt_str = ", ".join("3" for _ in range(len(faces)))
    idx_str = ", ".join(str(int(i)) for f in faces for i in f)
    api = 'prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsMeshCollisionAPI"]' if is_collision else ""
    purpose = 'uniform token purpose = "guide"' if is_collision else 'uniform token purpose = "render"'
    approx = 'uniform token physics:approximation = "convexDecomposition"' if is_collision else ""
    return f"""
            def Mesh "{prim_name}" ({api})
            {{
                {purpose}
                {approx}
                int[] faceVertexCounts = [{cnt_str}]
                int[] faceVertexIndices = [{idx_str}]
                point3f[] points = [{pts_str}]
            }}"""


def _write_simready_articulated_usda(
    spec: AssetForgeSpec,
    build_info: Mapping[str, Any],
    parts_dir: Path,
    out_usda: Path,
) -> Path:
    """Emit strict ART-001 single-root fixed-base SimReady OpenUSD with Links/*, Joints/*, & grasp frames."""
    root_name = spec.asset_id
    links_blocks: list[str] = []
    joints_blocks: list[str] = [
        f"""
        def PhysicsFixedJoint "RootFixedJoint" (
            prepend apiSchemas = ["PhysicsArticulationRootAPI"]
        )
        {{
            rel physics:body1 = </{root_name}/Links/Base>
        }}"""
    ]

    for lk in build_info["links"]:
        lname = str(lk["link_name"])
        vis_npz = parts_dir / lk["visual"]["npz_relpath"]
        col_npz = parts_dir / lk["collision"]["npz_relpath"]
        vis_mesh = _format_usd_mesh_prim(f"{lname}VisualMesh", vis_npz, is_collision=False)
        col_mesh = _format_usd_mesh_prim(f"{lname}CollisionMesh", col_npz, is_collision=True)

        grasp_block = ""
        jmeta = lk.get("joint")
        if jmeta and "grasp_frame_xyz" in jmeta:
            gx, gy, gz = jmeta["grasp_frame_xyz"]
            grasp_block = f"""
            def Xform "grasp"
            {{
                custom string scenarioForge:namedFrame = "grasp"
                double3 xformOp:translate = ({gx:.6f}, {gy:.6f}, {gz:.6f})
                uniform token[] xformOpOrder = ["xformOp:translate"]
            }}"""

        links_blocks.append(
            f"""
        def Xform "{lname}" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsMassAPI"]
        )
        {{
            float physics:mass = {spec.mass_kg * (0.72 if lname == "Base" else 0.093):.4f}
            def Scope "Visual"
            {{{vis_mesh}
            }}
            def Scope "Collision"
            {{{col_mesh}
            }}{grasp_block}
        }}"""
        )

        if jmeta:
            jname = str(jmeta["joint_name"])
            jtype = str(jmeta["joint_type"])
            parent = str(jmeta["parent"])
            axis = str(jmeta["axis"])
            px, py, pz = jmeta["pivot_xyz"]
            damping = float(jmeta["damping"])
            if jtype == "revolute":
                lo, hi = jmeta["limits_deg"]
                joints_blocks.append(
                    f"""
        def PhysicsRevoluteJoint "{jname}" (
            prepend apiSchemas = ["PhysicsDriveAPI:angular"]
        )
        {{
            uniform token physics:axis = "{axis}"
            rel physics:body0 = </{root_name}/Links/{parent}>
            rel physics:body1 = </{root_name}/Links/{lname}>
            point3f physics:localPos0 = ({px:.6f}, {py:.6f}, {pz:.6f})
            point3f physics:localPos1 = ({px:.6f}, {py:.6f}, {pz:.6f})
            float physics:lowerLimit = {lo:.3f}
            float physics:upperLimit = {hi:.3f}
            float drive:angular:physics:damping = {damping:.4f}
            float drive:angular:physics:stiffness = 0.0
        }}"""
                )
            elif jtype == "prismatic":
                lo, hi = jmeta["limits_m"]
                joints_blocks.append(
                    f"""
        def PhysicsPrismaticJoint "{jname}" (
            prepend apiSchemas = ["PhysicsDriveAPI:linear"]
        )
        {{
            uniform token physics:axis = "{axis}"
            rel physics:body0 = </{root_name}/Links/{parent}>
            rel physics:body1 = </{root_name}/Links/{lname}>
            point3f physics:localPos0 = ({px:.6f}, {py:.6f}, {pz:.6f})
            point3f physics:localPos1 = ({px:.6f}, {py:.6f}, {pz:.6f})
            float physics:lowerLimit = {lo:.4f}
            float physics:upperLimit = {hi:.4f}
            float drive:linear:physics:damping = {damping:.4f}
            float drive:linear:physics:stiffness = 0.0
        }}"""
                )

    usda = f"""#usda 1.0
(
    defaultPrim = "{root_name}"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "{root_name}" (
    kind = "component"
)
{{
    custom string blenderForge:schemaVersion = "blender-simready-forge/v1.0"
    custom string blenderForge:family = "{spec.family}"
    def Scope "Links"
    {{{''.join(links_blocks)}
    }}
    def Scope "Joints"
    {{{''.join(joints_blocks)}
    }}
}}
"""
    out_usda.parent.mkdir(parents=True, exist_ok=True)
    out_usda.write_text(usda, encoding="utf-8")
    return out_usda


def assemble_forged_asset(
    spec: AssetForgeSpec,
    worker_receipt: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    """Assemble Blender 4.4+ worker outputs into SimReady OpenUSD / bundle/v0.2 + Hygiene Report."""
    build_info = worker_receipt["build_info"]
    studio_info = worker_receipt["studio_info"]
    parts_dir = out_dir / "blender_parts"

    # 1. Compose 2x2 Cycles AgX Studio Contact Sheet
    sheet_path = _compose_2x2_contact_sheet(
        studio_info["view_paths"],
        out_dir / "studio_agx" / "studio_4view_contact_sheet.png",
        title=f"Blender {worker_receipt['blender_version']} Cycles AgX 4-View Studio Sheet | {spec.asset_id}",
        family=spec.family,
        template=spec.template,
    )

    # 2. Emit SimReady OpenUSD or 4-Engine Deformable bundle/v0.2
    deliverables: dict[str, Any] = {"studio_contact_sheet": sheet_path.as_posix()}
    if spec.family == "articulated_cad":
        usd_path = _write_simready_articulated_usda(
            spec, build_info, parts_dir, out_dir / f"{spec.asset_id}_simready.usda"
        )
        deliverables["simready_usda"] = usd_path.as_posix()
        deliverables["simready_usda_sha256"] = sha256(usd_path.read_bytes()).hexdigest()
    elif spec.family == "deformable_sculpted":
        dp = dict(spec.deformable_params)
        sx, sy, sz = spec.dimensions_xyz_m
        vol = max(sx * sy * sz, 1e-9)
        vis_npz = parts_dir / build_info["visual"]["npz_relpath"]
        proxy_npz = parts_dir / build_info["physics_proxy"]["npz_relpath"]
        d_spec = DeformableSourceSpec(
            asset_id=spec.asset_id,
            category=str(dp.get("category", "sculpted_deformable")),
            structural_family=str(dp.get("structural_family", "soft_solid")),
            dimensions_xyz_m=spec.dimensions_xyz_m,
            mass_kg=spec.mass_kg,
            density_kg_m3=spec.mass_kg / vol,
            youngs_modulus_pa=float(dp.get("youngs_modulus_pa", 18000.0)),
            poissons_ratio=float(dp.get("poissons_ratio", 0.30)),
            visual_mesh_relpath=vis_npz.as_posix(),
            proxy_mesh_relpath=proxy_npz.as_posix(),
            fragility_tier=str(dp.get("fragility_tier", "high")),
            source_dataset="blender_44_forge",
            source_asset_sha256=sha256(vis_npz.read_bytes()).hexdigest(),
        )
        budget = FractureBudgetV02(
            fragility_tier=d_spec.fragility_tier,
            max_normal_force_n=float(dp.get("max_normal_force_n", 4.5)),
            max_shear_force_n=float(dp.get("max_shear_force_n", 2.0)),
        )
        bundle, manifest_path = compile_deformable_bundle_v02(
            d_spec,
            out_dir / "bundle_v02",
            budget=budget,
            include_morphtwin_sidecar=True,
        )
        deliverables["deformable_bundle_v02_manifest"] = manifest_path.as_posix()
        deliverables["deformable_bundle_v02_engines"] = sorted(bundle.engines.keys())

    # 3. Evaluate Automated Geometry / Physics / Visual Hygiene Gate
    vh = build_info["visual_hygiene"]
    ch = build_info["collision_hygiene"]
    meas = tuple(float(v) for v in vh["dimensions_xyz_m"])
    dim_errs = [abs(meas[k] - spec.dimensions_xyz_m[k]) for k in range(3)]
    max_dim_err = float(max(dim_errs))
    dim_ok = max_dim_err <= spec.dimension_tolerance_m
    manifold_ok = int(vh["non_manifold_edges"]) == 0
    uv_ok = bool(vh["uv_present"])
    vis_col_sep = int(vh["triangles"]) > 0 and int(ch["triangles"]) > 0 and int(ch["triangles"]) <= int(vh["triangles"])

    vstats = studio_info["view_stats"]
    studio_ok = all(
        0.04 <= float(st["mean_luma"]) <= 0.92 and float(st["std_luma"]) >= 0.03
        for st in vstats.values()
    )
    notes: list[str] = []
    if not dim_ok:
        notes.append(f"Dimension error {max_dim_err*1000:.2f} mm exceeds tolerance {spec.dimension_tolerance_m*1000:.2f} mm")
    if not manifold_ok:
        notes.append(f"Non-manifold edges detected: {vh['non_manifold_edges']}")
    if not uv_ok:
        notes.append("Missing UV layer on one or more visual meshes")
    if not vis_col_sep:
        notes.append("Visual and collision/proxy meshes not properly separated or proxy not decimated")
    if not studio_ok:
        notes.append("One or more Cycles AgX studio views failed exposure/contrast check")

    hygiene = ForgeHygieneReport(
        asset_id=spec.asset_id,
        family=spec.family,
        blender_version=str(worker_receipt["blender_version"]),
        measured_dimensions_xyz_m=(meas[0], meas[1], meas[2]),
        max_dimension_error_m=round(max_dim_err, 6),
        dimension_gate_passed=dim_ok,
        non_manifold_edge_count=int(vh["non_manifold_edges"]),
        manifold_gate_passed=manifold_ok,
        uv_present=uv_ok,
        visual_collision_separated=vis_col_sep,
        total_visual_triangles=int(vh["triangles"]),
        total_collision_or_proxy_triangles=int(ch["triangles"]),
        studio_views_ok=studio_ok,
        studio_view_stats=vstats,
        overall_passed=bool(dim_ok and manifold_ok and uv_ok and vis_col_sep and studio_ok),
        notes=notes,
    )

    articulation_contract: dict[str, Any] | None = None
    if spec.family == "articulated_cad":
        articulation_contract = {
            "root_joint": "Joints/RootFixedJoint (PhysicsArticulationRootAPI -> Links/Base)",
            "links": [
                {
                    "link_name": lk["link_name"],
                    "visual_triangles": lk["visual"]["triangle_count"],
                    "collision_triangles": lk["collision"]["triangle_count"],
                    "joint": lk.get("joint"),
                }
                for lk in build_info["links"]
            ],
            "open_pose_verified_in_panel3": bool(build_info.get("open_pose_demo")),
        }

    handoff = {
        "schema_version": "blender-forge-critic-handoff/v1.0",
        "asset_id": spec.asset_id,
        "family": spec.family,
        "frozen_spec": spec.to_dict(),
        "articulation_contract": articulation_contract,
        "hygiene_report": hygiene.to_dict(),
        "deliverables": deliverables,
        "studio_views": studio_info["view_paths"],
        "blend_source": studio_info["blend_path"],
    }
    handoff_path = out_dir / "forge_manifest_and_critic_handoff.json"
    handoff_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    return handoff

