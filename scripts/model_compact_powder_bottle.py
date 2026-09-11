"""Task09 compact, hollow HDPE bottle: SI geometry and editable Blender source.

Ordinary Python: build_geometry() uses only the standard library.
Blender: blender -b -t 8 --python this_file.py -- --out DIR --render
The JSON is the geometry handoff; preview objects are never exported as assets.
"""
import argparse
from itertools import combinations
import json
import math
from pathlib import Path
import sys


SEGMENTS = 32
# .070 控制肩部内缩；等内径颈部合并 .096，保持 32*8+2=258 个凸片。
COLLISION_HEIGHTS = (.002, .004, .066, .070, .074, .082, .090, .0985, .100)
VISUAL_SEGMENTS = 128
DENSITY = 950.0
INSERT_TOP = .059
INSERT_THICKNESS = .002
INSERT_OVERLAP = .00015


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _unit(a):
    length = math.sqrt(_dot(a, a))
    return tuple(x / length for x in a)


def _ring(z, radius, exponent, count):
    points = []
    for i in range(count):
        angle = 2 * math.pi * i / count
        c, s = math.cos(angle), math.sin(angle)
        radial = radius / (abs(c)**exponent + abs(s)**exponent)**(1 / exponent)
        points.append((radial * c, radial * s, z))
    return points


def _profiles():
    # 身壁 1.8 mm；肩部内外同源过渡，避免只缩视觉外壳而保留厚碰撞。
    outer = [(0., .0282, 5.), (.0005, .0292, 5.), (.0012, .0298, 5.),
             (.002, .030, 5.), (.004, .030, 5.)]
    inner = [(.002, .0278, 5.), (.004, .0282, 5.)]
    for z in [.066, .070, .074, .078, .082, .086, .090]:
        t = (z - .066) / .024
        smooth = t * t * (3 - 2 * t)
        exponent = 5 - 3 * smooth
        outer.append((z, .030 - .0038 * smooth, exponent))
        inner.append((z, .0282 - .0042 * smooth, exponent))
    # 48 mm 喉口；最大 54 mm 外径，顶部只剩圆润冠部，不增加窄孔圈。
    for z, ro, ri in [(.096, .0262, .024), (.097, .02635, .024),
                      (.098, .0269, .024), (.0985, .027, .024),
                      (.099, .0269, .024), (.0996, .0264, .02425),
                      (.100, .0257, .0249)]:
        outer.append((z, ro, 2.))
        inner.append((z, ri, 2.))
    return outer, inner


def _loft(name, profile, count, material=None):
    points = [point for row in profile for point in _ring(*row, count)]
    faces = []
    for layer in range(len(profile) - 1):
        for i in range(count):
            a, b = layer * count + i, layer * count + (i + 1) % count
            # 三角化让非共面的肩部四边形在 JSON 和 Blender 中完全一致。
            faces.extend([[a, b, b + count], [a, b + count, a + count]])
    faces.append(list(reversed(range(count))))
    faces.append(list(range(len(points) - count, len(points))))
    result = dict(name=name, points=points, faces=faces)
    if material is not None:
        result['material'] = material
    return result


def _wall_hull(name, points):
    """Supporting planes of one eight-corner wall patch, not a vessel hull."""
    planes = {}
    for a, b, c in combinations(range(len(points)), 3):
        normal = _cross(_sub(points[b], points[a]), _sub(points[c], points[a]))
        if _dot(normal, normal) < 1e-24:
            continue
        normal = _unit(normal)
        distances = [_dot(normal, _sub(point, points[a])) for point in points]
        if max(distances) > 1e-10 and min(distances) < -1e-10:
            continue
        if max(distances) > 1e-10:
            normal = tuple(-v for v in normal)
        ids = tuple(i for i, d in enumerate(distances) if abs(d) <= 1e-10)
        planes[ids] = normal
    faces = []
    for ids, normal in planes.items():
        center = tuple(sum(points[i][k] for i in ids) / len(ids) for k in range(3))
        u = _unit(_sub(points[ids[0]], center))
        v = _cross(normal, u)
        face = sorted(ids, key=lambda i: math.atan2(_dot(_sub(points[i], center), v),
                                                    _dot(_sub(points[i], center), u)))
        faces.append(face)
    return dict(name=name, points=points, faces=faces)


def _moments(mesh):
    volume = 0.
    first = [0., 0., 0.]
    second = [0., 0., 0.]
    for face in mesh['faces']:
        for i in range(1, len(face) - 1):
            a, b, c = [mesh['points'][j] for j in (face[0], face[i], face[i + 1])]
            dv = _dot(a, _cross(b, c)) / 6
            volume += dv
            for k in range(3):
                total = a[k] + b[k] + c[k]
                first[k] += dv * total / 4
                second[k] += dv * (total * total + a[k]**2 + b[k]**2 + c[k]**2) / 20
    return volume, first, second


def build_geometry():
    """Return the fixed compact-bottle contract in metres, without SDK imports.

    Interpolate inner_profile radius and exponent linearly in z. Subtract the
    recommended radial clearance from the polar boundary, then account for the
    grain radius/contact margin separately. Colliders are authoritative.
    """
    outer, inner = _profiles()
    shell = _loft('BottleShell', outer + list(reversed(inner)), VISUAL_SEGMENTS, 'bottle')
    insert = _loft('FalseBottom', [(INSERT_TOP - INSERT_THICKNESS, .0282 + INSERT_OVERLAP, 5.),
                                   (INSERT_TOP, .0282 + INSERT_OVERLAP, 5.)],
                   VISUAL_SEGMENTS, 'insert')
    colliders = []
    outer_by_z = {row[0]: row for row in outer}
    # 碰撞 LOD 只抽取关键高度；视觉轮廓、假底和质量积分保持 r1 字节。
    collision_inner = [row for row in inner if row[0] in COLLISION_HEIGHTS]
    for layer, (low, high) in enumerate(zip(collision_inner, collision_inner[1:])):
        rings = [_ring(*row, SEGMENTS) for row in
                 [outer_by_z[low[0]], outer_by_z[high[0]], low, high]]
        for i in range(SEGMENTS):
            j = (i + 1) % SEGMENTS
            points = [ring[index] for ring in rings for index in [i, j]]
            colliders.append(_wall_hull(f'Wall_{layer:02d}_{i:02d}', points))
    colliders.append(_loft('Base', [(0., .0282, 5.), (.002, .030, 5.)], SEGMENTS))
    colliders.append(_loft('Insert', [(INSERT_TOP - INSERT_THICKNESS, .0282 + INSERT_OVERLAP, 5.),
                                     (INSERT_TOP, .0282 + INSERT_OVERLAP, 5.)], SEGMENTS))

    # 质量按实体并集算：假底只计内壁内的部分，重叠接缝不重复计质量。
    insert_effective = _loft('EffectiveInsert', [(INSERT_TOP - INSERT_THICKNESS, .0282, 5.),
                                               (INSERT_TOP, .0282, 5.)], VISUAL_SEGMENTS)
    moments = [_moments(part) for part in [shell, insert_effective]]
    volume = sum(row[0] for row in moments)
    first = [sum(row[1][k] for row in moments) for k in range(3)]
    second = [sum(row[2][k] for row in moments) for k in range(3)]
    com = [v / volume for v in first]
    mass = DENSITY * volume
    inertia = [DENSITY * sum(second[j] for j in range(3) if j != k)
               - mass * sum(com[j]**2 for j in range(3) if j != k) for k in range(3)]
    return dict(
        schema='compact-powder-bottle-geometry-v1',
        producer='ConvertAsset task09 procedural Blender bottle model_r2 collision LOD',
        root_scale=[1, 1, 1], meters_per_unit=1, up_axis='Z',
        visual_meshes=[shell, insert], colliders=colliders,
        inner_profile=[dict(z=z, radius=r, exponent=p) for z, r, p in inner],
        outer_profile=[dict(z=z, radius=r, exponent=p) for z, r, p in outer],
        volume_m3=volume, mass_kg=mass, center_of_mass_m=com,
        diagonal_inertia_kg_m2=inertia, principal_axes_wxyz=[1, 0, 0, 0],
        metadata=dict(
            height_m=.1, outer_dimensions_m=[.06, .06, .1],
            mouth_inner_diameter_m=.048, mouth_outer_diameter_m=.054,
            mouth_diameter_measurement='minimum clear bore and maximum rounded-lip OD; crown flares to 49.8 mm ID',
            body_wall_axis_thickness_m=.0018, neck_wall_radial_thickness_m=.0022,
            lip_max_radial_thickness_m=.003, base_thickness_m=.002,
            insert_top_m=INSERT_TOP, insert_thickness_m=INSERT_THICKNESS,
            insert_wall_overlap_radius_m=INSERT_OVERLAP,
            suggested_powder_surface_m=.070, suggested_powder_depth_m=.011,
            collider_segments=SEGMENTS, collider_wall_layers=len(collision_inner) - 1,
            collider_profile_heights_m=list(COLLISION_HEIGHTS),
            collider_lod_note='Add shoulder z=0.070; merge constant-bore neck across z=0.096. Neck exterior radial overreach <=0.565 mm against the visual profile; bore unchanged.',
            collider_count=len(colliders), collider_approximation='convexHull per closed piece only',
            recommended_clearance_m=.00075,
            clearance_usage='Subtract 0.75 mm from superellipse polar radius; add grain radius and contact margin separately; test the resulting sphere against actual convex pieces.',
            inner_profile_interpolation='linear radius and exponent in z; visual loft and convex chords discretize this envelope',
            rigid_body_owner='consumer bottle root only; no independent collider rigid bodies',
            density_kg_m3=DENSITY,
            mass_method='signed tetrahedral integration of closed visual shell plus insert clipped to inner wall; exact union for the authored mesh',
            inertia_axes='root XYZ are principal axes by fourfold/reflection symmetry',
            validation_scope='static geometry and Blender CPU previews; no runtime or particle qualification',
        ),
    )


def _create_blender(data, out, render, samples):
    import bpy
    import bmesh
    from mathutils import Vector

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.19, .22, .26, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25

    def collection(name):
        obj = bpy.data.collections.new(name)
        scene.collection.children.link(obj)
        return obj

    visual_collection = collection('ASSET_Visuals')
    collider_collection = collection('ASSET_ConvexColliders')
    preview_collection = collection('PREVIEW_Studio_not_asset')
    section_collection = collection('PREVIEW_Section_not_asset')
    collider_collection.hide_render = True
    collider_collection.hide_viewport = True
    section_collection.hide_render = True
    section_collection.hide_viewport = True
    root = bpy.data.objects.new('Bottle', None)
    visual_collection.objects.link(root)
    root['geometry_contract'] = 'geometry.json'
    root['mass_kg'] = data['mass_kg']
    root['insert_top_m'] = INSERT_TOP
    root['units'] = 'metres, Z up; geometry baked, scale 1'
    materials = {}
    for name, color, roughness in [('bottle', (.82, .805, .75, 1), .32),
                                    ('insert', (.79, .775, .72, 1), .44),
                                    ('accent', (.19, .26, .30, 1), .5)]:
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = color
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = color
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['IOR'].default_value = 1.46
        materials[name] = mat

    def mesh_object(part, target, asset=True):
        mesh = bpy.data.meshes.new(part['name'])
        mesh.from_pydata(part['points'], [], part['faces'])
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        if not all(edge.is_manifold for edge in bm.edges) or bm.calc_volume(signed=True) <= 0:
            raise ValueError(f"Non-manifold/inward geometry: {part['name']}")
        bm.free()
        obj = bpy.data.objects.new(part['name'], mesh)
        target.objects.link(obj)
        if asset:
            obj.parent = root
        if 'material' in part:
            mesh.materials.append(materials[part['material']])
            for face in mesh.polygons:
                face.use_smooth = abs(face.normal.z) < .995
        else:
            obj.display_type = 'WIRE'
            obj['collision_approximation'] = 'convexHull'
        return obj

    visuals = [mesh_object(part, visual_collection) for part in data['visual_meshes']]
    for part in data['colliders']:
        mesh_object(part, collider_collection)

    cut_material = bpy.data.materials.new('Section_cut_tint_DIAGNOSTIC_ONLY')
    cut_material.diffuse_color = (.50, .19, .065, 1)
    cut_material.use_nodes = True
    cut_shader = cut_material.node_tree.nodes['Principled BSDF']
    cut_shader.inputs['Base Color'].default_value = cut_material.diffuse_color
    cut_shader.inputs['Roughness'].default_value = .6
    # 剖面使用源网格的真实切割，切掉面向相机的一半；绝不添加粉末假面。
    for original in visuals:
        cut = original.copy()
        cut.data = original.data.copy()
        cut.name = original.name + '_Section'
        cut.parent = None
        cut.data.materials.append(cut_material)
        section_collection.objects.link(cut)
        bm = bmesh.new()
        bm.from_mesh(cut.data)
        result = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                                       dist=1e-8, plane_co=(0, 0, 0), plane_no=(0, -1, 0),
                                       clear_outer=True, clear_inner=False)
        boundary = [edge for edge in result['geom_cut']
                    if isinstance(edge, bmesh.types.BMEdge) and edge.is_boundary]
        filled = bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
        for face in filled['faces']:
            face.smooth = False
            face.material_index = 1
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if not all(edge.is_manifold for edge in bm.edges) or bm.calc_volume(signed=True) <= 0:
            raise ValueError('Section preview must be a closed, positive-volume cut')
        bm.to_mesh(cut.data)
        bm.free()

    def aim(obj, target):
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

    def light(name, location, energy, size, target=(0, 0, .05)):
        lamp = bpy.data.lights.new(name, 'AREA')
        lamp.energy = energy
        lamp.shape = 'DISK'
        lamp.size = size
        obj = bpy.data.objects.new(name, lamp)
        preview_collection.objects.link(obj)
        obj.location = location
        aim(obj, target)

    light('Key_softbox', (.10, -.12, .20), 1.2, .11)
    light('Fill_softbox', (-.13, -.06, .10), .25, .12)
    light('Rim_softbox', (.04, .10, .16), .65, .10)
    floor = bpy.data.meshes.new('StudioFloor')
    floor.from_pydata([(-1, -1, -.00015), (1, -1, -.00015),
                      (1, 1, -.00015), (-1, 1, -.00015)], [], [(0, 1, 2, 3)])
    floor_obj = bpy.data.objects.new('StudioFloor_not_asset', floor)
    preview_collection.objects.link(floor_obj)
    floor.materials.append(materials['accent'])
    camera_data = bpy.data.cameras.new('PreviewCamera')
    camera = bpy.data.objects.new('PreviewCamera', camera_data)
    preview_collection.objects.link(camera)
    camera_data.type = 'ORTHO'
    camera_data.clip_start = .001
    camera_data.clip_end = 10
    scene.camera = camera
    views = [
        ('preview_overall.png', (.16, -.23, .17), (0, 0, .049), .142, False),
        ('preview_mouth.png', (.10, -.13, .24), (0, 0, .081), .092, False),
        ('preview_section.png', (.0, -.30, .115), (0, 0, .049), .131, True),
    ]
    for name, location, target, scale, section in views:
        camera.location = location
        aim(camera, target)
        camera_data.ortho_scale = scale
        visual_collection.hide_render = section
        section_collection.hide_render = not section
        section_collection.hide_viewport = not section
        if render:
            scene.render.filepath = str(out / name)
            bpy.ops.render.render(write_still=True)
    visual_collection.hide_render = False
    section_collection.hide_render = True
    section_collection.hide_viewport = True
    camera.location = views[0][1]
    aim(camera, views[0][2])
    camera_data.ortho_scale = views[0][3]
    bpy.context.view_layer.objects.active = visuals[0]
    bpy.ops.object.select_all(action='DESELECT')
    visuals[0].select_set(True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'bottle.blend'))
    report = dict(blender_version=bpy.app.version_string, device=scene.cycles.device,
                  samples=samples, asset_meshes=len(visuals), colliders=len(data['colliders']),
                  asset_rigid_bodies=0, asset_scale=[1, 1, 1], meters_per_unit=1,
                  authored_meshes_manifold_positive_volume=True,
                  section_is_actual_mesh_cut=True, powder_preview_geometry=False,
                  section_cut_face_tint='diagnostic terracotta; not part of asset materials',
                  previews=[view[0] for view in views] if render else [])
    (out / 'blender_validation.json').write_text(json.dumps(report, indent=2) + '\n')


def main(argv=None):
    """Create JSON and Blender source, optionally rendering three CPU previews."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--samples', type=int, default=40)
    parser.add_argument('--json-only', action='store_true')
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error('--samples must be positive')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    data = build_geometry()
    (out / 'geometry.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    if not args.json_only:
        _create_blender(data, out, args.render, args.samples)
    print(json.dumps(dict(out=str(out), mass_kg=data['mass_kg'], volume_m3=data['volume_m3'],
                          center_of_mass_m=data['center_of_mass_m'],
                          colliders=len(data['colliders'])), indent=2))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
