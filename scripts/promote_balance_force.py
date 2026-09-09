"""Promote only exact, independently measured force-balance producer bytes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import zipfile


def promote(candidate, reports, out, render_logs=None):
    from pxr import Usd, UsdPhysics, UsdUtils
    from convert_asset.asset_application_normalizer.role_normalization import _visual_fingerprint
    from convert_asset.asset_application_normalizer.mdl_runtime_closure import parse_material_runtime_log
    digest=hashlib.sha256((candidate/'asset.usda').read_bytes()).hexdigest()
    manifest=json.loads((candidate/'manifest.json').read_text())
    division=manifest['configuration']['resolution_g']
    if division not in (.0001,.001,.01,.1):
        raise ValueError('unsupported display division')
    data=[json.loads(p.read_text()) for p in reports]
    if len(data)!=6 or len({d.get('pid') for d in data})!=6 or any(not d.get('pid') for d in data):
        raise ValueError('six independent producer processes required')
    seen=set()
    for d in data:
        seen.add((d.get('runtime','')[:3],d.get('initialization')))
        if d.get('asset_sha256')!=digest or d.get('status')!='measured' or not d.get('gpu'):
            raise ValueError('stale or incomplete producer qualification')
        if len(d.get('cases',[]))<11 or any(not all(math.isfinite(c[k]) for k in ('error_g','range_g'))
                or c['error_g']>division or c['range_g']>2*division for c in d['cases']):
            raise ValueError('measured precision did not pass')
    if seen!={(v,m) for v in ('4.1','4.5') for m in ('omitted','zero','pressed')}:
        raise ValueError('runtime and initialization matrix incomplete')
    stage=Usd.Stage.Open(str(candidate/'asset.usda'))
    root='/World/obj_analytical_balance'
    if not stage.GetPrimAtPath(root).HasAPI(UsdPhysics.ArticulationRootAPI):
        raise ValueError('articulation root missing')
    cell=stage.GetPrimAtPath(root+'/Instance/Joints/LoadCell')
    if (not cell or not cell.IsA(UsdPhysics.FixedJoint)
            or list(map(str,cell.GetRelationship('physics:body0').GetTargets()))!=[root+'/Instance/Body']
            or list(map(str,cell.GetRelationship('physics:body1').GetTargets()))!=[root+'/Instance/WeighingPan']):
        raise ValueError('load cell topology missing or incorrect')
    tare=stage.GetPrimAtPath(root+'/Instance/Joints/RightTarePress')
    if not tare or not tare.IsA(UsdPhysics.PrismaticJoint):
        raise ValueError('tare topology missing')
    links=[p for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    if {p.GetName() for p in links}!={'Body','RightTare','WeighingPan'}:
        raise ValueError('unexpected rigid link topology')
    for p in links:
        if not 0<p.GetAttribute('physics:mass').Get()<100:
            raise ValueError('invalid link mass')
    for p in stage.Traverse():
        if p.IsA(UsdPhysics.Joint):
            for key in ('physics:body0','physics:body1'):
                for target in p.GetRelationship(key).GetTargets():
                    if not stage.GetPrimAtPath(target):
                        raise ValueError('dangling joint target')
    if stage.GetPrimAtPath(root+'/Instance/Joints/BaseFixed'):
        raise ValueError('movable qualification cannot promote a fixed asset')
    for entry in ('asset.usda','asset_isaac41.usda'):
        layers,assets,missing=UsdUtils.ComputeAllDependencies(str(candidate/entry))
        dependencies=[*(Path(x.realPath) for x in layers if x.realPath),*(Path(x) for x in assets)]
        if missing or any(not p.resolve().is_relative_to(candidate.resolve()) for p in dependencies):
            raise ValueError('producer USD closure failed')
    if manifest.get('material_runtime_closure')!={'isaac41':'pass','isaac45':'pass'}:
        raise ValueError('producer MDL closure failed')
    if not render_logs or set(render_logs)!={'isaac41','isaac45'}:
        raise ValueError('both runtime material compiler logs required')
    compilers={k:parse_material_runtime_log(p.read_text()) for k,p in render_logs.items()}
    if any(v['status']!='pass' for v in compilers.values()):
        raise ValueError('material runtime compiler failed')
    visual_before=_visual_fingerprint(stage,[root])
    shutil.copytree(candidate,out,dirs_exist_ok=True,ignore=shutil.ignore_patterns('incoming','scene_support.usda'))
    visual_after=_visual_fingerprint(Usd.Stage.Open(str(out/'asset.usda')),[root])
    if visual_before['signature']!=visual_after['signature']:
        raise ValueError('producer visual preservation failed')
    evidence=out/'evidence'
    evidence.mkdir(exist_ok=True)
    closure=json.loads((out/'material_closure.json').read_text())
    for version,report in compilers.items():
        log=evidence/(version+'_material_runtime.log')
        shutil.copy2(render_logs[version],log)
        closure[version]['runtime_compiler']={**report,'log':str(log.relative_to(out)),
            'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
    (out/'material_closure.json').write_text(json.dumps(closure,indent=2))
    records=[]
    for i,path in enumerate(reports,1):
        dest=evidence/f'cold_start_{i}.json'
        shutil.copy2(path,dest)
        records.append({'path':str(dest.relative_to(out)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    manifest.update(status='promoted',asset_id='analytical_balance_force_r1',asset_sha256=digest,
                    qualification='GPU TGS force measurement; free base on horizontal support; independent load-cell link',
                    runtime_evidence=records,robot_grasp_verified=False,
                    runtime_versions=sorted({d['runtime'] for d in data}))
    manifest.update(overall_status='pass',blocked_reasons=[],
        source_license_status='not specified in user-provided incoming archive; NVIDIA MDL notices retained',
        visual_admission_mode='original_material_visual_preservation',
        visual_preservation_fingerprint={'status':'pass','raw_source':visual_before,
            'package_before_physics_profile':visual_after,'scope':[root],
            'source_kind':'producer-repaired candidate, not original incoming archive'},
        target_runtime_results={v:{'status':'pass','protocol':'independent GPU force qualification'} for v in ('isaac41','isaac45')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (evidence/'manifest.json').write_text(json.dumps({'overall_status':'pass','runtime_evidence':records,
        'asset_sha256':digest,'scope':manifest['qualification'],'robot_policy_success':False},indent=2))
    (out/'README.md').write_text('''# 受力天平资产 r1

这是设备资产，需放入带承托台面和 PhysicsScene 的场景。

- Isaac Sim 4.5：`asset.usda`；4.1：`asset_isaac41.usda`。
- 引用 source Prim：`/World/obj_analytical_balance`。实例化时保留完整设备，不单独实例化秤盘。
- 使用米制、Z 向上、9.81 m/s² 重力、GPU Dynamics、GPU Broadphase、TGS、120 Hz。
- 播放前配置根属性 `balance:tabletop_z` 为台面高度，并将设备足部放到台面。
- 机身可搬动；`Instance/Body`、`Instance/WeighingPan`、`Instance/RightTare` 是三个刚体。
  `LoadCell` 固定关节连接机身和秤盘；唯一可动 DOF 为 `RightTarePress`，单位米，范围 0–0.0015。
- 原始连续毛重、滤波净重、皮重分别在根属性 `balance:gross_g`、`balance:net_g`、`balance:tare_g`。
  正式读取前检查 `balance:valid` 和 `balance:stable`。`balance:lcd_readout` 是屏幕文本。
- 默认显示分度 0.1 g，量程 200 g 毛重。TARE 按下后等待稳定去皮；5 秒超时保留旧皮重。
- 设备脚本与两个版本所需的非原生 MDL 模块已在包内。保留 NVIDIA MDL 版权与许可头。
- 承托判断使用姿态、速度和台面高度范围；搬到另一台面需更新高度配置。
  验证不等于机器人抓取资格，不包含 CAL/OFF 等其他按钮功能。

具体资格、源哈希、材质闭包与独立进程报告见 `manifest.json`、`material_closure.json`、`evidence/`。
''')
    archive=out.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(out.rglob('*')):
            if path.is_file():
                z.write(path,str(Path(out.name)/path.relative_to(out)))
    with zipfile.ZipFile(archive) as z:
        if z.testzip():
            raise ValueError('ZIP CRC failure')
    return {'asset':str(out),'zip':str(archive),'asset_sha256':digest,
            'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--report',type=Path,action='append',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--render41-log',type=Path,required=True)
    p.add_argument('--render45-log',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(promote(a.candidate,a.report,a.out,{'isaac41':a.render41_log,'isaac45':a.render45_log}),indent=2))
