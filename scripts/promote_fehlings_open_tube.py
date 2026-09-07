"""Promote capless tube against exact, recorded water-bath integration fixtures."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--scene',type=Path,required=True)
    parser.add_argument('--report',type=Path,action='append',required=True)
    args=parser.parse_args()
    from pxr import Usd
    scene_sha=sha256(args.scene.read_bytes()).hexdigest()
    asset_sha=sha256((args.package/'asset.usd').read_bytes()).hexdigest()
    embedded=args.scene.parent/'deps/objects/obj_sample_tube/asset.usd'
    if sha256(embedded.read_bytes()).hexdigest()!=asset_sha:
        raise ValueError('integration does not contain the exact asset')
    reports=[json.loads(p.read_text()) for p in args.report]
    if len(reports)!=3 or len({p.resolve() for p in args.report})!=3:
        raise ValueError('three separate cold starts required')
    if any(d['status']!='pass' or d['scene_sha256']!=scene_sha for d in reports):
        raise ValueError('missing exact-scene pass')
    stage=Usd.Stage.Open(str(args.package/'asset.usd'))
    entry=stage.GetPrimAtPath('/World/CentrifugeTube15mlClosed')
    collisions=[str(p.GetPath()) for p in Usd.PrimRange(entry) if 'PhysicsCollisionAPI' in p.GetAppliedSchemas()
                and p.GetAttribute('physics:collisionEnabled').Get()]
    if len(collisions)!=1 or not collisions[0].endswith('Tube_Body_Hollow_Mesh'):
        raise ValueError('unexpected active collision geometry')
    profile={a.GetName():list(a.Get()) if a.GetName() in ('physics:centerOfMass','physics:diagonalInertia') else str(a.Get())
             for a in entry.GetAttributes() if a.GetName().startswith('physics:')}
    (args.package/'physics/open_tube_profile.json').write_text(json.dumps({'parameter_status':'provisional_geometry',
        'asset_sha256':asset_sha,'authored_properties':profile},indent=2)+'\n')
    retained=[]
    for i,p in enumerate(args.report,1):
        dest=args.package/f'evidence/runtime/water_bath_cold_{i}.json'
        dest.parent.mkdir(parents=True,exist_ok=True)
        data=json.loads(p.read_text())
        data.pop('snapshots',None)
        dest.write_text(json.dumps(data,indent=2)+'\n')
        retained.append(str(dest.relative_to(args.package)))
    path=args.package/'evidence/manifest.json'
    manifest=json.loads(path.read_text())
    manifest.update(overall_status='pass',physics_profile='physics/open_tube_profile.json',runtime_evidence=retained,
                    runtime='Isaac Sim 4.5',qualification_scope='published water-bath rack and immersion fixture')
    manifest['claims'].update(rack_static_stability=True,pbd_bath_integration=True,internal_pbd_containment=False)
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    # Sync metadata only. The asset bytes and the tested scene stay unchanged.
    destination=embedded.parent
    shutil.copytree(args.package/'evidence',destination/'evidence',dirs_exist_ok=True)
    shutil.copy2(args.package/'physics/open_tube_profile.json',destination/'physics/open_tube_profile.json')
    print(path)


if __name__=='__main__':
    main()
