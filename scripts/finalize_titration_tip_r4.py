"""Promote the exact r4 asset after independent runtime and static geometry checks."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

from scripts.build_titration_tip_r4 import audit


def promote(out,reports):
    from pxr import Usd
    package=out/'packages/station'
    digest=sha256((package/'asset.usd').read_bytes()).hexdigest()
    data=[json.loads(p.read_text()) for p in reports]
    if len(data)!=3 or len({d.get('process_id') for d in data})!=3:
        raise ValueError('three independent producer processes required')
    if any(d.get('asset_sha256')!=digest or d.get('status')!='pass' or d.get('runtime_version')!='4.5.0' for d in data):
        raise ValueError('unqualified producer report')
    audit(Usd.Stage.Open(str(package/'asset.usd')))
    evidence=package/'evidence'
    records=[]
    for i,path in enumerate(reports,1):
        target=evidence/f'cold_start_{i}.json'
        shutil.copy2(path,target)
        records.append(dict(path=str(target.relative_to(package)),sha256=sha256(target.read_bytes()).hexdigest()))
    p=evidence/'manifest.json'
    manifest=json.loads(p.read_text())
    manifest.update(overall_status='pass',blocked_reasons=[],runtime_evidence=records)
    p.write_text(json.dumps(manifest,indent=2)+'\n')
    receipt=dict(status='promoted',package_id='traditional_titration_station_r4',asset_sha256=digest,
                 runtime='Isaac Sim 4.5',runtime_evidence=records,static_audit_sha256=sha256((evidence/'static_audit.json').read_bytes()).hexdigest())
    (out/'promotion_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path,action='append',required=True)
    a=p.parse_args()
    print(promote(a.out,a.report))
