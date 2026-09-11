"""Blender-owned flared boat with original world dimensions and baked SI scale."""
import argparse
import json
from pathlib import Path
import sys


def main():
    import bpy
    import bmesh
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.out.mkdir(parents=True,exist_ok=False)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.
    def ring(x,y,z,c):
        return [(-x+c,-y,z),(x-c,-y,z),(x,-y+c,z),(x,y-c,z),
                (x-c,y,z),(-x+c,y,z),(-x,y-c,z),(-x,-y+c,z)]
    ob = ring(.035,.025,-.0064,.004)
    ot = ring(.054,.041,.0216,.006)
    it = ring(.052333333,.040,.0216,.005)
    ib = ring(.033333333,.024,-.0048,.003)
    points = ob+ot+it+ib
    faces = []
    for k in range(3):
        for i in range(8):
            j = (i+1)%8
            faces.append((k*8+i,k*8+j,(k+1)*8+j,(k+1)*8+i))
    faces.extend([tuple(reversed(range(8))),tuple(range(24,32))])
    mesh = bpy.data.meshes.new('WeighingBoatShell')
    mesh.from_pydata(points,[],faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    assert all(edge.is_manifold for edge in bm.edges)
    assert bm.calc_volume(signed=True)>0
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('WeighingBoat',mesh)
    scene.collection.objects.link(obj)
    obj.scale = (.6,1.,1.)
    obj['scope'] = 'SI geometry; original X scale is baked before export; root scale 1'
    mat = bpy.data.materials.new('White weighing boat')
    mat.diffuse_color = (.83,.84,.82,1.)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.83,.84,.82,1.)
    shader.inputs['Roughness'].default_value = .65
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bevel = obj.modifiers.new('Soft rim edges','BEVEL')
    bevel.width = .0005
    bevel.segments = 3
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mesh = obj.data
    colliders = []
    wall_faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    for i in range(8):
        j = (i+1)%8
        colliders.append(dict(name=f'Wall_{i}',points=[ob[i],ob[j],ot[i],ot[j],ib[i],ib[j],it[i],it[j]],faces=wall_faces))
    floor = ring(.035,.025,-.0064,.004)+ring(.035,.025,-.0048,.004)
    floor_faces = [tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    colliders.append(dict(name='Floor',points=floor,faces=floor_faces))
    for part in colliders:
        part['points'] = [(x*.6,y,z) for x,y,z in part['points']]
    import numpy as np
    from mathutils import Matrix
    mesh.calc_loop_triangles()
    vertices = np.array([tuple(v.co) for v in mesh.vertices])
    triangles = vertices[np.array([tuple(t.vertices) for t in mesh.loop_triangles])]
    a0,b0,c0 = triangles[:,0],triangles[:,1],triangles[:,2]
    volumes = np.einsum('ij,ij->i',a0,np.cross(b0,c0))/6
    volume = volumes.sum()
    sums = triangles.sum(1)
    com = np.einsum('i,ij->j',volumes,sums)/(4*volume)
    second = np.einsum('i,ij,ik->jk',volumes,sums,sums)/20
    for points0 in (a0,b0,c0):
        second += np.einsum('i,ij,ik->jk',volumes,points0,points0)/20
    inertia = .01/volume*(np.trace(second)*np.eye(3)-second)-.01*(com@com*np.eye(3)-np.outer(com,com))
    values,axes = np.linalg.eigh(inertia)
    assert volume>0 and values.min()>0
    if np.linalg.det(axes)<0:
        axes[:,0] *= -1
    q = Matrix(axes.tolist()).to_quaternion()
    data = dict(visual=dict(points=[tuple(v.co) for v in mesh.vertices],faces=[tuple(f.vertices) for f in mesh.polygons]),
                colliders=colliders,mass_kg=.01,root_scale=[1,1,1],physical_outer_dimensions_m=[.0648,.082,.028],
                center_of_mass_m=com.tolist(),diagonal_inertia_kg_m2=values.tolist(),principal_axes_wxyz=list(q),
                floor_top_local_z=-.0048,producer='Blender procedural flared weighing boat')
    (a.out/'geometry.json').write_text(json.dumps(data,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str((a.out/'weighing_boat.blend').resolve()))


if __name__=='__main__':
    main()
