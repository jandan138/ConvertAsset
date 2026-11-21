"""Task10 source-derived clamp and cavity contacts; no visual/source edits."""
import math

STATION_BODY = '/World/obj_titration_station/Instance/Body'
BURETTE_BODY = '/World/obj_titration_station/Instance/Burette/body_link'


def clipped_cylinder_x(radius, height, *, side, cut_y, segments=64):
    """Return a closed convex cylinder intersected with side*(y-cut_y)>=0."""
    if radius <= 0 or height <= 0 or side not in (-1, 1) or abs(cut_y) >= radius:
        raise ValueError('Invalid clipped pad dimensions')
    polygon = [(radius*math.cos(2*math.pi*i/segments), radius*math.sin(2*math.pi*i/segments)) for i in range(segments)]
    clipped = []
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        inside_a = side*(a[0]-cut_y) >= 0
        inside_b = side*(b[0]-cut_y) >= 0
        if inside_a:
            clipped.append(a)
        if inside_a != inside_b:
            t = (cut_y-a[0])/(b[0]-a[0])
            clipped.append((cut_y,a[1]+t*(b[1]-a[1])))
    n = len(clipped)
    points = [(x,y,z) for x in [-height/2,height/2] for y,z in clipped]
    faces = [list(reversed(range(n))),list(range(n,2*n))]
    faces += [[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
    return points,[len(f) for f in faces],[i for f in faces for i in f]


def repair_source_clamp(stage, source):
    """Replace the filled clamp proxy and clip pad solids at the glass exterior.

    The original C-shaped visible frame supplies three replacement box shapes.
    Four original pad collision paths remain enabled, now as clipped convex
    meshes. No liquid collision filtering, visible edits or transform motion.
    """
    import numpy as np
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
    outer = float(source.GetPrimAtPath(BURETTE_BODY+'/Visual/tube').GetAttribute('radius').Get())
    inner = float(source.GetPrimAtPath(BURETTE_BODY+'/Visual/liquid_column').GetAttribute('radius').Get())
    body_world = UsdGeom.Xformable(source.GetPrimAtPath(STATION_BODY)).ComputeLocalToWorldTransform(0)
    bore_world = UsdGeom.Xformable(source.GetPrimAtPath(BURETTE_BODY)).ComputeLocalToWorldTransform(0).ExtractTranslation()
    bore_local = body_world.GetInverse().Transform(bore_world)
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default','render','proxy'], False, True)
    result = {'kind':'source_visible_C_frame_and_outer_glass_clipped_pads',
              'visible_geometry_or_poses_changed':False,'fluid_collision_filtering':False,
              'glass_outer_radius_m':outer,'fluid_cavity_radius_m':inner,
              'before':[],'after':[],'retained_scope':'three source-visible C-frame boxes plus four solid pad portions outside the glass tangent planes'}

    def bbox(prim):
        bounds = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        return [list(bounds.GetMin()),list(bounds.GetMax())]

    def collision(prim, mesh=False):
        schemas = ['PhysicsCollisionAPI','PhysxCollisionAPI']
        if mesh:
            schemas += ['PhysicsMeshCollisionAPI','PhysxConvexHullCollisionAPI']
        prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=schemas))
        prim.CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True)
        prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.001)
        prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)
        if mesh:
            prim.CreateAttribute('physics:approximation',Sdf.ValueTypeNames.Token).Set('convexHull')
            prim.CreateAttribute('physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float).Set(0.)

    old_path = STATION_BODY+'/Collision/single_clamp_proxy'
    old = source.GetPrimAtPath(old_path)
    result['before'].append({'path':old_path,'type':old.GetTypeName(),'world_aabb_m':bbox(old),
        'inside_bore_witness_world_m':[float(bore_world[0]-.002),float(bore_world[1]),float(bore_world[2])],
        'reason':'solid box covers the negative-X half of the fluid bore'})
    stage.OverridePrim(old_path).CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool,custom=False).Set(False)
    for name in ['single_clamp','clamp_cheek_left','clamp_cheek_right']:
        original = source.GetPrimAtPath(STATION_BODY+'/Visual/'+name)
        cube = UsdGeom.Cube.Define(stage,STATION_BODY+'/Task10ClampCollision/'+name)
        cube.CreateSizeAttr(original.GetAttribute('size').Get())
        relative = UsdGeom.Xformable(original).ComputeLocalToWorldTransform(0)*body_world.GetInverse()
        cube.AddTransformOp(opSuffix='sourceFrame').Set(relative)
        cube.CreateVisibilityAttr('invisible')
        collision(cube.GetPrim())
        bounds = bbox(original)
        dx = max(bounds[0][0]-bore_world[0],0,bore_world[0]-bounds[1][0])
        dy = max(bounds[0][1]-bore_world[1],0,bore_world[1]-bounds[1][1])
        clearance = math.hypot(dx,dy)-inner
        if clearance <= 0:
            raise ValueError('Source C-frame geometry unexpectedly intersects bore')
        result['after'].append({'path':str(cube.GetPath()),'source_visual':str(original.GetPath()),
                               'world_aabb_m':bounds,'cavity_clearance_lower_bound_m':clearance})
    for name in ['pad_left_upper','pad_left_lower','pad_right_upper','pad_right_lower']:
        path = STATION_BODY+'/Collision/'+name
        original = source.GetPrimAtPath(path)
        if original.GetAttribute('axis').Get() != 'X':
            raise ValueError('Expected original pad axis X')
        original_world = UsdGeom.Xformable(original).ComputeLocalToWorldTransform(0)
        center_body = body_world.GetInverse().Transform(original_world.ExtractTranslation())
        side = 1 if center_body[1] > bore_local[1] else -1
        radius = float(original.GetAttribute('radius').Get())
        height = float(original.GetAttribute('height').Get())
        cut_local_y = float(bore_local[1]+side*outer-center_body[1])
        points,counts,indices = clipped_cylinder_x(radius,height,side=side,cut_y=cut_local_y)
        mesh = UsdGeom.Mesh.Define(stage,path)
        mesh.CreatePointsAttr([Gf.Vec3f(*(v*1000 for v in p)) for p in points])
        mesh.CreateFaceVertexCountsAttr(counts)
        mesh.CreateFaceVertexIndicesAttr(indices)
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateVisibilityAttr('invisible')
        original_local = UsdGeom.Xformable(original).GetLocalTransformation()
        transform = mesh.AddTransformOp(opSuffix='producerClamp')
        transform.Set(Gf.Matrix4d().SetScale(Gf.Vec3d(.001))*original_local)
        mesh.SetXformOpOrder([transform])
        collision(mesh.GetPrim(),mesh=True)
        world_points = np.asarray([original_world.Transform(Gf.Vec3d(*p)) for p in points])
        witness = [float(bore_world[0]),float(bore_world[1]+side*.004),float(original_world.ExtractTranslation()[2])]
        result['before'].append({'path':path,'type':'Cylinder','world_aabb_m':bbox(original),
                                'inside_bore_witness_world_m':witness,'reason':'original pad reaches 3mm from axis inside the 5mm fluid bore'})
        result['after'].append({'path':path,'type':'convex clipped Cylinder','world_aabb_m':[world_points.min(axis=0).tolist(),world_points.max(axis=0).tolist()],
                               'clip_plane_distance_from_bore_axis_m':outer,
                               'cavity_clearance_lower_bound_m':outer-inner,
                               'collision_enabled':True,'retained_fraction_analytic':(radius*radius*math.acos(side*cut_local_y/radius)-side*cut_local_y*math.sqrt(radius*radius-cut_local_y*cut_local_y))/(math.pi*radius*radius)})
    # Keep these as source-owned ancestors in the portable override layer.
    # Standalone authoring otherwise promotes them to untyped defs, whereas
    # authoring through a composed entry naturally leaves identical overs.
    for path in [STATION_BODY,STATION_BODY+'/Collision']:
        spec=stage.GetEditTarget().GetLayer().GetPrimAtPath(path)
        if spec:spec.specifier=Sdf.SpecifierOver
    result['before_active_proxy_count'] = 5
    result['after_active_proxy_count'] = 7
    result['all_replacements_have_positive_cavity_clearance'] = all(x['cavity_clearance_lower_bound_m']>0 for x in result['after'])
    return result


def subdivide_axial_profile(profile, max_span):
    """Retain every original radius knot while bounding axial cell lengths."""
    if max_span <= 0 or len(profile)<2:
        raise ValueError('A positive span and an axial profile are required')
    dense = [list(profile[0])]
    for a,b in zip(profile[:-1],profile[1:]):
        if b[0]<=a[0]:
            raise ValueError('Axial profile must increase strictly')
        count = max(1,math.ceil((b[0]-a[0])/max_span))
        dense += [[a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count] for i in range(1,count+1)]
    return dense


def refine_source_wall(stage, profile, wedge_builder, max_span=.02, sectors=32):
    """Add short convex cells around the same open source cavity, never a floor."""
    import numpy as np
    from pxr import Gf,Sdf,UsdGeom
    dense = subdivide_axial_profile(profile,max_span)
    prefix = BURETTE_BODY+'/Task10PBDCollision/SourceContactWall'
    count = 0
    for axial,(a,b) in enumerate(zip(dense[:-1],dense[1:])):
        for sector in range(sectors):
            points,counts,indices = wedge_builder(a[1],a[1]+.003,b[1],b[1]+.003,a[0],b[0],
                2*math.pi*sector/sectors-.002,2*math.pi*(sector+1)/sectors+.002)
            values = np.asarray(points)
            center = (values.min(axis=0)+values.max(axis=0))/2
            mesh = UsdGeom.Mesh.Define(stage,prefix+f'/S{axial:02d}_{sector:02d}')
            mesh.CreatePointsAttr([Gf.Vec3f(*map(float,p)) for p in (values-center)*1000])
            mesh.CreateFaceVertexCountsAttr(counts)
            mesh.CreateFaceVertexIndicesAttr(indices)
            mesh.CreateSubdivisionSchemeAttr('none')
            mesh.CreateVisibilityAttr('invisible')
            mesh.AddTranslateOp().Set(Gf.Vec3d(*map(float,center)))
            mesh.AddScaleOp().Set(Gf.Vec3f(.001))
            prim = mesh.GetPrim()
            prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
            prim.CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True)
            prim.CreateAttribute('physics:approximation',Sdf.ValueTypeNames.Token).Set('convexHull')
            prim.CreateAttribute('physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float).Set(0.)
            prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.0004)
            prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(.00025)
            count += 1
    # The same pre-existing numerical valve solid occupies [-.183,-.180].
    # An analytic surface duplicates its SDF top/bottom planes; it adds no floor.
    cap = UsdGeom.Cube.Define(stage,BURETTE_BODY+'/Task10PBDCollision/ValveSeatFluxCap')
    cap.CreateSizeAttr(1.)
    cap.AddTranslateOp().Set(Gf.Vec3d(0,0,-.1815))
    cap.AddScaleOp().Set(Gf.Vec3f(.008,.008,.003))
    cap.CreateVisibilityAttr('invisible')
    cap.GetPrim().SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysxCollisionAPI']))
    cap.GetPrim().CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True)
    cap.GetPrim().CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.0004)
    cap.GetPrim().CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(.00025)
    return {'path':prefix,'enabled_convex_cells':count,'source_inner_profile_local_m':profile,
            'analytic_existing_valve_flux_cap':{'path':str(cap.GetPath()),'solid_interval_local_m':[-.183,-.180],
                'same_existing_boundary_planes':True,'inside_original_opaque_valve_housing':True},
            'maximum_axial_cell_length_m':max_span,'angular_sectors':sectors,
            'maximum_chord_inset_m':max(p[1] for p in profile)*(1-math.cos(math.pi/sectors+.002)),
            'wall_outward_thickness_m':.003,'new_interior_floors':False,
            'source_SDF_retained':True,'visible_geometry_changed':False,
            'basis':'same existing Source cavity profile; shorter normalized convex side-wall contacts'}


def refine_receiver_wall(stage, profile, wedge_builder, max_span=.008, sectors=64):
    """Reinforce the exact flask profile, including its steep bottom bevel.

    Every original axial knot remains a cell boundary. Normalized local hull
    coordinates retain the submillimetre bottom segments during convex cooking.
    The original SDF remains active; a convex disk duplicates its original flat
    glass floor at the exact existing plane, with no raised interior floor.
    """
    import numpy as np
    from pxr import Gf, Sdf, UsdGeom
    dense=subdivide_axial_profile(profile,max_span)
    prefix='/World/obj_receiver_flask/Task10PBDCollision/ReceiverContactWall'
    count=0
    overlap=.002
    for axial,(a,b) in enumerate(zip(dense[:-1],dense[1:])):
        for sector in range(sectors):
            points,counts,indices=wedge_builder(a[1],a[1]+.003,b[1],b[1]+.003,a[0],b[0],
                2*math.pi*sector/sectors-overlap,2*math.pi*(sector+1)/sectors+overlap)
            values=np.asarray(points)
            center=(values.min(axis=0)+values.max(axis=0))/2
            mesh=UsdGeom.Mesh.Define(stage,prefix+f'/S{axial:02d}_{sector:02d}')
            mesh.CreatePointsAttr([Gf.Vec3f(*map(float,p)) for p in (values-center)*1000])
            mesh.CreateFaceVertexCountsAttr(counts)
            mesh.CreateFaceVertexIndicesAttr(indices)
            mesh.CreateSubdivisionSchemeAttr('none')
            mesh.CreateVisibilityAttr('invisible')
            mesh.AddTranslateOp().Set(Gf.Vec3d(*map(float,center)))
            mesh.AddScaleOp().Set(Gf.Vec3f(.001))
            prim=mesh.GetPrim()
            prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
            prim.CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True)
            prim.CreateAttribute('physics:approximation',Sdf.ValueTypeNames.Token).Set('convexHull')
            prim.CreateAttribute('physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float).Set(0.)
            prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00175)
            prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(.0015)
            count+=1
    # Duplicate the original glass disk at its exact top plane, not a raised
    # liquid floor. Convex normalized coordinates provide direct plane contacts.
    top,radius=profile[0]
    floor_path='/World/obj_receiver_flask/Task10PBDCollision/ReceiverOriginalFloor'
    floor=UsdGeom.Mesh.Define(stage,floor_path)
    vertices=[(radius*math.cos(2*math.pi*k/sectors),radius*math.sin(2*math.pi*k/sectors),z)
              for z in [-top/2,top/2] for k in range(sectors)]
    faces=[list(reversed(range(sectors))),list(range(sectors,2*sectors))]
    faces += [[k,(k+1)%sectors,(k+1)%sectors+sectors,k+sectors] for k in range(sectors)]
    floor.CreatePointsAttr([Gf.Vec3f(*(v*1000 for v in p)) for p in vertices])
    floor.CreateFaceVertexCountsAttr([len(f) for f in faces])
    floor.CreateFaceVertexIndicesAttr([v for f in faces for v in f])
    floor.CreateSubdivisionSchemeAttr('none')
    floor.CreateVisibilityAttr('invisible')
    floor.AddTranslateOp().Set(Gf.Vec3d(0,0,top/2))
    floor.AddScaleOp().Set(Gf.Vec3f(.001))
    prim=floor.GetPrim()
    prim.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
    prim.CreateAttribute('physics:collisionEnabled',Sdf.ValueTypeNames.Bool).Set(True)
    prim.CreateAttribute('physics:approximation',Sdf.ValueTypeNames.Token).Set('convexHull')
    prim.CreateAttribute('physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float).Set(0.)
    prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.0016)
    prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(.0006)
    return {'path':prefix,'enabled_convex_cells':count,'source_inner_profile_local_m':profile,
            'maximum_axial_cell_length_m':max_span,'angular_sectors':sectors,
            'maximum_chord_inset_m':max(p[1] for p in profile)*(1-math.cos(math.pi/sectors+overlap)),
            'wall_outward_thickness_m':.003,'new_interior_floors':False,
            'collider_contact_offset_m':.00175,'collider_rest_offset_m':.0015,
            'original_SDF_retained':True,'visible_geometry_changed':False,
            'analytic_existing_glass_floor':{'path':floor_path,'top_local_z_m':top,'bottom_local_z_m':0.,'radius_m':radius,
                'collider_contact_offset_m':.0016,'collider_rest_offset_m':.0006,'same_original_glass_boundary_plane':True},
            'basis':'same existing Receiver cavity profile including every bottom-bevel knot; normalized local convex wall contacts'}
