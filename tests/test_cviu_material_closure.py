import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal/fetch_material_closure.py'
s=importlib.util.spec_from_file_location('material_closure',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_single_slash_uri_and_local_asset():
 assert m.normalize('http:/example.com/Materials/A.mdl')=='https://example.com/Materials/A.mdl'
 assert m.normalize('./Materials/A.mdl') is None

def test_relative_mdl_module_root():
 text='using ..::Templates::GlassWithVolume import GlassWithVolume;\r\nusing ::OmniPBR import OmniPBR;'
 assert m.relative_modules(text)==['..::Templates::GlassWithVolume','::OmniPBR']
 assert m.module_url('https://host/Materials/Base/Glass/A.mdl','..::Templates::GlassWithVolume')=='https://host/Materials/Base/Templates/GlassWithVolume.mdl'


def test_unprefixed_sibling_module_imports():
 text='import GlassUtils::get_color;\nimport GlassUtils::get_volume_absorption;\nimport ::tex::*;'
 assert m.sibling_import_modules(text)==['GlassUtils']
 assert m.module_url('https://host/Materials/Base/Templates/GlassWithVolume.mdl','GlassUtils')=='https://host/Materials/Base/Templates/GlassUtils.mdl'
