# 2026-08-23 Task 11 static asset candidates

`scripts/build_task11_static_assets.py` consumes the source-bound LABSPIN X8
package and the reviewed 18+4 mixed-rack archive. It produces independent
static candidates for the rack, a closed 15 mL SDF liquid container and an r2
centrifuge facade. The r2 facade promotes the source
`LidOpenStaticButton` location to a prismatic button joint and exposes the
existing stop joint as the shutdown button.

The raw archive and source packages are unchanged. Button-to-lid and
shutdown-to-off causality remain pending; no robot or Task 11 success is
claimed. Downstream Isaac Sim 4.1 validation is limited to the composed
Scenario Forge candidate's three eight-second static runs.

Validation: `python -m pytest -q tests/test_build_task11_static_assets.py`
passes. Generated packages live under ignored
`outputs/task11_vr_static_assets_20260823/`.
