"""Use AAN's MDL closure builder to package each supported runtime's modules."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def localize(candidate, runtime41_root, runtime45_root):
    from pxr import Usd, Sdf
    from convert_asset.asset_application_normalizer.mdl_runtime_closure import build_material_runtime_closure
    receipts={}
    names=['OmniPBR.mdl','OmniGlass.mdl','OmniSurface.mdl']
    incoming=list((candidate/'SubUSDs/materials').glob('*.mdl'))
    for version,runtime in [('isaac41',runtime41_root),('isaac45',runtime45_root)]:
        package=candidate/'materials'/version
        directory=package/'deps/mdl'
        directory.mkdir(parents=True,exist_ok=True)
        records=[]
        for name in names:
            source=runtime/'Base'/name
            target=directory/name
            shutil.copy2(source,target)
            records.append({'material_prim':name,'source_mdl_assets':[{
                'package_path':str(target.relative_to(package)), 'resolved_path':str(source)}]})
        for source in incoming:
            name=('incoming_' if source.name in names else '')+source.name
            target=directory/name
            shutil.copy2(source,target)
            records.append({'material_prim':name,'source_mdl_assets':[{
                'package_path':str(target.relative_to(package)),'resolved_path':str(source)}]})
        result=build_material_runtime_closure(package,records,runtime_mdl_roots=[runtime/'mdl',runtime/'Base',runtime])
        if result.overall_status!='pass':
            raise ValueError(result.blocked_reasons)
        receipts[version]=result.material_runtime_closure
    # Asset and supporting source scene use runtime 4.5 by default.
    for name in ['asset.usda','scene_support.usda']:
        stage=Usd.Stage.Open(str(candidate/name),load=Usd.Stage.LoadNone)
        for prim in stage.Traverse():
            for attr in prim.GetAttributes():
                if attr.GetTypeName()==Sdf.ValueTypeNames.Asset:
                    value=attr.Get()
                    if value and value.path in names:
                        attr.Set(Sdf.AssetPath('./materials/isaac45/deps/mdl/'+value.path))
                    elif value and 'SubUSDs/materials/' in value.path:
                        leaf=Path(value.path).name
                        local=('incoming_' if leaf in names else '')+leaf
                        attr.Set(Sdf.AssetPath('./materials/isaac45/deps/mdl/'+local))
        stage.GetRootLayer().Save()
    stage=Usd.Stage.Open(str(candidate/'asset_isaac41.usda'))
    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            if attr.GetTypeName()==Sdf.ValueTypeNames.Asset:
                value=attr.Get()
                if value and '/materials/isaac45/' in value.path:
                    attr.Set(Sdf.AssetPath(value.path.replace('/isaac45/','/isaac41/')))
    stage.GetRootLayer().Save()
    manifest_path=candidate/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest.update(asset_sha256=hashlib.sha256((candidate/'asset.usda').read_bytes()).hexdigest(),
                    scene_support_sha256=hashlib.sha256((candidate/'scene_support.usda').read_bytes()).hexdigest(),
                    material_runtime_closure={k:v['status'] for k,v in receipts.items()},
                    material_localization='AAN material_runtime_closure; SDK copyright headers preserved')
    manifest_path.write_text(json.dumps(manifest,indent=2))
    (candidate/'material_closure.json').write_text(json.dumps(receipts,indent=2))
    return {k:v['status'] for k,v in receipts.items()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--runtime41-root',type=Path,required=True)
    p.add_argument('--runtime45-root',type=Path,default=Path('/isaac-sim/kit/mdl/core'))
    a=p.parse_args()
    print(localize(a.candidate,a.runtime41_root,a.runtime45_root))
