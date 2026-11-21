"""Load pilot USDs and record dependency failures without modifying assets."""
import argparse
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    from pxr import Usd, UsdUtils
    records = []
    for scene in json.loads(a.manifest.read_text())['scenes']:
        if scene['split'] != 'pilot':
            continue
        for condition in ['original','converted']:
            path = scene[condition]
            row = {'scene_id': scene['scene_id'], 'condition': condition, 'path': path}
            try:
                stage = Usd.Stage.Open(path)
                if stage is None:
                    raise ValueError('Stage.Open returned None')
                row['prim_count'] = sum(1 for _ in stage.Traverse())
                layers, assets, unresolved = UsdUtils.ComputeAllDependencies(path)
                row.update(layer_count=len(layers), asset_count=len(assets), unresolved=list(unresolved))
                row['status'] = 'dependency_errors' if unresolved else 'stage_loaded_render_unverified'
            except Exception as e:
                row.update(status='load_error', error=str(e))
            records.append(row)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x') as f:
        json.dump({'records': records}, f, indent=2)
    print(json.dumps({r['scene_id']+':'+r['condition']:r['status'] for r in records}))
    return int(any(r['status'] != 'stage_loaded_render_unverified' for r in records))

if __name__ == '__main__':
    raise SystemExit(main())
