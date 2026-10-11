import sys
from pathlib import Path
from pxr import Sdf, Usd
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from sciben_waterbath_recovery_rim_partition import authored_api_tokens, is_collision_downgrade


def test_preserves_target_runtime_schema_when_local_registry_does_not_know_it():
    stage = Usd.Stage.CreateInMemory()
    prim = stage.DefinePrim('/Body', 'Mesh')
    tokens = ['PhysicsCollisionAPI', 'UnregisteredTargetRuntimeCollisionAPI']
    prim.SetMetadata('apiSchemas', Sdf.TokenListOp.CreateExplicit(tokens))
    assert 'UnregisteredTargetRuntimeCollisionAPI' not in prim.GetAppliedSchemas()
    assert authored_api_tokens(prim) == tokens


def test_native_geometry_downgrade_is_failure_not_an_ignored_warning():
    message = ('[Warning] PhysicsUSD: Parse collision - triangle mesh collision cannot be a part of '
               'a dynamic body, falling back to convexHull approximation: /World/LowerSDF')
    assert is_collision_downgrade(message)
    assert not is_collision_downgrade('[Warning] texture decoder falling back to CPU')
