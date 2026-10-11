import sys,ast
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))

def test_observer_preserves_original_compute_return_and_cleanup():
    from sciben_waterbath_recovery_native_trace import wrap_trace_script
    original='def compute(db):\n    db.calls+=1\n    return 17\ndef cleanup(db):\n    db.cleaned=True\n'
    code=wrap_trace_script(original);assert code.startswith(original)
    scope={};exec(code,scope);seen=[];scope['_wb_diag_emit']=lambda db:seen.append(db.calls)
    db=SimpleNamespace(calls=0,per_instance_state=SimpleNamespace());assert scope['compute'](db)==17;assert seen==[1]
    scope['cleanup'](db);assert db.cleaned

def test_trace_fragment_has_no_physics_or_usd_write_calls():
    from sciben_waterbath_recovery_native_trace import TRACE
    calls=[n.func.attr for n in ast.walk(ast.parse(TRACE)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
    assert not any(v in ['Set','Apply','Define','set_rigid_body_pose','set_joint_positions','set_kinematic_targets','create_simulation_view'] for v in calls)


def test_case_specific_trace_window_and_palms_preserve_source_prefix():
    from sciben_waterbath_recovery_native_trace import wrap_trace_script
    source='def compute(db): return True\ndef cleanup(db): pass\n'
    result=wrap_trace_script(source,1200,2600,True)
    assert result.startswith(source) and '1200<=index<=2600' in result
    assert "for link in ['link6','link7','link8']" in result
