"""Blender 4.4.3 Cycles OptiX GPU Cinema Renderer for SIGGRAPH Asia 2027 Hero 1-4 Animations & 4K Keyframe Plates.

Invoke directly via Blender 4.4.3:
  blender.exe --background --python blender_cycles_reel.py -- --scene hero1 --cache hero1.npz --out-dir ...

Features SIGGRAPH Technical Papers Trailer visual production:
  - RTX 4090 Cycles OptiX GPU ray tracing with AI OptiX Denoiser
  - Translucent subsurface-scattering amber latex & emerald silicone shaders (optional strain-field emission tint)
  - Procedural woven linen/silk micro-bump 2D cloth pouch shader with grazing sheen
  - Refractive IOR 1.47 borosilicate 3-olive laboratory glass shader
  - Dark architectural studio cyclorama + 3-point softbox lighting + crisp keyframe 4K plates + 1080p MP4 reels
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import bpy
import numpy as np


def _clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _setup_cycles_optix(*, width: int = 1280, height: int = 720, samples: int = 36) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = int(samples)
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPTIX"
    except Exception:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 6

    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            gpu_found = False
            for d in prefs.devices:
                if d.type in ("OPTIX", "CUDA"):
                    d.use = True
                    gpu_found = True
                else:
                    d.use = False
            if gpu_found:
                scene.cycles.device = "GPU"
                break
        except Exception:
            continue

    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Punchy"
    except Exception:
        pass
    scene.view_settings.exposure = -0.35


def _setup_studio_world_and_lights(*, floor_z: float = -0.10, target_xyz=(0.0, 0.0, 0.0), scale: float = 1.0) -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.new("SIGAStudioWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.010, 0.015, 0.026, 1.0)
        bg.inputs[1].default_value = 0.40

    # Matte architectural dark slate studio floor (lets translucent latex & glass pop!)
    bpy.ops.mesh.primitive_plane_add(size=6.0 * scale, location=(target_xyz[0], target_xyz[1], floor_z))
    floor = bpy.context.active_object
    floor.name = "StudioFloor"
    mat_fl = bpy.data.materials.new("SlateFloorMat")
    mat_fl.use_nodes = True
    bsdf = mat_fl.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.014, 0.019, 0.030, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    floor.data.materials.append(mat_fl)

    tx, ty, tz = target_xyz
    # 3-Point Studio Area Softboxes: Warm Key, Cool Rim, Soft Overhead Fill
    lights = [
        ("KeyLight", (tx + 0.55 * scale, ty - 0.70 * scale, tz + 0.65 * scale), 32.0 * scale * scale, 0.55 * scale, (1.0, 0.96, 0.90)),
        ("RimLight", (tx - 0.50 * scale, ty + 0.65 * scale, tz + 0.50 * scale), 26.0 * scale * scale, 0.45 * scale, (0.76, 0.88, 1.0)),
        ("FillLight", (tx, ty - 0.25 * scale, tz + 0.95 * scale), 14.0 * scale * scale, 0.85 * scale, (0.90, 0.94, 1.0)),
    ]
    for name, loc, energy, sz, col in lights:
        ld = bpy.data.lights.new(name, type="AREA")
        ld.energy = energy
        ld.size = sz
        ld.color = col
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        direction = np.array(target_xyz, dtype=np.float64) - np.array(loc, dtype=np.float64)
        from mathutils import Vector
        lo.rotation_euler = Vector(direction.tolist()).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(lo)


def _setup_camera(eye_xyz, target_xyz, *, lens_mm: float = 55.0) -> bpy.types.Object:
    from mathutils import Vector
    cd = bpy.data.cameras.new("MainCam")
    cd.lens = float(lens_mm)
    cd.clip_start = 0.002
    cd.clip_end = 50.0
    cam = bpy.data.objects.new("MainCam", cd)
    cam.location = eye_xyz
    direction = Vector(target_xyz) - Vector(eye_xyz)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def _make_latex_material(name: str, base_rgb: tuple[float, float, float], *, use_strain_vc: bool = False) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.24
    bsdf.inputs["IOR"].default_value = 1.48
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.42
    if "Subsurface Scale" in bsdf.inputs:
        bsdf.inputs["Subsurface Scale"].default_value = 0.004
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.35
        bsdf.inputs["Coat Roughness"].default_value = 0.14

    if use_strain_vc:
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "StrainColor"
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*base_rgb, 1.0)
    return mat


def _make_cloth_material(name: str = "WovenLinenCloth") -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.20, 0.46, 0.72, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.76
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.65
        bsdf.inputs["Sheen Roughness"].default_value = 0.45
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.12

    # Crisp procedural woven fabric checker + micro-bump
    tc = nt.nodes.new("ShaderNodeTexCoord")
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 48.0
    chk.inputs["Color1"].default_value = (0.17, 0.43, 0.68, 1.0)
    chk.inputs["Color2"].default_value = (0.28, 0.56, 0.80, 1.0)
    nt.links.new(tc.outputs["Object"], chk.inputs["Vector"])
    nt.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.001
    nt.links.new(chk.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _make_borosilicate_glass_material(name: str = "BorosilicateGlass") -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.86, 0.96, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.03
    bsdf.inputs["IOR"].default_value = 1.47
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.94
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.94
    return mat


def _create_mesh_object(name: str, V: np.ndarray, F: np.ndarray, mat: bpy.types.Material, *, offset_xyz=(0.0, 0.0, 0.0), smooth: bool = True) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "Mesh")
    V_off = np.asarray(V, dtype=np.float64) + np.asarray(offset_xyz, dtype=np.float64)[None, :]
    mesh.from_pydata(V_off.tolist(), [], np.asarray(F, dtype=np.int32).tolist())
    mesh.update()
    if smooth:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def _update_mesh_vertices(obj: bpy.types.Object, V: np.ndarray, *, offset_xyz=(0.0, 0.0, 0.0), strain_vals: np.ndarray | None = None, strain_max: float = 0.60, base_rgb=(0.82, 0.44, 0.08)) -> None:
    V_off = (np.asarray(V, dtype=np.float64) + np.asarray(offset_xyz, dtype=np.float64)[None, :]).ravel()
    obj.data.vertices.foreach_set("co", V_off)
    if strain_vals is not None:
        me = obj.data
        ca = me.color_attributes.get("StrainColor")
        if ca is None:
            ca = me.color_attributes.new(name="StrainColor", type="BYTE_COLOR", domain="CORNER")
        s = np.clip(np.asarray(strain_vals, dtype=np.float64) / max(strain_max, 1e-6), 0.0, 1.0)
        # Blend warm amber latex -> glowing coral-red at high Brazier ovalization/hoop bulge!
        r = np.clip(base_rgb[0] * (1.0 - s) + 1.00 * s, 0.0, 1.0)
        g = np.clip(base_rgb[1] * (1.0 - s) + 0.16 * s, 0.0, 1.0)
        b = np.clip(base_rgb[2] * (1.0 - s) + 0.06 * s, 0.0, 1.0)
        v_rgba = np.column_stack([r, g, b, np.ones_like(r)]).astype(np.float32)
        loop_v = np.empty(len(me.loops), dtype=np.int32)
        me.loops.foreach_get("vertex_index", loop_v)
        ca.data.foreach_set("color", v_rgba[loop_v].ravel())
    obj.data.update()


def render_hero_scene(scene_name: str, cache_npz: Path, out_dir: Path, *, width: int = 1280, height: int = 720, samples: int = 36, frame_stride: int = 1, keyframe_only: bool = False) -> None:
    _clear_scene()
    _setup_cycles_optix(width=width, height=height, samples=samples)
    data = np.load(cache_npz)
    frames_dir = out_dir / f"{scene_name}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    if scene_name == "hero1":
        # 3-Way side-by-side: Back=DER (Rigid), Mid=3D Tet FEM, Front=Ours C1-Brazier — framed with full head-to-tail clearance!
        _setup_studio_world_and_lights(floor_z=-0.20, target_xyz=(0.11, 0.0, -0.07), scale=1.1)
        _setup_camera((0.40, -0.44, 0.14), (0.09, 0.0, -0.065), lens_mm=44.0)

        m_der = _make_latex_material("DERMat", (0.50, 0.56, 0.64))
        m_fem = _make_latex_material("FEM3DMat", (0.12, 0.52, 0.85))
        m_ours = _make_latex_material("OursBrazierMat", (0.82, 0.40, 0.05), use_strain_vc=True)

        off_d = (0.0, +0.085, 0.0)
        off_f = (0.0, 0.000, 0.0)
        off_o = (0.0, -0.085, 0.0)

        obj_d = _create_mesh_object("DER_Tube", data["der_V"][0], data["der_F"], m_der, offset_xyz=off_d)
        obj_f = _create_mesh_object("FEM3D_Tube", data["fem_V"][0], data["fem_F"], m_fem, offset_xyz=off_f)
        obj_o = _create_mesh_object("Ours_Tube", data["ours_V"][0], data["ours_F"], m_ours, offset_xyz=off_o)

        n_tot = len(data["ours_V"])
        f_list = [44] if keyframe_only else list(range(0, n_tot, frame_stride))
        for out_i, fi in enumerate(f_list):
            _update_mesh_vertices(obj_d, data["der_V"][fi], offset_xyz=off_d)
            _update_mesh_vertices(obj_f, data["fem_V"][fi], offset_xyz=off_f)
            _update_mesh_vertices(obj_o, data["ours_V"][fi], offset_xyz=off_o, strain_vals=data["ours_ov"][fi], strain_max=0.58)
            bpy.context.scene.render.filepath = str(out_dir / f"{scene_name}_4k_keyframe.png") if keyframe_only else str(frames_dir / f"frame_{out_i:04d}.png")
            bpy.ops.render.render(write_still=True)

    elif scene_name == "hero2":
        _setup_studio_world_and_lights(floor_z=-0.045, target_xyz=(0.0, 0.0, 0.0), scale=0.6)
        _setup_camera((0.0, -0.22, 0.18), (0.0, 0.0, 0.0), lens_mm=65.0)
        m_a = _make_latex_material("KnotAmber", (0.88, 0.48, 0.08), use_strain_vc=True)
        m_b = _make_latex_material("KnotEmerald", (0.08, 0.62, 0.46), use_strain_vc=True)
        obj_a = _create_mesh_object("KnotTubeA", data["Va"][0], data["Fa"], m_a)
        obj_b = _create_mesh_object("KnotTubeB", data["Vb"][0], data["Fb"], m_b)
        n_tot = len(data["Va"])
        f_list = [n_tot - 1] if keyframe_only else list(range(0, n_tot, frame_stride))
        for out_i, fi in enumerate(f_list):
            _update_mesh_vertices(obj_a, data["Va"][fi], strain_vals=data["ova"][fi], strain_max=0.45, base_rgb=(0.88, 0.48, 0.08))
            _update_mesh_vertices(obj_b, data["Vb"][fi], strain_vals=data["ovb"][fi], strain_max=0.45, base_rgb=(0.08, 0.62, 0.46))
            bpy.context.scene.render.filepath = str(out_dir / f"{scene_name}_4k_keyframe.png") if keyframe_only else str(frames_dir / f"frame_{out_i:04d}.png")
            bpy.ops.render.render(write_still=True)

    elif scene_name == "hero3":
        _setup_studio_world_and_lights(floor_z=-0.11, target_xyz=(0.0, 0.0, 0.028), scale=0.95)
        _setup_camera((0.34, -0.44, 0.27), (0.0, 0.0, 0.028), lens_mm=46.0)
        m_rod = _make_latex_material("DrawstringLatex", (0.90, 0.50, 0.10))
        m_sh = _make_cloth_material("WovenClothPouch")
        obj_r = _create_mesh_object("DrawstringTube", data["rod_V"][0], data["rod_F"], m_rod)
        obj_s = _create_mesh_object("ClothPouch", data["shell_V"][0], data["shell_F"], m_sh)
        n_tot = len(data["rod_V"])
        f_list = [n_tot - 1] if keyframe_only else list(range(0, n_tot, frame_stride))
        for out_i, fi in enumerate(f_list):
            _update_mesh_vertices(obj_r, data["rod_V"][fi])
            _update_mesh_vertices(obj_s, data["shell_V"][fi])
            bpy.context.scene.render.filepath = str(out_dir / f"{scene_name}_4k_keyframe.png") if keyframe_only else str(frames_dir / f"frame_{out_i:04d}.png")
            bpy.ops.render.render(write_still=True)

    elif scene_name == "hero4":
        _setup_studio_world_and_lights(floor_z=-0.055, target_xyz=(0.036, 0.0, 0.0), scale=0.50)
        _setup_camera((0.036, -0.195, 0.050), (0.036, 0.0, 0.0), lens_mm=58.0)
        m_glass = _make_borosilicate_glass_material("BorosilicateBarb")
        m_lock = _make_latex_material("HoseSelfLock", (0.86, 0.48, 0.08), use_strain_vc=True)
        m_slip = _make_latex_material("HoseZeroMuSlip", (0.30, 0.62, 0.85), use_strain_vc=True)

        off_top = (0.0, 0.0, +0.016)
        off_bot = (0.0, 0.0, -0.016)
        _create_mesh_object("GlassBarbTop", data["barb_V"], data["barb_F"], m_glass, offset_xyz=off_top)
        _create_mesh_object("GlassBarbBot", data["barb_V"], data["barb_F"], m_glass, offset_xyz=off_bot)
        obj_l = _create_mesh_object("HoseLock", data["lock_V"][0], data["hose_F"], m_lock, offset_xyz=off_top)
        obj_s = _create_mesh_object("HoseSlip", data["slip_V"][0], data["hose_F"], m_slip, offset_xyz=off_bot)

        n_tot = len(data["lock_V"])
        f_list = [n_tot - 1] if keyframe_only else list(range(0, n_tot, frame_stride))
        for out_i, fi in enumerate(f_list):
            _update_mesh_vertices(obj_l, data["lock_V"][fi], offset_xyz=off_top, strain_vals=data["lock_hp"][fi], strain_max=0.72, base_rgb=(0.86, 0.48, 0.08))
            _update_mesh_vertices(obj_s, data["slip_V"][fi], offset_xyz=off_bot, strain_vals=data["slip_hp"][fi], strain_max=0.72, base_rgb=(0.30, 0.62, 0.85))
            bpy.context.scene.render.filepath = str(out_dir / f"{scene_name}_4k_keyframe.png") if keyframe_only else str(frames_dir / f"frame_{out_i:04d}.png")
            bpy.ops.render.render(write_still=True)


def main() -> int:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=["hero1", "hero2", "hero3", "hero4"], required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--samples", type=int, default=36)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--keyframe-only", action="store_true")
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    render_hero_scene(
        args.scene,
        args.cache,
        args.out_dir,
        width=args.width,
        height=args.height,
        samples=args.samples,
        frame_stride=args.stride,
        keyframe_only=args.keyframe_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

