import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
spec=importlib.util.spec_from_file_location('events',Path(__file__).parents[1]/'scripts/sciben_waterbath_recovery_events.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def header(a,b,n):return NS(actor0=a,actor1=b,num_contact_data=n)

def test_reports_count_points_including_zero_impulse_and_ignore_other_actors():
 rows=[header('/tube','/bath',4),header('/bath','/tube',3),header('/robot','/bath',99),header('/tube','/bath',0)]
 assert m.contact_header_count(rows,'/tube','/bath',8192,str)==7
 # Pure stateless count only; sleeping-touch semantics require a live fixture.
 assert m.contact_header_count([],'/tube','/bath',8192,str)==0

def test_bad_or_over_capacity_data_fail_closed():
 for n in [-1,5]:
  with pytest.raises(RuntimeError):m.contact_header_count([header('/tube','/bath',n)],'/tube','/bath',4,str)

def test_patch_keeps_view_creation_and_heating_gate_without_new_lifecycle_state():
 source="    contact=state.repair_contacts.get_contact_data(1/120)\n    count=bounded_contact_count(contact[4],config['contact_capacity'])\n    allowed=heating_gate(count)\n    state.repair_contacts=create_view()\n"
 result=m.patch_source(source)
 assert 'state.repair_contacts=create_view()' in result
 assert 'get_contact_data(1/120)' not in result
 assert 'allowed=heating_gate(count)' in result
 assert 'get_contact_report()' in result
 assert 'subscribe_' not in result

def test_persistent_pairs_sleep_lost_and_late_initialization_fail_closed():
 c=m.PersistentContactCounts('/tube','/bath',8192)
 h=header('/tube','/bath',4);h.collider0='/t';h.collider1='/b';h.type='CONTACT_FOUND'
 assert c.read([h],str,False)==4
 assert c.read([],str,True)==4
 h.type='CONTACT_LOST';h.num_contact_data=0
 assert c.read([h],str,False)==0
 late=m.PersistentContactCounts('/tube','/bath',8192)
 with pytest.raises(RuntimeError,match='uninitialized'):late.read([],str,True)
 assert late.read([],str,False)==0
