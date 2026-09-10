"""Producer-owned adaptation of the supplied rigid-powder engineering fixture.

The incoming generator is an explicit, hashed build input, not a core dependency.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random


def grain_mass_kg(radius, density):
    if not all(math.isfinite(v) and v > 0 for v in (radius, density)):
        raise ValueError('positive finite radius and density required')
    return density * 4 * math.pi * radius**3 / 3


def fill_positions(count, bound, contact_offset, seed):
    spacing = 2*bound + 2*contact_offset + .00006
    nx, ny = int(.028/spacing), int(.022/spacing)
    if count <= 0 or nx < 1 or ny < 1 or math.ceil(count/(nx*ny))*spacing > .018:
        raise ValueError('initial fill exceeds source cavity')
    rng = random.Random(seed)
    return [((i%nx-(nx-1)/2)*spacing+rng.uniform(-.00001,.00001),
             ((i//nx)%ny-(ny-1)/2)*spacing+rng.uniform(-.00001,.00001),
             .006+bound+.00012+(i//(nx*ny))*spacing+rng.uniform(-.00001,.00001))
            for i in range(count)]


def build(source, output, *, count=4096, radius=.0005, shape='ico', seed=42, hz=240):
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf
    if output.exists():
        raise FileExistsError(output)
    spec = importlib.util.spec_from_file_location('incoming_powder_generator', source/'build_scene.py')
    template = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(template)
    cfg = json.loads((source/'config.json').read_text())
    cfg.update(count=count, equivalent_sphere_radius_m=radius, shape=shape, seed=seed,
               physics_hz=hz, sleep_threshold_m2_s2=0., position_iterations=24,
               velocity_iterations=4, angular_damping=.05)
    grain_mass_kg(radius, cfg['solid_density_kg_m3'])
    meta = template.build(cfg, output)
    stage = Usd.Stage.Open(str(output))
    points = fill_positions(count, meta['bounding_radius_m'], cfg['contact_offset_m'], seed)
    def material(name, color, metallic, roughness):
        mat = UsdShade.Material.Define(stage, '/World/Materials/'+name)
        shader = UsdShade.Shader.Define(stage, str(mat.GetPath())+'/Shader')
        shader.CreateIdAttr('UsdPreviewSurface')
        shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
        shader.CreateInput('metallic', Sdf.ValueTypeNames.Float).Set(metallic)
        shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(roughness)
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), 'surface')
        return mat
    colors = {
        'GrainSurface': ((.78,.63,.20),0.,.8),
        'SpoonSurface': ((.43,.52,.58),.8,.28),
        'SourceSurface': ((.7,.72,.70),0.,.4),
        'PanSurface': ((.035,.045,.052),0.,.62),
        'GroundSurface': ((.085,.12,.15),.1,.6),
    }
    mats = {k: material(k,*v) for k,v in colors.items()}
    for i, pos in enumerate(points):
        prim = stage.GetPrimAtPath(f'/World/Powder/g_{i:05d}')
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*pos))
        if shape == 'ico':
            # Cook a unit-sized shared shape; apply scale at the collider.
            # Avoid absolute mesh-cooking tolerances at submillimeter coordinates.
            mesh = UsdGeom.Mesh(prim)
            mesh.GetPointsAttr().Set([p/radius for p in mesh.GetPointsAttr().Get()])
            mesh.AddScaleOp().Set(Gf.Vec3f(radius))
        prim.CreateAttribute('physxRigidBody:stabilizationThreshold',Sdf.ValueTypeNames.Float).Set(0.)
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(mats['GrainSurface'])
    for name in ('Spoon','Source','Pan','Ground'):
        UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath('/World/'+name)).Bind(mats[name+'Surface'])
    stage.GetRootLayer().Save()
    meta.update(producer='ConvertAsset powder fixture r1',
                source_generator_sha256=hashlib.sha256((source/'build_scene.py').read_bytes()).hexdigest(),
                source_config_sha256=hashlib.sha256((source/'config.json').read_bytes()).hexdigest(),
                initial_fill='seeded jitter with bounded clearance',
                validation='candidate; requires runtime qualification')
    output.with_suffix('.json').write_text(json.dumps(meta,indent=2))
    return meta


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--count',type=int,default=4096)
    p.add_argument('--radius',type=float,default=.0005)
    p.add_argument('--shape',choices=['sphere','ico'],default='ico')
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--hz',type=int,default=240)
    a = p.parse_args()
    build(a.source,a.out,count=a.count,radius=a.radius,shape=a.shape,seed=a.seed,hz=a.hz)
