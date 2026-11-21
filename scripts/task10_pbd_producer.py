#!/usr/bin/env python3
"""Task10 source-bound GPU PBD candidate with preserved scene/material assets.

This independent task recipe requires runtime observations in both 4.1 and 4.5.
It is not a promotion of the older isaac41-only small-container recipe.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RECEIVER = '/World/obj_receiver_flask'
BURETTE = '/World/obj_titration_station/Instance/Burette'
BODY = BURETTE + '/body_link'
FLUID = '/World/Task10Fluid'
SPACING = .0015
DEAD_SPACING = .0002
PARTICLE_VOLUME_M3 = SPACING**3
PARTICLE_MASS_KG = PARTICLE_VOLUME_M3 * 1000


def sha(path):
    """Hash a source or output file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()



def physics_timestep(physics_hz):
    """Validate the native integer scene rate before writing any assets."""
    try:
        valid = not isinstance(physics_hz, bool) and math.isfinite(physics_hz) and physics_hz > 0 and int(physics_hz) == physics_hz
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise ValueError('physics_hz must be a positive integer')
    return 1.0 / int(physics_hz)


def configure_runtime_rate(contract, physics_hz):
    """Declare scene and driver rates without creating a host PhysicsScene."""
    contract = dict(contract)
    contract.update(physics_dt=physics_timestep(physics_hz), physics_hz=int(physics_hz),
                    scene_time_steps_per_second=int(physics_hz))
    contract['observed_step_dt_required'] = int(physics_hz) == 120
    return contract


def runtime_signature(physics_signature, contract):
    """Bind the complete runtime contract, including dt, to physical opinions."""
    value = {'physics_configuration_sha256': physics_signature, 'runtime_contract': contract}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_actual_step_dt(report, target_dt):
    """Reject nominal-rate certificates without consistent native step evidence."""
    evidence = report.get('actual_step_dt_evidence', {})
    if evidence.get('source') != 'native_physics_step_callback':
        raise ValueError('native physics-step callback evidence is required')
    count = evidence.get('count')
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError('native physics-step sample count is invalid')
    tolerance = 1e-8
    for key in ['min_s', 'max_s', 'target_s', 'world_physics_dt_s']:
        value = evidence.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value-target_dt) > tolerance:
            raise ValueError('native physics-step clock mismatch: ' + key)
    if evidence['min_s'] > evidence['max_s']:
        raise ValueError('native physics-step bounds are reversed')
    total = evidence.get('sum_s')
    if not isinstance(total, (int, float)) or not math.isfinite(total) or abs(total-count*target_dt) > count*tolerance:
        raise ValueError('native physics-step accumulated time mismatch')
    scene_rate = evidence.get('scene_time_steps_per_second')
    if not isinstance(scene_rate, (int, float)) or not math.isfinite(scene_rate) or scene_rate <= 0 or abs(1/scene_rate-target_dt) > tolerance:
        raise ValueError('native PhysicsScene rate mismatch')


def validate_settled_summary(evidence, tolerance, require_full_containment=False):
    """Validate surface bounds and the declared full-run or historical tail scope."""
    if evidence.get('tail_max_outside_count') != 0 or (require_full_containment and evidence.get('max_outside_count') != 0):
        raise ValueError('settled-state containment gate failed')
    height = evidence.get('tail_height_error_range_m', [])
    if len(height) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in height) or height[0] > height[1] or height[0] < -tolerance or height[1] > tolerance:
        raise ValueError('settled-state surface gate failed')


def validate_system_overrides(overrides):
    """Permit explicit positive physical scalars while preserving fluid dynamics."""
    allowed = {'fluidRestOffset', 'restOffset', 'solidRestOffset', 'contactOffset',
               'particleContactOffset', 'maxVelocity', 'maxDepenetrationVelocity'}
    result = {}
    for label, values in (overrides or {}).items():
        if label not in {'Source', 'Receiver', 'Falling', 'DeadPrecharge'} or not isinstance(values, dict):
            raise ValueError('invalid particle-system override target')
        result[label] = {}
        for name, value in values.items():
            if name not in allowed or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('invalid positive physical override: ' + name)
            result[label][name] = float(value)
    return result


def derive_runtime_candidate(baseline, out, physics_hz=120, system_overrides=None, repair_clamp=False, source_wall_refinement=False, receiver_wall_refinement=False):
    """Copy a hash-verified frozen seed without regenerating geometry or MDL.

    A changed rate requires new physical observations. Previous qualification is
    retained only as historical evidence, never assigned to the new candidate.
    """
    physics_timestep(physics_hz)
    system_overrides = validate_system_overrides(system_overrides)
    baseline = Path(baseline).resolve()
    out = Path(out).resolve()
    if out.exists() or baseline in out.parents:
        raise ValueError('candidate output must be new and outside its frozen baseline')
    inventory = json.loads((baseline / 'snapshot_hashes.json').read_text())
    for name, digest in inventory.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('invalid baseline inventory path: ' + name)
        if not (baseline / relative).is_file() or sha(baseline / relative) != digest:
            raise ValueError('frozen baseline hash mismatch: ' + name)
    actual = {str(p.relative_to(baseline)) for p in baseline.rglob('*') if p.is_file() and p != baseline / 'snapshot_hashes.json'}
    if actual != set(inventory):
        raise ValueError('frozen baseline inventory is incomplete')
    for required in ['manifest.json', 'initial_particles.npz', 'package/pbd.usda']:
        if required not in inventory:
            raise ValueError('frozen baseline missing ' + required)
    manifest = json.loads((baseline / 'manifest.json').read_text())
    shutil.copytree(baseline, out)
    evidence = out / 'evidence'
    evidence.mkdir(exist_ok=True)
    shutil.copy2(baseline / 'manifest.json', evidence / 'baseline_manifest.json')
    shutil.copy2(baseline / 'snapshot_hashes.json', evidence / 'baseline_snapshot_hashes.json')
    if system_overrides or repair_clamp or source_wall_refinement or receiver_wall_refinement:
        from pxr import Sdf, Usd
        layer = Sdf.Layer.FindOrOpen(str(out / 'package/pbd.usda'))
        if repair_clamp:
            from scripts.task10_120_collisions import repair_source_clamp
            target = Usd.Stage.Open(str(out/'package/isaac45.usda'))
            target.SetEditTarget(layer)
            source = Usd.Stage.Open(str(out/'package/source/scene.usd'))
            manifest['clamp_collision_repair'] = repair_source_clamp(target, source)
            manifest['collision_repair_producer_sha256'] = sha(ROOT/'scripts/task10_120_collisions.py')
        if source_wall_refinement:
            from scripts.task10_120_collisions import refine_source_wall
            target = Usd.Stage.Open(str(out/'package/isaac45.usda'))
            target.SetEditTarget(layer)
            manifest['source_wall_refinement'] = refine_source_wall(target,manifest['systems']['Source']['cavity_profile_local_m'],annular_wedge)
            manifest['collision_repair_producer_sha256'] = sha(ROOT/'scripts/task10_120_collisions.py')
        if receiver_wall_refinement:
            from scripts.task10_120_collisions import refine_receiver_wall
            target = Usd.Stage.Open(str(out/'package/isaac45.usda'))
            target.SetEditTarget(layer)
            manifest['receiver_wall_refinement'] = refine_receiver_wall(target,manifest['systems']['Receiver']['cavity_profile_local_m'],annular_wedge)
            manifest['collision_repair_producer_sha256'] = sha(ROOT/'scripts/task10_120_collisions.py')
        for label, values in system_overrides.items():
            for name, value in values.items():
                path = Sdf.Path(manifest['systems'][label]['system_path']).AppendProperty(name)
                spec = layer.GetAttributeAtPath(path)
                if not spec:
                    raise ValueError('physical override attribute is not authored: ' + str(path))
                spec.default = value
                manifest['particle_system_parameters'][label][name] = spec.default
        signature = physics_digest(layer, manifest['source_sha256'])
        layer.customLayerData = {**layer.customLayerData, 'physics_configuration_sha256': signature}
        layer.Save()
        manifest['physics_configuration_sha256'] = signature
        manifest['system_overrides'] = system_overrides
    manifest['runtime_contract'] = configure_runtime_rate(manifest['runtime_contract'], physics_hz)
    if source_wall_refinement or receiver_wall_refinement:
        manifest['runtime_contract']['scene_gpu_found_lost_aggregate_pairs_capacity']=8192
        manifest['runtime_contract']['scene_gpu_total_aggregate_pairs_capacity']=8192
    manifest['runtime_configuration_sha256'] = runtime_signature(manifest['physics_configuration_sha256'], manifest['runtime_contract'])
    manifest['producer_sha256'] = sha(__file__)
    manifest['status'] = 'static_candidate_runtime_unqualified'
    manifest['runtime_qualification'] = {'isaac41': 'not_run', 'isaac45': 'not_run'}
    manifest.pop('producer_settling_observation', None)
    manifest['initial_state'] = {
        'kind': 'frozen_baseline_seed_re_equilibration_required',
        'all_particles_preserved': True, 'measured_velocities_preserved': True,
        'baseline_manifest_sha256': inventory['manifest.json'],
        'baseline_pbd_sha256': inventory['package/pbd.usda'],
        'initial_particles_sha256': inventory['initial_particles.npz'],
        'baseline_manifest': 'evidence/baseline_manifest.json',
        'baseline_hash_inventory': 'evidence/baseline_snapshot_hashes.json',
        'runtime_cold_requalification': 'required at the declared native physics rate',
        'historical_evidence_scope': 'copied settling reports describe the baseline rate only; they do not qualify this candidate',
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    hashes = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p != out / 'snapshot_hashes.json'}
    (out / 'snapshot_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    return manifest


def reframe_settled(points, velocities, actual_matrix, original_matrix):
    """Re-express every measured particle under the original rigid container pose.

    This uses one rigid affine transform for all positions and its rotation for
    all velocities. It never clips, removes, or individually relocates a point.
    """
    import numpy as np
    points=np.asarray(points,dtype=float);velocities=np.asarray(velocities,dtype=float)
    if points.ndim!=2 or points.shape[1]!=3 or velocities.shape!=points.shape:
        raise ValueError('settled position/velocity shape mismatch')
    actual=np.asarray(actual_matrix,dtype=float);original=np.asarray(original_matrix,dtype=float)
    if actual.shape!=(4,4) or original.shape!=(4,4):raise ValueError('rigid matrix shape mismatch')
    if not all(np.isfinite(a).all() for a in [points,velocities,actual,original]):raise ValueError('nonfinite settled state')
    for matrix in [actual,original]:
        if not np.allclose(matrix[:3,:3]@matrix[:3,:3].T,np.eye(3),atol=1e-5):raise ValueError('settled reframing requires rigid unit-scale container transforms')
    rotation=np.linalg.inv(actual[:3,:3])@original[:3,:3]
    return (points-actual[3,:3])@rotation+original[3,:3],velocities@rotation


def physics_digest(layer, source_sha256):
    """Bind the immutable layer opinions while excluding mutable fluid state."""
    from pxr import Sdf
    clone=Sdf.Layer.CreateAnonymous();clone.TransferContent(layer);clone.customLayerData={}
    for label in ['Source','Receiver','Falling','DeadPrecharge']:
        for prop in ['points','velocities','widths','ids','physxParticle:simulationPoints']:
            spec=clone.GetAttributeAtPath(Sdf.Path(FLUID+'/'+label+'Particles').AppendProperty(prop))
            if spec:spec.ClearDefaultValue()
    return hashlib.sha256((source_sha256+clone.ExportToString()).encode()).hexdigest()

def profile_volume(profile):
    """Integrate the piecewise-linear axial cavity as conical frusta."""
    return sum(math.pi*(b[0]-a[0])*(a[1]**2+a[1]*b[1]+b[1]**2)/3 for a, b in zip(profile[:-1], profile[1:]))


def sample_profile(profile, spacing=SPACING, margin=.0007):
    """Seed a centered Cartesian lattice within an axial radius profile."""
    import numpy as np
    rows = np.asarray(profile, dtype=float)
    if len(rows) < 2 or np.any(np.diff(rows[:, 0]) <= 0) or np.any(rows[:, 1] <= 0):
        raise ValueError('axial profile must have increasing z and positive radius')
    extent = int(math.ceil(rows[:, 1].max()/spacing))
    coordinates = np.arange(-extent, extent+1)*spacing
    xx, yy = np.meshgrid(coordinates, coordinates)
    result = []
    for z in np.arange(rows[0, 0]+spacing/2, rows[-1, 0]-spacing/4, spacing):
        interval=min(len(rows)-2,max(0,int(np.searchsorted(rows[:,0],z)-1)))
        slope=(rows[interval+1,1]-rows[interval,1])/(rows[interval+1,0]-rows[interval,0])
        radius = float(np.interp(z, rows[:, 0], rows[:, 1]))-margin*math.sqrt(1+slope*slope)
        mask = xx*xx+yy*yy <= max(0, radius)**2
        if radius > 0:
            result.extend([[float(x), float(y), float(z)] for x, y in zip(xx[mask], yy[mask])])
    return result


def mesh_profile(stage, path):
    """Recover the modeled liquid envelope from axial mesh rings."""
    import numpy as np
    from pxr import UsdGeom
    points = np.asarray(UsdGeom.Mesh(stage.GetPrimAtPath(path)).GetPointsAttr().Get())
    z = np.round(points[:, 2], 7)
    r = np.linalg.norm(points[:, :2], axis=1)
    return [[float(level), float(r[z == level].max())] for level in np.unique(z) if r[z == level].max() > 1e-8]


def annular_wedge(r0, outer0, r1, outer1, z0, z1, angle0, angle1):
    """Construct one convex wall cell with no surface crossing the cavity."""
    vertices = [(r*math.cos(a), r*math.sin(a), z) for z, inner, outer in [(z0,r0,outer0),(z1,r1,outer1)] for r in [inner,outer] for a in [angle0,angle1]]
    faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    return vertices, [4]*6, [i for f in faces for i in f]



def closed_shell(profile, thickness=.003, bottom=.002, segments=64):
    """Build one watertight, open-mouth solid shell around an axial cavity."""
    vertices=[]; rings=[]
    # Outer bottom ring precedes axial wall rings.
    for z,r in [(profile[0][0]-bottom,profile[0][1]+thickness)]+[(z,r+thickness) for z,r in profile]+profile:
        rings.append(list(range(len(vertices),len(vertices)+segments)))
        vertices.extend([(r*math.cos(2*math.pi*i/segments),r*math.sin(2*math.pi*i/segments),z) for i in range(segments)])
    n=len(profile);outer=rings[:n+1];inner=rings[n+1:];faces=[]
    for a,b in zip(outer[:-1],outer[1:]):
        faces.extend([(a[i],a[(i+1)%segments],b[(i+1)%segments],b[i]) for i in range(segments)])
    for a,b in zip(inner[:-1],inner[1:]):
        faces.extend([(a[(i+1)%segments],a[i],b[i],b[(i+1)%segments]) for i in range(segments)])
    faces.extend([(inner[-1][i],outer[-1][i],outer[-1][(i+1)%segments],inner[-1][(i+1)%segments]) for i in range(segments)])
    center_inner=len(vertices);vertices.append((0,0,profile[0][0]))
    center_outer=len(vertices);vertices.append((0,0,profile[0][0]-bottom))
    faces.extend([(center_inner,inner[0][i],inner[0][(i+1)%segments]) for i in range(segments)])
    faces.extend([(center_outer,outer[0][(i+1)%segments],outer[0][i]) for i in range(segments)])
    return vertices,[len(f) for f in faces],[i for f in faces for i in f]

def attr(prim, name, type_name, value):
    """Author a schema-compatible typed USD property without importing simulator SDKs."""
    return prim.CreateAttribute(name, type_name, custom=False).Set(value)


def author_particles(stage, label, points, material_path, overrides=None):
    """Author independent fluid system, actual points, total set mass and isosurface."""
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics, UsdShade
    system_path = FLUID+'/'+label+'System'
    system = stage.DefinePrim(system_path, 'PhysxParticleSystem')
    system.SetMetadata('apiSchemas', Sdf.TokenListOp.Create(prependedItems=['PhysxParticleIsosurfaceAPI','PhysxParticleSmoothingAPI','PhysxParticleAnisotropyAPI']))
    params = {
        'particleContactOffset': .00125, 'contactOffset': .00125,
        'restOffset': .0004, 'solidRestOffset': .0004, 'fluidRestOffset': .000845 if label=='Source' else (.000847 if label=='Receiver' else .0009),
        'maxVelocity': 3.0 if label=='Falling' else (.01 if label=='DeadPrecharge' else .2), 'maxDepenetrationVelocity': 2.0,
        'physxParticleIsosurface:gridSpacing': .00075,
        'physxParticleIsosurface:surfaceDistance': .0012,
        'physxParticleIsosurface:gridSmoothingRadius': 2.0,
        'physxParticleAnisotropy:scale': 1.0,
        'physxParticleAnisotropy:min': .5, 'physxParticleAnisotropy:max': 2.0,
        'physxParticleSmoothing:strength': .5,
    }
    if label=='Receiver':
        params.update({'restOffset':.0015,'contactOffset':.002})
    if label=='Source':
        params.update({'restOffset':.001,'solidRestOffset':.00075,'particleContactOffset':.0015,'contactOffset':.0015})
    if label=='DeadPrecharge':
        params.update({'particleContactOffset':.00018,'contactOffset':.00045,'restOffset':.00032,'solidRestOffset':.0001,'fluidRestOffset':.000127,'physxParticleIsosurface:gridSpacing':.00016,'physxParticleIsosurface:surfaceDistance':.000395,'physxParticleIsosurface:gridSmoothingRadius':2.0})
    params.update(validate_system_overrides({label: overrides or {}})[label])
    set_spacing=DEAD_SPACING if label=='DeadPrecharge' else SPACING
    set_particle_mass=set_spacing**3*1000
    for name, value in params.items(): attr(system, name, Sdf.ValueTypeNames.Float, value)
    for name, value in {'solverPositionIterationCount':64,'physxParticleIsosurface:maxVertices':1000000,'physxParticleIsosurface:maxTriangles':2000000,'physxParticleIsosurface:maxSubgrids':10000,'physxParticleIsosurface:numMeshSmoothingPasses':1,'physxParticleIsosurface:numMeshNormalSmoothingPasses':1}.items():attr(system,name,Sdf.ValueTypeNames.Int,value)
    attr(system,'physxParticleIsosurface:gridFilteringPasses',Sdf.ValueTypeNames.String,'GSRS')
    for name in ['enableCCD','particleSystemEnabled','physxParticleIsosurface:isosurfaceEnabled','physxParticleAnisotropy:particleAnisotropyEnabled']:attr(system,name,Sdf.ValueTypeNames.Bool,True)
    attr(system,'physxParticleSmoothing:particleSmoothingEnabled',Sdf.ValueTypeNames.Bool,False)
    system.CreateRelationship('simulationOwner').SetTargets([])
    UsdShade.MaterialBindingAPI.Apply(system).Bind(UsdShade.Material(stage.GetPrimAtPath(material_path)))
    physics_mat = FLUID+'/WaterPhysics'
    material = stage.DefinePrim(physics_mat, 'Material')
    material.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysxPBDMaterialAPI']))
    for name, value in {'density':1000.,'friction':.1,'viscosity':0.0,'cohesion':0.0,'surfaceTension':0.0,'adhesion':0.0}.items():attr(material,'physxPBDMaterial:'+name,Sdf.ValueTypeNames.Float,value)
    UsdShade.MaterialBindingAPI.Apply(system).Bind(UsdShade.Material(material), materialPurpose='physics')
    values=[Gf.Vec3f(*map(float,p)) for p in points]
    geom=UsdGeom.Points.Define(stage,FLUID+'/'+label+'Particles')
    prim=geom.GetPrim()
    prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysxParticleSetAPI','PhysicsMassAPI','MaterialBindingAPI']))
    geom.CreatePointsAttr(values)
    geom.CreateVelocitiesAttr([Gf.Vec3f(0)]*len(values))
    geom.CreateWidthsAttr([set_spacing]*len(values))
    geom.CreateIdsAttr(list(range(len(values))))
    for name in ['fluid','selfCollision','particleEnabled']:attr(prim,'physxParticle:'+name,Sdf.ValueTypeNames.Bool,True)
    attr(prim,'physxParticle:particleGroup',Sdf.ValueTypeNames.Int,{'Source':0,'Falling':1,'Receiver':2,'DeadPrecharge':3}[label])
    prim.CreateRelationship('physxParticle:particleSystem').SetTargets([system_path])
    UsdPhysics.MassAPI(prim).CreateMassAttr(set_particle_mass*len(values))
    UsdShade.MaterialBindingAPI(prim).Bind(UsdShade.Material(stage.GetPrimAtPath(material_path)))



def author_sdf(stage, path, vertices, counts, indices, resolution, contact, rest):
    """Author a closed source-bound collision mesh in numerically stable local units."""
    import numpy as np
    from pxr import Gf,Sdf,UsdGeom
    values=np.asarray(vertices,dtype=float);center=(values.min(axis=0)+values.max(axis=0))/2
    mesh=UsdGeom.Mesh.Define(stage,path)
    mesh.CreatePointsAttr([Gf.Vec3f(*map(float,p)) for p in (values-center)*1000])
    mesh.CreateFaceVertexCountsAttr(counts);mesh.CreateFaceVertexIndicesAttr(indices);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible')
    mesh.AddTranslateOp().Set(Gf.Vec3d(*map(float,center)));mesh.AddScaleOp().Set(Gf.Vec3f(.001))
    prim=mesh.GetPrim();prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxSDFMeshCollisionAPI','PhysxTriangleMeshCollisionAPI']))
    attr(prim,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(prim,'physics:approximation',Sdf.ValueTypeNames.Token,'sdf')
    for name,value in [('sdfResolution',resolution),('sdfSubgridResolution',6)]:attr(prim,'physxSDFMeshCollision:'+name,Sdf.ValueTypeNames.Int,value)
    for name,value in [('sdfMargin',.01),('sdfNarrowBandThickness',.01)]:attr(prim,'physxSDFMeshCollision:'+name,Sdf.ValueTypeNames.Float,value)
    attr(prim,'physxTriangleMeshCollision:weldTolerance',Sdf.ValueTypeNames.Float,0.0);attr(prim,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,contact);attr(prim,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,rest)
    return mesh

def material_closure(source_stage, package, runtime, core):
    """Close authored MDL roots using existing AAN recursive helper mirroring."""
    from pxr import Sdf, Usd
    from convert_asset.asset_application_normalizer.mdl_runtime_closure import _mirror_mdl_runtime_dependencies, build_material_runtime_closure
    dest=package/'materials'/runtime
    (dest/'deps/mdl').mkdir(parents=True,exist_ok=True)
    records=[]; bindings=[]; names={}
    for prim in source_stage.Traverse():
        for prop in prim.GetAttributes():
            value=prop.Get()
            if not isinstance(value,Sdf.AssetPath) or not value.path.endswith('.mdl'):continue
            source=Path(value.resolvedPath)
            if not source.is_file():raise ValueError('unresolved MDL '+value.path)
            name=source.name; digest=sha(source)
            if name in names and names[name]!=digest:raise ValueError('conflicting MDL basename '+name)
            if name not in names:
                target=dest/'deps/mdl'/name;shutil.copy2(source,target);names[name]=digest
                records.append({'source_mdl_assets':[{'package_path':'deps/mdl/'+name,'resolved_path':str(source),'package_sha256':digest}]})
            bindings.append((str(prop.GetPath()),'deps/mdl/'+name))
    roots=[core/'mdl',core/'Base',core]
    actions=_mirror_mdl_runtime_dependencies(dest,records,runtime_mdl_roots=roots)
    result=build_material_runtime_closure(dest,records,runtime_mdl_roots=[])
    if result.overall_status!='pass':raise ValueError(str(result.blocked_reasons))
    stage=Usd.Stage.CreateNew(str(dest/'materials.usda'))
    for path,value in bindings:
        prop=Sdf.Path(path);prim=stage.OverridePrim(prop.GetPrimPath());attr(prim,prop.name,Sdf.ValueTypeNames.Asset,Sdf.AssetPath(value))
    stage.GetRootLayer().Save()
    report={'status':result.overall_status,'source_roots_preserved':True,'runtime_compiler':'not_run','material_runtime_closure':result.material_runtime_closure,'mirror_actions':actions}
    (dest/'closure.json').write_text(json.dumps(report,indent=2)+'\n')
    return {'runtime':runtime,'status':'static_pass','root_count':len(names),'binding_count':len(bindings)}


def author_on_label(stage, source):
    """Replace only baked OFF mesh with a small extruded ON stroke mesh in its plane."""
    import numpy as np
    from pxr import Gf,UsdGeom
    path='/World/obj_magnetic_stirrer/Labels/DisplayText/DisplayText_Curve'
    mesh=UsdGeom.Mesh(source.GetPrimAtPath(path));points=np.asarray(mesh.GetPointsAttr().Get())
    center=(points.min(axis=0)+points.max(axis=0))/2
    _,_,basis=np.linalg.svd(points-points.mean(axis=0),full_matrices=False);n=basis[-1]
    if n[2]<0:n=-n
    u=np.array([1.,0,0]);v=np.cross(n,u);v/=np.linalg.norm(v)
    # Same local text plane; source display remains at exactly its authored pose.
    strokes=[(-.003,-.0015,-.0026,.0015),(-.001,.0,-.0006,.0015),(-.001,-.0015,-.0006,0),(-.003,.0011,-.0006,.0015),(-.003,-.0015,-.0006,-.0011),(.0001,-.0015,.0005,.0015),(.0025,-.0015,.0029,.0015)]
    polygons=[[(a,b),(c,b),(c,d),(a,d)] for a,b,c,d in strokes]
    polygons.append([(.0004,.0015),(.0008,.0015),(.0026,-.0015),(.0022,-.0015)])
    verts=[];indices=[];counts=[]
    for polygon in polygons:
        k=len(verts)
        for h in [-.000015,.000045]:
            verts.extend([Gf.Vec3f(*map(float,center+u*x+v*y+n*h)) for x,y in polygon])
        for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:counts.append(4);indices.extend([k+j for j in face])
    target=UsdGeom.Mesh(stage.OverridePrim(path));target.CreatePointsAttr(verts);target.CreateFaceVertexCountsAttr(counts);target.CreateFaceVertexIndicesAttr(indices);target.CreateNormalsAttr().Block();target.CreateExtentAttr().Block();target.CreateSubdivisionSchemeAttr('none');target.GetPrim().CreateAttribute('primvars:sharp_face', mesh.GetPrim().GetAttribute('primvars:sharp_face').GetTypeName()).Block()
    return {'path':path,'label':'ON','physical_stirring':False,'geometry':'extruded stroke label in original text plane'}


def build(source_path, out, settled_state=None, settling_report=None, *, physics_hz=240, system_overrides=None, repair_clamp=False, source_wall_refinement=False, receiver_wall_refinement=False):
    """Produce source-preserving candidate package, world-space seeds and manifest."""
    physics_dt = physics_timestep(physics_hz)
    system_overrides = validate_system_overrides(system_overrides)
    import numpy as np
    from pxr import Gf,Sdf,Usd,UsdGeom,UsdPhysics,UsdShade,UsdUtils
    source_path=Path(source_path).resolve();out=Path(out).resolve();package=out/'package'
    package.mkdir(parents=True,exist_ok=True)
    source_hash=sha(source_path)
    if not (package/'source').exists():shutil.copytree(source_path.parent,package/'source')
    source=Usd.Stage.Open(str(source_path));cache=UsdGeom.XformCache()
    receiver_profile=mesh_profile(source,RECEIVER+'/VisualLiquid/Solution')
    lower=mesh_profile(source,BODY+'/Visual/liquid_precharge')
    full_source_profile=lower+[[.2297,.005],[.23,.005]]
    valve_z=-.18;valve_radius=float(np.interp(valve_z,*np.asarray(full_source_profile).T))
    dead_profile=[p for p in full_source_profile if p[0]<valve_z]+[[valve_z,valve_radius]]
    source_profile=[[valve_z,valve_radius]]+[p for p in full_source_profile if p[0]>valve_z]
    receiver_inner=[[.003684,.032737],[.0044044,.0373375],[.0065656,.0401355],[.010273,.0411575],[.0156322,.0404408],[.0314777,.0364366],[.0666443,.0278526],[.1011929,.0198689],[.1151844,.0168591],[.1215061,.0163219],[.1330451,.0160195],[.1441043,.016299],[.1489867,.0175035],[.15,.01905]]
    fill_profile=[p for p in receiver_inner if p[0]<.089]+[[.089,float(np.interp(.089,*np.asarray(receiver_inner).T))]]
    receiver_local=sample_profile(fill_profile,spacing=.00135,margin=.0018)
    receiver_target_count=int(round(profile_volume(receiver_profile)/PARTICLE_VOLUME_M3))
    receiver_local=[receiver_local[i] for i in np.linspace(0,len(receiver_local)-1,receiver_target_count,dtype=int)]
    raw_source_cavity=[[z,r+(.00005 if r<.005 else 0)] for z,r in source_profile]+[[.28,.005]]
    seat_profile=[[-.18,.001],[-.1797,.0018],[-.1793,.0024],[-.1788,.0029],[-.178,.00335],[-.1775,float(np.interp(-.1775,*np.asarray(raw_source_cavity).T))]]
    physical_source_profile=seat_profile+[p for p in raw_source_cavity if p[0]>-.1775]
    old_seat=[p for p in raw_source_cavity if p[0]<-.1775]+[seat_profile[-1]]
    seat_displaced_volume=profile_volume(old_seat)-profile_volume(seat_profile)
    source_seed_profile=[p for p in physical_source_profile if p[0]<=.23]
    source_local=sample_profile(source_seed_profile,spacing=.0012,margin=.00135)
    source_local=[p for p in source_local if p[2]>=-.17855]
    source_target_count=int(round((profile_volume(source_profile)-seat_displaced_volume)/PARTICLE_VOLUME_M3))
    if len(source_local)<source_target_count:raise ValueError('source seeds do not cover geometric inventory')
    source_local=[source_local[i] for i in np.linspace(0,len(source_local)-1,source_target_count,dtype=int)]
    dead_seed_profile=[[ -.278,float(np.interp(-.278,*np.asarray(dead_profile).T))]]+[p for p in dead_profile if -.278<p[0]<-.183]+[[-.183,float(np.interp(-.183,*np.asarray(dead_profile).T))]]
    dead_local=[p for p in sample_profile(dead_seed_profile,spacing=.000165,margin=.00033) if -.27755<=p[2]<=-.18365]
    dead_target_count=int(round(profile_volume(dead_seed_profile)/(DEAD_SPACING**3)))
    if len(dead_local)<dead_target_count:raise ValueError('insufficient dead precharge seeds')
    dead_local=[dead_local[i] for i in np.linspace(0,len(dead_local)-1,dead_target_count,dtype=int)]
    initial={}
    for name,local,path in [('Receiver',receiver_local,RECEIVER),('Source',source_local,BODY),('Falling',[],BODY),('DeadPrecharge',dead_local,BODY)]:
        transform=cache.GetLocalToWorldTransform(source.GetPrimAtPath(path))
        initial[name]=[[float(v) for v in transform.Transform(Gf.Vec3d(*point))] for point in local]
    layer=package/'pbd.usda';stage=Usd.Stage.CreateNew(str(layer));UsdGeom.SetStageMetersPerUnit(stage,1);UsdGeom.SetStageUpAxis(stage,'Z')
    for path in [RECEIVER+'/VisualLiquid/Solution',BODY+'/Visual/liquid_column',BODY+'/Visual/liquid_meniscus',BODY+'/Visual/liquid_precharge','/World/obj_titration_station/Instance/Runtime/TitrationFlowGraph']:
        stage.OverridePrim(path).SetActive(False)
    for name in ['Source','Falling','Receiver','DeadPrecharge']:
        mat=UsdShade.Material.Define(stage,FLUID+'/'+name+'Material')
        mat.GetPrim().GetReferences().AddInternalReference(RECEIVER+'/VisualLiquid/Looks/Water')
        author_particles(stage,name,initial[name],mat.GetPath(),system_overrides.get(name))
    # The exact source hollow flask wall remains the sole receiver collider.
    receiver_mesh=stage.OverridePrim(RECEIVER+'/Visual/Source/mesh')
    receiver_mesh.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysxSDFMeshCollisionAPI','PhysxCollisionAPI']))
    attr(receiver_mesh,'physics:approximation',Sdf.ValueTypeNames.Token,'sdf')
    for name,value in {'sdfResolution':512,'sdfSubgridResolution':6}.items():attr(receiver_mesh,'physxSDFMeshCollision:'+name,Sdf.ValueTypeNames.Int,value)
    for name,value in {'sdfMargin':.00035,'sdfNarrowBandThickness':.00035}.items():attr(receiver_mesh,'physxSDFMeshCollision:'+name,Sdf.ValueTypeNames.Float,value)
    for name,value in {'contactOffset':.00035,'restOffset':.000175}.items():attr(receiver_mesh,'physxCollision:'+name,Sdf.ValueTypeNames.Float,value)
    attr(receiver_mesh,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,False)
    receiver_inner=[[.003684,.032737],[.0044044,.0373375],[.0065656,.0401355],[.010273,.0411575],[.0156322,.0404408],[.0314777,.0364366],[.0666443,.0278526],[.1011929,.0198689],[.1151844,.0168591],[.1215061,.0163219],[.1330451,.0160195],[.1441043,.016299],[.1489867,.0175035],[.15,.01905]]
    dense_receiver=[receiver_inner[0]]
    for a,b in zip(receiver_inner[:-1],receiver_inner[1:]):
        count=max(1,int(math.ceil((b[0]-a[0])/.008)))
        dense_receiver.extend([[a[0]+(b[0]-a[0])*j/count,a[1]+(b[1]-a[1])*j/count] for j in range(1,count+1)])
    for segment,(a,b) in enumerate(zip(dense_receiver[:-1],dense_receiver[1:])):
        for ring in range(32):
            z0=max(receiver_inner[0][0],a[0]-.00015);z1=min(receiver_inner[-1][0],b[0]+.00015);r0=float(np.interp(z0,*np.asarray(receiver_inner).T));r1=float(np.interp(z1,*np.asarray(receiver_inner).T))
            pts,counts,ids=annular_wedge(r0,r0+.003,r1,r1+.003,z0,z1,2*math.pi*ring/32-.0087,2*math.pi*(ring+1)/32+.0087)
            mesh=UsdGeom.Mesh.Define(stage,RECEIVER+f'/Task10PBDWall/S{segment:02d}_{ring:02d}');mesh.CreatePointsAttr([Gf.Vec3f(*v) for v in pts]);mesh.CreateFaceVertexCountsAttr(counts);mesh.CreateFaceVertexIndicesAttr(ids);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible')
            p=mesh.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']));attr(p,'physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.0);attr(p,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(p,'physics:approximation',Sdf.ValueTypeNames.Token,'convexHull');attr(p,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.00025);attr(p,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.0001)
    for ring in range(32):
        angle0=2*math.pi*ring/32;angle1=2*math.pi*(ring+1)/32
        verts=[(0,0,z) for z in [0,.003684]]+[(.0339*math.cos(a),.0339*math.sin(a),z) for z in [0,.003684] for a in [angle0,angle1]]
        bottom=UsdGeom.Mesh.Define(stage,RECEIVER+f'/Task10PBDWall/GlassBottom_{ring:02d}');bottom.CreatePointsAttr([Gf.Vec3f(*v) for v in verts]);bottom.CreateFaceVertexCountsAttr([3,3,4,4,4]);bottom.CreateFaceVertexIndicesAttr([0,3,2,1,4,5,0,2,4,1,2,3,5,4,3,0,1,5]);bottom.CreateSubdivisionSchemeAttr('none');bottom.CreateVisibilityAttr('invisible');p=bottom.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']));attr(p,'physics:approximation',Sdf.ValueTypeNames.Token,'convexHull');attr(p,'physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.0);attr(p,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(p,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.00025);attr(p,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.0001)

    # Replace solid cylinder proxies with lumen-preserving wall wedges; the
    # tiny original outlet remains geometrically open (no artificial floor).
    disabled=[]
    for prim in Usd.PrimRange(source.GetPrimAtPath(BODY)):
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            attr(stage.OverridePrim(prim.GetPath()),'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,False);disabled.append(str(prim.GetPath()))
    wall_profile=[[lower[0][0]-.0002,.0004]]+[[z,r+(.00005 if r<.005 else 0)] for z,r in lower]+[[.28,.005]]
    wall_profile=sorted(wall_profile+[[-.18,float(np.interp(-.18,*np.asarray(wall_profile).T))]])
    dense_wall=[wall_profile[0]]
    for a,b in zip(wall_profile[:-1],wall_profile[1:]):
        n=max(1,int(math.ceil((b[0]-a[0])/.01)))
        dense_wall.extend([[a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n] for j in range(1,n+1)])
    wall_profile=dense_wall
    wall_count=0
    for segment,(a,b) in enumerate(zip(wall_profile[:-1],wall_profile[1:])):
        for ring in range(16):
            z0=max(wall_profile[0][0],a[0]-.00015);z1=min(wall_profile[-1][0],b[0]+.00015);r0=float(np.interp(z0,*np.asarray(wall_profile).T));r1=float(np.interp(z1,*np.asarray(wall_profile).T))
            def outer_radius(z):
                return .0008+(z+.28)/.05*.0012 if z<=-.23 else (.002 if z<=-.18 else (.00552 if z<=-.12 else .006))
            pts,counts,ids=annular_wedge(r0,r0+.003,r1,r1+.003,z0,z1,2*math.pi*ring/16-.0087,2*math.pi*(ring+1)/16+.0087)
            mesh=UsdGeom.Mesh.Define(stage,BODY+f'/Task10PBDWall/S{segment:02d}_{ring:02d}')
            mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in pts]);mesh.CreateFaceVertexCountsAttr(counts);mesh.CreateFaceVertexIndicesAttr(ids);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible')
            p=mesh.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
            attr(p,'physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.0);attr(p,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(p,'physics:approximation',Sdf.ValueTypeNames.Token,'convexHull');attr(p,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.00025);attr(p,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.0001);wall_count+=1
    for name,z,side,thickness in [('OutletFluxBoundary',-.279,.003,.002),('ValveSeatFluxBoundary',-.1815,.012,.003)]:
        cap=UsdGeom.Cube.Define(stage,BODY+'/Task10PBDWall/'+name);cap.CreateSizeAttr(1);cap.AddTranslateOp().Set(Gf.Vec3d(0,0,z));cap.AddScaleOp().Set(Gf.Vec3f(side,side,thickness));cap.CreateVisibilityAttr('invisible');cap.GetPrim().SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysxCollisionAPI']));attr(cap.GetPrim(),'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(cap.GetPrim(),'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.00008);attr(cap.GetPrim(),'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.00003)

    stage.OverridePrim(BODY+'/Task10PBDWall').SetActive(False)
    stage.OverridePrim(RECEIVER+'/Task10PBDWall').SetActive(False)
    physical_dead_profile=[[z,r+.00005] for z,r in dead_seed_profile]
    pts,counts,indices=closed_shell(physical_dead_profile,.003,.002,64)
    author_sdf(stage,BODY+'/Task10PBDCollision/DeadPrechargeShell',pts,counts,indices,4096,.00015,.000075)
    cap=UsdGeom.Cube.Define(stage,BODY+'/Task10PBDCollision/OutletFluxCap');cap.CreateSizeAttr(1);cap.AddTranslateOp().Set(Gf.Vec3d(0,0,-.279));cap.AddScaleOp().Set(Gf.Vec3d(.006,.006,.002));cap.CreateVisibilityAttr('invisible')
    cap.GetPrim().SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysxCollisionAPI']))
    attr(cap.GetPrim(),'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(cap.GetPrim(),'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.00015);attr(cap.GetPrim(),'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.000075)
    # Exact short convex contacts reinforce the same narrow outlet side wall.
    # Coordinates are normalized before hull cooking; no new fluid floor exists.
    for axial,(z0,z1) in enumerate(zip(np.linspace(-.278,-.230,13)[:-1],np.linspace(-.278,-.230,13)[1:])):
        r0=float(np.interp(z0,*np.asarray(physical_dead_profile).T));r1=float(np.interp(z1,*np.asarray(physical_dead_profile).T))
        for sector in range(32):
            points,counts,indices=annular_wedge(r0,r0+.003,r1,r1+.003,z0,z1,2*math.pi*sector/32-.002,2*math.pi*(sector+1)/32+.002)
            values=np.asarray(points);center=(values.min(axis=0)+values.max(axis=0))/2
            mesh=UsdGeom.Mesh.Define(stage,BODY+f'/Task10PBDCollision/OutletCollar/S{axial}_{sector:02d}');mesh.CreatePointsAttr([Gf.Vec3f(*map(float,v)) for v in (values-center)*1000]);mesh.CreateFaceVertexCountsAttr(counts);mesh.CreateFaceVertexIndicesAttr(indices);mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible');mesh.AddTranslateOp().Set(Gf.Vec3d(*map(float,center)));mesh.AddScaleOp().Set(Gf.Vec3f(.001))
            prim=mesh.GetPrim();prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']));attr(prim,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(prim,'physics:approximation',Sdf.ValueTypeNames.Token,'convexHull');attr(prim,'physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.0);attr(prim,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.00015);attr(prim,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.000075)
    pts,counts,indices=closed_shell(physical_source_profile,.003,.003,64)
    author_sdf(stage,BODY+'/Task10PBDCollision/SourceShell',pts,counts,indices,4096,.0004,.00025)
    original_mesh=UsdGeom.Mesh(source.GetPrimAtPath(RECEIVER+'/Visual/Source/mesh'))
    author_sdf(stage,RECEIVER+'/Task10PBDCollision/ReceiverShell',original_mesh.GetPointsAttr().Get(),original_mesh.GetFaceVertexCountsAttr().Get(),original_mesh.GetFaceVertexIndicesAttr().Get(),512,.00025,.0001)
    label=author_on_label(stage,source)
    source_wall_repair = None
    if source_wall_refinement:
        from scripts.task10_120_collisions import refine_source_wall
        source_wall_repair = refine_source_wall(stage,physical_source_profile,annular_wedge)
    receiver_wall_repair = None
    if receiver_wall_refinement:
        from scripts.task10_120_collisions import refine_receiver_wall
        receiver_wall_repair = refine_receiver_wall(stage,receiver_inner,annular_wedge)
    clamp_repair = None
    if repair_clamp:
        from scripts.task10_120_collisions import repair_source_clamp
        clamp_repair = repair_source_clamp(stage, source)
    stage.GetRootLayer().Save()
    runtime_roots={'isaac41':Path('/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/lib/python3.10/site-packages/omni/mdl/core'),'isaac45':Path('/isaac-sim/kit/mdl/core')}
    closures=[]
    for runtime,core in runtime_roots.items():
        closures.append(material_closure(source,package,runtime,core))
        entry=Usd.Stage.CreateNew(str(package/(runtime+'.usda')))
        entry.GetRootLayer().subLayerPaths=['pbd.usda',f'materials/{runtime}/materials.usda','source/scene.usd'];UsdGeom.SetStageMetersPerUnit(entry,1);UsdGeom.SetStageUpAxis(entry,'Z');entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save()
    tip=cache.GetLocalToWorldTransform(source.GetPrimAtPath(BURETTE+'/drop_origin')).ExtractTranslation()
    manifest={'schema':'convertasset.task10.pbd-producer.v1','source':str(source_path),'source_sha256':source_hash,'producer_sha256':sha(__file__),'status':'static_candidate_runtime_unqualified','runtime_qualification':{'isaac41':'not_run','isaac45':'not_run'},'particle_spacing_m':SPACING,'particle_volume_m3':PARTICLE_VOLUME_M3,'particle_volume_ml':PARTICLE_VOLUME_M3*1e6,'per_particle_mass_kg':PARTICLE_MASS_KG,'density_kg_m3':1000,'systems':{name:{'system_path':FLUID+'/'+name+'System','particle_path':FLUID+'/'+name+'Particles','material_path':FLUID+'/'+name+'Material','count':len(initial[name]),'particle_spacing_m':DEAD_SPACING if name=='DeadPrecharge' else SPACING,'particle_volume_ml':(DEAD_SPACING**3 if name=='DeadPrecharge' else PARTICLE_VOLUME_M3)*1e6,'per_particle_mass_kg':(DEAD_SPACING**3*1000 if name=='DeadPrecharge' else PARTICLE_MASS_KG),'initial_volume_ml':len(initial[name])*(DEAD_SPACING**3 if name=='DeadPrecharge' else PARTICLE_VOLUME_M3)*1e6,'initial_total_mass_kg':len(initial[name])*(DEAD_SPACING**3*1000 if name=='DeadPrecharge' else PARTICLE_MASS_KG)} for name in initial},'receiver_profile_local_m':receiver_profile,'receiver_reference_visual_volume_ml':profile_volume(receiver_profile)*1e6,'source_profile_body_local_m':source_profile,'source_reference_visual_volume_ml':profile_volume(source_profile)*1e6,'dead_precharge_profile_body_local_m':dead_profile,'dead_precharge_reference_visual_volume_ml':profile_volume(dead_profile)*1e6,'dead_precharge_cap_displaced_volume_ml':(profile_volume(dead_profile)-profile_volume(dead_seed_profile))*1e6,'dead_precharge_effective_seed_profile_body_local_m':dead_seed_profile,'full_original_source_volume_ml':profile_volume(full_source_profile)*1e6,'receiver_local_to_world':[[float(v) for v in row] for row in cache.GetLocalToWorldTransform(source.GetPrimAtPath(RECEIVER))],'source_local_to_world':[[float(v) for v in row] for row in cache.GetLocalToWorldTransform(source.GetPrimAtPath(BODY))],'drop_origin_world_m':list(tip),'controlled_emit_center_below_tip_m':.003,'recommended_emit_world_m':[float(tip[0]),float(tip[1]),float(tip[2])-.003],'receiver_mouth_world_z_m':.9767,'receiver_mouth_local_z_m':.15,'receiver_mouth_radius_m':.01905,'receiver_cavity_profile_local_m':receiver_inner,'receiver_floor_local_z_m':.003684,'receiver_wall':{'source_mesh':RECEIVER+'/Visual/Source/mesh','geometry_changed':False,'collision':'source_inner_profile_convex_partitions_and_original_glass_bottom','inner_profile_local_m':receiver_inner,'disabled_source_sdf':True},'burette_wall':{'profile_body_local_m':wall_profile,'partitions':wall_count,'disabled_solid_proxies':disabled,'outward_collision_thickness_m':.003,'thickness_scope':'No-robot containment surrogate; inner cavity and source visible geometry unchanged; no grasp clearance qualification.','bottom_open_visual':True,'numerical_flux_boundaries':['actual_outlet_z0.99','actual_valve_center_z1.09'],'controlled_flux_not_capillary_flow':True,'passive_precharge_separate_resolution':True,'radius_policy':'source fluid profile plus 50um lumen margin in precharge; column inner radius5mm'},'display_label':label,'material_closure':closures,'runtime_contract':{'physics_dt':physics_dt,'gpu_dynamics':True,'gpu_broadphase':True,'solver':'TGS','system_owner':'unbound; consumer bootstrap binds its live PhysicsScene','particle_ccd':True,'update_arrays_together':['points','velocities','widths','ids'],'readback':'Particle smoothing disabled. points is live physical position. simulationPoints is SDK read-only output and is not authored or written by producer.','mass_semantics':'physics:mass is TOTAL set mass = count * per_particle_mass_kg','source_to_tip':'Authorized controlled transfer removes live source particle volume and inserts live falling particles below physical tip; no full valve/throat microfluidics claim.','falling_to_receiver':'Only actual cavity admission permits transfer into receiver material/system; retain particle xyz and velocity during transfer.','dynamic_topology':'USD array resizing candidate must be observed on both runtime versions; no runtime support claim from static authoring.'},'limits':['Independent task-specific PBD parameters; not generic isaac41 recipe promotion to isaac45.','1.5mm lattice under-resolves the source .8mm outlet and differs from exact visual volume; discrete volumes are explicitly reported.','No fake liquid overlay, kinematic liquid or frozen isosurface.','No physical stirring implementation; ON is a static label only.','No GPU or rendered-material qualification at producer build.']}
    physical_dead_full=[[-.28,.0004]]+[[z,r+.00005] for z,r in dead_profile if z<-.183]+[[-.183,float(np.interp(-.183,*np.asarray(dead_profile).T))+.00005]]
    for name,system in manifest['systems'].items():
        if name=='Falling':continue
        system['container_body_path']=RECEIVER if name=='Receiver' else BODY
        system['cavity_profile_local_m']=receiver_inner if name=='Receiver' else (physical_source_profile if name=='Source' else physical_dead_full)
        system['lower_flux_boundary_local_z_m']={'Receiver':.003684,'Source':-.18,'DeadPrecharge':-.28}[name]
        system['upper_flux_boundary_local_z_m']={'Receiver':.15,'Source':.28,'DeadPrecharge':-.183}[name]
        system['numerical_liquid_floor_local_z_m']={'Receiver':.003684,'Source':-.18,'DeadPrecharge':-.278}[name]
        system['reference_visible_surface_local_z_m']={'Receiver':.089,'Source':.23,'DeadPrecharge':-.183}[name]
        system['containment_radial_slop_m']=.00005 if name=='DeadPrecharge' else .00015
        system['containment_z_slop_m']=.00005 if name=='DeadPrecharge' else .00015
        system['surface_height_tolerance_m']=.0005 if name=='DeadPrecharge' else .002
        system['boundary_kind']={'Receiver':['original_glass_floor','open_mouth'],'Source':['controlled_flux_closed_valve_seat','open_burette_mouth'],'DeadPrecharge':['controlled_flux_cap_at_actual_outlet','valve_seat_lower_surface']}[name]
    manifest['numerical_valve_seat_profile_local_m']=seat_profile
    manifest['numerical_valve_seat_displaced_volume_ml']=seat_displaced_volume*1e6
    manifest['raw_source_cavity_profile_local_m']=raw_source_cavity
    manifest['numerical_flux_solid_intervals_body_local_m']={'outlet':[-.28,-.278],'valve':[-.183,-.18]}
    if receiver_wall_repair is not None:
        manifest['receiver_wall_refinement']=receiver_wall_repair
        manifest['collision_repair_producer_sha256']=sha(ROOT/'scripts/task10_120_collisions.py')
    if source_wall_repair is not None:
        manifest['source_wall_refinement']=source_wall_repair
        manifest['collision_repair_producer_sha256']=sha(ROOT/'scripts/task10_120_collisions.py')
    if clamp_repair is not None:
        manifest['clamp_collision_repair']=clamp_repair
        manifest['collision_repair_producer_sha256']=sha(ROOT/'scripts/task10_120_collisions.py')
    manifest['system_overrides']=system_overrides
    manifest['runtime_contract']=configure_runtime_rate(manifest['runtime_contract'], physics_hz)
    if source_wall_refinement or receiver_wall_refinement:
        manifest['runtime_contract']['scene_gpu_found_lost_aggregate_pairs_capacity']=8192
        manifest['runtime_contract']['scene_gpu_total_aggregate_pairs_capacity']=8192
    manifest['runtime_contract']['scene_min_position_iterations']=64
    manifest['runtime_contract']['scene_max_position_iterations']=64
    manifest['runtime_contract']['empty_falling_isosurface']='Consumer sets only isosurfaceEnabled=false when Falling is empty and re-enables it for nonempty sets; particleSystemEnabled remains true. Do not SetActive or toggle systemEnabled for empty buffers.'
    manifest['particle_system_parameters']={name:{a.GetName():a.Get() for a in stage.GetPrimAtPath(FLUID+'/'+name+'System').GetAttributes() if a.HasAuthoredValueOpinion() and isinstance(a.Get(),(str,int,float,bool))} for name in initial}
    manifest['collision_revision']='source-profile continuous SDF shells; original receiver mesh cloned without world-space geometry changes; mm-local collision mesh coordinates with .001 uniform scale'
    manifest['receiver_wall']['collision']='closed source glass mesh cloned as SDF; original enabled collider disabled'
    manifest['receiver_wall']['disabled_source_sdf']=True
    manifest['burette_wall']['outlet_sidewall_collar']={'path':BODY+'/Task10PBDCollision/OutletCollar','local_z_interval_m':[-.278,-.230],'axial_cells':12,'angular_cells':32,'basis':'same source-derived inner radius profile plus existing 50um lumen margin; 3mm outward thickness; no interior cap or raised floor','maximum_polygon_chord_inset_m':.000009}
    manifest['burette_wall']['analytic_outlet_flux_cap']={'path':BODY+'/Task10PBDCollision/OutletFluxCap','top_local_z_m':-.278,'bottom_local_z_m':-.280,'same_boundary_as_sdf_floor':True,'purpose':'exact planar contact at the existing controlled-flux floor; no raised floor or relocated fluid'}
    manifest['receiver_wall']['active_replacement']=RECEIVER+'/Task10PBDCollision/ReceiverShell'
    signature=physics_digest(stage.GetRootLayer(),source_hash)
    stage.GetRootLayer().customLayerData={'physics_configuration_sha256':signature}
    manifest['physics_configuration_sha256']=signature
    manifest['runtime_configuration_sha256']=runtime_signature(signature, manifest['runtime_contract'])
    velocity_arrays={name:np.zeros((len(values),3),dtype=np.float32) for name,values in initial.items()}
    if settled_state is not None:
        if settling_report is None:raise ValueError('settled-state requires its measured settling report')
        state_report=json.loads(Path(settling_report).read_text())
        if state_report.get('physics_configuration_sha256')!=signature:raise ValueError('settled-state physics configuration differs')
        if abs(state_report.get('physics_dt',0)-manifest['runtime_contract']['physics_dt'])>1e-12:raise ValueError('settled-state physics step differs')
        if manifest['runtime_contract']['observed_step_dt_required']:
            validate_actual_step_dt(state_report, physics_dt)
            if state_report.get('runtime_configuration_sha256') != manifest['runtime_configuration_sha256']:raise ValueError('settled-state runtime configuration differs')
        if state_report.get('state_sha256')!=sha(settled_state):raise ValueError('settled-state file hash differs')
        state=np.load(settled_state,allow_pickle=False)
        for name in ['Source','Receiver','DeadPrecharge']:
            item=manifest['systems'][name];evidence=state_report['cavity_summary'][name]
            validate_settled_summary(evidence,item['surface_height_tolerance_m'],manifest['runtime_contract']['observed_step_dt_required'])
            if len(state[name])!=len(initial[name]):raise ValueError('settled-state particle count changed: '+name)
            original=np.asarray(cache.GetLocalToWorldTransform(source.GetPrimAtPath(item['container_body_path'])))
            values,velocities=reframe_settled(state[name],state[name+'_velocities'],state[name+'_body_matrix'],original)
            initial[name]=values.astype(np.float32).tolist();velocity_arrays[name]=velocities.astype(np.float32)
            points=UsdGeom.Points(stage.GetPrimAtPath(item['particle_path']));points.GetPointsAttr().Set([Gf.Vec3f(*map(float,v)) for v in values]);points.GetVelocitiesAttr().Set([Gf.Vec3f(*map(float,v)) for v in velocities])
        manifest['initial_state']={'kind':'measured_physics_settled','state_sha256':sha(settled_state),'report_sha256':sha(settling_report),'all_particles_preserved':True,'pose_mapping':'one rigid-frame map per container; original source placements retained; measured velocities rotated, not zeroed','runtime_cold_requalification':'required'}
        evidence=out/'evidence';evidence.mkdir(exist_ok=True);shutil.copy2(settled_state,evidence/'producer_settled_state.npz');shutil.copy2(settling_report,evidence/'producer_settling_report.json')
        manifest['initial_state']['state_record']='evidence/producer_settled_state.npz';manifest['initial_state']['settling_report']='evidence/producer_settling_report.json'
    stage.GetRootLayer().Save()
    np.savez_compressed(out/'initial_particles.npz',**{name.lower():np.asarray(values,dtype=np.float32).reshape(-1,3) for name,values in initial.items()},**{name.lower()+'_velocities':values for name,values in velocity_arrays.items()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if sha(source_path)!=source_hash:raise RuntimeError('immutable source changed')
    for runtime in runtime_roots:
        composed=Usd.Stage.Open(str(package/(runtime+'.usda')))
        assert composed.GetPrimAtPath(FLUID+'/ReceiverSystem')
        for name in initial:
            material=UsdShade.Material(composed.GetPrimAtPath(FLUID+'/'+name+'Material'))
            assert material.GetSurfaceOutput('mdl').HasConnectedSource()
        layers,assets,missing=UsdUtils.ComputeAllDependencies(str(package/(runtime+'.usda')))
        if missing:raise ValueError(f'missing USD assets: {missing}')
    print(json.dumps({'manifest':str(out/'manifest.json'),'systems':manifest['systems'],'tip':list(tip)},indent=2))
    return manifest


def main():
    """Build one source-bound task10 producer package."""
    parser=argparse.ArgumentParser(description=__doc__)
    origin=parser.add_mutually_exclusive_group(required=True)
    origin.add_argument('--source',type=Path)
    origin.add_argument('--baseline-snapshot',type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--physics-hz',type=int,default=240,help='Native PhysicsScene rate; 240 preserves the historical generator default')
    parser.add_argument('--refine-receiver-wall',action='store_true',help='Add exact receiver-profile normalized convex side-wall contacts')
    parser.add_argument('--refine-source-wall',action='store_true',help='Add open source-profile convex side-wall cells')
    parser.add_argument('--repair-clamp',action='store_true',help='Replace filled source clamp proxy and clip physical pads outside original outer glass')
    parser.add_argument('--system-overrides',type=Path,help='JSON mapping system names to explicit positive physical scalar overrides')
    parser.add_argument('--settled-state',type=Path)
    parser.add_argument('--settling-report',type=Path)
    args=parser.parse_args()
    overrides=json.loads(args.system_overrides.read_text()) if args.system_overrides else None
    if args.baseline_snapshot:
        if args.settled_state or args.settling_report:
            parser.error('baseline derivation preserves its measured seed; do not attach a settling certificate from another rate')
        manifest=derive_runtime_candidate(args.baseline_snapshot,args.out,args.physics_hz,overrides,repair_clamp=args.repair_clamp,source_wall_refinement=args.refine_source_wall,receiver_wall_refinement=args.refine_receiver_wall)
        print(json.dumps({'manifest':str(args.out/'manifest.json'),'runtime_contract':manifest['runtime_contract'],'status':manifest['status']},indent=2))
    else:
        build(args.source,args.out,args.settled_state,args.settling_report,physics_hz=args.physics_hz,system_overrides=overrides,repair_clamp=args.repair_clamp,source_wall_refinement=args.refine_source_wall,receiver_wall_refinement=args.refine_receiver_wall)


if __name__=='__main__':main()
