"""Headless Blender 4.4+ worker: high-craft Boolean/Bevel/SubSurf/Sculpt modeling, PBR, & Cycles AgX studio QA.

Invoke strictly with Blender >= 4.4.0:
  blender --background --factory-startup --python bpy_worker.py -- --spec spec.json --out-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

import bpy  # type: ignore
import bmesh  # type: ignore
from mathutils import Euler, Matrix, Vector  # type: ignore


def _assert_blender_44() -> None:
    if tuple(bpy.app.version[:2]) < (4, 4):
        raise RuntimeError(f"Blender >= 4.4.0 required, got {bpy.app.version_string}")


def _reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0


def _ensure_collection(name: str, parent: Any | None = None) -> Any:
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def _link_only_to(obj: Any, col: Any) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def _apply_all_modifiers(obj: Any) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)


def _apply_transforms(obj: Any) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.select_set(False)


def _make_pbr_material(
    name: str,
    *,
    base_color: tuple[float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.4,
    coat_weight: float = 0.0,
    transmission_weight: float = 0.0,
    emission_color: tuple[float, float, float] | None = None,
    emission_strength: float = 0.0,
    noise_bump_scale: float = 0.0,
    noise_bump_strength: float = 0.0,
    color_variation: tuple[float, float, float] | None = None,
) -> Any:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (520, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = float(metallic)
    bsdf.inputs["Roughness"].default_value = float(roughness)
    bsdf.inputs["Coat Weight"].default_value = float(coat_weight)
    bsdf.inputs["Transmission Weight"].default_value = float(transmission_weight)
    if emission_color is not None and emission_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = float(emission_strength)

    if noise_bump_scale > 0.0:
        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-560, -120)
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.location = (-340, -120)
        noise.inputs["Scale"].default_value = float(noise_bump_scale)
        noise.inputs["Detail"].default_value = 6.0
        noise.inputs["Roughness"].default_value = 0.58
        nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

        if noise_bump_strength > 0.0:
            bump = nt.nodes.new("ShaderNodeBump")
            bump.location = (-60, -220)
            bump.inputs["Strength"].default_value = float(noise_bump_strength)
            bump.inputs["Distance"].default_value = 0.0025
            nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

        if color_variation is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.location = (-60, 80)
            mix.inputs["A"].default_value = (*base_color, 1.0)
            mix.inputs["B"].default_value = (*color_variation, 1.0)
            nt.links.new(noise.outputs["Fac"], mix.inputs["Factor"])
            nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])

    return mat


def _create_box(
    name: str,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    col: Any,
    mat: Any | None = None,
    bevel_width: float = 0.0,
    bevel_segments: int = 3,
) -> Any:
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    if bevel_width > 0.0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = float(bevel_width)
        mod.segments = int(bevel_segments)
        mod.limit_method = "ANGLE"
        _apply_all_modifiers(obj)
    return obj


def _boolean_diff(target: Any, cutter: Any) -> None:
    mod = target.modifiers.new("BoolDiff", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    _apply_all_modifiers(target)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _auto_uv_and_smooth(obj: Any, *, auto_smooth: bool = True) -> None:
    if obj.type != "MESH" or len(obj.data.polygons) == 0:
        return
    if auto_smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def _measure_collection_hygiene(col: Any) -> dict[str, Any]:
    """Compute exact world AABB, manifold edge count, UV presence, and triangle count."""
    min_v = Vector((1e9, 1e9, 1e9))
    max_v = Vector((-1e9, -1e9, -1e9))
    non_manifold = 0
    total_tris = 0
    uv_all = True
    obj_count = 0

    for obj in col.objects:
        if obj.type != "MESH":
            continue
        obj_count += 1
        mesh = obj.data
        if len(mesh.uv_layers) == 0:
            uv_all = False
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.transform(obj.matrix_world)
        for v in bm.verts:
            for k in range(3):
                if v.co[k] < min_v[k]:
                    min_v[k] = v.co[k]
                if v.co[k] > max_v[k]:
                    max_v[k] = v.co[k]
        for e in bm.edges:
            if not e.is_manifold:
                non_manifold += 1
        bmesh.ops.triangulate(bm, faces=bm.faces)
        total_tris += len(bm.faces)
        bm.free()

    if obj_count == 0:
        return {
            "bbox_min": [0.0, 0.0, 0.0],
            "bbox_max": [0.0, 0.0, 0.0],
            "dimensions_xyz_m": [0.0, 0.0, 0.0],
            "non_manifold_edges": 0,
            "uv_present": False,
            "triangles": 0,
        }
    dims = max_v - min_v
    return {
        "bbox_min": [round(float(min_v[k]), 6) for k in range(3)],
        "bbox_max": [round(float(max_v[k]), 6) for k in range(3)],
        "dimensions_xyz_m": [round(float(dims[k]), 6) for k in range(3)],
        "non_manifold_edges": int(non_manifold),
        "uv_present": bool(uv_all),
        "triangles": int(total_tris),
    }


def _export_collection_mesh_npz(col: Any, out_npz: Path) -> dict[str, Any]:
    """Export combined world-space triangulated mesh + UV + per-face material info as portable NPZ."""
    import numpy as np  # bundled inside Blender 4.4 Python

    verts_all: list[np.ndarray] = []
    faces_all: list[np.ndarray] = []
    uvs_all: list[np.ndarray] = []
    mat_ids_all: list[np.ndarray] = []
    materials_meta: list[dict[str, Any]] = []
    mat_name_to_idx: dict[str, int] = {}
    v_offset = 0

    for obj in sorted(col.objects, key=lambda o: o.name):
        if obj.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.active

        # Map object material slots into global palette
        local_to_global: dict[int, int] = {}
        for slot_i, slot in enumerate(obj.material_slots):
            mat = slot.material
            mname = mat.name if mat else "DefaultMat"
            if mname not in mat_name_to_idx:
                base_c = [0.7, 0.7, 0.7]
                metallic = 0.0
                roughness = 0.45
                emissive = [0.0, 0.0, 0.0]
                opacity = 1.0
                if mat and mat.use_nodes:
                    for nd in mat.node_tree.nodes:
                        if nd.type == "BSDF_PRINCIPLED":
                            bc = nd.inputs["Base Color"].default_value
                            base_c = [float(bc[0]), float(bc[1]), float(bc[2])]
                            metallic = float(nd.inputs["Metallic"].default_value)
                            roughness = float(nd.inputs["Roughness"].default_value)
                            es = float(nd.inputs["Emission Strength"].default_value)
                            if es > 0.0:
                                ec = nd.inputs["Emission Color"].default_value
                                emissive = [float(ec[0] * es), float(ec[1] * es), float(ec[2] * es)]
                            tw = float(nd.inputs["Transmission Weight"].default_value)
                            if tw > 0.2:
                                opacity = max(0.25, 1.0 - 0.72 * tw)
                            break
                mat_name_to_idx[mname] = len(materials_meta)
                materials_meta.append(
                    {
                        "name": mname,
                        "base_color": base_c,
                        "metallic": metallic,
                        "roughness": roughness,
                        "emissive": emissive,
                        "opacity": opacity,
                    }
                )
            local_to_global[slot_i] = mat_name_to_idx[mname]

        verts = np.array([[v.co.x, v.co.y, v.co.z] for v in bm.verts], dtype=np.float32)
        faces = []
        mat_ids = []
        v_uv = np.zeros((len(bm.verts), 2), dtype=np.float32)
        for f in bm.faces:
            idx3 = [v.index + v_offset for v in f.verts]
            faces.append(idx3)
            mat_ids.append(local_to_global.get(f.material_index, 0))
            if uv_layer is not None:
                for lp in f.loops:
                    uv = lp[uv_layer].uv
                    v_uv[lp.vert.index] = [float(uv.x), float(uv.y)]

        verts_all.append(verts)
        faces_all.append(np.array(faces, dtype=np.int32))
        uvs_all.append(v_uv)
        mat_ids_all.append(np.array(mat_ids, dtype=np.int32))
        v_offset += len(verts)
        bm.free()

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    if verts_all:
        v_cat = np.concatenate(verts_all, axis=0)
        f_cat = np.concatenate(faces_all, axis=0)
        uv_cat = np.concatenate(uvs_all, axis=0)
        m_cat = np.concatenate(mat_ids_all, axis=0)
    else:
        v_cat = np.zeros((0, 3), dtype=np.float32)
        f_cat = np.zeros((0, 3), dtype=np.int32)
        uv_cat = np.zeros((0, 2), dtype=np.float32)
        m_cat = np.zeros((0,), dtype=np.int32)

    np.savez_compressed(
        out_npz,
        vertices=v_cat,
        faces=f_cat,
        uvs=uv_cat,
        face_material_ids=m_cat,
    )
    return {
        "npz_relpath": out_npz.name,
        "vertex_count": int(len(v_cat)),
        "triangle_count": int(len(f_cat)),
        "materials": materials_meta,
    }


def _build_precision_benchtop_incubator(spec: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Pilot A: Precision benchtop lab incubator/oven with Boolean cavity, bevels, hinged door, knurled dial, tray."""
    sx, sy, sz = (float(spec["dimensions_xyz_m"][0]), float(spec["dimensions_xyz_m"][1]), float(spec["dimensions_xyz_m"][2]))
    # Convention: X width, Y depth (-Y is front face), Z height [0, sz]
    foot_h = 0.014
    body_h = sz - foot_h
    body_cz = foot_h + 0.5 * body_h
    wall_t = 0.024
    panel_w = 0.088  # right-hand control panel strip

    # Materials (Blender 4.4 Principled BSDF)
    mat_chassis = _make_pbr_material(
        "ChassisPowderCoat",
        base_color=(0.86, 0.88, 0.90),
        metallic=0.08,
        roughness=0.34,
        coat_weight=0.15,
        noise_bump_scale=180.0,
        noise_bump_strength=0.04,
    )
    mat_steel = _make_pbr_material(
        "BrushedStainless",
        base_color=(0.74, 0.77, 0.80),
        metallic=0.92,
        roughness=0.24,
        noise_bump_scale=320.0,
        noise_bump_strength=0.03,
    )
    mat_dark_bezel = _make_pbr_material(
        "AnodizedBezel",
        base_color=(0.06, 0.08, 0.11),
        metallic=0.35,
        roughness=0.28,
        coat_weight=0.25,
    )
    mat_accent_blue = _make_pbr_material(
        "LabAccentBlue",
        base_color=(0.08, 0.34, 0.72),
        metallic=0.25,
        roughness=0.22,
        coat_weight=0.35,
    )
    mat_rubber = _make_pbr_material(
        "RubberFoot",
        base_color=(0.04, 0.04, 0.05),
        metallic=0.0,
        roughness=0.78,
    )
    mat_glass = _make_pbr_material(
        "TemperedGlass",
        base_color=(0.78, 0.90, 0.94),
        metallic=0.0,
        roughness=0.05,
        transmission_weight=0.82,
        coat_weight=0.4,
    )
    mat_oled = _make_pbr_material(
        "OledCyanDisplay",
        base_color=(0.01, 0.05, 0.08),
        roughness=0.10,
        coat_weight=0.35,
        emission_color=(0.04, 0.25, 0.34),
        emission_strength=0.45,
    )
    mat_led_green = _make_pbr_material(
        "StatusLedGreen",
        base_color=(0.05, 0.25, 0.10),
        roughness=0.15,
        emission_color=(0.12, 0.95, 0.42),
        emission_strength=4.0,
    )

    col_base_vis = _ensure_collection("Link_Base_Visual")
    col_base_col = _ensure_collection("Link_Base_Collision")
    col_door_vis = _ensure_collection("Link_Door_Visual")
    col_door_col = _ensure_collection("Link_Door_Collision")
    col_dial_vis = _ensure_collection("Link_Dial_Visual")
    col_dial_col = _ensure_collection("Link_Dial_Collision")
    col_tray_vis = _ensure_collection("Link_Tray_Visual")
    col_tray_col = _ensure_collection("Link_Tray_Collision")

    # Reserve front door + real 18mm standoff U-handle envelope within exact frozen sy
    handle_clearance = 0.018
    handle_bar_t = 0.008
    door_t = 0.018
    front_allowance = door_t + handle_clearance + handle_bar_t
    chassis_y = sy - front_allowance
    chassis_cy = 0.5 * front_allowance  # chassis back sits cleanly at +sy/2

    # Crystal-clear architectural tempered glass shader (Transparent + Fresnel Glossy, zero foggy blur)
    mat_glass = bpy.data.materials.new(name="ClearTemperedGlass")
    mat_glass.use_nodes = True
    g_nt = mat_glass.node_tree
    g_nt.nodes.clear()
    g_out = g_nt.nodes.new("ShaderNodeOutputMaterial")
    g_mix = g_nt.nodes.new("ShaderNodeMixShader")
    g_trans = g_nt.nodes.new("ShaderNodeBsdfTransparent")
    g_trans.inputs["Color"].default_value = (0.94, 0.98, 0.99, 1.0)
    g_gloss = g_nt.nodes.new("ShaderNodeBsdfGlossy")
    g_gloss.inputs["Color"].default_value = (0.95, 0.98, 1.0, 1.0)
    g_gloss.inputs["Roughness"].default_value = 0.03
    g_fres = g_nt.nodes.new("ShaderNodeLayerWeight")
    g_fres.inputs["Blend"].default_value = 0.14
    g_nt.links.new(g_fres.outputs["Facing"], g_mix.inputs["Fac"])
    g_nt.links.new(g_trans.outputs["BSDF"], g_mix.inputs[1])
    g_nt.links.new(g_gloss.outputs["BSDF"], g_mix.inputs[2])
    g_nt.links.new(g_mix.outputs["Shader"], g_out.inputs["Surface"])

    # --- 1. Base Housing with REAL Boolean Chamber Cutout ---
    housing = _create_box(
        "HousingShell",
        center=(0.0, chassis_cy, body_cz),
        size=(sx, chassis_y, body_h),
        col=col_base_vis,
        mat=mat_chassis,
        bevel_width=0.008,
        bevel_segments=4,
    )
    # Chamber sits on the left side (leaving panel_w on +X for control panel)
    cav_w = sx - panel_w - 2.0 * wall_t
    cav_d = chassis_y - wall_t + 0.006  # breaks cleanly through front face
    cav_h = body_h - 2.0 * wall_t
    cav_cx = -0.5 * sx + wall_t + 0.5 * cav_w
    cav_cy = chassis_cy - 0.5 * wall_t - 0.003
    cav_cz = body_cz
    cutter = _create_box("CavityCutter", (cav_cx, cav_cy, cav_cz), (cav_w, cav_d, cav_h), col_base_vis)
    _boolean_diff(housing, cutter)
    _auto_uv_and_smooth(housing, auto_smooth=False)

    # Stainless interior liner trim & bottom shelf rails inside cavity
    for side_s in (-1.0, 1.0):
        rail = _create_box(
            f"ShelfRail_{'L' if side_s < 0 else 'R'}",
            center=(cav_cx + side_s * (0.5 * cav_w - 0.004), chassis_cy, cav_cz - 0.02),
            size=(0.008, chassis_y - wall_t - 0.016, 0.007),
            col=col_base_vis,
            mat=mat_steel,
            bevel_width=0.001,
            bevel_segments=2,
        )
        _auto_uv_and_smooth(rail, auto_smooth=False)

    # Four chamfered rubber feet spanning [0, foot_h]
    for fx in (-0.5 * sx + 0.032, 0.5 * sx - 0.032):
        for fy in (chassis_cy - 0.5 * chassis_y + 0.032, chassis_cy + 0.5 * chassis_y - 0.032):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=24,
                radius=0.016,
                depth=foot_h,
                location=(fx, fy, 0.5 * foot_h),
            )
            foot = bpy.context.active_object
            foot.name = f"RubberFoot_{fx:+.2f}_{fy:+.2f}"
            _link_only_to(foot, col_base_vis)
            foot.data.materials.append(mat_rubber)
            _auto_uv_and_smooth(foot)

    # Right-side recessed control bezel, OLED display, tactile buttons, and status LED
    front_y = chassis_cy - 0.5 * chassis_y
    ctrl_cx = 0.5 * sx - 0.5 * panel_w
    bezel = _create_box(
        "ControlBezel",
        center=(ctrl_cx, front_y - 0.002, body_cz),
        size=(panel_w - 0.014, 0.006, body_h - 0.028),
        col=col_base_vis,
        mat=mat_dark_bezel,
        bevel_width=0.002,
        bevel_segments=2,
    )
    _auto_uv_and_smooth(bezel, auto_smooth=False)

    oled = _create_box(
        "OledScreen",
        center=(ctrl_cx, front_y - 0.0055, body_cz + 0.068),
        size=(panel_w - 0.028, 0.002, 0.044),
        col=col_base_vis,
        mat=mat_oled,
    )
    _auto_uv_and_smooth(oled, auto_smooth=False)

    # Blue brand stripe + 3 tactile buttons + green power LED
    stripe = _create_box(
        "BrandStripe",
        center=(ctrl_cx, front_y - 0.0053, body_cz + 0.105),
        size=(panel_w - 0.022, 0.002, 0.008),
        col=col_base_vis,
        mat=mat_accent_blue,
    )
    _auto_uv_and_smooth(stripe, auto_smooth=False)

    for b_i, bx_off in enumerate((-0.020, 0.0, 0.020)):
        btn = _create_box(
            f"TactileBtn_{b_i}",
            center=(ctrl_cx + bx_off, front_y - 0.006, body_cz + 0.020),
            size=(0.013, 0.005, 0.010),
            col=col_base_vis,
            mat=mat_steel if b_i != 1 else mat_accent_blue,
            bevel_width=0.001,
            bevel_segments=2,
        )
        _auto_uv_and_smooth(btn, auto_smooth=False)

    # Crisp vector key icons on tactile buttons (- / SET / +)
    mat_icon = _make_pbr_material("KeySilkScreenWhite", base_color=(0.94, 0.96, 0.98), roughness=0.35)
    # Left button: minus bar
    m_bar = _create_box("IconMinus", (ctrl_cx - 0.020, front_y - 0.0088, body_cz + 0.020), (0.0065, 0.001, 0.0016), col_base_vis, mat_icon)
    _auto_uv_and_smooth(m_bar, auto_smooth=False)
    # Center button: small square SET icon
    s_bar = _create_box("IconSet", (ctrl_cx, front_y - 0.0088, body_cz + 0.020), (0.0045, 0.001, 0.0045), col_base_vis, mat_icon)
    _auto_uv_and_smooth(s_bar, auto_smooth=False)
    # Right button: plus cross
    p_h = _create_box("IconPlusH", (ctrl_cx + 0.020, front_y - 0.0088, body_cz + 0.020), (0.0065, 0.001, 0.0016), col_base_vis, mat_icon)
    p_v = _create_box("IconPlusV", (ctrl_cx + 0.020, front_y - 0.0088, body_cz + 0.020), (0.0016, 0.001, 0.0065), col_base_vis, mat_icon)
    _auto_uv_and_smooth(p_h, auto_smooth=False)
    _auto_uv_and_smooth(p_v, auto_smooth=False)

    # Status LED positioned cleanly inside bezel (not cropped at frame edge)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.0038,
        depth=0.004,
        rotation=(math.radians(90.0), 0.0, 0.0),
        location=(ctrl_cx + 0.022, front_y - 0.0055, body_cz - 0.072),
    )
    led = bpy.context.active_object
    led.name = "PowerLed"
    _link_only_to(led, col_base_vis)
    led.data.materials.append(mat_led_green)
    _auto_uv_and_smooth(led)

    # Two real cylindrical stainless hinge knuckles on left side of front door edge
    hinge_x = cav_cx - 0.5 * (cav_w + 0.028) - 0.004
    for h_i, hz_off in enumerate((-0.055, 0.055)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=20,
            radius=0.0055,
            depth=0.024,
            location=(hinge_x, front_y - 0.005, cav_cz + hz_off),
        )
        h_pin = bpy.context.active_object
        h_pin.name = f"DoorHingeKnuckle_{h_i}"
        _link_only_to(h_pin, col_base_vis)
        h_pin.data.materials.append(mat_steel)
        _auto_uv_and_smooth(h_pin)

    # Side ventilation louvers on +X side wall (flush within +/- 0.5*sx)
    for v_i in range(6):
        vz = body_cz - 0.055 + v_i * 0.016
        louver = _create_box(
            f"VentSlot_{v_i}",
            center=(0.5 * sx - 0.0022, chassis_cy + 0.01, vz),
            size=(0.0044, 0.11, 0.005),
            col=col_base_vis,
            mat=mat_dark_bezel,
        )
        _auto_uv_and_smooth(louver, auto_smooth=False)

    # Crisp 7-segment temperature readout ("37.0") on OLED face
    seg_w, seg_h, seg_t = 0.0085, 0.0018, 0.0012
    oled_y = front_y - 0.0067
    oled_z = body_cz + 0.068
    mat_seg = _make_pbr_material(
        "OledDigitBright",
        base_color=(0.85, 0.99, 1.0),
        roughness=0.1,
        emission_color=(0.75, 0.98, 1.0),
        emission_strength=6.5,
    )
    digit_patterns = {
        "3": ("a", "b", "c", "d", "g"),
        "7": ("a", "b", "c"),
        "0": ("a", "b", "c", "d", "e", "f"),
    }
    seg_offsets = {
        "a": (0.0, 0.0095, seg_w, seg_h),
        "g": (0.0, 0.0, seg_w, seg_h),
        "d": (0.0, -0.0095, seg_w, seg_h),
        "b": (0.0045, 0.0048, seg_h, 0.0092),
        "c": (0.0045, -0.0048, seg_h, 0.0092),
        "f": (-0.0045, 0.0048, seg_h, 0.0092),
        "e": (-0.0045, -0.0048, seg_h, 0.0092),
    }
    for d_i, (ch_dig, dx_off) in enumerate((("3", -0.016), ("7", -0.002), ("0", 0.014))):
        for s_key in digit_patterns[ch_dig]:
            ox, oz, sw, sh = seg_offsets[s_key]
            sg = _create_box(
                f"OledSeg_{d_i}_{s_key}",
                center=(ctrl_cx + dx_off + ox, oled_y, oled_z + oz),
                size=(sw, seg_t, sh),
                col=col_base_vis,
                mat=mat_seg,
            )
            _auto_uv_and_smooth(sg, auto_smooth=False)
    dot = _create_box(
        "OledDot",
        center=(ctrl_cx + 0.006, oled_y, oled_z - 0.009),
        size=(0.0022, seg_t, 0.0022),
        col=col_base_vis,
        mat=mat_seg,
    )
    _auto_uv_and_smooth(dot, auto_smooth=False)
    # Degree circle + crisp "C" unit on right side of OLED
    deg_ring = _create_box(
        "OledDeg",
        center=(ctrl_cx + 0.0235, oled_y, oled_z + 0.0085),
        size=(0.0024, seg_t, 0.0024),
        col=col_base_vis,
        mat=mat_seg,
    )
    _auto_uv_and_smooth(deg_ring, auto_smooth=False)
    for c_key, (ox, oz, sw, sh) in (
        ("top", (0.0275, 0.0055, 0.0055, 0.0016)),
        ("bot", (0.0275, -0.0045, 0.0055, 0.0016)),
        ("left", (0.0252, 0.0005, 0.0016, 0.0110)),
    ):
        cs = _create_box(
            f"OledUnitC_{c_key}",
            center=(ctrl_cx + ox, oled_y, oled_z + oz),
            size=(sw, seg_t, sh),
            col=col_base_vis,
            mat=mat_seg,
        )
        _auto_uv_and_smooth(cs, auto_smooth=False)

    # --- Base Low-Poly Hollow-Cavity Collision (5 convex watertight slabs) ---
    # Back slab, Top slab, Bottom slab, Left slab, Right control column
    _create_box("Col_Back", (0.0, chassis_cy + 0.5 * chassis_y - 0.5 * wall_t, body_cz), (sx, wall_t, body_h), col_base_col)
    _create_box("Col_Bottom", (0.0, chassis_cy, foot_h + 0.5 * wall_t), (sx, chassis_y, wall_t), col_base_col)
    _create_box("Col_Top", (0.0, chassis_cy, sz - 0.5 * wall_t), (sx, chassis_y, wall_t), col_base_col)
    _create_box("Col_Left", (-0.5 * sx + 0.5 * wall_t, chassis_cy, body_cz), (wall_t, chassis_y, body_h), col_base_col)
    _create_box("Col_RightCtrl", (0.5 * sx - 0.5 * (panel_w + wall_t), chassis_cy, body_cz), (panel_w + wall_t, chassis_y, body_h), col_base_col)

    # --- 2. Link_Door (Hinged on left edge with Boolean glass viewing window + tubular handle) ---
    door_w = cav_w + 0.028
    door_h = cav_h + 0.028
    door_cx = cav_cx
    door_cy = front_y - 0.5 * door_t
    door_frame = _create_box(
        "DoorFrame",
        center=(door_cx, door_cy, cav_cz),
        size=(door_w, door_t - 0.004, door_h),
        col=col_door_vis,
        mat=mat_steel,
        bevel_width=0.003,
        bevel_segments=3,
    )
    win_w = door_w - 0.056
    win_h = door_h - 0.056
    win_cutter = _create_box("WinCutter", (door_cx, door_cy, cav_cz), (win_w, door_t + 0.01, win_h), col_door_vis)
    _boolean_diff(door_frame, win_cutter)
    _auto_uv_and_smooth(door_frame, auto_smooth=False)

    glass = _create_box(
        "DoorGlassPane",
        center=(door_cx, door_cy, cav_cz),
        size=(win_w + 0.004, 0.003, win_h + 0.004),
        col=col_door_vis,
        mat=mat_glass,
    )
    _auto_uv_and_smooth(glass, auto_smooth=False)

    # Dark rubber perimeter seal gasket around window inner rim
    gasket_t = 0.005
    for gname, gc, gs in (
        ("GasketTop", (door_cx, door_cy - 0.006, cav_cz + 0.5 * win_h), (win_w + gasket_t, 0.005, gasket_t)),
        ("GasketBot", (door_cx, door_cy - 0.006, cav_cz - 0.5 * win_h), (win_w + gasket_t, 0.005, gasket_t)),
        ("GasketL", (door_cx - 0.5 * win_w, door_cy - 0.006, cav_cz), (gasket_t, 0.005, win_h)),
        ("GasketR", (door_cx + 0.5 * win_w, door_cy - 0.006, cav_cz), (gasket_t, 0.005, win_h)),
    ):
        gk = _create_box(gname, gc, gs, col_door_vis, mat_rubber)
        _auto_uv_and_smooth(gk, auto_smooth=False)

    # Real U-shaped grab handle with 18 mm open finger/gripper standoff clearance (sits cleanly at -sy/2)
    handle_x = door_cx + 0.5 * door_w - 0.015
    handle_bar_y = -0.5 * sy + 0.5 * handle_bar_t
    door_front_y = front_y - door_t + 0.002
    standoff_len = max(abs(door_front_y - (handle_bar_y + 0.5 * handle_bar_t)), 0.012)
    standoff_cy = 0.5 * (door_front_y + handle_bar_y + 0.5 * handle_bar_t)
    handle_bar = _create_box(
        "DoorHandleBar",
        center=(handle_x, handle_bar_y, cav_cz),
        size=(0.011, handle_bar_t, 0.118),
        col=col_door_vis,
        mat=mat_accent_blue,
        bevel_width=0.0025,
        bevel_segments=3,
    )
    _auto_uv_and_smooth(handle_bar)
    for hz in (cav_cz - 0.048, cav_cz + 0.048):
        st = _create_box(
            f"DoorHandleStandoff_{hz:+.2f}",
            center=(handle_x, standoff_cy, hz),
            size=(0.010, standoff_len + 0.004, 0.010),
            col=col_door_vis,
            mat=mat_steel,
            bevel_width=0.0015,
            bevel_segments=2,
        )
        _auto_uv_and_smooth(st, auto_smooth=False)

    # Door collision proxy (door slab + U-handle grab box)
    _create_box("Col_Door", (door_cx, door_cy, cav_cz), (door_w, door_t, door_h), col_door_col)
    _create_box("Col_DoorHandle", (handle_x, handle_bar_y, cav_cz), (0.012, handle_bar_t, 0.118), col_door_col)

    # --- 3. Link_Dial (Knurled Rotary Encoder Knob on Control Panel) ---
    dial_r = 0.017
    dial_d = 0.014
    dial_cy = front_y - 0.5 * dial_d - 0.002
    dial_cz = body_cz - 0.036
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=36,
        radius=dial_r,
        depth=dial_d,
        rotation=(math.radians(90.0), 0.0, 0.0),
        location=(ctrl_cx, dial_cy, dial_cz),
    )
    knob = bpy.context.active_object
    knob.name = "RotaryDialBody"
    _link_only_to(knob, col_dial_vis)
    knob.data.materials.append(mat_steel)
    # Add 12 radial knurl ribs centered at local origin, rotated, then placed on knob rim
    for k_i in range(12):
        ang = 2.0 * math.pi * k_i / 12.0
        kx = ctrl_cx + (dial_r - 0.0005) * math.cos(ang)
        kz = dial_cz + (dial_r - 0.0005) * math.sin(ang)
        rib = _create_box(
            f"DialKnurl_{k_i}",
            center=(0.0, 0.0, 0.0),
            size=(0.0020, dial_d - 0.003, 0.0020),
            col=col_dial_vis,
            mat=mat_dark_bezel,
        )
        rib.rotation_euler = Euler((0.0, -ang, 0.0), "XYZ")
        rib.location = Vector((kx, dial_cy, kz))
        _apply_transforms(rib)
        # Bake location into mesh vertices so world matrix is identity
        bpy.context.view_layer.objects.active = rib
        rib.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        rib.select_set(False)
        _auto_uv_and_smooth(rib, auto_smooth=False)
    # Indicator notch on front face
    notch = _create_box(
        "DialNotch",
        center=(ctrl_cx, dial_cy - 0.5 * dial_d - 0.0005, dial_cz + 0.007),
        size=(0.0025, 0.002, 0.010),
        col=col_dial_vis,
        mat=mat_accent_blue,
    )
    _auto_uv_and_smooth(knob)
    _auto_uv_and_smooth(notch, auto_smooth=False)
    _create_box("Col_Dial", (ctrl_cx, dial_cy, dial_cz), (2 * dial_r, dial_d, 2 * dial_r), col_dial_col)

    # --- 4. Link_Tray (Sliding Perforated Stainless Sample Tray inside Cavity) ---
    tray_w = cav_w - 0.018
    tray_d = chassis_y - wall_t - 0.032
    tray_h = 0.010
    tray_cz = cav_cz - 0.012
    tray = _create_box(
        "SampleTrayPlate",
        center=(cav_cx, chassis_cy + 0.004, tray_cz),
        size=(tray_w, tray_d, tray_h),
        col=col_tray_vis,
        mat=mat_steel,
        bevel_width=0.0015,
        bevel_segments=2,
    )
    _auto_uv_and_smooth(tray, auto_smooth=False)
    tray_lip = _create_box(
        "SampleTrayFrontLip",
        center=(cav_cx, chassis_cy + 0.004 - 0.5 * tray_d + 0.003, tray_cz + 0.009),
        size=(tray_w * 0.65, 0.006, 0.012),
        col=col_tray_vis,
        mat=mat_accent_blue,
        bevel_width=0.0015,
        bevel_segments=2,
    )
    _auto_uv_and_smooth(tray_lip, auto_smooth=False)
    _create_box("Col_Tray", (cav_cx, chassis_cy + 0.004, tray_cz), (tray_w, tray_d, tray_h + 0.008), col_tray_col)

    # Export per-link Visual & Collision NPZ + compute hygiene
    parts_dir = out_dir / "blender_parts"
    link_defs = [
        ("Base", col_base_vis, col_base_col, None),
        (
            "Door",
            col_door_vis,
            col_door_col,
            {
                "joint_name": "DoorHingeJoint",
                "joint_type": "revolute",
                "parent": "Base",
                "axis": "Z",
                "pivot_xyz": [round(door_cx - 0.5 * door_w, 6), round(front_y, 6), round(cav_cz, 6)],
                "limits_deg": [-105.0, 0.0],
                "damping": 0.45,
                "grasp_frame_xyz": [round(handle_x, 6), round(handle_bar_y, 6), round(cav_cz, 6)],
            },
        ),
        (
            "Dial",
            col_dial_vis,
            col_dial_col,
            {
                "joint_name": "DialRotaryJoint",
                "joint_type": "revolute",
                "parent": "Base",
                "axis": "Y",
                "pivot_xyz": [round(ctrl_cx, 6), round(front_y, 6), round(dial_cz, 6)],
                "limits_deg": [-150.0, 150.0],
                "damping": 0.08,
                "grasp_frame_xyz": [round(ctrl_cx, 6), round(dial_cy, 6), round(dial_cz, 6)],
            },
        ),
        (
            "Tray",
            col_tray_vis,
            col_tray_col,
            {
                "joint_name": "TraySlideJoint",
                "joint_type": "prismatic",
                "parent": "Base",
                "axis": "Y",
                "pivot_xyz": [round(cav_cx, 6), round(chassis_cy, 6), round(tray_cz, 6)],
                "limits_m": [-0.14, 0.0],
                "damping": 2.5,
                "grasp_frame_xyz": [round(cav_cx, 6), round(chassis_cy + 0.004 - 0.5 * tray_d, 6), round(tray_cz + 0.009, 6)],
            },
        ),
    ]

    links_meta: list[dict[str, Any]] = []
    vis_collections = []
    col_collections = []
    for lname, c_vis, c_col, joint_meta in link_defs:
        vis_collections.append(c_vis)
        col_collections.append(c_col)
        v_exp = _export_collection_mesh_npz(c_vis, parts_dir / f"link_{lname.lower()}_visual.npz")
        c_exp = _export_collection_mesh_npz(c_col, parts_dir / f"link_{lname.lower()}_collision.npz")
        links_meta.append(
            {
                "link_name": lname,
                "visual": v_exp,
                "collision": c_exp,
                "joint": joint_meta,
            }
        )

    # Combine hygiene across all visual meshes
    all_vis = _ensure_collection("_TempAllVis")
    for c in vis_collections:
        for o in c.objects:
            all_vis.objects.link(o)
    vis_hygiene = _measure_collection_hygiene(all_vis)
    bpy.data.collections.remove(all_vis)

    all_col = _ensure_collection("_TempAllCol")
    for c in col_collections:
        for o in c.objects:
            all_col.objects.link(o)
    col_hygiene = _measure_collection_hygiene(all_col)
    bpy.data.collections.remove(all_col)

    # Hide collision collections before Cycles studio render!
    for c in col_collections:
        c.hide_render = True
        c.hide_viewport = True

    return {
        "links": links_meta,
        "visual_hygiene": vis_hygiene,
        "collision_hygiene": col_hygiene,
        "studio_focus_center": [0.0, 0.0, 0.5 * sz],
        "studio_radius": max(sx, sy, sz) * 0.72,
        "detail_focus_center": [round(cav_cx, 4), round(front_y - 0.02, 4), round(cav_cz, 4)],
        "ui_focus_center": [round(ctrl_cx, 4), round(front_y, 4), round(body_cz + 0.01, 4)],
        "open_pose_demo": {
            "door_collection": col_door_vis.name,
            "door_pivot": [round(door_cx - 0.5 * door_w, 6), round(front_y, 6), round(cav_cz, 6)],
            "door_angle_deg": -58.0,
            "tray_collection": col_tray_vis.name,
            "tray_slide_y": -0.055,
        },
    }


def _make_maillard_croissant_material() -> Any:
    """Physically realistic matte-flaky Maillard-browned pastry shader (zero plastic clearcoat)."""
    mat = bpy.data.materials.new(name="ArtisanMaillardCroissant")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (760, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (440, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Strictly zero clearcoat + low specular IOR so softbox NEVER mirrors like plastic/latex
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Coat Weight"].default_value = 0.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.14

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-780, 0)

    # Ambient Occlusion isolates deep folded crevices (pale matte dough) vs exposed crusts
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 16
    ao.inputs["Distance"].default_value = 0.014
    ao.location = (-520, 260)

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    geom.location = (-780, 280)
    sep_pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_pos.location = (-560, 120)
    nt.links.new(tex_coord.outputs["Generated"], sep_pos.inputs["Vector"])

    # Combine AO (crevice mask) + organic blotch noise (NO Z-gradient, so oven-baked bottom stays golden!)
    noise_macro = nt.nodes.new("ShaderNodeTexNoise")
    noise_macro.inputs["Scale"].default_value = 28.0
    noise_macro.inputs["Detail"].default_value = 9.0
    noise_macro.inputs["Roughness"].default_value = 0.68
    noise_macro.location = (-520, -60)
    nt.links.new(tex_coord.outputs["Object"], noise_macro.inputs["Vector"])

    # Sharpen AO so only deep folded crevices show pale dough while flat base & flanks stay golden-baked
    ao_pow = nt.nodes.new("ShaderNodeMath")
    ao_pow.operation = "POWER"
    ao_pow.inputs[1].default_value = 1.65
    ao_pow.location = (-280, 240)
    nt.links.new(ao.outputs["AO"], ao_pow.inputs[0])

    math_noise_wt = nt.nodes.new("ShaderNodeMath")
    math_noise_wt.operation = "MULTIPLY"
    math_noise_wt.inputs[1].default_value = 0.24
    math_noise_wt.location = (-280, 40)
    nt.links.new(noise_macro.outputs["Fac"], math_noise_wt.inputs[0])

    math_mix2 = nt.nodes.new("ShaderNodeMath")
    math_mix2.operation = "ADD"
    math_mix2.location = (-100, 180)
    nt.links.new(ao_pow.outputs["Value"], math_mix2.inputs[0])
    nt.links.new(math_noise_wt.outputs["Value"], math_mix2.inputs[1])

    # ColorRamp: pale matte dough ONLY in deep wrap crevices -> warm golden crust -> deep toasted chestnut crests
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (110, 220)
    elts = ramp.color_ramp.elements
    elts[0].position = 0.24
    elts[0].color = (0.78, 0.60, 0.28, 1.0)  # pale risen dough inside deep wrap seams
    elts[1].position = 0.62
    elts[1].color = (0.46, 0.19, 0.036, 1.0)  # golden-baked pastry body & bottom
    e2 = ramp.color_ramp.elements.new(0.88)
    e2.color = (0.17, 0.052, 0.009, 1.0)  # dark toasted Maillard ridges & horn tips
    nt.links.new(math_mix2.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # Broken egg-wash roughness contrast: matte dough crevices (0.88) vs crisp flaky egg-wash sheen (0.42)
    bsdf.inputs["Specular IOR Level"].default_value = 0.28
    r_mix = nt.nodes.new("ShaderNodeMath")
    r_mix.operation = "MULTIPLY_ADD"
    r_mix.inputs[1].default_value = 0.35
    r_mix.location = (-100, -20)
    nt.links.new(noise_macro.outputs["Fac"], r_mix.inputs[0])
    nt.links.new(ao_pow.outputs["Value"], r_mix.inputs[2])

    r_ramp = nt.nodes.new("ShaderNodeValToRGB")
    r_ramp.location = (110, -20)
    r_ramp.color_ramp.elements[0].position = 0.22
    r_ramp.color_ramp.elements[0].color = (0.88, 0.88, 0.88, 1.0)
    r_ramp.color_ramp.elements[1].position = 0.92
    r_ramp.color_ramp.elements[1].color = (0.40, 0.40, 0.40, 1.0)
    nt.links.new(r_mix.outputs["Value"], r_ramp.inputs["Fac"])
    nt.links.new(r_ramp.outputs["Color"], bsdf.inputs["Roughness"])

    # Multi-scale flaky crust micro-cracks & blister bump (Voronoi flakes + fine noise)
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 120.0
    vor.location = (-520, -280)
    nt.links.new(tex_coord.outputs["Object"], vor.inputs["Vector"])

    noise_fine = nt.nodes.new("ShaderNodeTexNoise")
    noise_fine.inputs["Scale"].default_value = 320.0
    noise_fine.inputs["Detail"].default_value = 12.0
    noise_fine.inputs["Roughness"].default_value = 0.76
    noise_fine.location = (-520, -460)
    nt.links.new(tex_coord.outputs["Object"], noise_fine.inputs["Vector"])

    bump_sum = nt.nodes.new("ShaderNodeMath")
    bump_sum.operation = "MULTIPLY_ADD"
    bump_sum.inputs[1].default_value = 0.55
    bump_sum.location = (-220, -340)
    nt.links.new(vor.outputs["Distance"], bump_sum.inputs[0])
    nt.links.new(noise_fine.outputs["Fac"], bump_sum.inputs[2])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.78
    bump.inputs["Distance"].default_value = 0.0036
    bump.location = (140, -280)
    nt.links.new(bump_sum.outputs["Value"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _build_artisan_butter_croissant(spec: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Pilot B: Overlapping stepped laminated pastry croissant (flat baked base, crisp step ledges, Maillard crust)."""
    sx, sy, sz = (float(spec["dimensions_xyz_m"][0]), float(spec["dimensions_xyz_m"][1]), float(spec["dimensions_xyz_m"][2]))

    mat_pastry = _make_maillard_croissant_material()
    col_vis = _ensure_collection("Deformable_Visual")
    col_proxy = _ensure_collection("Deformable_PhysicsProxy")

    # Build true laminated stepped spiral croissant in bmesh:
    # Asymmetric crescent curve + sharp sawtooth overlapping dough steps radiating outward from center apex!
    bm = bmesh.new()
    n_u = 84  # dense enough along arc for crisp overhanging stepped pastry lips
    n_v = 40  # around cross-section
    arc_span = math.radians(148.0)  # pronounced curved crescent horns
    ring_verts: list[list[Any]] = []

    for iu in range(n_u + 1):
        u = iu / n_u  # [0, 1]
        s_abs = abs(u - 0.5) * 2.0  # 0 at center apex, 1 at horn tips
        theta = -0.5 * arc_span + u * arc_span
        r_spine = 0.50 * sx
        cx = r_spine * math.sin(theta)
        cy = 0.52 * sy * (math.cos(theta) - 0.55)

        # Puffier single central crown + 2 staggered overlapping outer wraps per side (ZERO center V-seam!)
        env = max(0.08, (1.0 - 0.86 * (s_abs ** 1.45)))

        # Smooth single central puffed band for s_abs in [0, 0.25], then crisp stepped outer wraps at 0.25, 0.55, 0.80
        def _seam_groove(center_s: float, width: float, depth: float) -> float:
            d = (s_abs - center_s) / width
            return -depth * math.exp(-d * d)

        # Raised overlapping pastry wrap plateaus with crisp asymmetric seam grooves (never splitting center!)
        crown_bump = 0.14 * math.exp(-((u - 0.5) / 0.16) ** 2)
        seams = (
            _seam_groove(0.24, 0.036, 0.18)
            + _seam_groove(0.54, 0.034, 0.16)
            + _seam_groove(0.79, 0.030, 0.12)
        )
        # Subtle asymmetric overhang leaning outward from each seam
        overhang = (
            0.09 * math.exp(-((s_abs - 0.18) / 0.06) ** 2)
            + 0.08 * math.exp(-((s_abs - 0.47) / 0.06) ** 2)
            + 0.06 * math.exp(-((s_abs - 0.72) / 0.05) ** 2)
        )
        wrap_mod = 1.0 + crown_bump + seams + overhang

        rad_y_base = max(0.0022, 0.34 * sy * env)
        rad_z_base = max(0.0022, 0.52 * sz * env)
        rad_y = rad_y_base * wrap_mod
        rad_z = rad_z_base * wrap_mod

        tx = math.cos(theta)
        ty = -0.52 * (sy / max(r_spine, 1e-4)) * math.sin(theta)
        tn = math.hypot(tx, ty)
        tx, ty = tx / max(tn, 1e-6), ty / max(tn, 1e-6)
        nx, ny = -ty, tx

        ring = []
        for iv in range(n_v):
            phi = 2.0 * math.pi * iv / n_v
            c_phi = math.cos(phi)
            s_phi = math.sin(phi)
            # Smooth flat oven-baked base (decoupled from seam grooves => zero bottom pinch spikes!)
            if s_phi < -0.18:
                z_local = -0.30 * rad_z_base
                ry_local = rad_y_base * (1.0 + 0.35 * seams)
            else:
                # Triangular folded pastry apex tab across top center
                flap_edge = 0.11 * crown_bump * max(0.0, s_phi) * math.exp(-((c_phi - 0.35) / 0.45) ** 2)
                z_local = rad_z * (s_phi + flap_edge)
                ry_local = rad_y
            # Organic flaky micro-crust irregularity baked into upper crust silhouette
            micro_amp = 0.032 if s_phi >= -0.15 else 0.005
            micro = 1.0 + micro_amp * math.sin(23.0 * u + 9.0 * phi) * math.cos(13.0 * u - 7.0 * phi)
            px = cx + nx * (ry_local * c_phi * micro)
            py = cy + ny * (ry_local * c_phi * micro)
            pz = z_local * micro
            ring.append(bm.verts.new((px, py, pz)))
        ring_verts.append(ring)

    for iu in range(n_u):
        r0 = ring_verts[iu]
        r1 = ring_verts[iu + 1]
        for iv in range(n_v):
            iv2 = (iv + 1) % n_v
            bm.faces.new((r0[iv], r1[iv], r1[iv2], r0[iv2]))

    cap0 = bm.verts.new(
        sum((v.co for v in ring_verts[0]), Vector((0.0, 0.0, 0.0))) / len(ring_verts[0])
    )
    cap1 = bm.verts.new(
        sum((v.co for v in ring_verts[-1]), Vector((0.0, 0.0, 0.0))) / len(ring_verts[-1])
    )
    for iv in range(n_v):
        iv2 = (iv + 1) % n_v
        bm.faces.new((cap0, ring_verts[0][iv2], ring_verts[0][iv]))
        bm.faces.new((cap1, ring_verts[-1][iv], ring_verts[-1][iv2]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("ArtisanCroissantMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("ArtisanCroissantVisual", mesh)
    col_vis.objects.link(obj)
    obj.data.materials.append(mat_pastry)

    # Subdivision (level 1 -> ~27k tris) + real geometric flaky crust Displace modifier
    sub = obj.modifiers.new("SubSurf", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    tex = bpy.data.textures.new("FlakyCrustDisp", type="CLOUDS")
    tex.noise_scale = 0.012
    tex.noise_depth = 4
    disp = obj.modifiers.new("CrustDisplace", "DISPLACE")
    disp.texture = tex
    disp.texture_coords = "OBJECT"
    disp.strength = 0.0022
    disp.mid_level = 0.5
    _apply_all_modifiers(obj)

    def _normalize_to_frozen_dims(target_obj: Any) -> None:
        bm_n = bmesh.new()
        bm_n.from_mesh(target_obj.data)
        xs = [v.co.x for v in bm_n.verts]
        ys = [v.co.y for v in bm_n.verts]
        zs = [v.co.z for v in bm_n.verts]
        cx0 = 0.5 * (min(xs) + max(xs))
        cy0 = 0.5 * (min(ys) + max(ys))
        z0 = min(zs)
        dx = max(max(xs) - min(xs), 1e-6)
        dy = max(max(ys) - min(ys), 1e-6)
        dz = max(max(zs) - min(zs), 1e-6)
        for v in bm_n.verts:
            v.co.x = (v.co.x - cx0) * (sx / dx)
            v.co.y = (v.co.y - cy0) * (sy / dy)
            v.co.z = (v.co.z - z0) * (sz / dz)
        bm_n.to_mesh(target_obj.data)
        bm_n.free()
        target_obj.data.update()

    _normalize_to_frozen_dims(obj)
    _auto_uv_and_smooth(obj)

    # Watertight Voxel Remesh physics proxy
    proxy = obj.copy()
    proxy.data = obj.data.copy()
    proxy.name = "ArtisanCroissantPhysicsProxy"
    col_proxy.objects.link(proxy)
    remesh = proxy.modifiers.new("VoxelRemesh", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = max(min(sx, sy, sz) / 5.5, 0.005)
    remesh.adaptivity = 0.0
    _apply_all_modifiers(proxy)
    _normalize_to_frozen_dims(proxy)

    parts_dir = out_dir / "blender_parts"
    vis_exp = _export_collection_mesh_npz(col_vis, parts_dir / "deformable_visual.npz")
    proxy_exp = _export_collection_mesh_npz(col_proxy, parts_dir / "deformable_physics_proxy.npz")
    vis_hygiene = _measure_collection_hygiene(col_vis)
    proxy_hygiene = _measure_collection_hygiene(col_proxy)

    col_proxy.hide_render = True
    col_proxy.hide_viewport = True

    return {
        "visual": vis_exp,
        "physics_proxy": proxy_exp,
        "visual_hygiene": vis_hygiene,
        "collision_hygiene": proxy_hygiene,
        "studio_focus_center": [0.0, 0.0, 0.45 * sz],
        "studio_radius": max(sx, sy, sz) * 0.72,
        "detail_focus_center": [0.0, -0.008, 0.55 * sz],
        "ui_focus_center": [0.0, 0.008, 0.48 * sz],
    }


def _build_magnetic_heating_water_bath(spec: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Bilibili BV17t4y1V7XH Digital Magnetic Heating Stirrer + Borosilicate Crystallizing Water Bath (ART-001)."""
    sx, sy, sz = (float(spec["dimensions_xyz_m"][0]), float(spec["dimensions_xyz_m"][1]), float(spec["dimensions_xyz_m"][2]))
    foot_h = 0.008
    chassis_h = 0.044
    chassis_cz = foot_h + 0.5 * chassis_h
    knob_d = 0.012
    chassis_y = sy - knob_d
    chassis_cy = 0.5 * knob_d
    front_y = chassis_cy - 0.5 * chassis_y

    mat_chassis = _make_pbr_material(
        "StirrerChassisDark",
        base_color=(0.14, 0.16, 0.19),
        metallic=0.18,
        roughness=0.34,
        coat_weight=0.12,
        noise_bump_scale=190.0,
        noise_bump_strength=0.035,
    )
    mat_top_plate = _make_pbr_material(
        "CeramicHotplate",
        base_color=(0.82, 0.84, 0.87),
        metallic=0.88,
        roughness=0.22,
        noise_bump_scale=280.0,
        noise_bump_strength=0.025,
    )
    mat_panel = _make_pbr_material("ControlPanelBlack", base_color=(0.04, 0.05, 0.07), metallic=0.25, roughness=0.24)
    mat_led_seg = _make_pbr_material(
        "TempLedRed",
        base_color=(0.95, 0.22, 0.12),
        roughness=0.12,
        emission_color=(1.0, 0.22, 0.10),
        emission_strength=5.5,
    )
    mat_knob = _make_pbr_material("KnurledKnobWhite", base_color=(0.90, 0.92, 0.95), metallic=0.08, roughness=0.28)
    mat_accent = _make_pbr_material("KnobIndicatorBlue", base_color=(0.08, 0.42, 0.82), metallic=0.15, roughness=0.24)
    mat_rubber = _make_pbr_material("AntiVibFoot", base_color=(0.04, 0.04, 0.05), roughness=0.80)

    # Crystal-clear architectural borosilicate bath shader for Cycles AgX studio sheet
    mat_bath_glass = bpy.data.materials.new(name="BorosilicateBathGlass")
    mat_bath_glass.use_nodes = True
    g_nt = mat_bath_glass.node_tree
    g_nt.nodes.clear()
    g_out = g_nt.nodes.new("ShaderNodeOutputMaterial")
    g_mix = g_nt.nodes.new("ShaderNodeMixShader")
    g_trans = g_nt.nodes.new("ShaderNodeBsdfTransparent")
    g_trans.inputs["Color"].default_value = (0.94, 0.985, 1.0, 1.0)
    g_gloss = g_nt.nodes.new("ShaderNodeBsdfGlossy")
    g_gloss.inputs["Color"].default_value = (0.96, 0.99, 1.0, 1.0)
    g_gloss.inputs["Roughness"].default_value = 0.025
    g_fres = g_nt.nodes.new("ShaderNodeLayerWeight")
    g_fres.inputs["Blend"].default_value = 0.18
    g_nt.links.new(g_fres.outputs["Facing"], g_mix.inputs["Fac"])
    g_nt.links.new(g_trans.outputs["BSDF"], g_mix.inputs[1])
    g_nt.links.new(g_gloss.outputs["BSDF"], g_mix.inputs[2])
    g_nt.links.new(g_mix.outputs["Shader"], g_out.inputs["Surface"])

    col_base_vis = _ensure_collection("Link_Base_Visual")
    col_base_col = _ensure_collection("Link_Base_Collision")
    col_tdial_vis = _ensure_collection("Link_TempDial_Visual")
    col_tdial_col = _ensure_collection("Link_TempDial_Collision")
    col_sdial_vis = _ensure_collection("Link_StirDial_Visual")
    col_sdial_col = _ensure_collection("Link_StirDial_Collision")

    # 1. Base chassis with Boolean recessed front LED display pocket
    body = _create_box(
        "StirrerHousing",
        center=(0.0, chassis_cy, chassis_cz),
        size=(sx, chassis_y, chassis_h),
        col=col_base_vis,
        mat=mat_chassis,
        bevel_width=0.005,
        bevel_segments=3,
    )
    bay_cutter = _create_box(
        "DisplayBayCutter",
        center=(0.0, front_y + 0.003, chassis_cz + 0.003),
        size=(0.068, 0.010, 0.022),
        col=col_base_vis,
    )
    _boolean_diff(body, bay_cutter)
    _auto_uv_and_smooth(body, auto_smooth=False)

    disp_win = _create_box(
        "DisplayWindow",
        center=(0.0, front_y + 0.004, chassis_cz + 0.003),
        size=(0.064, 0.002, 0.018),
        col=col_base_vis,
        mat=mat_panel,
    )
    _auto_uv_and_smooth(disp_win, auto_smooth=False)

    # 7-segment "82.5°C" crisp LED digits inside recessed window
    seg_w, seg_h, seg_t = 0.0068, 0.0014, 0.0010
    led_y = front_y + 0.0028
    led_z = chassis_cz + 0.003
    digit_map = {
        "8": ("a", "b", "c", "d", "e", "f", "g"),
        "2": ("a", "b", "g", "e", "d"),
        "5": ("a", "f", "g", "c", "d"),
    }
    seg_offs = {
        "a": (0.0, 0.0052, seg_w, seg_h),
        "g": (0.0, 0.0, seg_w, seg_h),
        "d": (0.0, -0.0052, seg_w, seg_h),
        "b": (0.0032, 0.0026, seg_h, 0.0052),
        "c": (0.0032, -0.0026, seg_h, 0.0052),
        "f": (-0.0032, 0.0026, seg_h, 0.0052),
        "e": (-0.0032, -0.0026, seg_h, 0.0052),
    }
    for d_i, (dig_c, dx_off) in enumerate((("8", -0.020), ("2", -0.009), ("5", 0.005))):
        for sk in digit_map[dig_c]:
            ox, oz, sw, sh = seg_offs[sk]
            sg = _create_box(f"BathLed_{d_i}_{sk}", (dx_off + ox, led_y, led_z + oz), (sw, seg_t, sh), col_base_vis, mat_led_seg)
            _auto_uv_and_smooth(sg, auto_smooth=False)
    dp_box = _create_box("BathLedDot", (-0.0025, led_y, led_z - 0.0050), (0.0016, seg_t, 0.0016), col_base_vis, mat_led_seg)
    _auto_uv_and_smooth(dp_box, auto_smooth=False)
    deg_b = _create_box("BathLedDeg", (0.0135, led_y, led_z + 0.0046), (0.0018, seg_t, 0.0018), col_base_vis, mat_led_seg)
    _auto_uv_and_smooth(deg_b, auto_smooth=False)
    for ck, (ox, oz, sw, sh) in (
        ("t", (0.0185, 0.0042, 0.0048, 0.0014)),
        ("b", (0.0185, -0.0042, 0.0048, 0.0014)),
        ("l", (0.0164, 0.0, 0.0014, 0.0092)),
    ):
        cb = _create_box(f"BathLedC_{ck}", (ox, led_y, led_z + oz), (sw, seg_t, sh), col_base_vis, mat_led_seg)
        _auto_uv_and_smooth(cb, auto_smooth=False)

    # Four rubber feet spanning z=[0, foot_h]
    for fx in (-0.5 * sx + 0.020, 0.5 * sx - 0.020):
        for fy in (chassis_cy - 0.5 * chassis_y + 0.020, chassis_cy + 0.5 * chassis_y - 0.020):
            bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.010, depth=foot_h, location=(fx, fy, 0.5 * foot_h))
            ft = bpy.context.active_object
            ft.name = f"BathFoot_{fx:+.2f}_{fy:+.2f}"
            _link_only_to(ft, col_base_vis)
            ft.data.materials.append(mat_rubber)
            _auto_uv_and_smooth(ft, auto_smooth=False)

    # Top ceramic-aluminum heating disc
    plate_h = 0.006
    plate_z = foot_h + chassis_h + 0.5 * plate_h
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.44 * sx, depth=plate_h, location=(0.0, chassis_cy, plate_z))
    hplate = bpy.context.active_object
    hplate.name = "HeatingDisc"
    _link_only_to(hplate, col_base_vis)
    hplate.data.materials.append(mat_top_plate)
    _auto_uv_and_smooth(hplate, auto_smooth=False)

    # Artifact-free revolved 80-segment double-walled borosilicate bath dish (split normals at flat floor -> zero sawtooth spikes!)
    dish_base_z = foot_h + chassis_h + plate_h
    dish_top_z = sz
    dish_r = 0.46 * sx
    dish_in_r = dish_r - 0.0038
    prof_rz = [
        (0.0, dish_base_z),
        (dish_r - 0.0015, dish_base_z),
        (dish_r, dish_base_z + 0.0015),
        (dish_r, dish_top_z - 0.0012),
        (dish_r - 0.0008, dish_top_z),
        (dish_in_r + 0.0008, dish_top_z),
        (dish_in_r, dish_top_z - 0.0012),
        (dish_in_r, dish_base_z + 0.0055),
        (dish_in_r - 0.0015, dish_base_z + 0.0040),
        (0.0, dish_base_z + 0.0040),
    ]
    bm_d = bmesh.new()
    n_seg_d = 80
    c_bot = bm_d.verts.new((0.0, chassis_cy, dish_base_z))
    c_top_in = bm_d.verts.new((0.0, chassis_cy, dish_base_z + 0.0040))
    rings_d = []
    for isg in range(n_seg_d):
        ang = 2.0 * math.pi * isg / n_seg_d
        ca, sa = math.cos(ang), math.sin(ang)
        rings_d.append([bm_d.verts.new((rr * ca, chassis_cy + rr * sa, zz)) for rr, zz in prof_rz[1:-1]])
    for isg in range(n_seg_d):
        r0 = rings_d[isg]
        r1 = rings_d[(isg + 1) % n_seg_d]
        bm_d.faces.new((c_bot, r1[0], r0[0]))
        for ip in range(len(r0) - 1):
            bm_d.faces.new((r0[ip], r1[ip], r1[ip + 1], r0[ip + 1]))
        bm_d.faces.new((c_top_in, r0[-1], r1[-1]))
    bmesh.ops.recalc_face_normals(bm_d, faces=bm_d.faces)
    mesh_d = bpy.data.meshes.new("CrystallizingBathDishMesh")
    bm_d.to_mesh(mesh_d)
    bm_d.free()
    dish = bpy.data.objects.new("CrystallizingBathDish", mesh_d)
    col_base_vis.objects.link(dish)
    dish.data.materials.append(mat_bath_glass)
    _auto_uv_and_smooth(dish, auto_smooth=False)
    for poly in dish.data.polygons:
        # Smooth ONLY curved vertical walls; keep flat bottom/rim discs crisp flat so normals NEVER smear!
        poly.use_smooth = abs(poly.normal.z) < 0.55
    dish_h = dish_top_z - dish_base_z

    # Magnetic PTFE stir bar resting cleanly inside glass bath floor
    stir_bar = _create_box(
        "MagneticStirBar",
        center=(0.0, chassis_cy, dish_base_z + 0.0075),
        size=(0.026, 0.007, 0.006),
        col=col_base_vis,
        mat=mat_knob,
        bevel_width=0.002,
        bevel_segments=3,
    )
    _auto_uv_and_smooth(stir_bar)

    # Base hollow-cavity collision slabs (bottom + 4 thin bath walls)
    _create_box("Col_Chassis", (0.0, chassis_cy, 0.5 * dish_base_z), (sx, chassis_y, dish_base_z), col_base_col)
    wt = 0.006
    for wname, wc, ws in (
        ("Col_DishL", (-dish_r + 0.5 * wt, chassis_cy, dish_base_z + 0.5 * dish_h), (wt, 1.4 * dish_r, dish_h)),
        ("Col_DishR", (+dish_r - 0.5 * wt, chassis_cy, dish_base_z + 0.5 * dish_h), (wt, 1.4 * dish_r, dish_h)),
        ("Col_DishF", (0.0, chassis_cy - dish_r + 0.5 * wt, dish_base_z + 0.5 * dish_h), (1.4 * dish_r, wt, dish_h)),
        ("Col_DishB", (0.0, chassis_cy + dish_r - 0.5 * wt, dish_base_z + 0.5 * dish_h), (1.4 * dish_r, wt, dish_h)),
    ):
        _create_box(wname, wc, ws, col_base_col)

    # 2 & 3. Two Articulated Knurled Rotary Dials (36-seg body + 12 physical axial knurling ridges + blue tick!)
    dial_r = 0.0105
    dial_cy = -0.5 * sy + 0.5 * knob_d
    dial_cz = chassis_cz - 0.002
    for dname, dx, c_vis, c_col in (
        ("TempDial", -0.050, col_tdial_vis, col_tdial_col),
        ("StirDial", +0.050, col_sdial_vis, col_sdial_col),
    ):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=36,
            radius=dial_r,
            depth=knob_d,
            rotation=(math.radians(90.0), 0.0, 0.0),
            location=(dx, dial_cy, dial_cz),
        )
        kn = bpy.context.active_object
        kn.name = f"{dname}_Body"
        _link_only_to(kn, c_vis)
        kn.data.materials.append(mat_knob)
        _auto_uv_and_smooth(kn, auto_smooth=False)
        for poly in kn.data.polygons:
            poly.use_smooth = abs(poly.normal.y) < 0.55
        for ki in range(12):
            ang = 2.0 * math.pi * ki / 12.0
            kx = dx + (dial_r - 0.0004) * math.cos(ang)
            kz = dial_cz + (dial_r - 0.0004) * math.sin(ang)
            rib = _create_box(
                f"{dname}_Knurl_{ki}",
                center=(0.0, 0.0, 0.0),
                size=(0.0016, knob_d - 0.0025, 0.0016),
                col=c_vis,
                mat=mat_panel,
            )
            rib.rotation_euler = Euler((0.0, -ang, 0.0), "XYZ")
            rib.location = Vector((kx, dial_cy, kz))
            bpy.context.view_layer.objects.active = rib
            rib.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            rib.select_set(False)
            _auto_uv_and_smooth(rib, auto_smooth=False)
        ind = _create_box(
            f"{dname}_Tick",
            center=(dx, -0.5 * sy + 0.0008, dial_cz + 0.0052),
            size=(0.0020, 0.0018, 0.0062),
            col=c_vis,
            mat=mat_accent,
        )
        _auto_uv_and_smooth(ind, auto_smooth=False)
        _create_box(f"Col_{dname}", (dx, dial_cy, dial_cz), (2 * dial_r, knob_d, 2 * dial_r), c_col)

    parts_dir = out_dir / "blender_parts"
    link_defs = [
        ("Base", col_base_vis, col_base_col, None),
        (
            "TempDial",
            col_tdial_vis,
            col_tdial_col,
            {
                "joint_name": "TempDialJoint",
                "joint_type": "revolute",
                "parent": "Base",
                "axis": "Y",
                "pivot_xyz": [-0.050, round(front_y, 6), round(dial_cz, 6)],
                "limits_deg": [-150.0, 150.0],
                "damping": 0.06,
                "grasp_frame_xyz": [-0.050, round(dial_cy, 6), round(dial_cz, 6)],
            },
        ),
        (
            "StirDial",
            col_sdial_vis,
            col_sdial_col,
            {
                "joint_name": "StirDialJoint",
                "joint_type": "revolute",
                "parent": "Base",
                "axis": "Y",
                "pivot_xyz": [+0.050, round(front_y, 6), round(dial_cz, 6)],
                "limits_deg": [-150.0, 150.0],
                "damping": 0.06,
                "grasp_frame_xyz": [+0.050, round(dial_cy, 6), round(dial_cz, 6)],
            },
        ),
    ]

    links_meta: list[dict[str, Any]] = []
    vis_cols, col_cols = [], []
    for lname, c_vis, c_col, jmeta in link_defs:
        vis_cols.append(c_vis)
        col_cols.append(c_col)
        links_meta.append(
            {
                "link_name": lname,
                "visual": _export_collection_mesh_npz(c_vis, parts_dir / f"link_{lname.lower()}_visual.npz"),
                "collision": _export_collection_mesh_npz(c_col, parts_dir / f"link_{lname.lower()}_collision.npz"),
                "joint": jmeta,
            }
        )

    all_vis = _ensure_collection("_TempBathVis")
    for c in vis_cols:
        for o in c.objects:
            all_vis.objects.link(o)
    vis_hygiene = _measure_collection_hygiene(all_vis)
    bpy.data.collections.remove(all_vis)

    all_col = _ensure_collection("_TempBathCol")
    for c in col_cols:
        for o in c.objects:
            all_col.objects.link(o)
    col_hygiene = _measure_collection_hygiene(all_col)
    bpy.data.collections.remove(all_col)

    for c in col_cols:
        c.hide_render = True
        c.hide_viewport = True

    return {
        "links": links_meta,
        "visual_hygiene": vis_hygiene,
        "collision_hygiene": col_hygiene,
        "studio_focus_center": [0.0, 0.0, 0.50 * sz],
        "studio_radius": max(sx, sy, sz) * 0.96,
        "detail_focus_center": [0.0, front_y, 0.36 * sz],
        "ui_focus_center": [0.0, front_y, chassis_cz],
        "open_pose_demo": {
            "door_collection": col_tdial_vis.name,
            "door_pivot": [-0.050, round(front_y, 6), round(dial_cz, 6)],
            "door_angle_deg": 52.0,
            "door_axis": "Y",
            "dial2_collection": col_sdial_vis.name,
            "dial2_pivot": [+0.050, round(front_y, 6), round(dial_cz, 6)],
            "dial2_angle_deg": -44.0,
        },
    }


def _build_amber_latex_cooling_hose(spec: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Bilibili BV17t4y1V7XH Thin-Walled Natural Amber Latex Cooling Hose in S-Catenary Drape (bundle/v0.2)."""
    sx, sy, sz = (float(spec["dimensions_xyz_m"][0]), float(spec["dimensions_xyz_m"][1]), float(spec["dimensions_xyz_m"][2]))
    mat_latex = _make_pbr_material(
        "NaturalAmberLatex",
        base_color=(0.82, 0.52, 0.18),
        metallic=0.0,
        roughness=0.46,
        coat_weight=0.0,
        transmission_weight=0.18,
        noise_bump_scale=220.0,
        noise_bump_strength=0.05,
        color_variation=(0.74, 0.44, 0.14),
    )

    col_vis = _ensure_collection("Deformable_Visual")
    col_proxy = _ensure_collection("Deformable_PhysicsProxy")

    # Build smooth catenary S-curve manifold tube with reinforced ribbed nozzle cuffs at both ends
    bm = bmesh.new()
    n_u = 96
    n_v = 32
    pts = []
    for iu in range(n_u + 1):
        u = iu / n_u
        x = (u - 0.5) * 0.94 * sx
        y = 0.42 * sy * math.sin(2.0 * math.pi * (u - 0.5))
        # Natural sagging catenary belly resting flat near z=0 with raised condenser/tap ends
        z = 0.08 * sz + 0.86 * sz * ((2.0 * (u - 0.5)) ** 2) * (0.72 + 0.28 * u)
        pts.append(Vector((x, y, z)))

    tangents = []
    for i in range(len(pts)):
        if i == 0:
            t = (pts[1] - pts[0]).normalized()
        elif i == len(pts) - 1:
            t = (pts[-1] - pts[-2]).normalized()
        else:
            t = (pts[i + 1] - pts[i - 1]).normalized()
        tangents.append(t)

    nrm = Vector((0.0, 0.0, 1.0))
    nrm = (nrm - nrm.dot(tangents[0]) * tangents[0]).normalized()
    rings = []
    for iu, p in enumerate(pts):
        u = iu / n_u
        t = tangents[iu]
        nrm = (nrm - nrm.dot(t) * t).normalized()
        bnm = t.cross(nrm).normalized()
        # Subtle ribbed barb cuff flare near u=0 and u=1
        end_dist = min(u, 1.0 - u)
        cuff_flare = 1.0 + (0.22 * math.cos(end_dist * 110.0) ** 2 if end_dist < 0.07 else 0.0)
        r_tube = 0.0056 * cuff_flare
        ring = []
        for iv in range(n_v):
            ang = 2.0 * math.pi * iv / n_v
            d = math.cos(ang) * nrm + math.sin(ang) * bnm
            ring.append(bm.verts.new(p + r_tube * d))
        rings.append(ring)

    for iu in range(n_u):
        r0, r1 = rings[iu], rings[iu + 1]
        for iv in range(n_v):
            iv2 = (iv + 1) % n_v
            bm.faces.new((r0[iv], r0[iv2], r1[iv2], r1[iv]))

    # Clean manifold end-caps
    c0 = bm.verts.new(pts[0])
    c1 = bm.verts.new(pts[-1])
    for iv in range(n_v):
        iv2 = (iv + 1) % n_v
        bm.faces.new((c0, rings[0][iv2], rings[0][iv]))
        bm.faces.new((c1, rings[-1][iv], rings[-1][iv2]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("AmberLatexHoseMesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("AmberLatexHoseVisual", mesh)
    col_vis.objects.link(obj)
    obj.data.materials.append(mat_latex)
    sub = obj.modifiers.new("SubSurf", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    _apply_all_modifiers(obj)

    def _norm_hose_dims(target_obj: Any) -> None:
        bm_n = bmesh.new()
        bm_n.from_mesh(target_obj.data)
        xs = [v.co.x for v in bm_n.verts]
        ys = [v.co.y for v in bm_n.verts]
        zs = [v.co.z for v in bm_n.verts]
        cx0, cy0, z0 = 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), min(zs)
        dx, dy, dz = max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6), max(max(zs) - min(zs), 1e-6)
        for v in bm_n.verts:
            v.co.x = (v.co.x - cx0) * (sx / dx)
            v.co.y = (v.co.y - cy0) * (sy / dy)
            v.co.z = (v.co.z - z0) * (sz / dz)
        bm_n.to_mesh(target_obj.data)
        bm_n.free()
        target_obj.data.update()

    _norm_hose_dims(obj)
    _auto_uv_and_smooth(obj)

    # Decimated watertight proxy tube (`proxy_tris < visual_tris`)
    proxy = obj.copy()
    proxy.data = obj.data.copy()
    proxy.name = "AmberLatexHosePhysicsProxy"
    col_proxy.objects.link(proxy)
    dec = proxy.modifiers.new("DecimateProxy", "DECIMATE")
    dec.ratio = 0.35
    _apply_all_modifiers(proxy)
    _norm_hose_dims(proxy)

    parts_dir = out_dir / "blender_parts"
    vis_exp = _export_collection_mesh_npz(col_vis, parts_dir / "deformable_visual.npz")
    proxy_exp = _export_collection_mesh_npz(col_proxy, parts_dir / "deformable_physics_proxy.npz")
    vis_hygiene = _measure_collection_hygiene(col_vis)
    proxy_hygiene = _measure_collection_hygiene(col_proxy)

    col_proxy.hide_render = True
    col_proxy.hide_viewport = True

    return {
        "visual": vis_exp,
        "physics_proxy": proxy_exp,
        "visual_hygiene": vis_hygiene,
        "collision_hygiene": proxy_hygiene,
        "studio_focus_center": [0.0, 0.0, 0.42 * sz],
        "studio_radius": max(sx, sy, sz) * 0.68,
        "detail_focus_center": [-0.36 * sx, 0.0, 0.65 * sz],
        "ui_focus_center": [0.0, 0.0, 0.25 * sz],
    }


def _render_cycles_agx_studio_sheet(
    spec: dict[str, Any],
    build_info: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    """Render 4-view Cycles AgX studio sheet using Blender 4.4+ native AgX + OpenImageDenoise."""
    import numpy as np

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    device = str(spec.get("cycles_device", "CPU")).upper()
    if device == "CPU":
        scene.cycles.device = "CPU"
    else:
        scene.cycles.device = "GPU"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = device
        prefs.get_devices()
    scene.cycles.samples = int(spec.get("cycles_samples", 32))
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 6

    # Native Blender 4.4+ AgX color management
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        scene.view_settings.look = "None"
    scene.view_settings.exposure = -0.15

    rw, rh = int(spec["render_resolution"][0]), int(spec["render_resolution"][1])
    scene.render.resolution_x = rw
    scene.render.resolution_y = rh
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    # Studio backdrop floor + soft neutral world
    col_studio = _ensure_collection("_StudioRig")
    world = bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.14, 0.16, 0.20, 1.0)
        bg.inputs["Strength"].default_value = 0.45

    rad = float(build_info["studio_radius"])
    floor_mat = _make_pbr_material("StudioFloor", base_color=(0.52, 0.55, 0.59), roughness=0.72)
    bpy.ops.mesh.primitive_plane_add(size=max(rad * 14.0, 2.0), location=(0.0, 0.0, -0.0004))
    floor = bpy.context.active_object
    floor.name = "StudioFloorPlane"
    _link_only_to(floor, col_studio)
    floor.data.materials.append(floor_mat)

    # Physically distance-scaled 3-point softbox lighting (strictly proportional to rad^2 for scale invariance)
    rad2 = max(rad * rad, 1e-4)
    lights = [
        ("KeyLight", (rad * 2.2, -rad * 2.6, rad * 2.4), 190.0 * rad2, rad * 1.5, (1.0, 0.96, 0.91)),
        ("FillLight", (-rad * 2.5, -rad * 1.8, rad * 1.6), 85.0 * rad2, rad * 1.9, (0.90, 0.95, 1.0)),
        ("RimLight", (0.2 * rad, rad * 2.6, rad * 2.2), 120.0 * rad2, rad * 1.4, (0.96, 0.98, 1.0)),
    ]
    focus = Vector(build_info["studio_focus_center"])
    for lname, lpos, energy, lsize, lcol in lights:
        ldata = bpy.data.lights.new(name=lname, type="AREA")
        ldata.energy = float(energy)
        ldata.size = float(lsize)
        ldata.color = lcol
        lobj = bpy.data.objects.new(name=lname, object_data=ldata)
        col_studio.objects.link(lobj)
        lobj.location = focus + Vector(lpos)
        direction = focus - lobj.location
        lobj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    cam_data = bpy.data.cameras.new("StudioCam")
    cam_data.lens = 55.0
    cam_data.clip_start = 0.005
    cam_obj = bpy.data.objects.new("StudioCam", cam_data)
    col_studio.objects.link(cam_obj)
    scene.camera = cam_obj

    detail_f = Vector(build_info["detail_focus_center"])
    ui_f = Vector(build_info["ui_focus_center"])
    is_deformable = str(spec.get("family")) == "deformable_sculpted"
    if is_deformable:
        views = [
            ("preview_iso", focus, focus + Vector((-rad * 1.95, -rad * 2.05, rad * 1.35))),
            ("preview_front", focus, focus + Vector((0.0, -rad * 2.65, rad * 0.42))),
            ("preview_detail", detail_f, detail_f + Vector((-rad * 0.65, -rad * 1.50, rad * 0.92))),
            ("preview_ui", ui_f, ui_f + Vector((rad * 1.65, rad * 1.85, rad * 1.15))),
        ]
    else:
        views = [
            ("preview_iso", focus, focus + Vector((-rad * 1.95, -rad * 2.15, rad * 1.35))),
            ("preview_front", focus, focus + Vector((rad * 1.15, -rad * 2.35, rad * 0.65))),
            ("preview_detail", detail_f, detail_f + Vector((rad * 0.85, -rad * 1.85, rad * 0.72))),
            ("preview_ui", ui_f, ui_f + Vector((rad * 0.65, -rad * 1.45, rad * 0.35))),
        ]

    studio_dir = out_dir / "studio_agx"
    studio_dir.mkdir(parents=True, exist_ok=True)
    view_paths: dict[str, Path] = {}
    view_stats: dict[str, dict[str, float]] = {}

    open_demo = build_info.get("open_pose_demo")

    def _apply_open_pose(enable: bool) -> list[tuple[Any, Matrix]]:
        saved: list[tuple[Any, Matrix]] = []
        if not open_demo:
            return saved
        door_col = bpy.data.collections.get(open_demo.get("door_collection", ""))
        tray_col = bpy.data.collections.get(open_demo.get("tray_collection", ""))
        pivot = Vector(open_demo["door_pivot"])
        axis_str = str(open_demo.get("door_axis", "Z"))
        rot_m = (
            Matrix.Translation(pivot)
            @ Matrix.Rotation(math.radians(float(open_demo["door_angle_deg"])), 4, axis_str)
            @ Matrix.Translation(-pivot)
        )
        if enable:
            if door_col:
                for o in door_col.objects:
                    saved.append((o, o.matrix_world.copy()))
                    o.matrix_world = rot_m @ o.matrix_world
            if "dial2_collection" in open_demo:
                d2_col = bpy.data.collections.get(open_demo["dial2_collection"])
                p2 = Vector(open_demo["dial2_pivot"])
                rm2 = (
                    Matrix.Translation(p2)
                    @ Matrix.Rotation(math.radians(float(open_demo["dial2_angle_deg"])), 4, "Y")
                    @ Matrix.Translation(-p2)
                )
                if d2_col:
                    for o in d2_col.objects:
                        saved.append((o, o.matrix_world.copy()))
                        o.matrix_world = rm2 @ o.matrix_world
            if tray_col:
                dy = float(open_demo["tray_slide_y"])
                for o in tray_col.objects:
                    saved.append((o, o.matrix_world.copy()))
                    o.matrix_world = Matrix.Translation(Vector((0.0, dy, 0.0))) @ o.matrix_world
        return saved

    for vname, target_pt, cam_pos in views:
        saved_mats: list[tuple[Any, Matrix]] = []
        if vname == "preview_detail" and open_demo:
            saved_mats = _apply_open_pose(True)
        cam_obj.location = cam_pos
        cam_obj.rotation_euler = (target_pt - cam_pos).to_track_quat("-Z", "Y").to_euler()
        out_png = studio_dir / f"{vname}.png"
        scene.render.filepath = str(out_png)
        bpy.ops.render.render(write_still=True)
        for o, m in saved_mats:
            o.matrix_world = m
        view_paths[vname] = out_png

        # Load rendered PNG inside Blender to verify exposure & contrast
        img = bpy.data.images.load(str(out_png), check_existing=False)
        px = np.asarray(img.pixels[:], dtype=np.float32).reshape(rh, rw, 4)[:, :, :3]
        bpy.data.images.remove(img)
        view_stats[vname] = {
            "mean_luma": round(float(np.mean(px)), 4),
            "std_luma": round(float(np.std(px)), 4),
            "p95_luma": round(float(np.percentile(px, 95)), 4),
        }

    # Save editable .blend source file (hide studio rig so asset opens clean)
    col_studio.hide_viewport = True
    bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f"{spec['asset_id']}.blend"))

    return {
        "view_paths": {k: v.as_posix() for k, v in view_paths.items()},
        "view_stats": view_stats,
        "blend_path": (out_dir / f"{spec['asset_id']}.blend").as_posix(),
    }


def main() -> None:
    _assert_blender_44()
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    _reset_scene()

    template = str(spec["template"])
    if template == "precision_benchtop_incubator":
        build_info = _build_precision_benchtop_incubator(spec, out_dir)
    elif template == "artisan_butter_croissant":
        build_info = _build_artisan_butter_croissant(spec, out_dir)
    elif template == "magnetic_heating_water_bath":
        build_info = _build_magnetic_heating_water_bath(spec, out_dir)
    elif template == "amber_latex_cooling_hose":
        build_info = _build_amber_latex_cooling_hose(spec, out_dir)
    else:
        raise ValueError(f"Unsupported BlenderForge template: {template!r}")

    studio_info = _render_cycles_agx_studio_sheet(spec, build_info, out_dir)
    receipt = {
        "blender_version": bpy.app.version_string,
        "spec": spec,
        "build_info": build_info,
        "studio_info": studio_info,
    }
    (out_dir / "blender_worker_receipt.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

