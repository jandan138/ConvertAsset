"""Isolated original-scene initialization reproduction; never alters its source."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--init',choices=['omitted','zero','pressed'],required=True)
    a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    report=dict(status='started',pid=os.getpid(),initialization=a.init)
    a.out.write_text(json.dumps(report))
    sys.argv=[sys.argv[0]]
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True,'multi_gpu':False})
    try:
        import numpy as np
        import omni.usd
        try:
            from isaacsim.core.api import World
            from isaacsim.core.prims import SingleArticulation as Articulation
        except ImportError:
            from omni.isaac.core import World
            from omni.isaac.core.articulations import Articulation
        ctx=omni.usd.get_context()
        ctx.open_stage(str(a.scene.resolve()))
        while ctx.get_stage_loading_status()[2]:
            app.update()
        stage=ctx.get_stage()
        stage.SetEditTarget(stage.GetSessionLayer())
        world=World(stage_units_in_meters=1)
        obj=world.scene.add(Articulation('/World/obj_analytical_balance',name='balance'))
        for _ in range(3):
            world.reset()
            if a.init!='omitted':
                index=obj.dof_names.index('RightTarePress')
                obj.set_joint_positions(np.array([0 if a.init=='zero' else .001]),joint_indices=np.array([index]))
            for _ in range(120):
                world.step(render=False)
        report.update(status='passed_this_reproduction',runtime=app.app.get_app_version(),dof_names=obj.dof_names)
    except BaseException:
        import traceback
        report.update(status='failed',exception=traceback.format_exc())
        print(report['exception'],flush=True)
    finally:
        a.out.write_text(json.dumps(report,indent=2))
        print('REPORT',report,flush=True)
        app.close()


if __name__=='__main__':
    main()
