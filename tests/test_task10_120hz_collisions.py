"""The source clamp must keep an actual glass-clear opening, with solid pads."""
import importlib.util
import math
from pathlib import Path
from collections import defaultdict
import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('task10_clamp', Path(__file__).parents[1]/'scripts/task10_120_collisions.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


@pytest.mark.parametrize('side', [-1, 1])
def test_clipped_pad_is_closed_solid_with_glass_clearance(side):
    pts, counts, indices = mod.clipped_cylinder_x(.006, .012, side=side, cut_y=-side*.003)
    points = np.asarray(pts)
    # A pad translated to y=+/-9mm retains only y beyond the 6mm outer glass.
    assert np.min(side*(points[:,1]+side*.009)) >= .006-1e-12
    assert np.linalg.norm(points[:,1:3],axis=1).max() <= .006+1e-12
    edges = defaultdict(list)
    volume = 0.
    cursor = 0
    for n in counts:
        face = indices[cursor:cursor+n];cursor += n
        for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))].append((a,b))
        for i in range(1,n-1):
            a,b,c = points[[face[0],face[i],face[i+1]]]
            volume += np.dot(a,np.cross(b,c))/6
    assert all(len(e)==2 and e[0]==e[1][::-1] for e in edges.values())
    area = .006**2*math.acos(-.5)+.003*math.sqrt(.006**2-.003**2)
    assert volume == pytest.approx(area*.012,rel=.003)


def test_source_wall_subdivision_preserves_knots_and_cavity_profile():
    rows = [[-.18,.001],[-.1797,.0018],[-.12,.00465],[-.1198,.005],[.28,.005]]
    dense = mod.subdivide_axial_profile(rows,.02)
    for point in rows:
        assert any(np.allclose(point,p,rtol=0,atol=1e-12) for p in dense)
    assert max(b[0]-a[0] for a,b in zip(dense[:-1],dense[1:])) <= .02+1e-12
    assert np.asarray(dense)[:,1] == pytest.approx(np.interp(np.asarray(dense)[:,0],*np.asarray(rows).T))


def test_clamp_override_is_identical_when_authored_standalone_or_composed():
    from pxr import Usd,UsdGeom,UsdPhysics,Sdf,Gf
    source = Usd.Stage.CreateInMemory()
    UsdGeom.Xform.Define(source,mod.STATION_BODY)
    UsdGeom.Xform.Define(source,mod.BURETTE_BODY).AddTranslateOp().Set(Gf.Vec3d(.22,0,.515))
    for name,radius in [('tube',.006),('liquid_column',.005)]:
        UsdGeom.Cylinder.Define(source,mod.BURETTE_BODY+'/Visual/'+name).CreateRadiusAttr(radius)
    shapes = [('single_clamp',(.1825,0,.515),(.015,.06,.025)),
              ('clamp_cheek_left',(.205,-.024,.515),(.045,.012,.025)),
              ('clamp_cheek_right',(.205,.024,.515),(.045,.012,.025))]
    for name,pos,scale in shapes:
        cube=UsdGeom.Cube.Define(source,mod.STATION_BODY+'/Visual/'+name)
        cube.CreateSizeAttr(1);cube.AddTranslateOp().Set(Gf.Vec3d(*pos));cube.AddScaleOp().Set(Gf.Vec3f(*scale))
    old=UsdGeom.Cube.Define(source,mod.STATION_BODY+'/Collision/single_clamp_proxy')
    old.CreateSizeAttr(1);old.AddTranslateOp().Set(Gf.Vec3d(.1975,0,.515));old.AddScaleOp().Set(Gf.Vec3f(.045,.05,.025))
    UsdPhysics.CollisionAPI.Apply(old.GetPrim())
    for side,y in [('left',-.009),('right',.009)]:
        for level,z in [('upper',.524),('lower',.506)]:
            pad=UsdGeom.Cylinder.Define(source,mod.STATION_BODY+f'/Collision/pad_{side}_{level}')
            pad.CreateAxisAttr('X');pad.CreateRadiusAttr(.006);pad.CreateHeightAttr(.012)
            pad.AddTranslateOp().Set(Gf.Vec3d(.223,y,z));UsdPhysics.CollisionAPI.Apply(pad.GetPrim())
    source_before=source.GetRootLayer().ExportToString()
    standalone=Usd.Stage.CreateInMemory();standalone.DefinePrim('/World/obj_titration_station/Instance')
    strong_stage=Usd.Stage.CreateInMemory();strong_stage.DefinePrim('/World/obj_titration_station/Instance')
    strong=strong_stage.GetRootLayer()
    entry=Sdf.Layer.CreateAnonymous();entry.subLayerPaths=[strong.identifier,source.GetRootLayer().identifier]
    composed=Usd.Stage.Open(entry);composed.SetEditTarget(strong)
    a=mod.repair_source_clamp(standalone,source)
    b=mod.repair_source_clamp(composed,source)
    assert standalone.GetRootLayer().ExportToString()==strong.ExportToString()
    assert a==b
    assert source.GetRootLayer().ExportToString()==source_before
    assert a['after_active_proxy_count']==7
    assert a['all_replacements_have_positive_cavity_clearance']


def test_receiver_refinement_preserves_profile_floor_and_other_bodies():
    """Motion reinforcement follows every glass profile knot without a new floor."""
    from pxr import Usd, UsdGeom, UsdPhysics, Gf
    spec = importlib.util.spec_from_file_location('producer_for_wall', Path(__file__).parents[1]/'scripts/task10_pbd_producer.py')
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    stage=Usd.Stage.CreateInMemory()
    body='/World/obj_receiver_flask'
    UsdGeom.Xform.Define(stage,body)
    shell=UsdGeom.Mesh.Define(stage,body+'/Task10PBDCollision/ReceiverShell')
    UsdPhysics.CollisionAPI.Apply(shell.GetPrim()).CreateCollisionEnabledAttr(True)
    source=UsdGeom.Xform.Define(stage,mod.BURETTE_BODY).GetPrim()
    source.SetCustomDataByKey('unchanged','Source and Fine')
    profile=[[.003684,.032737],[.0044044,.0373375],[.0065656,.0401355],[.010273,.0411575],[.0666443,.0278526],[.15,.01905]]
    result=mod.refine_receiver_wall(stage,profile,producer.annular_wedge)
    assert result['maximum_chord_inset_m'] < .00006
    assert not result['new_interior_floors']
    assert result['original_SDF_retained']
    floor=result['analytic_existing_glass_floor']
    assert floor['top_local_z_m']==profile[0][0]
    assert floor['radius_m']==profile[0][1]
    assert floor['bottom_local_z_m']==0
    floor_prim=stage.GetPrimAtPath(floor['path'])
    assert floor_prim.GetAttribute('physics:collisionEnabled').Get()
    floor_points=np.array([UsdGeom.Xformable(floor_prim).ComputeLocalToWorldTransform(0).Transform(Gf.Vec3d(*map(float,p))) for p in UsdGeom.Mesh(floor_prim).GetPointsAttr().Get()])
    assert floor_points[:,2].min()==pytest.approx(0,abs=1e-9)
    assert floor_points[:,2].max()==pytest.approx(profile[0][0],abs=1e-9)
    assert np.linalg.norm(floor_points[:,:2],axis=1).max()==pytest.approx(profile[0][1])
    assert shell.GetPrim().GetAttribute('physics:collisionEnabled').Get()
    assert source.GetCustomDataByKey('unchanged')=='Source and Fine'
    cells=[p for p in stage.Traverse() if str(p.GetPath()).startswith(result['path']+'/')]
    assert len(cells)==result['enabled_convex_cells']
    knots=set()
    for prim in cells:
        mesh=UsdGeom.Mesh(prim)
        points=np.array([UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(0).Transform(Gf.Vec3d(*map(float,p))) for p in mesh.GetPointsAttr().Get()])
        z=points[:,2];r=np.linalg.norm(points[:,:2],axis=1)
        assert z.max()-z.min() <= .008+1e-8
        assert z.min() >= profile[0][0]-1e-8
        assert z.max() <= profile[-1][0]+1e-8
        assert np.min(r-np.interp(z,*np.asarray(profile).T)) >= -1e-8
        assert prim.GetAttribute('physics:approximation').Get()=='convexHull'
        assert prim.GetAttribute('physxCollision:restOffset').Get()==pytest.approx(.0015)
        assert prim.GetAttribute('physxCollision:contactOffset').Get()==pytest.approx(.00175)
        knots.update(np.round(z,7))
    assert all(round(z,7) in knots for z,r in profile)
