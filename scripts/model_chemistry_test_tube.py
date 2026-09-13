"""Generic engineering 18 x 150 mm glass tube, exact JSON and editable Blender.

Run in Blender 4.4.3 with --out DIR --render; --reopen audits the saved source
in a separate process without regenerating or modifying it. All lengths are SI.
"""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys


SEGMENTS = 128
DENSITY = 2230.0


def file_sha(path):
    """Hash artifact bytes, never a pathname or a reserialized document."""
    return sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    """Write human-readable finite JSON evidence."""
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def _profiles():
    def hemisphere(radius):
        return [[.009-radius*math.cos(i*math.pi/96), radius*math.sin(i*math.pi/96)]
                for i in range(49)]

    outer, inner = hemisphere(.009), hemisphere(.008)
    outer[0], inner[0] = [0., 0.], [.001, 0.]
    for z in [i/1000 for i in range(11, 148, 2)]:
        outer.append([z, .009])
        inner.append([z, .008])
    # Gentle outward flare, then the upper half of a 1 mm roll centred at
    # radius 9 mm / z149 mm. No overlapping torus or seam solids.
    for i in range(1, 17):
        t = i/16
        outer.append([.147+.002*t, .009+.001*t*t*(3-2*t)])
    for i in range(1, 25):
        a = i*math.pi/48
        outer.append([.149+.001*math.sin(a), .009+.001*math.cos(a)])
    inner.append([.149, .008])
    for i in range(1, 25):
        a = math.pi-i*math.pi/48
        inner.append([.149+.001*math.sin(a), .009+.001*math.cos(a)])
    outer[-1] = inner[-1] = [.150, .009]
    return outer, inner


def _shell(profile):
    points, rings, faces = [], [], []
    for z, radius in profile:
        start = len(points)
        if radius == 0:
            points.append([0., 0., z])
            rings.append([start])
        else:
            points.extend([[radius*math.cos(2*math.pi*i/SEGMENTS),
                            radius*math.sin(2*math.pi*i/SEGMENTS), z]
                           for i in range(SEGMENTS)])
            rings.append(list(range(start, len(points))))
    for low, high in zip(rings, rings[1:]):
        for i in range(SEGMENTS):
            j = (i+1) % SEGMENTS
            if len(low) == 1:
                faces.append([low[0], high[j], high[i]])
            elif len(high) == 1:
                faces.append([low[i], low[j], high[0]])
            else:
                faces.extend([[low[i], low[j], high[j]], [low[i], high[j], high[i]]])
    return dict(name='GlassShell', points=points, faces=faces)


def build_geometry():
    """Build the approved fixed nominal shape using signed glass-solid moments."""
    # Reuse the established standard-library geometry/moments implementation.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from model_compact_powder_bottle import _moments

    outer, inner = _profiles()
    mesh = _shell(outer + list(reversed(inner[:-1])))
    volume, first, second = _moments(mesh)
    com = [value/volume for value in first]
    mass = DENSITY*volume
    inertia = [DENSITY*sum(second[j] for j in range(3) if j != k)
               - mass*sum(com[j]**2 for j in range(3) if j != k) for k in range(3)]
    return dict(
        schema='chemistry-test-tube-geometry-v1', mesh=mesh,
        parameter_status='engineering_geometry', meters_per_unit=1, up_axis='Z',
        root_scale=[1, 1, 1], outer_profile_m=outer, cavity_profile_m=inner,
        outer_radius_m=.009, max_rim_radius_m=.010, mouth_z_m=.150,
        wall_thickness_m=.001, density_kg_m3=DENSITY,
        bottom_sphere_center_m=[0, 0, .009], bottom_outer_radius_m=.009,
        bottom_inner_radius_m=.008, volume_m3=volume, mass_kg=mass,
        center_of_mass_m=com, diagonal_inertia_kg_m2=inertia,
        principal_axes_wxyz=[1, 0, 0, 0], segments=SEGMENTS,
        cavity_interpolation='linear radius in z between actual meridian vertices; '
        '128-sided angular chords lie inside this envelope (max body radial deficit 2.41 micrometres)',
        mass_method='signed tetrahedral integration of the exact closed triangulated glass solid; '
        'XYZ principal axes by rotational/reflection symmetry',
        source_evidence=dict(
            urls=['https://www.sigmaaldrich.com/US/en/product/sigma/z653543',
                  'https://www.smithscientific.com/product/test-tubes-neutral-borosilicate-18x150-08wall-with-rim-100pcs-per-pack-6213/'],
            availability='User-supplied indexed product sizes; full pages unavailable. '
            'Nominal 18 x 150 mm only; no manufacturer-replica claim.',
            engineering_parameters=['1.0 mm wall', 'lip profile', '2230 kg/m3 density',
                                    'IOR 1.47', 'roughness 0.02']),
    )


def _blender_audit(data):
    import bmesh
    import bpy

    obj = bpy.data.objects['GlassShell']
    root = bpy.data.objects['TestTube']
    expected = data['mesh']
    actual = dict(points=[list(v.co) for v in obj.data.vertices],
                  faces=[list(p.vertices) for p in obj.data.polygons])
    if actual['faces'] != expected['faces'] or len(actual['points']) != len(expected['points']):
        raise ValueError('Blender topology differs from geometry JSON')
    error = max(abs(a-b) for p, q in zip(actual['points'], expected['points'])
                for a, b in zip(p, q))
    if error > 1e-8:
        raise ValueError('Blender points differ from geometry JSON')
    for node in (root, obj):
        if (max(abs(v) for v in node.location) > 1e-12
                or max(abs(v) for v in node.rotation_euler) > 1e-12
                or list(node.scale) != [1., 1., 1.]):
            raise ValueError('Nonidentity asset transform')
    if obj.parent != root or len(obj.modifiers):
        raise ValueError('Unexpected source hierarchy/modifiers')
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    volume = bm.calc_volume(signed=True)
    closed = all(e.is_manifold and e.is_contiguous for e in bm.edges)
    nondegenerate = all(f.calc_area() > 1e-15 for f in bm.faces)
    euler = len(bm.verts)-len(bm.edges)+len(bm.faces)
    outward = True
    for face in bm.faces:
        center = face.calc_center_median()
        if .01 < center.z < .14:
            radial = math.hypot(center.x, center.y)
            dot = face.normal.x*center.x + face.normal.y*center.y
            outward &= dot > 0 if radial > .0085 else dot < 0
    bm.free()
    if not (closed and nondegenerate and outward and euler == 2
            and abs(volume/data['volume_m3']-1) < 1e-5):
        raise ValueError('Failed bmesh closed glass-solid/orientation/volume checks')
    # Independent triangle BVH rays descend through the opening to the real floor.
    for x, expected_z in [(0., .001), (.003, .009-math.sqrt(.008**2-.003**2))]:
        hit, location, normal, _ = obj.ray_cast((x, 0, .16), (0, 0, -1))
        if not hit or abs(location.z-expected_z) > .00001 or normal.z <= 0:
            raise ValueError('Lumen blocked or inner bottom normal reversed')
    shader = obj.data.materials[0].node_tree.nodes['Principled BSDF']
    if (shader.inputs['Transmission Weight'].default_value != 1
            or abs(shader.inputs['IOR'].default_value-1.47) > 1e-6
            or abs(shader.inputs['Roughness'].default_value-.02) > 1e-6
            or list(shader.inputs['Base Color'].default_value) != [1., 1., 1., 1.]
            or shader.inputs['Emission Strength'].default_value != 0):
        raise ValueError('Source material must remain clear transmissive glass')
    return dict(status='pass', blender_version=bpy.app.version_string,
                vertices=len(actual['points']), triangles=len(actual['faces']),
                max_point_error_m=error, bmesh_volume_m3=volume,
                closed_manifold=True, consistent_winding=True, outward_from_glass=True,
                nondegenerate=True, euler_characteristic=euler, lumen_rays_pass=True,
                material_transmission=1, glass_ior=1.47, roughness=.02,
                source_hierarchy='TestTube/GlassShell', scale=[1, 1, 1])


def _create_blender(data, out, render, samples):
    import bpy
    from mathutils import Vector

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 16
    scene.cycles.transmission_bounces = 12
    scene.render.resolution_x, scene.render.resolution_y = 720, 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.6, .6, .6, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    asset = bpy.data.collections.new('ASSET_Visuals')
    studio = bpy.data.collections.new('PREVIEW_Studio_not_asset')
    scene.collection.children.link(asset)
    scene.collection.children.link(studio)
    root = bpy.data.objects.new('TestTube', None)
    asset.objects.link(root)
    root['geometry_contract'] = 'geometry.json'
    root['parameter_status'] = 'engineering_geometry'
    root['mass_kg'] = data['mass_kg']
    mesh = bpy.data.meshes.new('GlassShell')
    mesh.from_pydata(data['mesh']['points'], [], data['mesh']['faces'])
    mesh.update()
    obj = bpy.data.objects.new('GlassShell', mesh)
    asset.objects.link(obj)
    obj.parent = root
    material = bpy.data.materials.new('Clear_colorless_borosilicate_engineering')
    material.use_nodes = True
    shader = material.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (1, 1, 1, 1)
    shader.inputs['Transmission Weight'].default_value = 1
    shader.inputs['Roughness'].default_value = .02
    shader.inputs['IOR'].default_value = 1.47
    shader.inputs['Emission Strength'].default_value = 0
    mesh.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True

    def aim(node, target):
        node.rotation_euler = (Vector(target)-node.location).to_track_quat('-Z', 'Y').to_euler()

    for name, position, energy, size in [
            ('Key', (.08, -.10, .15), 1.5, .12),
            ('Rim', (-.07, .06, .10), 2.0, .10),
            ('Top', (.03, .02, .22), .6, .08)]:
        lamp = bpy.data.lights.new(name, 'AREA')
        lamp.energy, lamp.size = energy, size
        node = bpy.data.objects.new(name, lamp)
        studio.objects.link(node)
        node.location = position
        aim(node, (0, 0, .08))
    # Neutral contrasting studio floor: no tint, label or insert on the asset.
    floor = bpy.data.meshes.new('Floor')
    floor.from_pydata([(-2, -2, -.0001), (2, -2, -.0001),
                      (2, 2, -.0001), (-2, 2, -.0001)], [], [(0, 1, 2, 3)])
    node = bpy.data.objects.new('Floor_not_asset', floor)
    studio.objects.link(node)
    backdrop = bpy.data.materials.new('Neutral_studio')
    backdrop.use_nodes = True
    bsdf = backdrop.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (.10, .10, .10, 1)
    bsdf.inputs['Roughness'].default_value = .65
    floor.materials.append(backdrop)
    camera_data = bpy.data.cameras.new('PreviewCamera')
    camera = bpy.data.objects.new('PreviewCamera', camera_data)
    studio.objects.link(camera)
    camera_data.type, camera_data.clip_start, camera_data.clip_end = 'ORTHO', .001, 10
    scene.camera = camera
    views = [('preview_overview.png', (.18, -.30, .16), (0, 0, .075), .18),
             ('preview_mouth.png', (.04, -.06, .207), (0, 0, .147), .036)]
    audit = _blender_audit(data)
    for name, position, target, scale in views:
        camera.location = position
        aim(camera, target)
        camera_data.ortho_scale = scale
        if render:
            scene.render.filepath = str(out/name)
            bpy.ops.render.render(write_still=True)
    camera.location = views[0][1]
    aim(camera, views[0][2])
    camera_data.ortho_scale = views[0][3]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'tube.blend'))
    audit.update(device='CPU', engine='CYCLES', samples=samples,
                 blend_sha256=file_sha(out/'tube.blend'),
                 geometry_sha256=file_sha(out/'geometry.json'),
                 previews={v[0]: file_sha(out/v[0]) for v in views} if render else {})
    write_json(out/'blender_production.json', audit)


def main(argv=None):
    """Create fresh source or independently reopen it in this Blender process."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--samples', type=int, default=64)
    parser.add_argument('--reopen', action='store_true')
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error('samples must be positive')
    out = args.out.resolve()
    if args.reopen:
        import bpy
        before = file_sha(out/'tube.blend')
        bpy.ops.wm.open_mainfile(filepath=str(out/'tube.blend'))
        data = json.loads((out/'geometry.json').read_text())
        report = _blender_audit(data)
        if file_sha(out/'tube.blend') != before:
            raise ValueError('Reopen changed source bytes')
        report.update(independent_process_reopen=True, blend_sha256=before,
                      geometry_sha256=file_sha(out/'geometry.json'))
        write_json(out/'blender_reopen.json', report)
    else:
        out.mkdir(parents=True, exist_ok=False)
        data = build_geometry()
        write_json(out/'geometry.json', data)
        _create_blender(data, out, args.render, args.samples)
    print(json.dumps(dict(out=str(out), mass_kg=data['mass_kg'], status='pass')))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
