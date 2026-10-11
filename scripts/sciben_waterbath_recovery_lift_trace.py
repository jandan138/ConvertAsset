"""Read-only per-native particle telemetry around unchanged producer lift probe."""
import argparse,hashlib,json,sys
from pathlib import Path


def particle_summary(local,velocities,profile,tolerance):
    import numpy as np
    points=np.asarray(local);pr=np.asarray(profile);radius=np.interp(points[:,2],pr[:,0],pr[:,1]);margin=np.minimum.reduce([radius+tolerance-np.linalg.norm(points[:,:2],axis=1),points[:,2]-(pr[0,0]-tolerance),pr[-1,0]+tolerance-points[:,2]]);bad=np.flatnonzero(margin<0);lowest=int(np.argmin(points[:,2]));chosen=list(dict.fromkeys([lowest]+bad[:32].tolist()))
    return {'outside_count':len(bad),'bad_indices':bad.tolist(),'lowest_index':lowest,'minimum_margin_m':float(margin.min()),'selected_particles':[{'index':int(i),'local_position_m':points[i].tolist(),'local_velocity_m_s':velocities[i].tolist(),'margin_m':float(margin[i])} for i in chosen]}


def main():
    p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--out',required=True);p.add_argument('--seconds',type=float,default=17);a=p.parse_args();out=Path(a.out).resolve();package=Path(a.package).resolve();trace=Path(str(out)+'_particletrace.jsonl');metadata=Path(str(out)+'_instrumentation.json');assert not out.exists();import sciben_waterbath_producer as original
    manifest=json.loads((package/'manifest.json').read_text());source=Path(original.__file__);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();metadata.write_text(json.dumps({'scope':'Diagnostic only; exact original producer.probe with outside_count return unchanged and read-only particle/pose/velocity telemetry. No physical or particle writes introduced. Timing may differ; never erases prior failure.','original_probe_sha256':sha(source),'wrapper_sha256':sha(Path(__file__)),'scene_sha256':sha(package/'scene.usda'),'probe_sha256':sha(package/'probe.usda'),'manifest_sha256':sha(package/'manifest.json'),'trace':str(trace),'seconds':a.seconds,'motion':True},indent=2)+'\n');original_count=original.outside_count
    with trace.open('x') as stream:
        def observed_count(points,profile,tolerance):
            result=original_count(points,profile,tolerance);frame=sys._getframe(1);values=frame.f_locals
            if frame.f_code.co_name=='measure_native' and values.get('label')=='Sample':
                import numpy as np
                q=values['q'];rotation=values['rotation'];stage=values['stage'];vel=np.asarray(stage.GetPrimAtPath(manifest['liquids']['Sample']['points']).GetAttribute('velocities').Get(),dtype=float)@rotation.T;row=particle_summary(points,vel,profile,tolerance);assert row['outside_count']==result;row.update(native_tick=len(values['dt']),container_position=[q.p.x,q.p.y,q.p.z],container_orientation_xyzw=[q.r.x,q.r.y,q.r.z,q.r.w],native_callback='existing post-physics measure_native after update_transformations',velocity_scope='Particle world velocity rotated into body axes; not subtracting container translation/angular velocity.');stream.write(json.dumps(row)+'\n');stream.flush()
            return result
        original.outside_count=observed_count
        try:original.probe(package,out,a.seconds,motion=True,render=False)
        finally:original.outside_count=original_count
if __name__=='__main__':main()
