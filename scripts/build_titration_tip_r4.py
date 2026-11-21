"""Producer-owned open downward tip and lumen-fitted precharge; preserve the prim tree."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil

from scripts.build_titration_filled_visuals_r3 import lower_profile as old_profile, lathe, physical_signature

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/traditional_titration_assets_r3_filled_visuals_20260907/packages/station'
OUTPUT=ROOT/'outputs/traditional_titration_assets_r4_open_tip_20260908'
ENTRY='/World/TitrationStation'
VISUAL=ENTRY+'/Instance/Burette/body_link/Visual'


def inner_radius(z):
    return .0004+(z+.28)/.05*(.00155-.0004)


def lower_profile():
    return [(-.2798,inner_radius(-.2798)-.00005),(-.23,.0015)]+old_profile()[2:]


def tip_mesh():
    n=96
    rings=[(-.03,.0008),(.02,.002),(-.03,.0004),(.02,.00155)]
    points=[(r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for z,r in rings for i in range(n)]
    counts,indices,normals=[],[],[]
    for part in ('outer','inner','top','bottom'):
        for i in range(n):
            j=(i+1)%n
            ids={'outer':(i,j,n+j,n+i),'inner':(2*n+j,2*n+i,3*n+i,3*n+j),
                 'top':(n+i,n+j,3*n+j,3*n+i),'bottom':(j,i,2*n+i,2*n+j)}[part]
            counts.append(4)
            indices.extend(ids)
            for vertex in ids:
                angle=2*math.pi*(vertex%n)/n
                if part in ('top','bottom'):
                    normal=(0,0,1 if part=='top' else -1)
                else:
                    sign=1 if part=='outer' else -1
                    slope=(.002-.0008)/.05 if part=='outer' else (.00155-.0004)/.05
                    length=math.sqrt(1+slope*slope)
                    normal=(sign*math.cos(angle)/length,sign*math.sin(angle)/length,-sign*slope/length)
                normals.append(normal)
    return points,counts,indices,normals


def audit(stage):
    from pxr import UsdGeom
    mesh=stage.GetPrimAtPath(VISUAL+'/delivery_tip')
    if mesh.GetTypeName()!='Mesh':
        raise ValueError('tip must be an open tapered mesh')
    pts=mesh.GetAttribute('points').Get()
    expected,counts,indices,_=tip_mesh()
    if len(pts)!=len(expected) or max(abs(a-b) for p,q in zip(pts,expected) for a,b in zip(p,q))>1e-8:
        raise ValueError('tip profile differs')
    if list(mesh.GetAttribute('faceVertexCounts').Get())!=counts or list(mesh.GetAttribute('faceVertexIndices').Get())!=indices:
        raise ValueError('invalid open-wall topology')
    liquid=stage.GetPrimAtPath(VISUAL+'/liquid_precharge')
    points=liquid.GetAttribute('points').Get()
    expected_liquid,_,_=lathe(lower_profile())
    if len(points)!=len(expected_liquid) or max(abs(a-b) for p,q in zip(points,expected_liquid) for a,b in zip(p,q))>1e-8:
        raise ValueError('precharge profile differs')
    outside=[]
    for x,y,z in points:
        if z<=-.23 and (z<-.279801 or math.hypot(x,y)>inner_radius(z)-.000049):
            outside.append((x,y,z))
    if outside:
        raise ValueError('precharge leaves the lumen')
    if UsdGeom.Imageable(liquid).ComputeVisibility()=='invisible':
        raise ValueError('precharge initially hidden')
    return dict(status='pass',downward_taper=True,open_lumen=True,tip_length_m=.05,
                outer_radii_top_bottom_m=[.002,.0008],inner_radii_top_bottom_m=[.00155,.0004],
                radial_liquid_clearance_m=.00005,outlet_liquid_recess_m=.0002,
                outside_lumen_vertices=0,lower_profile_m=lower_profile())


def build(source=SOURCE,out=OUTPUT):
    from pxr import Gf,Usd,UsdGeom,UsdUtils
    package=out/'packages/station'
    if package.exists():
        raise FileExistsError(package)
    shutil.copytree(source,package,ignore=lambda directory,names:{'evidence'} if Path(directory)==source else set())
    (package/'evidence').mkdir()
    stage=Usd.Stage.Open(str(package/'asset.usd'))
    before=physical_signature(stage)
    paths={str(p.GetPath()):p.GetTypeName() for p in stage.TraverseAll()}
    prim=stage.GetPrimAtPath(VISUAL+'/delivery_tip')
    prim.SetTypeName('Mesh')
    for name in ('axis','height','radius'):
        prim.RemoveProperty(name)
    mesh=UsdGeom.Mesh(prim)
    points,counts,indices,normals=tip_mesh()
    mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in points])
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateNormalsAttr([Gf.Vec3f(*v) for v in normals])
    mesh.SetNormalsInterpolation('faceVarying')
    mesh.CreateSubdivisionSchemeAttr('none')
    mesh.CreateDoubleSidedAttr(False)
    mesh.CreateExtentAttr([Gf.Vec3f(-.002,-.002,-.03),Gf.Vec3f(.002,.002,.02)])
    liquid=UsdGeom.Mesh(stage.GetPrimAtPath(VISUAL+'/liquid_precharge'))
    points,counts,indices=lathe(lower_profile())
    liquid.GetPointsAttr().Set([Gf.Vec3f(*p) for p in points])
    liquid.GetFaceVertexCountsAttr().Set(counts)
    liquid.GetFaceVertexIndicesAttr().Set(indices)
    liquid.CreateExtentAttr([Gf.Vec3f(*[min(p[i] for p in points) for i in range(3)]),
                             Gf.Vec3f(*[max(p[i] for p in points) for i in range(3)])])
    stage.GetRootLayer().Save()
    if before!=physical_signature(stage):
        raise ValueError('producer physics changed')
    after={str(p.GetPath()):p.GetTypeName() for p in stage.TraverseAll()}
    if set(paths)!=set(after) or [p for p in paths if paths[p]!=after[p]]!=[VISUAL+'/delivery_tip']:
        raise ValueError('producer structure changed')
    report=audit(stage)
    layers,assets,missing=UsdUtils.ComputeAllDependencies(str(package/'asset.usd'))
    all_paths={Path(layer.realPath).resolve() for layer in layers if layer.realPath}|{Path(str(a)).resolve() for a in assets}
    if missing or any(not p.is_relative_to(package.resolve()) for p in all_paths):
        raise ValueError('producer closure failed')
    digest=sha256((package/'asset.usd').read_bytes()).hexdigest()
    report.update(asset_sha256=digest,physical_content_identical=True,prim_paths_unchanged=True,dependency_closure=True)
    (package/'evidence/static_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    original=json.loads((source/'evidence/manifest.json').read_text())
    original.update(package_id='traditional_titration_station_r4',overall_status='runtime_pending',
                    blocked_reasons=['runtime_pending'],asset_sha256=digest,
                    source=dict(package_id='traditional_titration_station_r3',asset_sha256=sha256((source/'asset.usd').read_bytes()).hexdigest()),
                    tip_recipe=report)
    for key in ('runtime_evidence','runtime_reports','runtime_cold_starts'):
        original.pop(key,None)
    (package/'evidence/manifest.json').write_text(json.dumps(original,indent=2)+'\n')
    return package


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=SOURCE)
    p.add_argument('--out',type=Path,default=OUTPUT)
    a=p.parse_args()
    print(build(a.source,a.out))
