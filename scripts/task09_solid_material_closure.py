#!/usr/bin/env python3
"""Package task09 and task14 MDLs with existing AAN recursive closure helpers.

Only sourceAsset path opinions are authored; material parameters and source MDL
root bytes are preserved. A runtime compiler/visual check remains mandatory.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build(source, out, scope, exclude_scope, runtime_roots):
    """Mirror source MDLs, close helper imports, and emit portable path opinions."""
    from pxr import Sdf, Usd
    from convert_asset.asset_application_normalizer.evidence_manifest import sha256_file
    from convert_asset.asset_application_normalizer.mdl_runtime_closure import (
        _mirror_mdl_runtime_dependencies,
        build_material_runtime_closure,
    )

    stage = Usd.Stage.Open(str(source))
    records, bindings, names = [], [], {}
    out.mkdir(parents=True, exist_ok=True)
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if scope and path != scope and not path.startswith(scope + '/'):
            continue
        if exclude_scope and (path == exclude_scope or path.startswith(exclude_scope + '/')):
            continue
        for attr in prim.GetAttributes():
            value = attr.Get()
            if not isinstance(value, Sdf.AssetPath) or not value.path.lower().endswith('.mdl'):
                continue
            if not value.resolvedPath:
                raise ValueError(f'unresolved source MDL {attr.GetPath()}: {value.path}')
            source_mdl = Path(value.resolvedPath)
            name = source_mdl.name
            if name in names and names[name] != sha256_file(source_mdl):
                raise ValueError(f'conflicting source MDL basename {name}')
            if name not in names:
                target = out / 'deps/mdl' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_mdl, target)
                names[name] = sha256_file(source_mdl)
                records.append({'source_mdl_assets': [{
                    'package_path': target.relative_to(out).as_posix(),
                    'resolved_path': str(source_mdl),
                    'package_sha256': names[name],
                }]})
            bindings.append({'attribute': str(attr.GetPath()), 'original_asset_path': value.path,
                             'original_resolved_path': str(source_mdl), 'package_asset_path': f'deps/mdl/{name}'})
    if not bindings:
        raise ValueError('no selected MDL source assets')
    # Existing helper mirrors imports without substituting the source roots.
    actions = _mirror_mdl_runtime_dependencies(out, records, runtime_mdl_roots=runtime_roots)
    # Empty runtime roots make unresolved external helpers fail static validation.
    result = build_material_runtime_closure(out, records, runtime_mdl_roots=[])
    result.material_runtime_closure['mirror_actions'] = actions
    for name, expected in names.items():
        assert sha256_file(out / 'deps/mdl' / name) == expected, f'root changed: {name}'
    overlay_path = out / 'materials.usda'
    overlay = Usd.Stage.CreateNew(str(overlay_path))
    for binding in bindings:
        path = Sdf.Path(binding['attribute'])
        prim = overlay.OverridePrim(path.GetPrimPath())
        attr = prim.CreateAttribute(path.name, Sdf.ValueTypeNames.Asset, custom=False)
        attr.Set(Sdf.AssetPath(binding['package_asset_path']))
    overlay.GetRootLayer().Save()
    report = {
        'source': str(source), 'source_sha256': sha256_file(source),
        'scope': scope, 'exclude_scope': exclude_scope,
        'source_root_mdl_bytes_preserved': True,
        'runtime_helper_roots': [str(root) for root in runtime_roots],
        'bindings': bindings, 'closure': asdict(result),
        'files': [{'path': path.relative_to(out).as_posix(), 'sha256': sha256_file(path)}
                  for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'closure.json'],
        'limits': ['Static dependency closure only; no runtime compiler or visual parity check.',
                   'Native MDL modules anno/base/df/math/state/tex are supplied by the simulator.',
                   'USD-authored textures remain in the consumer source package; this overlay only remaps MDL assets.'],
    }
    (out / 'closure.json').write_text(json.dumps(report, indent=2) + '\n')
    if result.overall_status != 'pass':
        raise ValueError(f'MDL closure blocked for {source}: {result.blocked_reasons}')
    return {'source': str(source), 'overlay': str(overlay_path), 'bindings': len(bindings),
            'mdl_files': len(list(out.rglob('*.mdl'))), 'status': result.overall_status}


def main():
    """Produce independent source-preserved material closures for both runtimes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--isaac41-mdl', type=Path, default=Path('/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/lib/python3.10/site-packages/omni/mdl/core'))
    parser.add_argument('--isaac45-mdl', type=Path, default=Path('/isaac-sim/kit/mdl/core'))
    args = parser.parse_args()
    summaries = []
    for runtime, core in [('isaac41', args.isaac41_mdl), ('isaac45', args.isaac45_mdl)]:
        roots = [core / 'mdl', core / 'Base', core]
        if not all(root.is_dir() for root in roots):
            raise ValueError(f'runtime MDL roots missing: {roots}')
        for name, folder, scope, exclude in [
            ('task09', 'task_09_solid_weighing', None, '/World/obj_analytical_balance'),
            ('task14', 'task_14_fixed_weight_weighing', '/World/obj_analytical_balance', None),
        ]:
            summaries.append(build(args.sources.resolve() / folder / 'scene.usd',
                                   args.out.resolve() / runtime / name, scope, exclude, roots))
    (args.out / 'handoff.json').write_text(json.dumps(summaries, indent=2) + '\n')
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
