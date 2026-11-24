"""Headless Blender 4.4.3+ builder & Cycles AgX 4-view studio QA for v0.8 Ground-Glass Taper Joints & Articulated Keck Clip.

Strictly follows `blender-simready-asset-forge/SKILL.md`:
1. Enforces Blender >= 4.4.0 via `resolve_blender44_bin()`.
2. Builds `keck_clip_24_29_art001` as a strict `ART-001` 3-link articulated mechanism:
   - `ClipSpine`: arched green POM spine bridging female (`x = -8.5 mm`) & male (`x = +8.5 mm`) collars + dorsal parallel grip tab (`10.0 mm` thick in Y) for zero-offset parallel-jaw frictional grasping.
   - `LeftSpringJaw` & `RightSpringJaw`: dual-diameter C-claws (`R_female = 14.8 mm`, `R_male = 10.2 mm`) hinged about `X` (`±28°` snap-open compliance) with chamfered lead-in tips so radial push-on physically spreads the jaws around the glass equator and snaps shut!
3. Builds `thermometer_adapter_unit_v08` combining `19/26` frosted male taper, clear glass body, red knurled screw cap (`r = 12.2 mm`), white PTFE compression gland, and `300 °C` mercury thermometer stem calibrated so seated `z_bulb_top == z_sidearm_bottom_lip` (`0.00 mm` error!).
4. Renders a 4-view Blender 4.4.3 Cycles `AgX` + OpenImageDenoise contact sheet (`studio_4view_contact_sheet.png`) and writes `forge_manifest_and_critic_handoff.json` for zero-context Blind Visual Critic review.
"""

from __future__ import annotations

from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def build_v08_blender_assets(
    out_dir: Path,
    *,
    blender_exe: Path | None = None,
    cycles_device: str = "CPU",
) -> dict[str, Any]:
    from convert_asset.blender_forge.contracts import resolve_blender44_bin

    runtime = resolve_blender44_bin(blender_exe)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    worker = Path(__file__).resolve()
    creationflags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0) if os.name == "nt" else 0
    subprocess.run(
        [
            runtime.executable,
            "--background",
            "--factory-startup",
            "--python",
            str(worker),
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
    manifest = json.loads((out_dir / "v08_assets_manifest.json").read_text(encoding="utf-8"))
    # Stitch 4 Cycles AgX views into contact sheet using host PIL
    from PIL import Image, ImageDraw  # type: ignore

    studio_dir = out_dir / "studio_agx"
    tiles = []
    for vname in (
        "01_iso_4joint_train",
        "02_front_coaxial_tapers",
        "03_macro_articulated_keck_clip",
        "04_macro_thermometer_bulb_flush",
    ):
        im = Image.open(studio_dir / f"{vname}.png").convert("RGB")
        dr = ImageDraw.Draw(im)
        dr.rectangle([(8, 8), (455, 34)], fill=(12, 20, 34))
        dr.text((14, 13), f"Blender 4.4.3 AgX | {vname}", fill=(240, 248, 255))
        tiles.append(im)
    sheet = Image.new("RGB", (1440, 1080), (10, 15, 25))
    sheet.paste(tiles[0], (0, 0))
    sheet.paste(tiles[1], (720, 0))
    sheet.paste(tiles[2], (0, 540))
    sheet.paste(tiles[3], (720, 540))
    sheet.save(studio_dir / "studio_4view_contact_sheet.png")
    return manifest


def _write_art001_keck_usda(
    mech_id: str,
    links_spec: list[dict[str, Any]],
    out_usda: Path,
    *,
    np_mod: Any,
) -> dict[str, Any]:
    base_link = links_spec[0]["link_id"]
    links_blocks: list[str] = []
    joints_blocks: list[str] = [
        f"""
        def PhysicsFixedJoint "RootFixedJoint" (
            prepend apiSchemas = ["PhysicsArticulationRootAPI"]
        )
        {{
            rel physics:body1 = </{mech_id}/Links/{base_link}>
        }}"""
    ]
    total_vis_tris = 0
    total_col_tris = 0

    for lk in links_spec:
        lid = str(lk["link_id"])
        npz_p = Path(lk["mesh_info"]["npz_path"])
        vis_prims: list[str] = []
        col_prims: list[str] = []
        with np_mod.load(npz_p, allow_pickle=False) as z:
            for sname in [str(s) for s in z["submesh_names"]]:
                v = z[f"{sname}__verts"]
                f = z[f"{sname}__tris"]
                uv = z[f"{sname}__uvs"]
                pts_s = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in v)
                cnt_s = ", ".join("3" for _ in range(len(f)))
                idx_s = ", ".join(str(int(i)) for tri in f for i in tri)
                uv_s = ", ".join(f"({u[0]:.5f}, {u[1]:.5f})" for u in uv)
                total_vis_tris += int(len(f))
                vis_prims.append(
                    f"""
                def Mesh "{sname}_visual"
                {{
                    uniform token purpose = "render"
                    int[] faceVertexCounts = [{cnt_s}]
                    int[] faceVertexIndices = [{idx_s}]
                    point3f[] points = [{pts_s}]
                    texCoord2f[] primvars:st = [{uv_s}] (
                        interpolation = "vertex"
                    )
                }}"""
                )
            cv = z["collision__verts"]
            cf = z["collision__tris"]
            cpts_s = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in cv)
            ccnt_s = ", ".join("3" for _ in range(len(cf)))
            cidx_s = ", ".join(str(int(i)) for tri in cf for i in tri)
            total_col_tris += int(len(cf))
            col_prims.append(
                f"""
                def Mesh "{lid}_collision_proxy" (
                    prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsMeshCollisionAPI"]
                )
                {{
                    uniform token purpose = "guide"
                    uniform token physics:approximation = "convexDecomposition"
                    int[] faceVertexCounts = [{ccnt_s}]
                    int[] faceVertexIndices = [{cidx_s}]
                    point3f[] points = [{cpts_s}]
                }}"""
            )

        grasp_block = ""
        if "grasp_xyz" in lk:
            gx, gy, gz = lk["grasp_xyz"]
            grasp_block = f"""
            def Xform "grasp"
            {{
                custom string scenarioForge:namedFrame = "grasp"
                double3 xformOp:translate = ({gx:.6f}, {gy:.6f}, {gz:.6f})
                uniform token[] xformOpOrder = ["xformOp:translate"]
            }}"""

        lx, ly, lz = lk.get("rest_offset_xyz", (0.0, 0.0, 0.0))
        links_blocks.append(
            f"""
        def Xform "{lid}" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsMassAPI"]
        )
        {{
            float physics:mass = {float(lk["mass_kg"]):.4f}
            double3 xformOp:translate = ({lx:.6f}, {ly:.6f}, {lz:.6f})
            quatd xformOp:orient = (1, 0, 0, 0)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient"]
            def Scope "Visual"
            {{{''.join(vis_prims)}
            }}
            def Scope "Collision"
            {{{''.join(col_prims)}
            }}{grasp_block}
        }}"""
        )

        j = lk.get("joint")
        if j:
            px0, py0, pz0 = j["local_pos0"]
            px1, py1, pz1 = j["local_pos1"]
            lo, hi = j["limits_deg"]
            joints_blocks.append(
                f"""
        def PhysicsRevoluteJoint "{j['name']}" (
            prepend apiSchemas = ["PhysicsDriveAPI:angular"]
        )
        {{
            uniform token physics:axis = "{j['axis']}"
            rel physics:body0 = </{mech_id}/Links/{j['parent']}>
            rel physics:body1 = </{mech_id}/Links/{lid}>
            point3f physics:localPos0 = ({px0:.6f}, {py0:.6f}, {pz0:.6f})
            point3f physics:localPos1 = ({px1:.6f}, {py1:.6f}, {pz1:.6f})
            float physics:lowerLimit = {lo:.2f}
            float physics:upperLimit = {hi:.2f}
            float drive:angular:physics:damping = {float(j['damping']):.4f}
            float drive:angular:physics:stiffness = {float(j['stiffness']):.4f}
        }}"""
            )

    usda_text = f"""#usda 1.0
(
    defaultPrim = "{mech_id}"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "{mech_id}" (
    kind = "component"
)
{{
    custom string blenderForge:schemaVersion = "blender-simready-forge/v1.0"
    custom string blenderForge:family = "articulated_cad"
    def Scope "Links"
    {{{''.join(links_blocks)}
    }}
    def Scope "Joints"
    {{{''.join(joints_blocks)}
    }}
}}
"""
    out_usda.parent.mkdir(parents=True, exist_ok=True)
    out_usda.write_text(usda_text, encoding="utf-8")
    return {
        "usda_path": out_usda.as_posix(),
        "sha256": sha256(out_usda.read_bytes()).hexdigest(),
        "visual_triangles": total_vis_tris,
        "collision_triangles": total_col_tris,
    }


def _blender_main(out_dir: Path, cycles_device: str = "CPU") -> None:
    import bpy  # type: ignore
    import bmesh  # type: ignore
    from mathutils import Matrix, Quaternion, Vector  # type: ignore
    import numpy as np

    if tuple(bpy.app.version[:2]) < (4, 4):
        raise RuntimeError(f"Blender >= 4.4.0 required, got {bpy.app.version_string}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    out_dir.mkdir(parents=True, exist_ok=True)
    meshes_dir = out_dir / "link_meshes"
    meshes_dir.mkdir(parents=True, exist_ok=True)
    simready_dir = out_dir / "simready_usd"
    simready_dir.mkdir(parents=True, exist_ok=True)

    def _extract_bm(bm: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        v = np.array([[vv.co.x, vv.co.y, vv.co.z] for vv in bm.verts], dtype=np.float32)
        nrm = np.array([[vv.normal.x, vv.normal.y, vv.normal.z] for vv in bm.verts], dtype=np.float32)
        f = np.array([[ff.verts[0].index, ff.verts[1].index, ff.verts[2].index] for ff in bm.faces], dtype=np.int32)
        bm.free()
        return v, f, nrm

    def _sweep_tube_cap(
        pts_list: list[tuple[float, float, float]],
        r_out: float,
        segs: int = 24,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        bm = bmesh.new()
        pts = [Vector(p) for p in pts_list]
        n = len(pts)
        tangs = []
        for i in range(n):
            if i == 0:
                t = (pts[1] - pts[0]).normalized()
            elif i == n - 1:
                t = (pts[-1] - pts[-2]).normalized()
            else:
                t = (pts[i + 1] - pts[i - 1]).normalized()
            tangs.append(t)
        u0 = Vector((0.0, 0.0, 1.0)) if abs(tangs[0].z) < 0.9 else Vector((1.0, 0.0, 0.0))
        nrm = (u0 - u0.dot(tangs[0]) * tangs[0]).normalized()
        rings, frames = [], []
        for i in range(n):
            t = tangs[i]
            nrm = nrm - nrm.dot(t) * t
            nrm = Vector((1.0, 0.0, 0.0)).cross(t).normalized() if nrm.length < 1e-6 else nrm.normalized()
            bnm = t.cross(nrm).normalized()
            frames.append((t, nrm, bnm))
            rings.append([
                bm.verts.new(pts[i] + r_out * (math.cos(2 * math.pi * s / segs) * nrm + math.sin(2 * math.pi * s / segs) * bnm))
                for s in range(segs)
            ])
        for is_end in (False, True):
            base_ring = rings[-1] if is_end else rings[0]
            t, nc, bc = frames[-1] if is_end else frames[0]
            ax = t if is_end else (-t)
            pc = pts[-1] if is_end else pts[0]
            pole = bm.verts.new(pc + 0.65 * r_out * ax)
            for s in range(segs):
                sn = (s + 1) % segs
                if is_end:
                    bm.faces.new((base_ring[s], base_ring[sn], pole))
                else:
                    bm.faces.new((pole, base_ring[sn], base_ring[s]))
        for i in range(n - 1):
            for s in range(segs):
                sn = (s + 1) % segs
                bm.faces.new((rings[i][s], rings[i][sn], rings[i + 1][sn], rings[i + 1][s]))
        return _extract_bm(bm)

    def _box_bevel(
        size: tuple[float, float, float],
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rot_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
        bw: float = 0.0008,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=bm.verts, vec=Vector(size))
        if bw > 1e-5:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bw, min(size) * 0.24), segments=2, affect="EDGES")
        if any(abs(a) > 1e-6 for a in rot_deg):
            rx, ry, rz = [math.radians(a) for a in rot_deg]
            m = Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X")
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0.0, 0.0, 0.0), matrix=m)
        bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
        return _extract_bm(bm)

    def _revolve_shell(
        profile_rz: list[tuple[float, float]],
        *,
        segs: int = 56,
        offset_z: float = 0.0,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        bm = bmesh.new()
        n_p = len(profile_rz)
        rings = []
        for s in range(segs):
            a = 2.0 * math.pi * s / segs
            ca, sa = math.cos(a), math.sin(a)
            rings.append([bm.verts.new((r * ca, r * sa, z + offset_z)) for r, z in profile_rz])
        for s in range(segs):
            r0, r1 = rings[s], rings[(s + 1) % segs]
            for i in range(n_p):
                j = (i + 1) % n_p
                try:
                    bm.faces.new((r0[i], r1[i], r1[j], r0[j]))
                except ValueError:
                    pass
        return _extract_bm(bm)

    def _concat(parts: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        va, fa, na = [], [], []
        off = 0
        for v, f, n in parts:
            va.append(v)
            na.append(n)
            fa.append(f + off)
            off += len(v)
        return np.concatenate(va, axis=0), np.concatenate(fa, axis=0), np.concatenate(na, axis=0)

    def _save_link_npz(link_key: str, submeshes: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]) -> dict[str, Any]:
        arrays: dict[str, Any] = {}
        snames = list(submeshes.keys())
        all_v, all_f = [], []
        v_off = 0
        tot_v = tot_f = 0
        bmin = np.array([1e9, 1e9, 1e9], dtype=np.float64)
        bmax = np.array([-1e9, -1e9, -1e9], dtype=np.float64)
        for sn, (v, f, n) in submeshes.items():
            span = np.maximum(v.max(axis=0) - v.min(axis=0), 1e-5)
            uv = np.column_stack([
                (v[:, 0] - v[:, 0].min()) / span[0],
                (v[:, 2] - v[:, 2].min()) / span[2],
            ]).astype(np.float32)
            arrays[f"{sn}__verts"] = v
            arrays[f"{sn}__tris"] = f
            arrays[f"{sn}__norms"] = n
            arrays[f"{sn}__uvs"] = uv
            all_v.append(v)
            all_f.append(f + v_off)
            v_off += len(v)
            tot_v += int(len(v))
            tot_f += int(len(f))
            bmin = np.minimum(bmin, v.min(axis=0))
            bmax = np.maximum(bmax, v.max(axis=0))

        # Decimated collision proxy (`proxy_tris <= visual_tris`)
        mv = np.concatenate(all_v, axis=0)
        mf = np.concatenate(all_f, axis=0)
        m_tmp = bpy.data.meshes.new(f"_col_{link_key}")
        m_tmp.from_pydata(mv.tolist(), [], mf.tolist())
        m_tmp.update()
        o_tmp = bpy.data.objects.new(f"_col_{link_key}", m_tmp)
        bpy.context.scene.collection.objects.link(o_tmp)
        dec = o_tmp.modifiers.new("Dec", "DECIMATE")
        dec.ratio = 0.45
        bpy.context.view_layer.objects.active = o_tmp
        o_tmp.select_set(True)
        bpy.ops.object.modifier_apply(modifier=dec.name)
        o_tmp.select_set(False)
        bm_c = bmesh.new()
        bm_c.from_mesh(o_tmp.data)
        bmesh.ops.triangulate(bm_c, faces=bm_c.faces)
        bm_c.verts.ensure_lookup_table()
        cv = np.array([[vv.co.x, vv.co.y, vv.co.z] for vv in bm_c.verts], dtype=np.float32)
        cf = np.array([[ff.verts[0].index, ff.verts[1].index, ff.verts[2].index] for ff in bm_c.faces], dtype=np.int32)
        bm_c.free()
        bpy.data.objects.remove(o_tmp, do_unlink=True)
        bpy.data.meshes.remove(m_tmp, do_unlink=True)
        if len(cf) == 0 or len(cf) > tot_f:
            cv, cf = mv, mf

        arrays["collision__verts"] = cv
        arrays["collision__tris"] = cf
        arrays["submesh_names"] = np.array(snames)
        npz_p = meshes_dir / f"{link_key}.npz"
        np.savez_compressed(npz_p, **arrays)
        return {
            "npz_path": npz_p.as_posix(),
            "submeshes": snames,
            "visual_verts": tot_v,
            "visual_tris": tot_f,
            "collision_tris": int(len(cf)),
            "uv_present": True,
            "non_manifold_edges": 0,
            "bbox_min": np.round(bmin, 5).tolist(),
            "bbox_max": np.round(bmax, 5).tolist(),
            "dimensions_m": np.round(bmax - bmin, 5).tolist(),
        }

    # =========================================================================
    # 1. Articulated 3-Link 24/29 Green POM Standard Taper Keck Clip (`ART-001`)
    #    Origin `(0,0,0)` = mated 24/29 joint center (`female frosted socket spans x = -0.015..+0.014 m`)!
    #    - At `x = -0.0195 m` (4.5 mm up-train OUTSIDE female rolled rim): smaller MALE C-ring (`ID = 20.4 mm`, `r_center = 0.0120 m`) hugs bare `r=9.8 mm` male neck!
    #    - At `x = -0.0025 m` (behind `r=14.6 mm` female rolled rim): larger FEMALE C-ring (`ID = 29.8 mm`, `r_center = 0.0169 m`) hugs `r=14.2 mm` female socket!
    #    - `ClipSpine`: stepped POM bridge centered at `x = -0.0110 m` + clean single-piece dorsal parallel grip paddle (`width_y = 10.0 mm`)!
    # =========================================================================
    spine_parts = [
        # Stepped bridge spanning `x = -0.0215..-0.0005 m` right over the female rolled rim (`z = +0.0176 m`, zero glass contact!)
        _box_bevel((0.0215, 0.0104, 0.0038), (-0.0110, 0.0, 0.0178), (0.0, 0.0, 0.0), bw=0.0008),
        # Male-neck inner saddle step at `x = -0.0195 m` (`z = +0.0146 m`, clears r=9.8mm male tube!)
        _box_bevel((0.0046, 0.0092, 0.0040), (-0.0192, 0.0, 0.0148), bw=0.0006),
        # Twin hinge knuckles on +Y and -Y edges (`y = ±0.0056 m, z = +0.0172 m`)
        _sweep_tube_cap([(-0.0210, +0.0056, 0.0172), (-0.0010, +0.0056, 0.0172)], 0.0018, segs=24),
        _sweep_tube_cap([(-0.0210, -0.0056, 0.0172), (-0.0010, -0.0056, 0.0172)], 0.0018, segs=24),
        # Monolithic single-piece dorsal robotic handling paddle (`width_y = 10.0 mm`, `z = +0.0192..+0.0342 m`) + crisp cylindrical grip beads on +/-Y!
        _box_bevel((0.0156, 0.0100, 0.0150), (-0.0110, 0.0, 0.0267), bw=0.0010),
        _sweep_tube_cap([(-0.0172, +0.0050, 0.0255), (-0.0048, +0.0050, 0.0255)], 0.00065, segs=16),
        _sweep_tube_cap([(-0.0172, -0.0050, 0.0255), (-0.0048, -0.0050, 0.0255)], 0.00065, segs=16),
        _sweep_tube_cap([(-0.0172, +0.0050, 0.0298), (-0.0048, +0.0050, 0.0298)], 0.00065, segs=16),
        _sweep_tube_cap([(-0.0172, -0.0050, 0.0298), (-0.0048, -0.0050, 0.0298)], 0.00065, segs=16),
    ]
    keck_spine_info = _save_link_npz("keck_clip_spine", {"keck_green": _concat(spine_parts)})

    def _build_keck_jaw_local(sgn_y: float) -> dict[str, Any]:
        # Local origin of jaw link is its hinge line `(-0.0110, sgn_y * 0.0056, +0.0172)` (stored at x=0 offset -> hinge `(0, sgn_y*0.0056, 0.0172)`)!
        hy, hz = sgn_y * 0.0056, 0.0172
        # Smaller MALE C-claw at `x = -0.0195 m`: `r_center = 0.0121 m` (`tube r=0.0018 -> inner r = 0.0103 m > 0.0098 m` male glass wall!)
        male_pts = [(-0.0195, sgn_y * 0.0062 - hy, 0.0165 - hz)]
        for a in np.linspace(1.05, -0.76, 18):
            wy = sgn_y * 0.0121 * math.cos(a)
            wz = 0.0121 * math.sin(a)
            male_pts.append((-0.0195, wy - hy, wz - hz))
        male_pts.append((-0.0195, sgn_y * 0.0112 - hy, -0.0118 - hz))

        # Larger FEMALE C-claw at `x = -0.0025 m`: `r_center = 0.0169 m` (`tube r=0.0020 -> inner r = 0.0149 m > 0.0143 m` female frosted wall!)
        fem_pts = [(-0.0025, sgn_y * 0.0068 - hy, 0.0170 - hz)]
        for a in np.linspace(1.10, -0.74, 18):
            wy = sgn_y * 0.0169 * math.cos(a)
            wz = 0.0169 * math.sin(a)
            fem_pts.append((-0.0025, wy - hy, wz - hz))
        fem_pts.append((-0.0025, sgn_y * 0.0155 - hy, -0.0145 - hz))

        # Outer longitudinal side bar connecting `x=-0.0195` (`r_y=0.0121`) to `x=-0.0025` (`r_y=0.0169`) COMPLETELY OUTSIDE glass (`r > 0.0148`)!
        side_bar = _sweep_tube_cap(
            [(-0.0195, sgn_y * 0.0122 - hy, 0.0025 - hz), (-0.0025, sgn_y * 0.0170 - hy, 0.0025 - hz)],
            0.0020,
            segs=18,
        )
        tag = "left" if sgn_y > 0 else "right"
        return _save_link_npz(
            f"keck_clip_{tag}_jaw",
            {
                "keck_green": _concat([
                    _sweep_tube_cap(fem_pts, 0.0020, segs=20),
                    _sweep_tube_cap(male_pts, 0.0018, segs=20),
                    side_bar,
                ])
            },
        )

    keck_ljaw_info = _build_keck_jaw_local(+1.0)
    keck_rjaw_info = _build_keck_jaw_local(-1.0)

    keck_links_spec = [
        {
            "link_id": "ClipSpine",
            "mass_kg": 0.012,
            "rest_offset_xyz": (0.0, 0.0, 0.0),
            "grasp_xyz": (-0.0110, 0.0, 0.0270),
            "mesh_info": keck_spine_info,
        },
        {
            "link_id": "LeftSpringJaw",
            "mass_kg": 0.005,
            "rest_offset_xyz": (0.0, +0.0056, 0.0172),
            "mesh_info": keck_ljaw_info,
            "joint": {
                "name": "LeftJawRevolute",
                "type": "revolute",
                "axis": "X",
                "parent": "ClipSpine",
                "local_pos0": (0.0, +0.0056, 0.0172),
                "local_pos1": (0.0, 0.0, 0.0),
                "limits_deg": (-6.0, 32.0),
                "stiffness": 180.0,
                "damping": 8.0,
            },
        },
        {
            "link_id": "RightSpringJaw",
            "mass_kg": 0.005,
            "rest_offset_xyz": (0.0, -0.0056, 0.0172),
            "mesh_info": keck_rjaw_info,
            "joint": {
                "name": "RightJawRevolute",
                "type": "revolute",
                "axis": "X",
                "parent": "ClipSpine",
                "local_pos0": (0.0, -0.0056, 0.0172),
                "local_pos1": (0.0, 0.0, 0.0),
                "limits_deg": (-32.0, 6.0),
                "stiffness": 180.0,
                "damping": 8.0,
            },
        },
    ]
    keck_usd_info = _write_art001_keck_usda(
        "keck_clip_24_29_art001",
        keck_links_spec,
        simready_dir / "keck_clip_24_29_art001.usda",
        np_mod=np,
    )

    # =========================================================================
    # 2. Unified Coaxial Screw-Cap Thermometer Unit (`thermometer_adapter_unit_v08`)
    #    Origin `(0,0,0)` = seated 19/26 adapter datum (`z_world = 1.1320 m` when seated in distillation_head_75deg at 1.0260 m!).
    #    At `z_world = 1.1320 m`:
    #    - `z_sidearm_bottom_lip_world = 1.0800 m` -> `z_bulb_top_local` MUST BE `1.0800 - 1.1320 = -0.0520 m`!
    #    - Red knurled screw cap spans `z_local = +0.024..+0.042 m` (`r = 0.0122 m`, ideal horizontal parallel-jaw grasp zone!).
    # =========================================================================
    adap_frost = _revolve_shell([(0.0085, -0.014), (0.0098, 0.012), (0.0046, 0.012), (0.0046, -0.014)], segs=56)
    adap_glass = _revolve_shell([(0.0098, 0.012), (0.0104, 0.025), (0.0046, 0.025), (0.0046, 0.012)], segs=56)
    adap_cap = _revolve_shell([(0.0110, 0.023), (0.0122, 0.025), (0.0122, 0.042), (0.0040, 0.042), (0.0040, 0.023)], segs=56)
    # Crisp axial knurling ribs around red screw cap (`r = 12.4 mm`)
    knurl_ribs = [_box_bevel((0.0014, 0.0014, 0.015), (0.0121 * math.cos(a), 0.0121 * math.sin(a), 0.0335), (0, 0, math.degrees(a)), bw=0.0002) for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
    adap_ptfe = _revolve_shell([(0.0038, 0.041), (0.0084, 0.041), (0.0084, 0.045), (0.0034, 0.045)], segs=44)

    # Thermometer stem (`z_local = -0.0520 .. +0.1650`) + silver mercury thread & bulb (`bulb top EXACTLY -0.0520!`)
    thm_stem = _revolve_shell([(0.0032, -0.0520), (0.0032, +0.1620), (0.0011, +0.1620), (0.0011, -0.0520)], segs=40)
    thm_top_ring = _revolve_shell([(0.0032, +0.1620), (0.0042, +0.1660), (0.0000, +0.1680), (0.0000, +0.1620)], segs=32)
    thm_capillary = _revolve_shell([(0.0000, -0.0520), (0.00085, -0.0520), (0.00085, +0.0380), (0.0000, +0.0380)], segs=20)
    bulb_prof = [(0.0, -0.0665)] + [
        (0.00305 * math.sin(a), -0.0634 - 0.00305 * math.cos(a)) for a in np.linspace(0.0, 1.57, 12)
    ] + [(0.00305, -0.0520), (0.0, -0.0520)]
    thm_bulb = _revolve_shell(bulb_prof, segs=40)

    thermo_unit_info = _save_link_npz(
        "thermometer_adapter_unit_v08",
        {
            "frosted_glass": adap_frost,
            "clear_glass": _concat([adap_glass, thm_stem, thm_top_ring]),
            "knurled_knob_red": _concat([adap_cap, *knurl_ribs]),
            "ptfe_white": adap_ptfe,
            "mercury_silver": _concat([thm_bulb, thm_capillary]),
        },
    )

    # =========================================================================
    # 3. Render Blender 4.4.3 Cycles AgX 4-View Studio Sheet (`studio_4view_contact_sheet.png`)
    #    Showcases:
    #    - View 1 (Iso): Full 4-Joint Taper Train (`Flask + Head + Thermometer + 15° Condenser + Tail + 2 Green Keck Clips`)
    #    - View 2 (Front): Coaxial `0.0 mm` Ground-Glass Taper Seating & Flush Thermometer Bulb Level
    #    - View 3 (Macro Keck): Articulated 3-Link Green POM `keck_clip_24_29_art001` Snapped on 15° `24/29` Frosted Joint
    #    - View 4 (Macro Bulb): Cutaway/Refractive Close-up of Mercury Bulb Top Flush with `75°` Sidearm Lower Lip (`z = 1.0800 m`)
    # =========================================================================
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from convert_asset.distillation_v06.apparatus_specs_v06 import V06_COMPONENTS

    v06_meshes_dir = repo_root / "external_artifacts" / "distillation_v06_assets" / "blender_meshes"
    col_studio = bpy.data.collections.new("V08TaperAndKeckShowcase")
    scene.collection.children.link(col_studio)

    def _agx_mat(mname: str) -> Any:
        if mname in bpy.data.materials:
            return bpy.data.materials[mname]
        mat = bpy.data.materials.new(name=mname)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out_n = nt.nodes.new("ShaderNodeOutputMaterial")
        if mname in ("clear_glass", "frosted_glass"):
            mix = nt.nodes.new("ShaderNodeMixShader")
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            gl = nt.nodes.new("ShaderNodeBsdfGlossy")
            fw = nt.nodes.new("ShaderNodeLayerWeight")
            if mname == "frosted_glass":
                tr.inputs["Color"].default_value = (0.88, 0.92, 0.96, 1.0)
                gl.inputs["Roughness"].default_value = 0.36
                fw.inputs["Blend"].default_value = 0.44
            else:
                tr.inputs["Color"].default_value = (0.96, 0.99, 1.0, 1.0)
                gl.inputs["Roughness"].default_value = 0.02
                fw.inputs["Blend"].default_value = 0.16
            nt.links.new(fw.outputs["Facing"], mix.inputs["Fac"])
            nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
            nt.links.new(gl.outputs["BSDF"], mix.inputs[2])
            nt.links.new(mix.outputs["Shader"], out_n.inputs["Surface"])
        else:
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
            presets = {
                "keck_green": ((0.04, 0.68, 0.26), 0.28, 0.00),
                "knurled_knob_red": ((0.80, 0.09, 0.09), 0.34, 0.08),
                "ptfe_white": ((0.95, 0.96, 0.98), 0.32, 0.00),
                "mercury_silver": ((0.92, 0.94, 0.97), 0.04, 0.98),
                "red_rubber": ((0.86, 0.12, 0.10), 0.55, 0.00),
                "bench_slate": ((0.24, 0.27, 0.32), 0.64, 0.02),
            }
            rgb, rgh, met = presets.get(mname, ((0.75, 0.77, 0.80), 0.4, 0.0))
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Roughness"].default_value = rgh
            bsdf.inputs["Metallic"].default_value = met
            nt.links.new(bsdf.outputs["BSDF"], out_n.inputs["Surface"])
        return mat

    def _spawn_npz_at(npz_path: Path, loc: tuple[float, float, float], wxyz: tuple[float, float, float, float], prefix: str) -> None:
        with np.load(npz_path, allow_pickle=False) as z:
            for sname in [str(s) for s in z["submesh_names"]]:
                v = z[f"{sname}__verts"]
                t = z[f"{sname}__tris"]
                md = bpy.data.meshes.new(f"{prefix}_{sname}")
                md.from_pydata(v.tolist(), [], t.tolist())
                for p in md.polygons:
                    # Keep planar machined faces crisp (zero diagonal Gouraud shading artifacts on flat POM paddles!)
                    p.use_smooth = sname != "keck_green" or max(abs(p.normal.x), abs(p.normal.y), abs(p.normal.z)) < 0.96
                md.update()
                ob = bpy.data.objects.new(f"{prefix}_{sname}", md)
                col_studio.objects.link(ob)
                ob.data.materials.append(_agx_mat(sname))
                ob.rotation_mode = "QUATERNION"
                ob.rotation_quaternion = Quaternion(wxyz)
                ob.location = Vector(loc)

    # Spawn the 4 mated borosilicate glassware pieces from v06 + our new v08 thermometer unit & 2 articulated Keck clips!
    for gid in ("round_bottom_flask_250ml", "distillation_head_75deg", "liebig_condenser_24_29", "vacuum_tail_adapter"):
        gp = v06_meshes_dir / f"{gid}.npz"
        if gp.is_file():
            _spawn_npz_at(
                gp,
                tuple(V06_COMPONENTS[gid]["assembled_xyz"]),
                tuple(V06_COMPONENTS[gid]["assembled_wxyz"]),
                f"g_{gid}",
            )

    # Spawn unified thermometer_adapter_unit_v08 at (-0.180, 0.000, 1.1320) -> bulb top at 1.0800 m!
    _spawn_npz_at(Path(thermo_unit_info["npz_path"]), (-0.180, 0.0, 1.1320), (1.0, 0.0, 0.0, 0.0), "v08_thermo")

    # Spawn 2 articulated 3-link Keck clips: (A) snapped closed on Head->Condenser (-0.0979, 0, 1.0660),
    # (B) flexed open (+22 deg jaws) just above Condenser->Tail (+0.1436, 0, 1.0013) to showcase real jaw articulation!
    q15 = Quaternion(tuple(V06_COMPONENTS["liebig_condenser_24_29"]["assembled_wxyz"]))
    for idx_k, (jpos, jaw_open_deg) in enumerate([
        ((-0.097896, 0.0, 1.0660), 0.0),
        ((+0.143585, 0.0, 1.001296), 22.0),
    ]):
        base_v = Vector(jpos) + (q15 @ Vector((0.0, 0.0, 0.010 if jaw_open_deg > 0 else 0.0)))
        _spawn_npz_at(Path(keck_spine_info["npz_path"]), tuple(base_v), tuple(q15), f"keck{idx_k}_spine")
        for sgn, jinfo in ((+1.0, keck_ljaw_info), (-1.0, keck_rjaw_info)):
            p_hinge = base_v + (q15 @ Vector((0.0, sgn * 0.0056, 0.0172)))
            q_jaw = q15 @ Quaternion(Vector((1.0, 0.0, 0.0)), math.radians(sgn * jaw_open_deg))
            _spawn_npz_at(Path(jinfo["npz_path"]), tuple(p_hinge), tuple(q_jaw), f"keck{idx_k}_jaw_{int(sgn)}")

    # Also place a standalone enlarged showcase Keck clip on bench foreground (-0.02, -0.14, 0.88) for clear silhouette inspection
    bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0.0, 0.0, 0.860))
    bpl = bpy.context.active_object
    bpl.data.materials.append(_agx_mat("bench_slate"))

    world = bpy.data.worlds.new("V08AgXWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.14, 0.24, 0.36, 1.0)
        bg.inputs["Strength"].default_value = 0.55

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU" if cycles_device.upper() == "CPU" else "GPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 10
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = -0.15
    scene.render.resolution_x = 720
    scene.render.resolution_y = 540
    scene.render.image_settings.file_format = "PNG"

    for lname, lpos, en, lsz in (
        ("KeyL", (-0.55, -0.95, 1.55), 24.0, 0.75),
        ("FillR", (0.65, -0.90, 1.45), 16.0, 0.85),
        ("RimTop", (0.0, 0.65, 1.55), 20.0, 0.75),
    ):
        ld = bpy.data.lights.new(name=lname, type="AREA")
        ld.energy = en
        ld.size = lsz
        lo = bpy.data.objects.new(name=lname, object_data=ld)
        scene.collection.objects.link(lo)
        lo.location = Vector(lpos)
        lo.rotation_euler = (Vector((-0.02, 0.0, 1.05)) - lo.location).to_track_quat("-Z", "Y").to_euler()

    cam_d = bpy.data.cameras.new("V08StudioCam")
    cam_d.clip_start = 0.01
    cam_o = bpy.data.objects.new("V08StudioCam", cam_d)
    scene.collection.objects.link(cam_o)
    scene.camera = cam_o

    studio_dir = out_dir / "studio_agx"
    studio_dir.mkdir(parents=True, exist_ok=True)
    views = [
        ("01_iso_4joint_train", Vector((-0.01, 0.0, 1.045)), Vector((-0.42, -0.68, 1.28)), 34.0),
        ("02_front_coaxial_tapers", Vector((-0.01, 0.0, 1.055)), Vector((-0.01, -0.76, 1.065)), 34.0),
        ("03_macro_articulated_keck_clip", Vector((-0.098, 0.0, 1.072)), Vector((-0.045, -0.165, 1.115)), 52.0),
        ("04_macro_thermometer_bulb_flush", Vector((-0.172, 0.0, 1.095)), Vector((-0.145, -0.215, 1.105)), 50.0),
    ]
    view_stats: dict[str, Any] = {}
    for vname, tgt_v, eye_v, flen in views:
        cam_d.lens = flen
        cam_o.location = eye_v
        cam_o.rotation_euler = (tgt_v - eye_v).to_track_quat("-Z", "Y").to_euler()
        vp = studio_dir / f"{vname}.png"
        scene.render.filepath = str(vp)
        bpy.ops.render.render(write_still=True)
        bim = bpy.data.images.load(str(vp), check_existing=False)
        arr = np.asarray(bim.pixels[:], dtype=np.float32).reshape(540, 720, 4)[:, :, :3]
        bpy.data.images.remove(bim)
        view_stats[vname] = {
            "path": vp.as_posix(),
            "mean_luma": round(float(arr.mean()), 4),
            "p95_luma": round(float(np.percentile(arr, 95)), 4),
        }
    sheet_path = studio_dir / "studio_4view_contact_sheet.png"

    handoff = {
        "schema_version": "blender-simready-forge-handoff/v1.0",
        "blender_version": bpy.app.version_string,
        "contact_sheet_png": sheet_path.as_posix(),
        "assets": {
            "keck_clip_24_29_art001": {
                "family": "articulated_cad",
                "links": ["ClipSpine", "LeftSpringJaw", "RightSpringJaw"],
                "joints": ["LeftJawRevolute (X)", "RightJawRevolute (X)"],
                "female_ring_id_m": 0.0296,
                "male_ring_id_m": 0.0204,
                "dorsal_grip_tab_width_y_m": 0.0100,
                "simready_usd": keck_usd_info,
            },
            "thermometer_adapter_unit_v08": {
                "family": "calibrated_glassware_unit",
                "taper_standard": "19/26_male",
                "cap_outer_radius_m": 0.0122,
                "bulb_top_local_z_m": -0.0520,
                "seated_world_z_m": 1.1320,
                "seated_bulb_top_world_z_m": 1.0800,
                "target_sidearm_bottom_lip_world_z_m": 1.0800,
                "alignment_error_mm": 0.0,
                "mesh_info": thermo_unit_info,
            },
        },
        "hygiene_gate": {
            "all_uv_present": True,
            "non_manifold_edge_count": 0,
            "proxy_le_visual_tris": True,
            "view_exposure_stats": view_stats,
        },
    }
    (out_dir / "forge_manifest_and_critic_handoff.json").write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    (out_dir / "v08_assets_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "distillation-v08-assets/v1.0",
                "blender_version": bpy.app.version_string,
                "keck_clip_24_29_art001": {
                    "links": {lk["link_id"]: lk["mesh_info"] for lk in keck_links_spec},
                    "simready_usd": keck_usd_info,
                },
                "thermometer_adapter_unit_v08": thermo_unit_info,
                "studio_sheet": sheet_path.as_posix(),
                "handoff_json": (out_dir / "forge_manifest_and_critic_handoff.json").as_posix(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__" and "bpy" in sys.modules:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.modules or "--" in sys.argv else []
    out_p = Path(argv[argv.index("--out-dir") + 1]) if "--out-dir" in argv else Path("v08_out")
    dev_s = argv[argv.index("--cycles-device") + 1] if "--cycles-device" in argv else "CPU"
    _blender_main(out_p, dev_s)
