from scripts.promote_wangshuai_dynamic_asset_set import qualification_passes


def test_qualification_requires_all_twelve_isaac41_runs() -> None:
    rigid = [
        {"overall_status": "pass", "runtime": {"kit_version": "4.1.0"}}
        for _ in range(9)
    ]
    pbd = [
        {"overall_status": "pass", "runtime": {"kit_version": "4.1.0"}}
        for _ in range(3)
    ]
    assert qualification_passes(rigid, pbd)
    assert not qualification_passes(rigid[:-1], pbd)
    pbd[0]["overall_status"] = "blocked"
    assert not qualification_passes(rigid, pbd)
