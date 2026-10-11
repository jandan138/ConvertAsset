"""Single-variable Sample PBD convergence diagnostic at unchanged native120Hz."""
import argparse,hashlib,json,shutil
from pathlib import Path


def author(stage,iterations):
    from pxr import Sdf
    if not isinstance(iterations,int) or not 1<=iterations<=255:raise ValueError('PhysX PBD iterations must be1..255')
    root='/World';sample=stage.GetPrimAtPath(root+'/WaterbathFluid/SampleSystem');bath=stage.GetPrimAtPath(root+'/WaterbathFluid/BathSystem');attr=sample.GetAttribute('solverPositionIterationCount')
    if attr.Get()!=64 or bath.GetAttribute('solverPositionIterationCount').Get()!=64:raise ValueError('Expected unmodified64-iteration systems')
    if not stage.GetPrimAtPath(root+'/obj_sample_tube/PBDBottomProxy/Floor').IsActive():raise ValueError('Must start from original solidcap with original Floor')
    cap=root+'/obj_sample_tube/RigidSolidBottom/SolidCap';targets=sample.GetRelationship('physics:filteredPairs').GetTargets()
    if len(targets)!=145 or Sdf.Path(cap) not in targets:raise ValueError('Expected original solidcap PBD filtering')
    attr.Set(iterations)
    return {'only_changed_property':str(sample.GetPath())+'.solverPositionIterationCount','before':64,'after':iterations,'Bath_iterations':64,'native_hz':120,'external_substeps':1,'original_PBD_Floor_active':True,'solidcap_still_particle_filtered':True,'geometry_mass_COM_I_offsets_particle_state_CCD_velocity_parameters_unchanged':True}


def build(source,out,iterations):
    from pxr import Usd
    from sciben_waterbath_recovery_bath import invariant_snapshot
    source=Path(source).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);s=Usd.Stage.CreateInMemory();s.GetRootLayer().subLayerPaths=[str(source)];before=invariant_snapshot(s,'/World');audit=author(s,iterations);after=invariant_snapshot(s,'/World');changed=[k for k in before if before[k]!=after[k]];assert changed==['/World/WaterbathFluid/SampleSystem::solverPositionIterationCount'];layer=s.GetRootLayer();layer.subLayerPaths=[];delta=out/'pbd_iterations_delta.usda';layer.Export(str(delta));entry=Usd.Stage.CreateNew(str(out/'scene.usda'));entry.GetRootLayer().subLayerPaths=[str(delta),str(source)];entry.SetDefaultPrim(entry.GetPrimAtPath('/World'));entry.GetRootLayer().Save();shutil.copy2(source.parent/'probe.usda',out/'probe.usda');m=json.loads((source.parent/'manifest.json').read_text());m.update(status='PBD_iterations_diagnostic_pending',PBD_solver_position_iterations={'Sample':iterations,'Bath':64},physical_delta_receipt=str(out/'receipt.json'));(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');audit.update(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),delta=str(delta),delta_sha256=hashlib.sha256(delta.read_bytes()).hexdigest(),generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),attributes_compared=len(before),changed_attributes=changed,qualified=False);(out/'receipt.json').write_text(json.dumps(audit,indent=2)+'\n');return audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--iterations',required=True,type=int);a=p.parse_args();print(json.dumps(build(a.source,a.out,a.iterations),indent=2))
