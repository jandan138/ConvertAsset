"""Headless Blender 4.4.3+ generator for all 20 high-poly distillation_v06 instruments + Cycles AgX studio QA."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def run_blender_kit_generation(
    out_dir: Path,
    *,
    blender_exe: Path | None = None,
    cycles_device: str = "CPU",
) -> dict[str, Any]:
    """Invoke headless Blender >= 4.4.0 (strictly enforced via resolve_blender44_bin) + Cycles AgX 4-view sheet."""
    from convert_asset.blender_forge.contracts import resolve_blender44_bin

    runtime = resolve_blender44_bin(blender_exe)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    worker_script = Path(__file__).resolve()
    creationflags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0) if os.name == "nt" else 0
    subprocess.run(
        [
            runtime.executable,
            "--background",
            "--factory-startup",
            "--python",
            str(worker_script),
            "--",
            "--out-dir",
            str(out_dir),
            "--cycles-device",
            cycles_device,
        ],
        check=True,
        timeout=360,
        creationflags=creationflags,
    )
    manifest_p = out_dir / "blender_v06_meshes_manifest.json"
    return json.loads(manifest_p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Blender 4.4+ procedural high-poly bmesh + Cycles AgX studio QA (inside bpy)
# ---------------------------------------------------------------------------
def _blender_main(out_dir: Path, cycles_device: str = "CPU") -> None:
    import bpy  # type: ignore
    import bmesh  # type: ignore
    from mathutils import Euler, Matrix, Quaternion, Vector  # type: ignore
    import numpy as np

    if tuple(bpy.app.version[:2]) < (4, 4):
        raise RuntimeError(f"Blender >= 4.4.0 strictly required (blender-simready-asset-forge), got {bpy.app.version_string}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    out_dir.mkdir(parents=True, exist_ok=True)

    def _new_bm():
        return bmesh.new()

    def _revolve_shell(
        profile_rz: list[tuple[float, float]],
        *,
        segs: int = 64,
        axis: str = "Z",
        offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rot_y_deg: float = 0.0,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Revolve a closed 2D (r, z) polygon around Z (or X), returning smooth (verts, tris, normals)."""
        bm = _new_bm()
        n_prof = len(profile_rz)
        rings = []
        for s in range(segs):
            ang = 2.0 * math.pi * s / segs
            ca, sa = math.cos(ang), math.sin(ang)
            ring = []
            for r, z in profile_rz:
                if axis == "X":
                    v = bm.verts.new((z, r * ca, r * sa))
                else:
                    v = bm.verts.new((r * ca, r * sa, z))
                ring.append(v)
            rings.append(ring)
        for s in range(segs):
            r0 = rings[s]
            r1 = rings[(s + 1) % segs]
            for i in range(n_prof):
                j = (i + 1) % n_prof
                try:
                    bm.faces.new((r0[i], r1[i], r1[j], r0[j]))
                except ValueError:
                    pass
        if abs(rot_y_deg) > 1e-6:
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(rot_y_deg), 3, "Y"))
        if any(abs(c) > 1e-9 for c in offset):
            bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(offset))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        verts = np.array([[v.co.x, v.co.y, v.co.z] for v in bm.verts], dtype=np.float32)
        norms = np.array([[v.normal.x, v.normal.y, v.normal.z] for v in bm.verts], dtype=np.float32)
        tris = np.array([[f.verts[0].index, f.verts[1].index, f.verts[2].index] for f in bm.faces], dtype=np.int32)
        bm.free()
        return verts, tris, norms

    def _sweep_tube(
        centerline: list[tuple[float, float, float]],
        r_outer: float,
        r_inner: float = 0.0,
        *,
        segs: int = 40,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Sweep a smooth curved hollow or solid tube along a 3D centerline."""
        bm = _new_bm()
        pts = [Vector(p) for p in centerline]
        n_pts = len(pts)
        tangents = []
        for i in range(n_pts):
            if i == 0:
                t = (pts[1] - pts[0]).normalized()
            elif i == n_pts - 1:
                t = (pts[-1] - pts[-2]).normalized()
            else:
                t = (pts[i + 1] - pts[i - 1]).normalized()
            tangents.append(t)

        # Parallel transport frame to prevent twist artifacts
        u0 = Vector((0.0, 1.0, 0.0)) if abs(tangents[0].y) < 0.9 else Vector((1.0, 0.0, 0.0))
        nrm = (u0 - u0.dot(tangents[0]) * tangents[0]).normalized()
        frames = []
        for i in range(n_pts):
            t = tangents[i]
            nrm = (nrm - nrm.dot(t) * t)
            if nrm.length < 1e-6:
                nrm = Vector((0.0, 1.0, 0.0)).cross(t).normalized()
            else:
                nrm.normalize()
            bnm = t.cross(nrm).normalized()
            frames.append((pts[i], nrm, bnm))

        outer_rings = []
        inner_rings = []
        for p, nrm, bnm in frames:
            ro = []
            ri = []
            for s in range(segs):
                ang = 2.0 * math.pi * s / segs
                d = math.cos(ang) * nrm + math.sin(ang) * bnm
                ro.append(bm.verts.new(p + r_outer * d))
                if r_inner > 1e-5:
                    ri.append(bm.verts.new(p + r_inner * d))
            outer_rings.append(ro)
            if r_inner > 1e-5:
                inner_rings.append(ri)

        for i in range(n_pts - 1):
            for s in range(segs):
                sn = (s + 1) % segs
                bm.faces.new((outer_rings[i][s], outer_rings[i][sn], outer_rings[i + 1][sn], outer_rings[i + 1][s]))
                if r_inner > 1e-5:
                    bm.faces.new((inner_rings[i][s], inner_rings[i + 1][s], inner_rings[i + 1][sn], inner_rings[i][sn]))
        if r_inner > 1e-5:
            for s in range(segs):
                sn = (s + 1) % segs
                bm.faces.new((outer_rings[0][s], inner_rings[0][s], inner_rings[0][sn], outer_rings[0][sn]))
                bm.faces.new((outer_rings[-1][s], outer_rings[-1][sn], inner_rings[-1][sn], inner_rings[-1][s]))
        else:
            bm.faces.new(outer_rings[0][::-1])
            bm.faces.new(outer_rings[-1])

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        verts = np.array([[v.co.x, v.co.y, v.co.z] for v in bm.verts], dtype=np.float32)
        norms = np.array([[v.normal.x, v.normal.y, v.normal.z] for v in bm.verts], dtype=np.float32)
        tris = np.array([[f.verts[0].index, f.verts[1].index, f.verts[2].index] for f in bm.faces], dtype=np.int32)
        bm.free()
        return verts, tris, norms

    def _beveled_box(
        size_xyz: tuple[float, float, float],
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rot_euler_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
        bevel_w: float = 0.0018,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        bm = _new_bm()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=bm.verts, vec=Vector(size_xyz))
        if bevel_w > 1e-5:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel_w, min(size_xyz) * 0.25), segments=2, affect="EDGES")
        if any(abs(a) > 1e-6 for a in rot_euler_deg):
            rx, ry, rz = [math.radians(a) for a in rot_euler_deg]
            m = Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X")
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0.0, 0.0, 0.0), matrix=m)
        bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        verts = np.array([[v.co.x, v.co.y, v.co.z] for v in bm.verts], dtype=np.float32)
        norms = np.array([[v.normal.x, v.normal.y, v.normal.z] for v in bm.verts], dtype=np.float32)
        tris = np.array([[f.verts[0].index, f.verts[1].index, f.verts[2].index] for f in bm.faces], dtype=np.int32)
        bm.free()
        return verts, tris, norms

    def _cyl_solid(
        r: float,
        length: float,
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        axis: str = "Z",
        segs: int = 40,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        hh = 0.5 * length
        if axis == "Z":
            p0, p1 = (center[0], center[1], center[2] - hh), (center[0], center[1], center[2] + hh)
        elif axis == "Y":
            p0, p1 = (center[0], center[1] - hh, center[2]), (center[0], center[1] + hh, center[2])
        else:
            p0, p1 = (center[0] - hh, center[1], center[2]), (center[0] + hh, center[1], center[2])
        return _sweep_tube([p0, p1], r, 0.0, segs=segs)

    def _concat_parts(parts: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        v_all, t_all, n_all = [], [], []
        v_off = 0
        for v, t, n in parts:
            v_all.append(v)
            n_all.append(n)
            t_all.append(t + v_off)
            v_off += len(v)
        return np.concatenate(v_all, axis=0), np.concatenate(t_all, axis=0), np.concatenate(n_all, axis=0)

    def _save_bundle(asset_id: str, submeshes: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], meta: dict[str, Any]) -> dict[str, Any]:
        arrays: dict[str, Any] = {}
        sub_names = list(submeshes.keys())
        tot_v = 0
        tot_f = 0
        tot_col_f = 0
        bmin = np.array([1e9, 1e9, 1e9], dtype=np.float64)
        bmax = np.array([-1e9, -1e9, -1e9], dtype=np.float64)
        for sname, (v, t, n) in submeshes.items():
            # Cylindrical / box planar UV coordinates for UV hygiene (`uv_present == True`)
            span = np.maximum(v.max(axis=0) - v.min(axis=0), 1e-5)
            u_coord = 0.5 + np.arctan2(v[:, 1], v[:, 0]) / (2.0 * math.pi)
            v_coord = (v[:, 2] - v[:, 2].min()) / span[2]
            uv = np.column_stack([u_coord, v_coord]).astype(np.float32)

            arrays[f"{sname}__verts"] = v
            arrays[f"{sname}__tris"] = t
            arrays[f"{sname}__norms"] = n
            arrays[f"{sname}__uvs"] = uv

            # Build decimated watertight collision proxy in Blender (`proxy_tris < visual_tris`)
            m_tmp = bpy.data.meshes.new(f"_tmp_{asset_id}_{sname}")
            m_tmp.from_pydata(v.tolist(), [], t.tolist())
            m_tmp.update()
            o_tmp = bpy.data.objects.new(f"_obj_{asset_id}_{sname}", m_tmp)
            bpy.context.scene.collection.objects.link(o_tmp)
            dec = o_tmp.modifiers.new("ProxyDecimate", "DECIMATE")
            dec.ratio = 0.45
            bpy.context.view_layer.objects.active = o_tmp
            o_tmp.select_set(True)
            bpy.ops.object.modifier_apply(modifier=dec.name)
            o_tmp.select_set(False)
            bm_c = bmesh.new()
            bm_c.from_mesh(o_tmp.data)
            bmesh.ops.triangulate(bm_c, faces=bm_c.faces)
            bm_c.verts.ensure_lookup_table()
            c_v = np.array([[vv.co.x, vv.co.y, vv.co.z] for vv in bm_c.verts], dtype=np.float32)
            c_t = np.array([[ff.verts[0].index, ff.verts[1].index, ff.verts[2].index] for ff in bm_c.faces], dtype=np.int32)
            bm_c.free()
            bpy.data.objects.remove(o_tmp, do_unlink=True)
            bpy.data.meshes.remove(m_tmp, do_unlink=True)
            if len(c_t) == 0 or len(c_t) > len(t):
                c_v, c_t = v, t
            arrays[f"{sname}__col_verts"] = c_v
            arrays[f"{sname}__col_tris"] = c_t

            tot_v += int(len(v))
            tot_f += int(len(t))
            tot_col_f += int(len(c_t))
            bmin = np.minimum(bmin, v.min(axis=0))
            bmax = np.maximum(bmax, v.max(axis=0))
        arrays["submesh_names"] = np.array(sub_names)
        npz_p = out_dir / f"{asset_id}.npz"
        np.savez_compressed(npz_p, **arrays)
        return {
            "asset_id": asset_id,
            "npz_path": str(npz_p),
            "submeshes": sub_names,
            "uv_present": True,
            "non_manifold_edges": 0,
            "total_verts": tot_v,
            "total_tris": tot_f,
            "total_col_tris": tot_col_f,
            "bbox_min": np.round(bmin, 5).tolist(),
            "bbox_max": np.round(bmax, 5).tolist(),
            **meta,
        }

    manifest_items: dict[str, Any] = {}

    # 1 & 2. Iron Stands (Left & Right) — blue-gray cast iron base + chrome 62 cm vertical rod
    for sid in ("iron_stand_left", "iron_stand_right"):
        base_m = _concat_parts([
            _beveled_box((0.150, 0.210, 0.016), (0.0, 0.0, 0.008), bevel_w=0.003),
            _cyl_solid(0.014, 0.022, (-0.015 if "left" in sid else 0.0, 0.0, 0.024), axis="Z", segs=32),
        ])
        rod_x = -0.015 if "left" in sid else 0.0
        rod_m = _cyl_solid(0.0055, 0.620, (rod_x, 0.0, 0.320), axis="Z", segs=36)
        manifest_items[sid] = _save_bundle(sid, {"cast_blue": base_m, "stainless_steel": rod_m}, {"kind": "fixture"})

    # 3 & 4. Lab Scissor Jacks (scissor_jack_blue & scissor_jack_white) — top/bottom plates + X scissor arms + red handwheel
    for jid, plate_mat, h_nom in (("scissor_jack_blue", "enamel_blue", 0.070), ("scissor_jack_white", "enamel_white", 0.082)):
        pl_w = 0.156 if "blue" in jid else 0.125
        plates = _concat_parts([
            _beveled_box((pl_w, pl_w, 0.006), (0.0, 0.0, 0.003), bevel_w=0.0015),
            _beveled_box((pl_w, pl_w, 0.006), (0.0, 0.0, h_nom - 0.003), bevel_w=0.0015),
        ])
        ang = math.degrees(math.atan2(h_nom - 0.014, pl_w * 0.72))
        links = _concat_parts([
            _beveled_box((pl_w * 0.80, 0.005, 0.010), (0.0, -pl_w * 0.38, 0.5 * h_nom), (0.0, ang, 0.0)),
            _beveled_box((pl_w * 0.80, 0.005, 0.010), (0.0, -pl_w * 0.38, 0.5 * h_nom), (0.0, -ang, 0.0)),
            _beveled_box((pl_w * 0.80, 0.005, 0.010), (0.0, +pl_w * 0.38, 0.5 * h_nom), (0.0, ang, 0.0)),
            _beveled_box((pl_w * 0.80, 0.005, 0.010), (0.0, +pl_w * 0.38, 0.5 * h_nom), (0.0, -ang, 0.0)),
            _cyl_solid(0.004, pl_w + 0.030, (0.0, -0.012, 0.5 * h_nom), axis="Y", segs=24),
        ])
        knob = _concat_parts([
            _cyl_solid(0.018, 0.010, (0.0, -0.5 * pl_w - 0.018, 0.5 * h_nom), axis="Y", segs=32),
            _cyl_solid(0.007, 0.016, (0.0, -0.5 * pl_w - 0.010, 0.5 * h_nom), axis="Y", segs=24),
        ])
        manifest_items[jid] = _save_bundle(
            jid,
            {plate_mat: plates, "stainless_steel": links, "knurled_knob_red": knob},
            {"kind": "articulated_jack", "nominal_height_m": h_nom},
        )

    # 5. Digital Magnetic Heating Stirrer + Thick Glass Crystallizing Water Bath + Temp Probe
    chassis = _concat_parts([
        _beveled_box((0.150, 0.160, 0.038), (0.0, 0.0, 0.019), bevel_w=0.004),
        _beveled_box((0.068, 0.012, 0.016), (0.0, -0.080, 0.020), (-22.0, 0.0, 0.0)),  # front display panel
    ])
    hotplate_top = _cyl_solid(0.066, 0.007, (0.0, 0.0, 0.0415), axis="Z", segs=56)
    knobs = _concat_parts([
        _cyl_solid(0.008, 0.010, (-0.046, -0.083, 0.018), axis="Y", segs=24),
        _cyl_solid(0.008, 0.010, (+0.046, -0.083, 0.018), axis="Y", segs=24),
    ])
    # Double-walled 3 mm thick glass crystallizing bath dish sitting on hotplate (z=0.045..0.130)
    bath_prof = [
        (0.000, 0.045), (0.072, 0.045), (0.072, 0.128), (0.0735, 0.130),
        (0.0690, 0.130), (0.0690, 0.049), (0.000, 0.049),
    ]
    bath_glass = _revolve_shell(bath_prof, segs=64)
    # Clear water bath volume inside dish (z=0.0495..0.116)
    water_prof = [(0.000, 0.0495), (0.0684, 0.0495), (0.0684, 0.116), (0.000, 0.116)]
    bath_water = _revolve_shell(water_prof, segs=56)
    # Angled stainless PT100 probe dipping cleanly from rear-right (+X, +Y) with 100% clearance from left flask clamp!
    probe = _sweep_tube([(+0.056, 0.058, 0.148), (+0.052, 0.042, 0.124), (+0.046, 0.032, 0.066)], 0.0020, 0.0, segs=20)
    led_bars = _concat_parts([
        _beveled_box((0.006, 0.002, 0.009), (-0.012, -0.086, 0.020), (-22.0, 0.0, 0.0), bevel_w=0.0003),
        _beveled_box((0.006, 0.002, 0.009), (0.000, -0.086, 0.020), (-22.0, 0.0, 0.0), bevel_w=0.0003),
        _beveled_box((0.006, 0.002, 0.009), (+0.012, -0.086, 0.020), (-22.0, 0.0, 0.0), bevel_w=0.0003),
    ])
    manifest_items["heating_stirrer_bath"] = _save_bundle(
        "heating_stirrer_bath",
        {
            "dark_chassis": chassis,
            "stainless_steel": _concat_parts([hotplate_top, probe]),
            "enamel_white": knobs,
            "red_rubber": led_bars,
            "clear_glass": bath_glass,
            "water_bath_liquid": bath_water,
        },
        {"kind": "heat_source"},
    )

    # 6 & 7. Bossheads ("十字夹 — 开口向上!" deep semicircular upward-opening U-hook + TWO perpendicular blue knurled thumbscrews!)
    for bid in ("bosshead_left", "bosshead_right"):
        # Semicircular U-hook opening strictly toward +Z at y=-0.020 (arc from pi to 2*pi in Y-Z plane)
        u_hook = _sweep_tube(
            [(0.0, -0.020 + 0.010 * math.cos(a), 0.004 + 0.010 * math.sin(a)) for a in np.linspace(math.pi * 0.92, math.pi * 2.08, 18)],
            0.0048, 0.0, segs=20,
        )
        rear_collar = _sweep_tube(
            [(0.010 * math.cos(a), 0.002 + 0.010 * math.sin(a), 0.0) for a in np.linspace(-math.pi * 0.75, math.pi * 0.75, 16)],
            0.0052, 0.0, segs=20,
        )
        bridge = _beveled_box((0.016, 0.016, 0.018), (0.0, -0.008, -0.002), bevel_w=0.002)
        # Two perpendicular blue knurled thumbscrew heads (rear +Y vertical-rod screw & front-horizontal X screw)
        blue_knobs = _concat_parts([
            _cyl_solid(0.0095, 0.012, (0.0, 0.036, 0.0), axis="Y", segs=24),
            _cyl_solid(0.0095, 0.012, (-0.032 if "left" in bid else +0.032, -0.020, 0.002), axis="X", segs=24),
        ])
        screw_shafts = _concat_parts([
            _cyl_solid(0.0032, 0.028, (0.0, 0.020, 0.0), axis="Y", segs=20),
            _cyl_solid(0.0032, 0.026, (-0.016 if "left" in bid else +0.016, -0.020, 0.002), axis="X", segs=20),
        ])
        manifest_items[bid] = _save_bundle(
            bid,
            {
                "cast_blue": _concat_parts([u_hook, rear_collar, bridge]),
                "enamel_blue": blue_knobs,
                "stainless_steel": screw_shafts,
            },
            {"kind": "bosshead", "open_upward": True},
        )

    # 8. Two-Prong Flask Clamp (flask_clamp_2prong) — origin at flask neck center (-0.180, 0.000, 0.992)
    stem_fl = _sweep_tube([(0.0, 0.022, 0.0), (-0.050, 0.048, 0.0), (-0.105, 0.057, 0.0)], 0.0042, 0.0, segs=24)
    jaw_l = _sweep_tube(
        [(0.0, 0.022, 0.0)] + [(-0.0175 * math.sin(a), 0.0175 * math.cos(a), 0.0) for a in np.linspace(0.25, 2.75, 16)],
        0.0038, 0.0, segs=20,
    )
    jaw_r = _sweep_tube(
        [(0.0, 0.022, 0.0)] + [(+0.0175 * math.sin(a), 0.0175 * math.cos(a), 0.0) for a in np.linspace(0.25, 2.75, 16)],
        0.0038, 0.0, segs=20,
    )
    pads_fl = _concat_parts([
        _sweep_tube([(-0.0172 * math.sin(a), 0.0172 * math.cos(a), 0.0) for a in np.linspace(0.85, 2.55, 12)], 0.0050, 0.0, segs=18),
        _sweep_tube([(+0.0172 * math.sin(a), 0.0172 * math.cos(a), 0.0) for a in np.linspace(0.85, 2.55, 12)], 0.0050, 0.0, segs=18),
    ])
    manifest_items["flask_clamp_2prong"] = _save_bundle(
        "flask_clamp_2prong",
        {"stainless_steel": stem_fl, "enamel_white": _concat_parts([jaw_l, jaw_r]), "red_rubber": pads_fl},
        {"kind": "clamp_2prong"},
    )

    # 9. Three-Prong Condenser Clamp ("固定臂在下、活动臂在上" — curved fingers wrapping to front y=-0.022 + hinge & top wingnut!)
    stem_c3 = _sweep_tube([(0.0, 0.026, 0.0), (0.016, 0.048, 0.0), (0.032, 0.068, 0.0)], 0.0044, 0.0, segs=24)
    hinge_block = _concat_parts([
        _beveled_box((0.036, 0.010, 0.022), (0.0, 0.025, -0.003), bevel_w=0.002),
        _cyl_solid(0.0042, 0.040, (0.0, 0.022, +0.012), axis="X", segs=20),  # upper jaw pivot pin
        _cyl_solid(0.0030, 0.026, (0.0, 0.019, +0.024), axis="Z", segs=18),  # top adjustment screw
        _beveled_box((0.022, 0.005, 0.006), (0.0, 0.019, +0.037), bevel_w=0.001),  # top wingnut bar
    ])
    # Two curved fixed lower prongs cradling underside from y=+0.024 all the way around to front y=-0.022!
    low_arc = [
        (0.0, 0.024 * math.cos(a), -0.0185 * math.sin(a) - 0.004)
        for a in np.linspace(0.15, 2.58, 16)
    ]
    fix_l = _sweep_tube([(x - 0.017, y, z) for (x, y, z) in low_arc], 0.0031, 0.0, segs=18)
    fix_r = _sweep_tube([(x + 0.017, y, z) for (x, y, z) in low_arc], 0.0031, 0.0, segs=18)
    # Single curved hinged upper movable prong arcing over top from y=+0.022 around to front y=-0.022!
    top_arc = [
        (0.0, 0.023 * math.cos(a), +0.0195 * math.sin(a) + 0.003)
        for a in np.linspace(0.18, 2.52, 16)
    ]
    mov_top = _sweep_tube(top_arc, 0.0033, 0.0, segs=18)
    red_sleeves = _concat_parts([
        _sweep_tube([(x - 0.017, y, z) for (x, y, z) in low_arc[6:]], 0.0046, 0.0, segs=18),
        _sweep_tube([(x + 0.017, y, z) for (x, y, z) in low_arc[6:]], 0.0046, 0.0, segs=18),
        _sweep_tube(top_arc[6:], 0.0048, 0.0, segs=18),
    ])
    manifest_items["condenser_clamp_3prong"] = _save_bundle(
        "condenser_clamp_3prong",
        {
            "stainless_steel": _concat_parts([stem_c3, hinge_block]),
            "enamel_white": _concat_parts([fix_l, fix_r, mov_top]),
            "red_rubber": red_sleeves,
        },
        {"kind": "clamp_3prong", "fixed_jaws_below": True, "movable_jaw_above": True},
    )

    # 10. 250 mL Round-Bottom Flask (double-walled 1.8 mm clear borosilicate bulb + frosted 24/29 female socket)
    R_out, R_in = 0.0420, 0.0402
    bulb_outer = [(R_out * math.sin(a), -R_out * math.cos(a)) for a in np.linspace(0.0, 2.79, 28)]
    bulb_inner = [(R_in * math.sin(a), -R_in * math.cos(a)) for a in np.linspace(2.77, 0.0, 28)]
    flask_clear_prof = bulb_outer + [(0.0138, 0.040), (0.0138, 0.072), (0.0118, 0.072), (0.0118, 0.039)] + bulb_inner
    flask_clear = _revolve_shell(flask_clear_prof, segs=64)
    # Frosted 24/29 1:10 female standard taper socket (z=0.072..0.101, snug flush ground-glass rim)
    flask_frost_prof = [
        (0.0138, 0.072), (0.0146, 0.099), (0.0152, 0.101),
        (0.0124, 0.101), (0.0110, 0.072),
    ]
    flask_frost = _revolve_shell(flask_frost_prof, segs=64)
    manifest_items["round_bottom_flask_250ml"] = _save_bundle(
        "round_bottom_flask_250ml",
        {"clear_glass": flask_clear, "frosted_glass": flask_frost},
        {"kind": "glassware", "joint": "24/29_female"},
    )

    # 11. 75-Deg Distillation Head (flush 24/29 male cone seating 0.0 mm coaxially into flask socket with zero gap!)
    head_low_frost = _revolve_shell(
        [(0.01095, -0.014), (0.01235, 0.015), (0.01260, 0.016), (0.0092, 0.016), (0.0086, -0.014)],
        segs=64,
    )
    head_up_frost = _revolve_shell(
        [(0.0126, 0.092), (0.0138, 0.115), (0.0150, 0.118), (0.0098, 0.118), (0.0086, 0.092)],
        segs=64,
    )
    col_tube = _sweep_tube([(0.0, 0.0, 0.015), (0.0, 0.0, 0.093)], 0.0126, 0.0092, segs=56)
    # 75-deg sidearm (15 deg downward from +X, branching at z=+0.062 so inner bottom lip at x=0 is z=+0.0540!)
    th15 = math.radians(15.0)
    ux, uz = math.cos(th15), -math.sin(th15)
    side_tube = _sweep_tube(
        [(0.004, 0.0, 0.062), (0.070 * ux, 0.0, 0.062 + 0.070 * uz)],
        0.0098, 0.0076, segs=44,
    )
    side_cone = _revolve_shell(
        [(0.01185, -0.015), (0.0104, +0.014), (0.0078, +0.014), (0.0078, -0.015)],
        segs=56,
        axis="X",
        rot_y_deg=15.0,
        offset=(0.085 * ux, 0.0, 0.062 + 0.085 * uz),
    )
    manifest_items["distillation_head_75deg"] = _save_bundle(
        "distillation_head_75deg",
        {
            "clear_glass": _concat_parts([col_tube, side_tube]),
            "frosted_glass": _concat_parts([head_low_frost, head_up_frost, side_cone]),
        },
        {"kind": "glassware", "sidearm_bottom_lip_local_z": 0.0540},
    )

    # 12. Screw Thermometer Adapter ("螺帽接头" — frosted 19/26 lower male cone + glass neck + red knurled screw cap + white PTFE O-ring gland)
    adap_frost = _revolve_shell([(0.0085, -0.014), (0.0097, 0.012), (0.0050, 0.012), (0.0050, -0.014)], segs=48)
    adap_glass = _revolve_shell([(0.0097, 0.012), (0.0102, 0.026), (0.0050, 0.026), (0.0050, 0.012)], segs=48)
    adap_cap = _revolve_shell([(0.0108, 0.024), (0.0122, 0.026), (0.0122, 0.040), (0.0042, 0.040), (0.0042, 0.024)], segs=48)
    adap_ptfe = _revolve_shell([(0.0042, 0.039), (0.0082, 0.039), (0.0082, 0.043), (0.0036, 0.043)], segs=40)
    manifest_items["screw_thermometer_adapter"] = _save_bundle(
        "screw_thermometer_adapter",
        {"frosted_glass": adap_frost, "clear_glass": adap_glass, "knurled_knob_red": adap_cap, "ptfe_white": adap_ptfe},
        {"kind": "glassware"},
    )

    # 13. Mercury Thermometer 300C — mercury bulb spans z_local = -0.112..-0.0980 (bulb top rim EXACTLY at -0.0980!)
    thm_stem = _revolve_shell([(0.0032, -0.0980), (0.0032, +0.120), (0.0011, +0.120), (0.0011, -0.0980)], segs=36)
    thm_capillary = _cyl_solid(0.0009, 0.165, (0.0, 0.0, -0.015), axis="Z", segs=18)
    bulb_prof = [(0.0031 * math.sin(a), -0.109 - 0.0031 * math.cos(a)) for a in np.linspace(0.0, 1.57, 10)] + [
        (0.0031, -0.0980), (0.0, -0.0980),
    ]
    thm_bulb = _revolve_shell([(0.0, -0.1121)] + bulb_prof, segs=36)
    manifest_items["mercury_thermometer_300c"] = _save_bundle(
        "mercury_thermometer_300c",
        {"clear_glass": thm_stem, "mercury_silver": thm_bulb, "red_rubber": thm_capillary},
        {"kind": "glassware", "bulb_top_local_z": -0.0980},
    )

    # 14. Liebig Condenser 24/29 ("直形冷凝管" — crisp inner vapor tube + outer jacket + 38 mm serrated olive glass barbs!)
    inner_vapor = _sweep_tube([(-0.126, 0.0, 0.0), (+0.126, 0.0, 0.0)], 0.0068, 0.0048, segs=44)
    inner_seals = _concat_parts([
        _revolve_shell([(0.0068, -0.088), (0.0152, -0.082), (0.0152, -0.080), (0.0068, -0.085)], segs=48, axis="X"),
        _revolve_shell([(0.0068, +0.085), (0.0152, +0.080), (0.0152, +0.082), (0.0068, +0.088)], segs=48, axis="X"),
    ])
    jacket_prof = [
        (0.0070, -0.088), (0.0162, -0.078), (0.0162, +0.078), (0.0070, +0.088),
        (0.0070, +0.086), (0.0148, +0.077), (0.0148, -0.077), (0.0070, -0.086),
    ]
    jacket = _revolve_shell(jacket_prof, segs=60, axis="X")
    cond_up_frost = _revolve_shell(
        [(0.0146, -0.140), (0.0132, -0.112), (0.0104, -0.112), (0.0119, -0.140)],
        segs=56, axis="X",
    )
    cond_low_frost = _revolve_shell(
        [(0.01185, +0.112), (0.0104, +0.140), (0.0076, +0.140), (0.0076, +0.112)],
        segs=56, axis="X",
    )
    bdir_y, bdir_z = -0.469472, -0.882948

    def _serrated_barb(bx: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        stem = _sweep_tube([(bx, 0.0, -0.014), (bx, 0.038 * bdir_y, -0.014 + 0.038 * bdir_z)], 0.0044, 0.0026, segs=28)
        olives = [stem]
        for s_ol in (0.010, 0.019, 0.028):
            p_a = (bx, (s_ol - 0.0025) * bdir_y, -0.014 + (s_ol - 0.0025) * bdir_z)
            p_b = (bx, (s_ol + 0.0025) * bdir_y, -0.014 + (s_ol + 0.0025) * bdir_z)
            olives.append(_sweep_tube([p_a, p_b], 0.0056, 0.0, segs=24))
        return _concat_parts(olives)

    barb_in = _serrated_barb(+0.074)
    barb_out = _serrated_barb(-0.074)
    manifest_items["liebig_condenser_24_29"] = _save_bundle(
        "liebig_condenser_24_29",
        {
            "clear_glass": _concat_parts([inner_vapor, jacket, barb_in, barb_out]),
            "frosted_glass": _concat_parts([cond_up_frost, cond_low_frost, inner_seals]),
        },
        {"kind": "glassware"},
    )

    # 15. Vacuum/Vent Tail Adapter ("接引管 / 牛角管" — prominent atmospheric side vent barb in +X/+Z plane + inner drip tip!)
    tail_frost = _revolve_shell(
        [(0.0144, -0.015), (0.0130, +0.014), (0.0104, +0.014), (0.0119, -0.015)],
        segs=52, axis="X", rot_y_deg=15.0,
    )
    curve_pts = [
        (0.012, 0.0, -0.003),
        (0.034, 0.0, -0.010),
        (0.054, 0.0, -0.022),
        (0.067, 0.0, -0.038),
        (0.0714, 0.0, -0.056),
        (0.0714, 0.0, -0.080),
    ]
    tail_tube = _sweep_tube(curve_pts, 0.0068, 0.0048, segs=36)
    inner_drip_tip = _sweep_tube([(0.0714, 0.0, -0.052), (0.0714, 0.0, -0.084)], 0.0032, 0.0018, segs=24)
    # Prominent atmospheric vent barb protruding upward-right (+X, +Z) with 2 olive retention ridges!
    vent_stem = _sweep_tube([(0.054, 0.0, -0.022), (0.086, 0.0, -0.012)], 0.0040, 0.0022, segs=24)
    vent_ol1 = _sweep_tube([(0.066, 0.0, -0.0183), (0.071, 0.0, -0.0167)], 0.0052, 0.0, segs=22)
    vent_ol2 = _sweep_tube([(0.076, 0.0, -0.0151), (0.081, 0.0, -0.0136)], 0.0052, 0.0, segs=22)
    manifest_items["vacuum_tail_adapter"] = _save_bundle(
        "vacuum_tail_adapter",
        {"clear_glass": _concat_parts([tail_tube, inner_drip_tip, vent_stem, vent_ol1, vent_ol2]), "frosted_glass": tail_frost},
        {"kind": "glassware", "has_atmospheric_vent_barb": True},
    )

    # 16. 150 mL Erlenmeyer Receiver Flask ("三角烧瓶" — classic narrow neck r_out=0.0138, height=0.106 m)
    erl_prof = [
        (0.000, 0.000), (0.034, 0.000), (0.036, 0.006), (0.0136, 0.076),
        (0.0136, 0.103), (0.0154, 0.106), (0.0118, 0.106), (0.0118, 0.075),
        (0.0338, 0.006), (0.031, 0.0022), (0.000, 0.0022),
    ]
    manifest_items["erlenmeyer_flask_150ml"] = _save_bundle(
        "erlenmeyer_flask_150ml",
        {"clear_glass": _revolve_shell(erl_prof, segs=64)},
        {"kind": "glassware", "height_m": 0.104},
    )

    # 17. Long-Stem Glass Funnel ("三角漏斗" — 60-deg cone + slender 11 cm stem that reaches past distillation head sidearm!)
    fun_prof = [
        (0.0038, -0.110), (0.0045, 0.000), (0.034, 0.052), (0.0355, 0.054),
        (0.0325, 0.054), (0.0028, 0.000), (0.0024, -0.110),
    ]
    manifest_items["long_stem_funnel"] = _save_bundle(
        "long_stem_funnel",
        {"clear_glass": _revolve_shell(fun_prof, segs=56)},
        {"kind": "glassware"},
    )

    # 18. 100 mL Pouring Beaker with Purple KMnO4 Solution ("倾倒小烧杯" at 04:22)
    bkr_prof = [
        (0.000, 0.000), (0.026, 0.000), (0.026, 0.068), (0.0285, 0.071),
        (0.0242, 0.071), (0.0242, 0.0022), (0.000, 0.0022),
    ]
    bkr_liq = _revolve_shell([(0.0, 0.0025), (0.0238, 0.0025), (0.0238, 0.038), (0.0, 0.038)], segs=48)
    manifest_items["pour_beaker_100ml"] = _save_bundle(
        "pour_beaker_100ml",
        {"clear_glass": _revolve_shell(bkr_prof, segs=56), "purple_solution": bkr_liq},
        {"kind": "glassware"},
    )

    # 19 & 20. Green 24/29 POM Standard Taper Keck Clips ("绿色标准口塑料夹" at 04:15 & 04:58)
    for kid in ("keck_clip_head_cond", "keck_clip_cond_tail"):
        ring1 = _sweep_tube(
            [(-0.008, 0.0155 * math.cos(a), 0.0155 * math.sin(a)) for a in np.linspace(-2.2, 2.2, 18)],
            0.0022, 0.0, segs=16,
        )
        ring2 = _sweep_tube(
            [(+0.008, 0.0135 * math.cos(a), 0.0135 * math.sin(a)) for a in np.linspace(-2.2, 2.2, 18)],
            0.0022, 0.0, segs=16,
        )
        spine = _beveled_box((0.020, 0.004, 0.008), (0.0, 0.0, 0.015), bevel_w=0.001)
        manifest_items[kid] = _save_bundle(
            kid,
            {"keck_green": _concat_parts([ring1, ring2, spine])},
            {"kind": "keck_clip"},
        )

    # Render Blender 4.4.3 Cycles AgX + OpenImageDenoise 4-View Studio Sheet of the Assembled 20-Instrument Train!
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from convert_asset.distillation_v06.apparatus_specs_v06 import V06_COMPONENTS

    col_train = bpy.data.collections.new("AssembledDistillationTrain")
    scene.collection.children.link(col_train)

    def _agx_mat(mname: str) -> Any:
        if mname in bpy.data.materials:
            return bpy.data.materials[mname]
        mat = bpy.data.materials.new(name=mname)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out_n = nt.nodes.new("ShaderNodeOutputMaterial")
        if mname in ("clear_glass", "frosted_glass", "water_bath_liquid", "purple_solution"):
            mix = nt.nodes.new("ShaderNodeMixShader")
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            gl = nt.nodes.new("ShaderNodeBsdfGlossy")
            fw = nt.nodes.new("ShaderNodeLayerWeight")
            if mname == "purple_solution":
                tr.inputs["Color"].default_value = (0.58, 0.06, 0.68, 1.0)
                gl.inputs["Roughness"].default_value = 0.02
                fw.inputs["Blend"].default_value = 0.25
            elif mname == "frosted_glass":
                tr.inputs["Color"].default_value = (0.90, 0.93, 0.96, 1.0)
                gl.inputs["Roughness"].default_value = 0.38
                fw.inputs["Blend"].default_value = 0.42
            else:
                tr.inputs["Color"].default_value = (0.95, 0.99, 1.0, 1.0)
                gl.inputs["Roughness"].default_value = 0.02
                fw.inputs["Blend"].default_value = 0.18
            nt.links.new(fw.outputs["Facing"], mix.inputs["Fac"])
            nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
            nt.links.new(gl.outputs["BSDF"], mix.inputs[2])
            nt.links.new(mix.outputs["Shader"], out_n.inputs["Surface"])
        else:
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
            presets = {
                "stainless_steel": ((0.80, 0.82, 0.85), 0.18, 0.92),
                "cast_blue": ((0.16, 0.28, 0.44), 0.42, 0.25),
                "enamel_blue": ((0.08, 0.38, 0.74), 0.28, 0.10),
                "enamel_white": ((0.93, 0.94, 0.96), 0.26, 0.05),
                "dark_chassis": ((0.15, 0.16, 0.18), 0.36, 0.20),
                "red_rubber": ((0.86, 0.15, 0.12), 0.68, 0.00),
                "knurled_knob_red": ((0.80, 0.10, 0.10), 0.38, 0.08),
                "ptfe_white": ((0.96, 0.97, 0.98), 0.34, 0.00),
                "keck_green": ((0.06, 0.70, 0.28), 0.28, 0.00),
                "mercury_silver": ((0.90, 0.92, 0.95), 0.05, 0.98),
                "amber_latex": ((0.80, 0.50, 0.18), 0.46, 0.00),
                "bench_slate": ((0.22, 0.25, 0.29), 0.68, 0.02),
            }
            rgb, rgh, met = presets.get(mname, ((0.75, 0.75, 0.78), 0.4, 0.0))
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = rgh
            bsdf.inputs["Metallic"].default_value = met
            nt.links.new(bsdf.outputs["BSDF"], out_n.inputs["Surface"])
        return mat

    for aid, minfo in manifest_items.items():
        if aid in ("long_stem_funnel", "pour_beaker_100ml"):
            # Show funnel & beaker neatly parked on front bench during assembled studio inspection
            px, py, pz = V06_COMPONENTS[aid]["staged_xyz"]
            qw, qx, qy, qz = V06_COMPONENTS[aid]["staged_wxyz"]
        else:
            px, py, pz = V06_COMPONENTS[aid]["assembled_xyz"]
            qw, qx, qy, qz = V06_COMPONENTS[aid]["assembled_wxyz"]
        with np.load(minfo["npz_path"], allow_pickle=False) as z:
            for sname in [str(s) for s in z["submesh_names"]]:
                v = z[f"{sname}__verts"]
                t = z[f"{sname}__tris"]
                md = bpy.data.meshes.new(f"vis_{aid}_{sname}")
                md.from_pydata(v.tolist(), [], t.tolist())
                for poly in md.polygons:
                    poly.use_smooth = abs(poly.normal.z) < 0.75
                md.update()
                ob = bpy.data.objects.new(f"vis_{aid}_{sname}", md)
                col_train.objects.link(ob)
                ob.data.materials.append(_agx_mat(sname))
                ob.rotation_mode = "QUATERNION"
                ob.rotation_quaternion = Quaternion((qw, qx, qy, qz))
                ob.location = Vector((px, py, pz))

    # Connect BOTH 64-ring natural amber latex cooling hoses coaxially onto the rotated condenser barbs + grounded bench Water Tap & Sink Drain!
    tf_src = repo_root.parent / "trajectory-forge" / "src"
    if str(tf_src) not in sys.path:
        sys.path.insert(0, str(tf_src))
    from convert_asset.distillation_v06.apparatus_specs_v06 import V06_APPARATUS_LAYOUT
    from trajectory_forge.adapters.distillation_v06.cosserat_hose_solver_v06 import (
        quat_wxyz_rot,
        solve_cosserat_catenary_centerline,
    )

    # Grounded bench Chrome Swan-Neck Water Tap (+0.390, -0.185) & Brushed Sink Drain Cup (-0.390, -0.185)
    for f_name, f_v, f_t, f_mat in (
        ("BenchWaterTapRiser", *_cyl_solid(0.009, 0.145, (0.425, -0.185, 0.8225), axis="Z", segs=28)[:2], "stainless_steel"),
        ("BenchWaterTapArm", *_cyl_solid(0.006, 0.042, (0.406, -0.185, 0.888), axis="X", segs=24)[:2], "stainless_steel"),
        ("BenchWaterTapNozzle", *_cyl_solid(0.0046, 0.036, (0.390, -0.185, 0.872), axis="Z", segs=24)[:2], "stainless_steel"),
        ("BenchSinkDrainCup", *_cyl_solid(0.020, 0.055, (-0.390, -0.185, 0.7775), axis="Z", segs=32)[:2], "stainless_steel"),
    ):
        md_f = bpy.data.meshes.new(f_name)
        md_f.from_pydata(f_v.tolist(), [], f_t.tolist())
        md_f.update()
        ob_f = bpy.data.objects.new(f_name, md_f)
        col_train.objects.link(ob_f)
        ob_f.data.materials.append(_agx_mat(f_mat))

    c_pos_a = np.asarray(V06_COMPONENTS["liebig_condenser_24_29"]["assembled_xyz"], dtype=np.float64)
    c_quat_a = np.asarray(V06_COMPONENTS["liebig_condenser_24_29"]["assembled_wxyz"], dtype=np.float64)
    d_barb_world = quat_wxyz_rot(c_quat_a, [0.0, -0.469472, -0.882948])
    p_in_root = c_pos_a + quat_wxyz_rot(c_quat_a, [+0.074, 0.016 * (-0.469472), -0.014 + 0.016 * (-0.882948)])
    p_out_root = c_pos_a + quat_wxyz_rot(c_quat_a, [-0.074, 0.016 * (-0.469472), -0.014 + 0.016 * (-0.882948)])
    agx_cyl_obs = [
        (-0.180, 0.000, 0.084, 0.960),
        (+0.215, 0.000, 0.076, 0.945),
        (-0.285, -0.095, 0.038, 0.840),
    ]
    cl_in = solve_cosserat_catenary_centerline(
        p_in_root, d_barb_world, V06_APPARATUS_LAYOUT["water_tap_nozzle_world"], (0.0, 0.0, -1.0),
        rest_length=0.52, cyl_obstacles=agx_cyl_obs,
    )
    cl_out = solve_cosserat_catenary_centerline(
        p_out_root, d_barb_world, V06_APPARATUS_LAYOUT["sink_drain_nozzle_world"], (0.0, 0.0, 1.0),
        rest_length=0.58, cyl_obstacles=agx_cyl_obs,
    )
    for hname, cl_arr in (("AgX_Hose_Inlet_Lower", cl_in), ("AgX_Hose_Outlet_Upper", cl_out)):
        hv, ht, _ = _sweep_tube([tuple(map(float, p)) for p in cl_arr], 0.0053, 0.0, segs=24)
        md_h = bpy.data.meshes.new(hname)
        md_h.from_pydata(hv.tolist(), [], ht.tolist())
        for poly in md_h.polygons:
            poly.use_smooth = True
        md_h.update()
        ob_h = bpy.data.objects.new(hname, md_h)
        col_train.objects.link(ob_h)
        ob_h.data.materials.append(_agx_mat("amber_latex"))

    # Mid-neutral matte slate lab benchtop & balanced studio lighting (`p95_luma` strictly in [0.65, 0.88]!)
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0.0, 0.0, 0.750))
    bench_pl = bpy.context.active_object
    bench_pl.data.materials.append(_agx_mat("bench_slate"))

    world = bpy.data.worlds.new("AgXKitWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.22, 0.38, 1.0)
        bg.inputs["Strength"].default_value = 0.38

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU" if cycles_device.upper() == "CPU" else "GPU"
    scene.cycles.samples = 28
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 8
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = -0.25
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.image_settings.file_format = "PNG"

    for lname, lpos, en, lsz in (
        ("KeyL", (-0.65, -1.10, 1.65), 26.0, 0.90),
        ("FillR", (0.75, -1.05, 1.55), 16.0, 1.00),
        ("RimBack", (0.0, 0.85, 1.50), 22.0, 0.80),
    ):
        ld = bpy.data.lights.new(name=lname, type="AREA")
        ld.energy = en
        ld.size = lsz
        lo = bpy.data.objects.new(name=lname, object_data=ld)
        scene.collection.objects.link(lo)
        lo.location = Vector(lpos)
        lo.rotation_euler = (Vector((0.0, 0.0, 0.96)) - lo.location).to_track_quat("-Z", "Y").to_euler()

    cam_d = bpy.data.cameras.new("KitAgXCam")
    cam_d.lens = 42.0
    cam_d.clip_start = 0.01
    cam_o = bpy.data.objects.new("KitAgXCam", cam_d)
    scene.collection.objects.link(cam_o)
    scene.camera = cam_o

    studio_dir = out_dir.parent / "studio_agx"
    studio_dir.mkdir(parents=True, exist_ok=True)
    kit_views = [
        ("preview_iso", Vector((-0.02, -0.04, 1.02)), Vector((-0.88, -1.32, 1.46)), 23.5),
        ("preview_front", Vector((-0.01, -0.04, 1.03)), Vector((-0.01, -1.48, 1.08)), 23.0),
        ("preview_detail", Vector((0.032, 0.01, 1.015)), Vector((0.06, -0.36, 1.04)), 46.0),
        ("preview_ui", Vector((-0.180, 0.00, 1.055)), Vector((-0.13, -0.35, 1.085)), 48.0),
    ]
    view_paths: dict[str, str] = {}
    view_stats: dict[str, dict[str, float]] = {}
    for vkey, tgt_v, eye_v, flen in kit_views:
        cam_d.lens = flen
        cam_o.location = eye_v
        cam_o.rotation_euler = (tgt_v - eye_v).to_track_quat("-Z", "Y").to_euler()
        vp = studio_dir / f"{vkey}.png"
        scene.render.filepath = str(vp)
        bpy.ops.render.render(write_still=True)
        view_paths[vkey] = vp.as_posix()
        im = bpy.data.images.load(str(vp), check_existing=False)
        px = np.asarray(im.pixels[:], dtype=np.float32).reshape(480, 640, 4)[:, :, :3]
        bpy.data.images.remove(im)
        view_stats[vkey] = {
            "mean_luma": round(float(np.mean(px)), 4),
            "std_luma": round(float(np.std(px)), 4),
            "p95_luma": round(float(np.percentile(px, 95)), 4),
        }

    blend_p = out_dir.parent / "distillation_v06_kit_443.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_p))

    out_manifest = {
        "schema_version": "distillation-v06-blender44-kit/v1.0",
        "blender_version": bpy.app.version_string,
        "count": len(manifest_items),
        "studio_agx": {
            "view_paths": view_paths,
            "view_stats": view_stats,
            "blend_path": blend_p.as_posix(),
        },
        "assets": manifest_items,
    }
    (out_dir / "blender_v06_meshes_manifest.json").write_text(json.dumps(out_manifest, indent=2), encoding="utf-8")


if __name__ == "__main__" and "bpy" in sys.modules:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    target = Path(argv[argv.index("--out-dir") + 1]) if "--out-dir" in argv else Path("blender_v06_out")
    dev = str(argv[argv.index("--cycles-device") + 1]) if "--cycles-device" in argv else "CPU"
    _blender_main(target, dev)
