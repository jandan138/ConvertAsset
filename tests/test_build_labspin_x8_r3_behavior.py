from pathlib import Path
import ast

SCRIPT = Path(__file__).parents[1] / "scripts/build_labspin_x8_r3_behavior.py"


def test_r3_embeds_behavior_without_external_python_file():
    source = SCRIPT.read_text()
    ast.parse(source)
    assert "omni.graph.scriptnode.ScriptNode" in source
    assert "external_python_required" in source
    assert "db.node.get_prim_path()" in source
    assert "lid_open_button_joint" in source and "rotor_spin_joint" in source
    assert "-1.361356817" in source
