"""Editable Blender source for the exact open-cavity powder diagnostic tools.

Run: blender --background --factory-startup --python THIS -- --out tools.blend
The authoritative dynamic bodies and collisions are in the producer USD fixture.
"""
import argparse
from pathlib import Path
import sys


def main():
    import bpy
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.out.exists():
        raise FileExistsError(args.out)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.
    def material(name,color,metallic):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color,1.)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color,1.)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = .4
        return mat
    source_mat = material('Source ceramic',(.7,.72,.7),0.)
    pan_mat = material('Receiving boat',(.035,.045,.052),0.)
    spoon_mat = material('Scoop steel',(.43,.52,.58),.8)
    def box(name,center,dimensions,parent,mat):
        bpy.ops.mesh.primitive_cube_add(size=1,location=center)
        obj = bpy.context.object
        obj.name = name
        obj.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.parent = parent
        obj.data.materials.append(mat)
        obj['collision_role'] = 'one convex box of the compound tool; see producer USD'
    def tray(name,location,inner,height,thickness,mat,open_front=False):
        parent = bpy.data.objects.new(name,None)
        scene.collection.objects.link(parent)
        parent.location = location
        x,y = inner
        parts = [('Floor',(0,0,-thickness/2),(x+2*thickness,y+2*thickness,thickness)),
                 ('Left',(0,-(y+thickness)/2,height/2),(x+2*thickness,thickness,height)),
                 ('Right',(0,(y+thickness)/2,height/2),(x+2*thickness,thickness,height)),
                 ('Back',(-(x+thickness)/2,0,height/2),(thickness,y,height))]
        if not open_front:
            parts.append(('Front',((x+thickness)/2,0,height/2),(thickness,y,height)))
        for part,center,dimensions in parts:
            box(name+'_'+part,center,dimensions,parent,mat)
        return parent
    tray('Source',(0,0,.006),(.030,.024),.020,.002,source_mat)
    tray('Receiver',(.070,0,.006),(.034,.030),.010,.002,pan_mat)
    spoon = tray('Spoon',(-.007,0,.040),(.012,.008),.004,.001,spoon_mat,True)
    box('Neck',(-.0065,0,.013),(.001,.005,.026),spoon,spoon_mat)
    box('Handle',(-.024,0,.026),(.036,.005,.002),spoon,spoon_mat)
    scene['scope'] = 'Editable diagnostic-tool geometry; dynamics qualified in Isaac USD, not Blender'
    args.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()))


if __name__ == '__main__':
    main()
