"""Protect immutable source materials when repairing runtime module lookup."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('formal_mdl_library', ROOT / 'paper/shared/evidence/experiments/13_cviu_formal/prepare_mdl_library.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_library_repairs_copy_and_preserves_source_and_resources(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    original = b'mdl 1.6;\r\nimport ::KooPbr::KooMtl;\r\n'
    (source / 'MI_test.mdl').write_bytes(original)
    (source / 'KooPbr.mdl').write_text('mdl 1.6;\n')
    (source / 'Textures').mkdir()
    (source / 'Textures' / 'example.png').write_bytes(b'unchanged texture fixture')
    alias = tmp_path / 'source_alias'
    alias.symlink_to(source, target_is_directory=True)
    out = tmp_path / 'isolated'
    receipt = module.prepare(alias, out, ROOT / 'scripts/fix_mdl_absolute_imports.py')
    assert (source / 'MI_test.mdl').read_bytes() == original
    assert not (out / 'MI_test.mdl').is_symlink()
    assert b'using .::KooPbr import KooMtl;\r\n' in (out / 'MI_test.mdl').read_bytes()
    assert (out / 'Textures').resolve() == source / 'Textures'
    assert receipt['changed_files'] == 1
    assert (out / 'KooPbr.mdl').read_bytes() == (source / 'KooPbr.mdl').read_bytes()
