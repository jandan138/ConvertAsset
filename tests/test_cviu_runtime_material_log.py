import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('material_log', ROOT / 'paper/shared/evidence/experiments/13_cviu_formal/audit_capture_logs.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_headless_warning_is_not_material_failure(tmp_path):
    log = tmp_path / 'render.log'
    log.write_text('[Error] GLInteropContext::init: carb::windowing is not available\n')
    assert module.inspect_log(log)['material_error_count'] == 0


def test_mdl_compiler_failure_blocks_even_if_capture_succeeded(tmp_path):
    log = tmp_path / 'render.log'
    log.write_text("[Error] MDLC comp error: C120 could not find module '::KooPbr'\ncaptured 0 ok\n")
    result = module.inspect_log(log)
    assert result['status'] == 'FAIL'
    assert result['material_errors'][0]['line'] == 1
