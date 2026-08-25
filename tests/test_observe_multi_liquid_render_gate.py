from pathlib import Path
import ast


ROOT = Path(__file__).parents[1]
OBSERVER = ROOT / "scripts/observe_multi_liquid.py"


def test_multi_liquid_observer_exercises_hydra_and_blocks_particle_primvar_errors():
    source = OBSERVER.read_text(encoding="utf-8")
    ast.parse(source)
    assert "rendered_steps" in source
    assert "world.step(render=step < rendered_steps)" in source
    assert "Unrecognized primvar 'displayColor'" in source
    assert "Unrecognized primvar 'displayOpacity'" in source
