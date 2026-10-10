"""Measured source profile helpers; no simulator imports in pure geometry."""
import math


def validate_profile(profile):
    """Reject malformed local-metre axial profiles."""
    if len(profile)<2 or any(len(row)!=2 or not all(math.isfinite(v) for v in row) or row[1]<=0 for row in profile):
        raise ValueError('profile needs finite positive radius rows')
    if any(b[0]<=a[0] for a,b in zip(profile,profile[1:])):
        raise ValueError('profile height must strictly increase')
    return profile


def profile_volume(profile):
    """Integrate exact frustum volumes, cubic metres."""
    validate_profile(profile)
    return sum(math.pi*(b[0]-a[0])*(a[1]**2+a[1]*b[1]+b[1]**2)/3 for a,b in zip(profile,profile[1:]))


def particle_mass(total_mass_kg, count):
    """Keep declared total physical mass independent of lattice quantization."""
    if total_mass_kg<=0 or count<=0: raise ValueError('positive mass and particle count required')
    return total_mass_kg/count


def seed_profile(profile, spacing, margin):
    """Seed fluid centers inside the source profile with a finite wall margin."""
    import numpy as np
    validate_profile(profile)
    if spacing<=0 or margin<0: raise ValueError('invalid lattice spacing/margin')
    rows=np.asarray(profile); n=math.ceil(max(rows[:,1])/spacing)
    xy=np.arange(-n,n+1)*spacing; xx,yy=np.meshgrid(xy,xy); result=[]
    for z in np.arange(rows[0,0]+spacing, rows[-1,0]-spacing/4, spacing):
        radius=np.interp(z,rows[:,0],rows[:,1])-margin
        if radius<=0:continue
        m=xx*xx+yy*yy<=radius*radius
        result.extend(zip(xx[m],yy[m],np.full(m.sum(),z)))
    return np.asarray(result,dtype=float).reshape(-1,3)


def outside_count(points, profile, tolerance):
    """Count centers outside the same cavity, allowing explicit metre tolerance."""
    import numpy as np
    validate_profile(profile)
    p=np.asarray(points); rows=np.asarray(profile)
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():raise ValueError('non-finite or invalid particles')
    radius=np.interp(p[:,2],rows[:,0],rows[:,1])
    return int(((np.linalg.norm(p[:,:2],axis=1)>radius+tolerance)|(p[:,2]<rows[0,0]-tolerance)|(p[:,2]>rows[-1,0]+tolerance)).sum())


def collision_profile(profile, min_span=.0001):
    """Coalesce tiny bevel/rim intervals; original semantic profile stays intact."""
    validate_profile(profile)
    result=[profile[0]]
    for row in profile[1:]:
        if row[0]-result[-1][0]>=min_span:result.append(row)
    if result[-1]!=profile[-1]:
        if len(result)>1 and profile[-1][0]-result[-1][0]<min_span:result.pop()
        result.append(profile[-1])
    return result


def author_profile_colliders(stage, parent, profile, thickness, sectors=32):
    """Use normalized convex cells at source cavity boundaries, open at the mouth."""
    import numpy as np
    from pxr import Gf,Sdf,UsdGeom
    from task10_pbd_producer import annular_wedge,attr
    validate_profile(profile)
    physical_profile=collision_profile(profile)
    dense=[physical_profile[0]]
    for a,b in zip(physical_profile,physical_profile[1:]):
        steps=max(1,math.ceil((b[0]-a[0])/.015))
        dense += [[a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps] for i in range(1,steps+1)]
    cell_count=0
    for j,(a,b) in enumerate(zip(dense,dense[1:])):
        for i in range(sectors):
            cell_count+=1
            verts,counts,indices=annular_wedge(a[1],a[1]+thickness,b[1],b[1]+thickness,a[0],b[0],2*math.pi*i/sectors-.001,2*math.pi*(i+1)/sectors+.001)
            xyz=np.asarray(verts); center=(xyz.min(0)+xyz.max(0))/2; scale=np.maximum(xyz.max(0)-xyz.min(0),1e-9)
            mesh=UsdGeom.Mesh.Define(stage,parent+f'/S{j:03d}_{i:02d}')
            mesh.CreatePointsAttr([Gf.Vec3f(*v) for v in (xyz-center)/scale]);mesh.CreateFaceVertexCountsAttr(counts);mesh.CreateFaceVertexIndicesAttr(indices)
            mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateVisibilityAttr('invisible');mesh.AddTranslateOp().Set(Gf.Vec3d(*center));mesh.AddScaleOp().Set(Gf.Vec3f(*scale))
            p=mesh.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
            attr(p,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(p,'physics:approximation',Sdf.ValueTypeNames.Token,'convexHull')
            attr(p,'physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.)
            attr(p,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.0014 if 'sample_tube' in parent else .0008);attr(p,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.0005 if 'sample_tube' in parent else 0.)
    # The actual source bottom extends to z=0; no raised internal support.
    top,radius=profile[0]
    disk=UsdGeom.Mesh.Define(stage,parent+'/Floor')
    verts=[(radius*math.cos(2*math.pi*i/sectors),radius*math.sin(2*math.pi*i/sectors),z) for z in [-top/2,top/2] for i in range(sectors)]
    faces=[list(reversed(range(sectors))),list(range(sectors,2*sectors))]+[[i,(i+1)%sectors,(i+1)%sectors+sectors,i+sectors] for i in range(sectors)]
    disk.CreatePointsAttr([Gf.Vec3f(*(v*1000 for v in p)) for p in verts]);disk.CreateFaceVertexCountsAttr([len(f) for f in faces]);disk.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);disk.CreateSubdivisionSchemeAttr('none');disk.CreateVisibilityAttr('invisible')
    disk.AddTranslateOp().Set(Gf.Vec3d(0,0,top/2));disk.AddScaleOp().Set(Gf.Vec3f(.001))
    p=disk.GetPrim();p.SetMetadata('apiSchemas',Sdf.TokenListOp.Create(prependedItems=['PhysicsCollisionAPI','PhysicsMeshCollisionAPI','PhysxCollisionAPI','PhysxConvexHullCollisionAPI']))
    attr(p,'physics:collisionEnabled',Sdf.ValueTypeNames.Bool,True);attr(p,'physics:approximation',Sdf.ValueTypeNames.Token,'convexHull');attr(p,'physxConvexHullCollision:minThickness',Sdf.ValueTypeNames.Float,0.)
    attr(p,'physxCollision:contactOffset',Sdf.ValueTypeNames.Float,.0016);attr(p,'physxCollision:restOffset',Sdf.ValueTypeNames.Float,.0006)
    return cell_count+1


def separate_tube_contacts(stage, root='/World'):
    """Keep supplemental tube contacts fluid-facing, retaining original rigid SDF.

    Collection-based filtering follows USD composition when the task root is
    mounted. The rest-of-scene group excludes the particle helper subtree, so
    fluid-wall collisions remain enabled; rigid contacts use the original tube.
    """
    from pxr import UsdPhysics, Sdf
    groups=root+'/WaterbathCollisionGroups'
    fluid_wall=UsdPhysics.CollisionGroup.Define(stage,groups+'/TubeFluidWalls')
    rigid=UsdPhysics.CollisionGroup.Define(stage,groups+'/RigidScene')
    fluid_wall.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets([root+'/obj_sample_tube/WaterbathCollision'])
    rigid.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets([root])
    rigid.GetCollidersCollectionAPI().CreateExcludesRel().SetTargets([root+'/obj_sample_tube/WaterbathCollision',root+'/WaterbathFluid'])
    fluid_wall.CreateFilteredGroupsRel().SetTargets([rigid.GetPath()])
    rigid.CreateFilteredGroupsRel().SetTargets([fluid_wall.GetPath()])
    original=stage.GetPrimAtPath(root+'/obj_sample_tube/Visual/GlassShell')
    if not original or not original.GetAttribute('physics:collisionEnabled').Get():
        raise ValueError('Rigid-contact source tube SDF must remain enabled')
    return {'supplemental_group':str(fluid_wall.GetPath()),'rigid_group':str(rigid.GetPath()),'particle_exclusion':root+'/WaterbathFluid','rigid_contact_mesh':str(original.GetPath())}
