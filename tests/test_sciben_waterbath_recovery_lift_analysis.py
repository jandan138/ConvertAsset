import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from sciben_waterbath_recovery_lift_analysis import intervals,summarize


def test_intervals_do_not_join_reentry_gap():
    r=intervals([7,8,10,10,11]);assert [(x['first_native_tick'],x['last_native_tick']) for x in r]==[(7,8),(10,11)]


def test_exact_native_duration_not_sparse_snapshot_duration():
    rows=[{'native_tick':i,'bad_indices':[9] if i in [2,3] else [],'outside_count':int(i in [2,3]),'selected_particles':[{'index':9,'local_position_m':[0,0,0],'local_velocity_m_s':[0,0,0]}],'container_position':[0,0,0],'container_orientation_xyzw':[0.,0.,0.,1.]} for i in range(1,5)]
    r=summarize(rows);assert r['outside_native_steps']==2 and r['outside_intervals'][0]['sample_duration_s']==2/120;assert r['all_callback_ticks_consecutive']


def test_bad_ids_beyond_selected_telemetry_keep_intervals():
    r=summarize([{'native_tick':1,'bad_indices':[7],'outside_count':1,'selected_particles':[],'container_position':[0,0,0],'container_orientation_xyzw':[0.,0.,0.,1.]}]);assert r['per_particle']['7']['last_observation'] is None;assert r['per_particle']['7']['intervals'][0]['sample_count']==1
