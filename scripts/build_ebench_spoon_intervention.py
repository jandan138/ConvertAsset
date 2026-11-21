#!/usr/bin/env python3
"""Blender-authored handle interventions on an existing EBench spoon mesh.

The source scene is read-only. USD composition/materials remain producer-owned;
Blender deforms mesh points and provides recomputed face-corner normals. Both
the control and intervention take the same Blender path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def handle_weight(z, start=-0.1, end=0.1):
    """Full handle at z<=start, smooth join, exact unmodified bowl at z>=end."""
    t = max(0.0, min(1.0, (z - start) / (end - start)))
    return 1.0 - t * t * (3.0 - 2.0 * t)


def deform_point(point, cross_section_scale):
    if not 1.0 <= cross_section_scale <= 3.0:
        raise ValueError("Cross-section scale must be in [1, 3]")
    x, y, z = point
    factor = 1.0 + (cross_section_scale - 1.0) * handle_weight(z)
    return [x * factor, y * factor, z]


def blender_phase(mesh_path, output):
    import bpy
    from mathutils import Vector

    data = json.loads(mesh_path.read_text())
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for scale in data["cross_section_scales"]:
        tag = f"handle_{str(scale).replace('.', 'p')}"
        mesh = bpy.data.meshes.new(tag)
        points = [deform_point(p, scale) for p in data["points"]]
        mesh.from_pydata(points, [], data["faces"])
        mesh.update()
        obj = bpy.data.objects.new(tag, mesh)
        bpy.context.collection.objects.link(obj)
        obj.scale = (data["runtime_scale"],) * 3
        obj["handle_cross_section_scale"] = scale
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        faces = [list(poly.vertices) for poly in mesh.polygons]
        if faces != data["faces"]:
            raise ValueError("Blender changed mesh topology")
        payload = {"points": [list(v.co) for v in mesh.vertices],
                   "corner_normals": [list(n.vector) for n in mesh.corner_normals],
                   "faces": faces, "scale": scale, "blender_version": bpy.app.version_string}
        (output / f"{tag}.json").write_text(json.dumps(payload))
        # Keep both editable meshes at the same object origin; the USD asset
        # exports are separate. Hide the other objects when inspecting the blend.
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "spoon_variants.blend"))
    # Geometry-only preview; source USD materials remain untouched. This is not
    # a simulator observation and must not be used as model input evidence.
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = 400
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.15, 0.15, 0.15)
    material = bpy.data.materials.new("Geometry inspection only")
    material.diffuse_color = (0.4, 0.45, 0.5, 1.0)
    objects = [o for o in scene.objects if o.type == "MESH"]
    for obj in objects:
        obj.data.materials.append(material)
    bpy.ops.object.camera_add(location=(0., -0.7, 0.))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0., 0., 0.)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.26
    scene.camera = camera
    bpy.ops.object.light_add(type="AREA", location=(0.2, -0.3, 0.3))
    light = bpy.context.object
    light.data.energy = 20
    light.data.shape = "DISK"
    light.data.size = 0.3
    light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()
    for obj in objects:
        for other in objects:
            other.hide_render = other != obj
        scene.render.filepath = str(output / f"{obj.name}_geometry_preview.png")
        bpy.ops.render.render(write_still=True)


def build(source, prim_path, blender, output, scales):
    from pxr import Gf, Sdf, Usd, UsdGeom, Vt

    if any(not 1 <= scale <= 3 for scale in scales) or len(set(scales)) != len(scales):
        raise ValueError("Require unique cross-section scales in [1, 3]")
    if 1.0 not in scales:
        raise ValueError("The same-process control (scale 1) is required")
    stage = Usd.Stage.Open(str(source))
    root = stage.GetPrimAtPath(prim_path)
    if not root:
        raise ValueError("Spoon source prim missing")
    meshes = [p for p in Usd.PrimRange(root) if p.IsA(UsdGeom.Mesh)]
    if len(meshes) != 1:
        raise ValueError("This intervention requires exactly one spoon mesh")
    mesh = UsdGeom.Mesh(meshes[0])
    points = [list(p) for p in mesh.GetPointsAttr().Get()]
    indices = list(mesh.GetFaceVertexIndicesAttr().Get())
    faces, offset = [], 0
    for count in mesh.GetFaceVertexCountsAttr().Get():
        faces.append(indices[offset:offset + count])
        offset += count
    if offset != len(indices):
        raise ValueError("Invalid source topology")
    # The native task applies uniform scale 0.2. Keep coordinates/pivot in the
    # source frame, so runtime orientation and placement can be reused exactly.
    scale = 0.2
    output.mkdir(parents=True, exist_ok=False)
    mesh_input = {"points": points, "faces": faces, "runtime_scale": scale,
                  "cross_section_scales": scales}
    (output / "mesh_input.json").write_text(json.dumps(mesh_input))
    command = [str(blender), "--background", "--factory-startup", "--python",
               str(Path(__file__).resolve()), "--", "--blender-phase", "--mesh-input",
               str(output / "mesh_input.json"), "--out", str(output)]
    with (output / "blender.log").open("w") as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    report = {"source": str(source.resolve()), "source_prim": prim_path,
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "source_mesh": str(mesh.GetPath()), "runtime_scale": scale,
              "mass_treatment": "source_authored_mass_retained_in_both_variants",
              "source_authored_mass": root.GetAttribute("physics:mass").Get(),
              "inertia_treatment": "source_inertia_settings_retained_runtime_resolution_pending",
              "physics_qualified": False, "variants": []}
    relative_mesh = mesh.GetPath().MakeRelativePath(root.GetPath())
    for factor in scales:
        tag = f"handle_{str(factor).replace('.', 'p')}"
        result = json.loads((output / f"{tag}.json").read_text())
        if len(result["corner_normals"]) != len(indices):
            raise ValueError("Blender face-corner normal count changed")
        expected = [deform_point(p, factor) for p in points]
        error = max(abs(a - b) for p, q in zip(expected, result["points"])
                    for a, b in zip(p, q))
        if len(result["points"]) != len(points) or result["faces"] != faces or error > 1e-6:
            raise ValueError("Blender output differs from declared deformation")
        if any(p != q for p, q in zip(points, result["points"]) if p[2] >= 0.1):
            raise ValueError("Bowl vertices changed")
        path = output / f"{tag}.usda"
        asset = Usd.Stage.CreateNew(str(path))
        UsdGeom.SetStageMetersPerUnit(asset, 1.0)
        UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
        world = UsdGeom.Xform.Define(asset, "/World")
        asset.SetDefaultPrim(world.GetPrim())
        spoon = UsdGeom.Xform.Define(asset, "/World/Spoon")
        spoon.GetPrim().GetReferences().AddReference(str(source.resolve()), prim_path)
        spoon.ClearXformOpOrder()
        spoon.AddScaleOp(opSuffix="intervention").Set(Gf.Vec3f(scale))
        target = UsdGeom.Mesh(asset.GetPrimAtPath(Sdf.Path("/World/Spoon").AppendPath(relative_mesh)))
        target.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in result["points"]]))
        target.GetNormalsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in result["corner_normals"]]))
        target.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
        lo = [min(p[i] for p in result["points"]) for i in range(3)]
        hi = [max(p[i] for p in result["points"]) for i in range(3)]
        target.GetExtentAttr().Set([Gf.Vec3f(*lo), Gf.Vec3f(*hi)])
        # Export only the composed spoon subtree. Keeping a reference to the
        # whole room pulls unrelated room texture failures into asset intake.
        asset.Flatten().Export(str(path))
        report["variants"].append({"id": tag, "cross_section_scale": factor,
            "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "vertex_count": len(points), "bowl_vertices_unchanged": True,
            "max_deformation_error": error, "blender_version": result["blender_version"],
            "local_bounds": [lo, hi], "self_contained": False})
    (output / "generation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def build_native_overlay(source, prim_path, prepared_asset, output):
    """Map the prepared asset into the original scene namespace and pose."""
    from pxr import Sdf, Usd, UsdGeom, UsdShade

    if output.exists():
        raise FileExistsError(output)
    original = Usd.Stage.Open(str(source))
    prepared = Usd.Stage.Open(str(prepared_asset))
    source_prim = original.GetPrimAtPath(prim_path)
    if not source_prim or not prepared.GetPrimAtPath("/World/Spoon"):
        raise ValueError("Missing source or prepared spoon")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(output))
    parent = Sdf.Path(prim_path).GetParentPath()
    stage.SetDefaultPrim(UsdGeom.Xform.Define(stage, parent).GetPrim())
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.GetStageMetersPerUnit(original))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.GetStageUpAxis(original))
    Sdf.CopySpec(prepared.Flatten(), "/World/Spoon", stage.GetRootLayer(), prim_path)
    root = stage.GetPrimAtPath(prim_path)
    for name in root.GetPropertyNames():
        if name.startswith("xformOp:") or name == "xformOpOrder":
            root.RemoveProperty(name)
    original_flat = original.Flatten()
    for name in source_prim.GetPropertyNames():
        if name.startswith("xformOp:") or name == "xformOpOrder":
            path = Sdf.Path(prim_path).AppendProperty(name)
            Sdf.CopySpec(original_flat, path, stage.GetRootLayer(), path)
    old, new = Sdf.Path("/World/Spoon"), Sdf.Path(prim_path)
    for prim in Usd.PrimRange(root):
        for rel in prim.GetRelationships():
            targets = rel.GetTargets()
            if targets:
                rel.SetTargets([p.ReplacePrefix(old, new) for p in targets])
        for attr in prim.GetAttributes():
            targets = attr.GetConnections()
            if targets:
                attr.SetConnections([p.ReplacePrefix(old, new) for p in targets])
        if prim.IsA(UsdGeom.Mesh):
            material, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
            if not material:
                raise ValueError("Material binding lost during namespace mapping")
    if UsdGeom.Xformable(root).GetLocalTransformation() != UsdGeom.Xformable(source_prim).GetLocalTransformation():
        raise ValueError("Native source transform changed")
    stage.GetRootLayer().Save()
    print(json.dumps({"overlay": str(output), "source_pose_preserved": True,
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--prim", default="/root/obj_spoon")
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--scales", nargs="+", type=float, default=[1.0, 2.0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blender-phase", action="store_true")
    parser.add_argument("--mesh-input", type=Path)
    parser.add_argument("--overlay-asset", type=Path)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None
    args = parser.parse_args(argv)
    if args.blender_phase:
        blender_phase(args.mesh_input, args.out.resolve())
    elif args.overlay_asset:
        if args.source is None:
            parser.error("--source is required for an overlay")
        build_native_overlay(args.source, args.prim, args.overlay_asset, args.out.resolve())
    else:
        if args.source is None or args.blender is None:
            parser.error("--source and --blender are required")
        build(args.source, args.prim, args.blender, args.out.resolve(), args.scales)


if __name__ == "__main__":
    main()
