"""Derive a capless SDF 15 mL tube from the exact legacy water-bath asset."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'outputs/scientific_workbench_r7_task_assets_20260813/packages/centrifuge_tube_15ml_closed'
OUT = ROOT/'outputs/fehlings_open_tube15_r1_20260907/package'
ENTRY = '/World/CentrifugeTube15mlClosed'
SOURCE_ROOT = ENTRY+'/Visual/Source/centrifuge_tube_15ml_red_cap_ROOT'
BODY = SOURCE_ROOT+'/Tube_Body_Hollow/Tube_Body_Hollow_Mesh'
CAP = SOURCE_ROOT+'/Cap_Controller'


def mass_ratio(body_volume, cap_volume, source_mass):
    return source_mass*body_volume/(body_volume+cap_volume)


def build():
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
    import numpy as np
    import trimesh
    from convert_asset.simple_sdf_liquid_runtime import _triangles, _ray_x_intersection

    if OUT.exists():
        raise FileExistsError(OUT)
    shutil.copytree(SOURCE, OUT)
    shutil.rmtree(OUT/'evidence')
    (OUT/'evidence').mkdir()
    stage = Usd.Stage.Open(str(OUT/'asset.usd'))
    inverse = UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath(ENTRY)).GetInverse()

    def geometry(path):
        triangles = [tuple(tuple(inverse.Transform(Gf.Vec3d(*p))) for p in tri) for tri in _triangles(stage, path)]
        mesh = trimesh.Trimesh(vertices=np.asarray(triangles).reshape(-1,3), faces=np.arange(len(triangles)*3).reshape(-1,3), process=True)
        mesh.fix_normals()
        if not mesh.is_watertight or mesh.volume <= 0:
            raise ValueError(f'source mesh is not a closed solid: {path}')
        return mesh, triangles

    body, triangles = geometry(BODY)
    cap, _ = geometry(CAP+'/Cap_Removable/Cap_Shell_Mesh')
    root = stage.GetPrimAtPath(ENTRY)
    mass = mass_ratio(body.volume, cap.volume, root.GetAttribute('physics:mass').Get())
    stage.OverridePrim(CAP).SetActive(False)
    for name in ('__aan_collision_proxy', '__aan_frame_support'):
        stage.OverridePrim(ENTRY+'/'+name).SetActive(False)
    prim = stage.GetPrimAtPath(BODY)
    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr('sdf')
    prim.AddAppliedSchema('PhysxSDFMeshCollisionAPI')
    prim.AddAppliedSchema('PhysxCollisionAPI')
    prim.CreateAttribute('physxSDFMeshCollision:sdfResolution', Sdf.ValueTypeNames.Float).Set(256.0)
    prim.CreateAttribute('physxCollision:contactOffset', Sdf.ValueTypeNames.Float).Set(0.001)
    prim.CreateAttribute('physxCollision:restOffset', Sdf.ValueTypeNames.Float).Set(0.0)
    props = body.mass_properties
    tensor = np.asarray(props['inertia'])*mass/body.volume
    eigenvalues, axes = np.linalg.eigh(tensor)
    if np.linalg.det(axes) < 0:
        axes[:,0] *= -1
    from scipy.spatial.transform import Rotation
    q = Rotation.from_matrix(axes).as_quat()
    api = UsdPhysics.MassAPI.Apply(root)
    api.CreateMassAttr(mass)
    api.CreateCenterOfMassAttr(Gf.Vec3f(*body.center_mass))
    api.CreateDiagonalInertiaAttr(Gf.Vec3f(*eigenvalues))
    api.CreatePrincipalAxesAttr(Gf.Quatf(float(q[3]), Gf.Vec3f(*q[:3])))
    UsdPhysics.RigidBodyAPI(root).CreateKinematicEnabledAttr(False)
    # Producer-measured conservative cavity rings for the visual reaction sample.
    profile = []
    for z in np.linspace(0.004, 0.090, 88):
        hits = [v for tri in triangles if (v := _ray_x_intersection(1e-7,float(z),tri)) is not None and v > 1e-6]
        if len(hits) < 2:
            continue
        profile.append([float(z), min(hits)-0.0002])
    stage.GetRootLayer().Save()
    manifest = {'package_id': 'fehlings_open_tube15_r1', 'overall_status': 'runtime_pending',
        'entrypoints': {'root_usd': 'asset.usd', 'asset_entry_prim': ENTRY, 'default_prim': 'World'},
        'source': {'asset': str(SOURCE/'asset.usd'), 'sha256': sha256((SOURCE/'asset.usd').read_bytes()).hexdigest()},
        'asset_sha256': sha256((OUT/'asset.usd').read_bytes()).hexdigest(),
        'changes': ['cap and old closed collision proxies inactive', 'exact unchanged hollow body mesh SDF', 'cap-excluded provisional geometry mass'],
        'mass_kg': mass, 'center_of_mass_m': list(body.center_mass), 'parameter_status': 'provisional_geometry',
        'cavity_profile_m': profile, 'mouth_z_m': 0.101, 'outer_radius_m': 0.00861,
        'claims': {'body_visual_mesh_unchanged': True, 'cap_collision_disabled': True,
                   'robot_policy_success': False, 'benchmark_success': False}}
    (OUT/'evidence/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(OUT)


if __name__ == '__main__':
    build()
